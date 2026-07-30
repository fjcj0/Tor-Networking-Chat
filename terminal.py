import socks
import threading
import json
import os
from colorama import init
from crypto_chat import encrypt_message, decrypt_message
from prompt_toolkit.application import Application, get_app
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import (
    HSplit,
    Window,
    ScrollablePane
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets import (
    TextArea,
    Frame
)
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.dimension import Dimension
init(autoreset=True)
server = None
username = ""
chat_lines = []
chat_control = FormattedTextControl(
    text=""
)
chat_window = Window(
    content=chat_control,
    wrap_lines=True
)
scroll = ScrollablePane(
    chat_window,
    height=Dimension(
        preferred=20
    )
)
def add_message(text):
    chat_lines.append(text)
    if len(chat_lines) > 500:
        chat_lines.pop(0)
    chat_control.text = "\n".join(
        chat_lines
    )
    try:
        get_app().invalidate()
    except:
        pass
def receive_messages(sock):
    while True:
        try:
            data = sock.recv(8192)
            if not data:
                add_message(
                    "Disconnected from server."
                )
                break
            msg = json.loads(
                decrypt_message(data)
            )
            text = (
                f"[{msg['time']}] "
                f"{msg['sender']}: "
                f"{msg['message']}"
            )
            add_message(text)
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
        server.send(
            encrypt_message(msg)
        )
    except:
        add_message(
            "Send failed."
        )
    buf.text = ""
input_field = TextArea(
    height=1,
    prompt="> ",
    multiline=False
)
kb = KeyBindings()
@kb.add("enter")
def enter(event):
    send_message(
        input_field
    )
@kb.add("up")
def scroll_up(event):
    try:
        scroll.vertical_scroll -= 3
    except:
        pass
@kb.add("down")
def scroll_down(event):
    try:
        scroll.vertical_scroll += 3
    except:
        pass
root_container = HSplit(
    [
        Frame(
            scroll,
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

    s.recv(1024)
    s.send(
        encrypt_message(username)
    )
    s.recv(1024)
    s.send(
        encrypt_message(password)
    )
    add_message(
        "Waiting for approval..."
    )
    while True:
        resp = decrypt_message(
            s.recv(1024)
        )
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