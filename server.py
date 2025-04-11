import socket
import json
import threading
import os
import base64

from db import MiniDB  # Припускаємо, що клас MiniDB знаходиться у файлі db.py

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

# Завантажуємо зображення у БД (якщо вона порожня)
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

@command("get_next")
def cmd_next(user, request):
    current_index = user_positions.get(user, -1)
    new_index = current_index + 1
    if new_index >= len(images.data):
        new_index = 0  # циклічний перехід
    user_positions[user] = new_index
    record = images.data[new_index]
    image_path = record['path']
    try:
        with open(image_path, 'rb') as img_file:
            image_bytes = img_file.read()
    except Exception as e:
        return {"status": "error", "error": f"Не вдалося відкрити зображення: {image_path}"}
    b64_data = base64.b64encode(image_bytes).decode('utf-8')

    # Шукаємо оцінку для даної картинки від цього користувача
    current_rating = 0
    for r in ratings.data:
        # Припускаємо, що r - це словник з полями 'ip', 'image' та 'rating'
        if r['ip'] == user and int(r['image']) == record['id']:
            current_rating = int(r['rating'])
            break

    return {"status": "ok", "action": "get_next", "image": b64_data,
            "id": record['id'], "path": image_path, "current_rating": current_rating}

@command("get_prev")
def cmd_prev(user, request):
    current_index = user_positions.get(user, 0)
    new_index = current_index - 1
    if new_index < 0:
        new_index = len(images.data) - 1  # переходимо до останнього зображення
    user_positions[user] = new_index
    record = images.data[new_index]
    image_path = record['path']
    try:
        with open(image_path, 'rb') as img_file:
            image_bytes = img_file.read()
    except Exception as e:
        return {"status": "error", "error": f"Не вдалося відкрити зображення: {image_path}"}
    b64_data = base64.b64encode(image_bytes).decode('utf-8')

    # Пошук оцінки для даної картинки від цього користувача
    current_rating = 0
    for r in ratings.data:
        if r['ip'] == user and int(r['image']) == record['id']:
            current_rating = int(r['rating'])
            break

    return {"status": "ok", "action": "get_prev", "image": b64_data,
            "id": record['id'], "path": image_path, "current_rating": current_rating}

@command("rate")
def cmd_rate(user, request):
    image_id = request.get("image")
    rating_value = request.get("rating")
    if image_id is None or rating_value is None:
        return {"status": "error", "error": "Некоректний запит: відсутні поля image або rating"}
    ratings.add((user, image_id, rating_value))
    ratings.save_to_file(RATINGS_DB)
    return {"status": "ok", "action": "rate"}

def handle_client(client_socket, address):
    user_id = address[0]
    try:
        # Читаємо один запит
        data = client_socket.recv(4096).decode()
        if not data:
            return
        request = json.loads(data)
        action = request.get("action")
        if action in commands:
            response = commands[action](user_id, request)
        else:
            response = {"status": "error", "error": "Невідома команда"}
        # Відправляємо відповідь
        client_socket.send(json.dumps(response).encode())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()  # Закриваємо з’єднання після відповіді

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
