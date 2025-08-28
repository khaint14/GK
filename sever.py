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
# Validate
# =====================
def is_valid_phone(phone):
    return bool(re.match(r'^\d{10}$', phone))
def is_valid_name(name):
    return bool(re.match(r'^[A-Za-z\s]{2,}$', name))
def generate_ticket_id():
    return str(uuid.uuid4())[:8]