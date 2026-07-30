import socks
import threading
import json
import os
from colorama import init
from crypto_chat import encrypt_message, decrypt_message
from prompt_toolkit.application import Application, get_app
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.widgets import TextArea, Frame
from prompt_toolkit.key_binding import KeyBindings
init(autoreset=True)
server = None
username = ""
chat_lines = []
def recv_full(sock):
    data = b""
    while True:
        part = sock.recv(4096)
        if not part:
            break
        data += part
        if len(part) < 4096:
            break
    return data
chat_window = TextArea(
    text="",
    focusable=False,
    scrollbar=True,
    wrap_lines=True,
    read_only=True
)
input_field = TextArea(
    height=1,
    prompt="> ",
    multiline=False
)
def add_message(text):
    chat_lines.append(text)
    if len(chat_lines) > 500:
        chat_lines.pop(0)
    chat_window.text = "\n".join(chat_lines)
    chat_window.buffer.cursor_position = len(
        chat_window.text
    )
    try:
        get_app().invalidate()
    except:
        pass
def receive_messages(sock):
    while True:
        try:
            data = recv_full(sock)
            if not data:
                add_message(
                    "Disconnected from server."
                )
                break
            decrypted = decrypt_message(data)
            try:
                msg = json.loads(decrypted)
                text = (
                    f"[{msg['time']}] "
                    f"{msg['sender']}: "
                    f"{msg['message']}"
                )
                add_message(text)
            except:
                add_message(decrypted)
        except Exception as e:
            add_message(
                f"Connection error: {e}"
            )
            break
def send_message(buf):
    global server
    msg = buf.text.strip()
    if not msg:
        return
    if msg == "/exit":
        try:
            server.close()
        except:
            pass
        os._exit(0)
    try:
        server.sendall(
            encrypt_message(msg)
        )
    except Exception as e:
        add_message(
            f"Send error: {e}"
        )
    buf.text = ""
kb = KeyBindings()
@kb.add("enter")
def enter(event):
    send_message(
        input_field
    )
root_container = HSplit(
    [
        Frame(
            chat_window,
            title="BITX CHAT"
        ),
        Frame(
            input_field
        )
    ]
)
app = Application(
    layout=Layout(
        root_container
    ),
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
    server_onion = input(
        "Server: "
    ).strip()
    port = int(
        input(
            "Port: "
        )
    )
    s = socks.socksocket()
    s.set_proxy(
        socks.SOCKS5,
        "127.0.0.1",
        9050
    )
    s.connect(
        (
            server_onion,
            port
        )
    )
    server = s
    username = input(
        "Username: "
    ).strip()
    password = input(
        "Password: "
    ).strip()
    recv_full(s)
    s.sendall(
        encrypt_message(username)
    )
    recv_full(s)
    s.sendall(
        encrypt_message(password)
    )
    add_message(
        "Waiting for approval..."
    )
    while True:
        data = recv_full(s)
        if not data:
            add_message(
                "Server closed connection."
            )
            return
        resp = decrypt_message(data)
        if "accepted" in resp.lower():
            add_message(
                "Connected."
            )
            break
        if "rejected" in resp.lower():
            add_message(
                "Rejected."
            )
            return
    start_receiver(s)
    app.run()
if __name__ == "__main__":
    main()