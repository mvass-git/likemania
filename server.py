import socket
import json
import threading
import os
from db import MiniDB
import base64


IMAGES_FOLDER = 'images'
IMAGES_DB = 'images.txt'
RATINGS_DB = 'ratings.txt'

CLEAN_ON_START = False
if CLEAN_ON_START:
    open(IMAGES_DB, 'w').close()
    open(RATINGS_DB, 'w').close()

images = MiniDB(['id','path'], IMAGES_DB)
ratings = MiniDB(['ip','image','rating'], RATINGS_DB)



def scan_image(path):
    result = []
    for p in os.listdir(path):
        full_path = os.path.join(path, p)
        if (p.lower().endswith('.png') or p.lower().endswith('.jpg')) and os.path.isfile(full_path):
            result.append(full_path)
    return result

if not images.data:
    image_list = scan_image(IMAGES_FOLDER)
    id = 1
    for img_path in image_list:
        images.add((id, img_path))
        id +=1
images.save_to_file(IMAGES_DB)

user_positions = {}

HOST, PORT = "0.0.0.0", 9999



def update_user_position(user, shift, default_value):
    total = len(images.data)
    current = user_positions.get(user, default_value)
    new_index = (current + shift)% total
    user_positions[user]=new_index
    return new_index

def get_image_response(user, record, action):
    image_path = record['path']
    try:
        with open(image_path, 'rb') as img_file:
            image_bytes = img_file.read()
    except Exception as e:
        return {'status':"error", "error":f"{e}"}
    b64_data = base64.b64encode(image_bytes).decode('utf-8')
    current_rating = 0
    for r in ratings.data:
        if r["ip"] == user and r['image'] == record['id']:
            current_rating = int(r["rating"])
    
    msg ={
        "status":"ok",
        "action":action,
        "image":b64_data,
        "id":record['id'],
        "path":image_path,
        "current_rating":current_rating
    }

    print(msg)
    return msg

commands = {}
def command(action):
    def decorator(func):
        commands[action] = func
        return func
    return decorator

@command("get_next")
def cmd_next(user, request):
    index = update_user_position(user, 1, 0)
    record = images.data[index]
    return get_image_response(user, record, "get_next")

@command("get_prev")
def cmd_prev(user, request):
    index = update_user_position(user, -1, 0)
    record = images.data[index]
    return get_image_response(user, record, "get_prev")

@command("rate")
def cmd_rate(user, request):
    image_id = request.get('image')
    rating_value = request.get("rating")
    if image_id is None or rating_value is None:
        return {
            "status":"error",
            "error":"incorrect request"
        }
    rating_found = False
    for r in ratings.data:
        if r['ip'] == user and int(r['image']) == int(image_id):
            r['rating'] = rating_value
            rating_found = True
            break
    if not rating_found:
        ratings.add((user, image_id, rating_value))
    return {"status":"ok", "action":"rate"}

def handle_client(client_socket, address):
    user_id = address[0]
    try:
        data = client_socket.recv(1024).decode()
        if not data:
            return
        request = json.loads(data)
        action = request.get("action")
        #handling commands
        if action in commands:
            response = commands[action](user_id, request)
        else:
            response = None
        client_socket.send(json.dumps(response).encode())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(10)
    print(f"server is listening on port {PORT}")
    while True:
        client_socket, addr = server.accept()
        print(f"Connected client: {addr}")
        threading.Thread(target=handle_client,args=(client_socket, addr), daemon=True).start()

if __name__ == '__main__':
    start_server()