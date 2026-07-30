import socks
import threading
import json
from colorama import init
from crypto_chat import encrypt_message, decrypt_message
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.widgets import TextArea, Frame
from prompt_toolkit.key_binding import KeyBindings
import os
init(autoreset=True)
server = None
username = ""
chat_lines = []
def add_message(text):
    chat_lines.append(text)
    if len(chat_lines) > 200:
        chat_lines.pop(0)
    chat_window.text = "\n".join(chat_lines)
def receive_messages(sock):
    while True:
        try:
            data = sock.recv(8192)
            if not data:
                add_message("Disconnected from server.")
                break
            msg = json.loads(decrypt_message(data))
            text = f"[{msg['time']}] {msg['sender']}: {msg['message']}"
            add_message(text)
        except Exception:
            add_message("Connection error.")
            break
def send_message(buf):
    global server
    msg = buf.text.strip()
    if msg == "/exit":
        try:
            print("Exiting chat...")
            server.close()
        except:
            pass
        os._exit(0)
        return
    if msg:
        server.send(encrypt_message(msg))
    buf.text = "" 
chat_window = TextArea(
    text="",
    focusable=False,
    scrollbar=True,
    wrap_lines=True
)
input_field = TextArea(
    height=1,
    prompt="> ",
    multiline=False
)
def on_enter(event):
    send_message(input_field)
kb = KeyBindings()
kb.add("enter")(on_enter)
root_container = HSplit([
    Frame(chat_window, title="BITX CHAT"),
    Frame(input_field)
])
app = Application(
    layout=Layout(root_container),
    key_bindings=kb,
    full_screen=True
)
def start_receiver(sock):
    threading.Thread(
        target=receive_messages,
        args=(sock,),
        daemon=True
    ).start()
def main():
    global server, username
    server_onion = input("Server: ").strip()
    port = int(input("Port: ").strip())
    s = socks.socksocket()
    s.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
    s.connect((server_onion, port))
    server = s
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    s.recv(1024)
    s.send(encrypt_message(username))
    s.recv(1024)
    s.send(encrypt_message(password))
    print("Waiting for approval...")
    while True:
        resp = decrypt_message(s.recv(1024))
        if "accepted" in resp.lower():
            print("Accepted!")
            break
        if "rejected" in resp.lower():
            print("Rejected")
            return
    start_receiver(s)
    app.run()
if __name__ == "__main__":
    main()