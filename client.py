import threading
import socks
import json
import os
from crypto_chat import encrypt_message, decrypt_message
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox
)
from PySide6.QtCore import Signal, QObject
server = None
username = ""
class Receiver(QObject):
    message_received = Signal(str)
receiver = Receiver()
def receive_messages(sock):
    while True:
        try:
            data = sock.recv(8192)
            if not data:
                receiver.message_received.emit(
                    "Disconnected from server"
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
            receiver.message_received.emit(
                text
            )
        except Exception:
            receiver.message_received.emit(
                "Connection error"
            )
            break
def start_receiver(sock):
    thread = threading.Thread(
        target=receive_messages,
        args=(sock,),
        daemon=True
    )
    thread.start()
class ConnectWindow(QWidget):
    connected = Signal()
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "BITX CHAT LOGIN"
        )
        self.resize(
            420,
            350
        )
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText(
            "Server onion address"
        )
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText(
            "Port"
        )
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(
            "Username"
        )
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(
            "Password"
        )
        self.password_input.setEchoMode(
            QLineEdit.Password
        )
        self.connect_btn = QPushButton(
            "Connect"
        )
        inputs = [
            self.server_input,
            self.port_input,
            self.username_input,
            self.password_input
        ]
        for field in inputs:
            field.setMinimumHeight(40)
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(
            60,
            50,
            60,
            50
        )
        layout.addWidget(
            self.server_input
        )
        layout.addWidget(
            self.port_input
        )
        layout.addWidget(
            self.username_input
        )
        layout.addWidget(
            self.password_input
        )
        layout.addSpacing(10)
        layout.addWidget(
            self.connect_btn
        )
        self.setLayout(
            layout
        )
        self.setStyleSheet("""
            QLineEdit {
                border: 1px solid #444;
                border-radius: 10px;
                padding-left: 12px;
                padding-right: 12px;
                font-size: 14px;
            }
        """)
        self.connect_btn.clicked.connect(
            self.connect_server
        )
    def connect_server(self):
        global server, username
        try:
            onion = self.server_input.text().strip()
            port = int(
                self.port_input.text()
            )
            username = (
                self.username_input.text()
                .strip()
            )
            password = (
                self.password_input.text()
            )
            s = socks.socksocket()
            s.set_proxy(
                socks.SOCKS5,
                "127.0.0.1",
                9050
            )
            s.connect(
                (
                    onion,
                    port
                )
            )
            s.recv(1024)
            s.send(
                encrypt_message(username)
            )
            s.recv(1024)
            s.send(
                encrypt_message(password)
            )
            response = decrypt_message(
                s.recv(1024)
            )
            if "accepted" in response.lower():
                server = s
                start_receiver(
                    s
                )
                self.connected.emit()
                self.close()
            else:
                QMessageBox.warning(
                    self,
                    "Login Failed",
                    "Server rejected login"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Connection Error",
                str(e)
            )
class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "BITX CHAT"
        )
        self.resize(
            700,
            500
        )
        self.chat_box = QTextEdit()
        self.chat_box.setReadOnly(
            True
        )
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText(
            "Write message..."
        )
        self.input_box.setStyleSheet("""
            QLineEdit {
               border: 1px solid #444;
               border-radius: 10px;
               padding-left: 15px;
               padding-right: 15px;
               padding-top: 8px;
               padding-bottom: 8px;
               font-size: 14px;
            }
        """)
        self.send_btn = QPushButton(
            "Send"
        )
        self.exit_btn = QPushButton(
            "Exit"
        )
        bottom = QHBoxLayout()
        bottom.addWidget(
            self.input_box
        )
        bottom.addWidget(
            self.send_btn
        )
        layout = QVBoxLayout()
        layout.addWidget(
            self.chat_box
        )
        layout.addLayout(
            bottom
        )
        layout.addWidget(
            self.exit_btn
        )
        self.setLayout(
            layout
        )
        self.send_btn.clicked.connect(
            self.send_message
        )
        self.input_box.returnPressed.connect(
            self.send_message
        )
        self.exit_btn.clicked.connect(
            self.close_app
        )
        receiver.message_received.connect(
            self.add_message
        )
    def add_message(self, msg):
        self.chat_box.append(
            msg
        )
    def send_message(self):
        global server
        msg = (
            self.input_box.text()
            .strip()
        )
        if not msg:
            return
        if msg == "/exit":
            self.close_app()
            return
        try:
            server.send(
                encrypt_message(msg)
            )
            self.input_box.clear()
        except:
            self.add_message(
                "Send failed"
            )
    def close_app(self):
        global server
        try:
            server.close()
        except:
            pass
        os._exit(0)
if __name__ == "__main__":
    app = QApplication([])
    login = ConnectWindow()
    chat = ChatWindow()
    def show_chat():
        chat.show()
    login.connected.connect(
        show_chat
    )
    login.show()
    app.exec()