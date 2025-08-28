import socket
import json
import tkinter as tk
from tkinter import messagebox, ttk
import re
import pyperclip

SERVER_HOST = 'localhost'
SERVER_PORT = 5555

def send_json(sock, obj):
    data = json.dumps(obj) + '\n'
    sock.sendall(data.encode('utf-8'))

def recv_json(sock, buffer):
    while '\n' not in buffer:
        chunk = sock.recv(4096).decode('utf-8')
        if not chunk:
            return None, buffer
        buffer += chunk
    line, rest = buffer.split('\n', 1)
    return json.loads(line), rest
