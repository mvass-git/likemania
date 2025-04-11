import socket
import json
import threading
import os
import base64

from db import MiniDB  # Припускаємо, що клас MiniDB визначено у файлі db.py

IMAGES_FOLDER = 'images'
IMAGES_DB = 'images.txt'
RATINGS_DB = 'ratings.txt'
HOST, PORT = "0.0.0.0", 9999

commands = {}

# Якщо потрібно очистити файли при запуску сервера
CLEAN_ON_START = False
if CLEAN_ON_START:
    open(IMAGES_DB, 'w').close()
    open(RATINGS_DB, 'w').close()

# Ініціалізація баз даних
images = MiniDB(('id', 'path'), IMAGES_DB)
ratings = MiniDB(('ip', 'image', 'rating'), RATINGS_DB)

def scan_images(path):
    result = []
    for p in os.listdir(path):
        full_path = os.path.join(path, p)
        if (p.lower().endswith('.png') or p.lower().endswith('.jpg')) and os.path.isfile(full_path):
            result.append(full_path)
    return result

# Якщо база зображень порожня – скануємо папку та зберігаємо дані
if not images.data:
    image_list = scan_images(IMAGES_FOLDER)
    for idx, img_path in enumerate(image_list):
        images.add((idx, img_path))
images.save_to_file(IMAGES_DB)

# Глобальний словник для зберігання позиції зображення для кожного користувача (за IP)
user_positions = {}

def command(action):
    def decorator(func):
        commands[action] = func
        return func
    return decorator

def update_user_position(user, shift, default_value):
    """
    Оновлює позицію користувача з урахуванням циклічного перемикання.
    """
    total = len(images.data)
    current = user_positions.get(user, default_value)
    new_index = (current + shift) % total
    user_positions[user] = new_index
    return new_index

def get_image_response(user, record, action):
    """
    Формує відповідь для запиту зображення:
    - Зчитує файл з зображенням та кодує його в base64
    - Повертає поточну оцінку (якщо вона задана)
    """
    image_path = record['path']
    try:
        with open(image_path, 'rb') as img_file:
            image_bytes = img_file.read()
    except Exception as e:
        return {"status": "error", "error": f"Не вдалося відкрити зображення: {image_path}"}
    
    b64_data = base64.b64encode(image_bytes).decode('utf-8')

    current_rating = 0
    for r in ratings.data:
        # Якщо для даного користувача та зображення вже встановлено оцінку, її повертаємо
        if r['ip'] == user and r['image'] == record['id']:
            current_rating = int(r['rating'])
            break

    return {
        "status": "ok",
        "action": action,
        "image": b64_data,
        "id": record['id'],
        "path": image_path,
        "current_rating": current_rating
    }

@command("get_next")
def cmd_next(user, request):
    index = update_user_position(user, shift=1, default_value=-1)
    record = images.data[index]
    return get_image_response(user, record, "get_next")

@command("get_prev")
def cmd_prev(user, request):
    index = update_user_position(user, shift=-1, default_value=0)
    record = images.data[index]
    return get_image_response(user, record, "get_prev")

@command("rate")
def cmd_rate(user, request):
    image_id = request.get("image")
    rating_value = request.get("rating")
    if image_id is None or rating_value is None:
        return {"status": "error", "error": "Некоректний запит: відсутні поля image або rating"}
    # Перевіряємо, чи вже існує запис оцінки для даного користувача та картинки
    rating_found = False
    for r in ratings.data:
        if r['ip'] == user and int(r['image']) == int(image_id):
            r['rating'] = rating_value  # оновлюємо оцінку
            rating_found = True
            break
    if not rating_found:
        ratings.add((user, image_id, rating_value))
    ratings.save_to_file(RATINGS_DB)
    return {"status": "ok", "action": "rate"}

def handle_client(client_socket, address):
    user_id = address[0]
    try:
        data = client_socket.recv(4096).decode()
        if not data:
            return
        request = json.loads(data)
        action = request.get("action")
        if action in commands:
            response = commands[action](user_id, request)
        else:
            response = {"status": "error", "error": "Невідома команда"}
        client_socket.send(json.dumps(response).encode())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(10)
    print(f"Сервер слухає порт {PORT}")
    while True:
        client_socket, addr = server.accept()
        print(f"Підключено клієнта: {addr}")
        threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()

if __name__ == '__main__':
    start_server()
