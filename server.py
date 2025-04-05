import socket
import json
import threading
import os

IMAGES_FOLDER = 'images'
IMAGES_DB = 'images.txt'
RATINGS_DB = 'ratings.txt'

HOST, PORT = "0.0.0.0", 9999

commands = {}

def command(action):
    def decorator(func):
        commands[action] = func
        return func
    return decorator

@command("get_next")
def cmd_next(user, request):
    pass

@command("rate")
def cmd_rate(user, request):
    pass

def handle_client(client_socket, address):
    user_id = address[0]
    try:
        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            request = json.loads(data)
            action = request.get("action")
            #handling commands: rate, get_next
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
        #thread

if __name__ == '__main__':
    start_server()