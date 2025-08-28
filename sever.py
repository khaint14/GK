import socket
import json
import re
from datetime import datetime
import uuid
import threading

# =====================
# Dữ liệu chuyến chung
# =====================
trips = {
    'BINH DINH -> HCM': {'total_seats': 20, 'booked_seats': {}},
    'HCM -> BINH DINH': {'total_seats': 20, 'booked_seats': {}},
    'DAK LAK -> HCM': {'total_seats': 20, 'booked_seats': {}},
    'HCM -> DAK LAK': {'total_seats': 20, 'booked_seats': {}},
}
# =====================
# Helper gửi/nhận JSON
# =====================
def send_json(sock, obj):
    data = json.dumps(obj) + "\n"
    sock.sendall(data.encode("utf-8"))

def recv_json(sock, buffer):
    while "\n" not in buffer:
        chunk = sock.recv(4096).decode("utf-8")
        if not chunk:
            return None, buffer
        buffer += chunk
    line, rest = buffer.split("\n", 1)
    return json.loads(line), rest

# =====================
# Validate
# =====================
def is_valid_phone(phone):
    return bool(re.match(r'^\d{10}$', phone))
def is_valid_name(name):
    return bool(re.match(r'^[A-Za-z\s]{2,}$', name))
def generate_ticket_id():
    return str(uuid.uuid4())[:8]

def handle_client(client_sock, addr):
    buffer = ""
    client_id = str(uuid.uuid4())  # ID duy nhất cho client
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [+] Client {client_id} ({addr}) kết nối") 

    try:
        #Dieu kien dung
        while True:
            req, buffer = recv_json(client_sock, buffer)
            if req is None:
                if buffer == "":
                    break
                else:
                    continue

            cmd = req.get("command")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            #get id
            if cmd == "get_client_id":
                send_json(client_sock, {"status": "success", "client_id": client_id})

            elif cmd == "view_trips":
                available = {
                    t: info['total_seats'] - len(info['booked_seats'])
                    for t, info in trips.items()
                }
                send_json(client_sock, {"status": "success", "trips": available})
                
    except Exception as e:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [!] Lỗi với client {client_id} ({addr}): {e}")
    finally:
        client_sock.close()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [-] Client {client_id} ({addr}) ngắt kết nối")

#chay sever
def start_server(host='localhost', port=5555):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen(5)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Server chạy tại {host}:{port}")


    # kiem tra ngoai le - Kim Ngan
    try:
        while True:
            client_sock, addr = server_sock.accept()
            # Start a new thread to handle the client
            client_thread = threading.Thread(target=handle_client, args=(client_sock, addr))
            client_thread.start()
    except KeyboardInterrupt:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tắt server.")
    finally:
        server_sock.close()

if __name__ == "__main__":
    start_server()
