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

            elif cmd == "get_seats":
                trip_id = req.get("trip_id")
                only_mine = req.get("only_mine", False)
                if trip_id in trips:
                    if only_mine:
                        booked = {int(s): info for s, info in trips[trip_id]['booked_seats'].items()
                                  if info['owner_id'] == client_id}
                    else:
                        booked = {int(s): info for s, info in trips[trip_id]['booked_seats'].items()}
                    send_json(client_sock, {"status": "success", "booked_seats": booked})
                else:
                    send_json(client_sock, {"status": "error", "message": "Chuyến không tồn tại"})

            elif cmd == "book_seat":
                trip_id = req.get("trip_id")
                seat_num = req.get("seat_num")
                user_info = req.get("user_info", {})
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] Client {client_id} ({addr}) đặt ghế {seat_num} trên chuyến {trip_id}")

                if trip_id not in trips:
                    send_json(client_sock, {"status": "error", "message": "Chuyến không tồn tại"})
                    print(f"[{timestamp}] Client {client_id} ({addr}) lỗi: Chuyến {trip_id} không tồn tại")
                elif not is_valid_name(user_info.get("name", "")):
                    send_json(client_sock, {"status": "error", "message": "Tên không hợp lệ"})
                    print(f"[{timestamp}] Client {client_id} ({addr}) lỗi: Tên không hợp lệ")
                elif not is_valid_phone(user_info.get("phone", "")):
                    send_json(client_sock, {"status": "error", "message": "SĐT không hợp lệ"})
                    print(f"[{timestamp}] Client {client_id} ({addr}) lỗi: SĐT không hợp lệ")
                elif seat_num < 1 or seat_num > trips[trip_id]['total_seats']:
                    send_json(client_sock, {"status": "error", "message": "Số ghế không hợp lệ"})
                    print(f"[{timestamp}] Client {client_id} ({addr}) lỗi: Ghế {seat_num} không hợp lệ")
                elif str(seat_num) in trips[trip_id]['booked_seats']:
                    send_json(client_sock, {"status": "error", "message": "Ghế đã được đặt"})
                    print(f"[{timestamp}] Client {client_id} ({addr}) lỗi: Ghế {seat_num} trên chuyến {trip_id} đã được đặt")
                else:
                    tid = generate_ticket_id()
                    trips[trip_id]['booked_seats'][str(seat_num)] = {
                        "user_info": user_info,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "ticket_id": tid,
                        "owner_id": client_id
                    }
                    send_json(client_sock, {"status": "success", "message": f"Đặt vé thành công! Mã vé: {tid}"})
                    print(f"[{timestamp}] Client {client_id} ({addr}) đặt ghế {seat_num} trên chuyến {trip_id} thành công, mã vé: {tid}") 

            elif cmd == "get_booking_info":
                trip_id = req.get("trip_id")
                seat_num = req.get("seat_num")
                if trip_id in trips and str(seat_num) in trips[trip_id]['booked_seats']:
                    send_json(client_sock, {"status": "success", "info": trips[trip_id]['booked_seats'][str(seat_num)]})
                else:
                    send_json(client_sock, {"status": "error", "message": "Không tìm thấy thông tin vé"}) 


            elif cmd == "cancel_booking":
                trip_id = req.get("trip_id")
                seat_num = req.get("seat_num")
                ticket_id = req.get("ticket_id")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] Client {client_id} ({addr}) hủy ghế {seat_num} trên chuyến {trip_id}, mã vé: {ticket_id}")
                if trip_id in trips and str(seat_num) in trips[trip_id]['booked_seats']:
                    booking = trips[trip_id]['booked_seats'][str(seat_num)]
                    if booking['ticket_id'] != ticket_id:
                        send_json(client_sock, {"status": "error", "message": "Mã vé sai"})
                        print(f"[{timestamp}] Client {client_id} ({addr}) lỗi: Mã vé sai cho ghế {seat_num} trên chuyến {trip_id}")
                    elif booking['owner_id'] != client_id:
                        send_json(client_sock, {"status": "error", "message": "Bạn không thể hủy vé của người khác"})
                        print(f"[{timestamp}] Client {client_id} ({addr}) lỗi: Không thể hủy vé của người khác cho ghế {seat_num} trên chuyến {trip_id}")
                    else:
                        del trips[trip_id]['booked_seats'][str(seat_num)]
                        send_json(client_sock, {"status": "success", "message": "Hủy vé thành công"})
                        print(f"[{timestamp}] Client {client_id} ({addr}) hủy ghế {seat_num} trên chuyến {trip_id} thành công")
                else:
                    send_json(client_sock, {"status": "error", "message": "Không tìm thấy vé"})
                    print(f"[{timestamp}] Client {client_id} ({addr}) lỗi: Không tìm thấy vé cho ghế {seat_num} trên chuyến {trip_id}")

            else:
                send_json(client_sock, {"status": "error", "message": "Lệnh không hợp lệ"})
                print(f"[{timestamp}] Client {client_id} ({addr}) lỗi: Lệnh không hợp lệ - {cmd}")

                     
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
