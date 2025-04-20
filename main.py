from kivy.app import App

from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage

import socket
import json
import threading
import base64
import os
import io


HOST, PORT = "127.0.0.1", 9999

def send_request(action, data, callback):
    def worker():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            request = {"action":action}
            if data:
                request.update(data)
            print('preloopa')
            s.sendall(json.dumps(request).encode())
            print('zaaaloopa')
            response_data = b""
            while True:
                print('prezaloopa')
                chunk = s.recv(4096)
                print('zaloopa')
                if not chunk:
                    break
                response_data += chunk
            response = json.loads(response_data.decode())
            print(response)
        except Exception as e:
            print(e)
            response = {"status":"error", "error":f"{e}"}
        finally:
            s.close()
        Clock.schedule_once(lambda dt: callback(response))
    threading.Thread(target=worker, daemon=True).start()


class Rate(BoxLayout):
    def __init__(self):
        super().__init__()
        self.orientation = 'vertical'
        btnBox=BoxLayout()
        lbl_title = Label(text="Оцініть фото", font_size=32, halign="center", size_hint=[1,0.1])

        self.buttons = []
        self.img = Image(source="photos/photo_2025-03-22_12-47-05.jpg")

        self.add_widget(lbl_title)
        self.add_widget(self.img)

        for i in range(5):
            btn = Button(text=str(i+1), background_normal="star0.png", color=[0,0,0,0], background_down="star0.png")
            self.buttons.append(btn)
            btnBox.add_widget(btn)
            btn.bind(on_press=self.rating)
        self.add_widget(btnBox)
        self.request_image("get_next")
    
    def rating(self, btn):
        index = int(btn.text) - 1
        for i in range(len(self.buttons)):
            if i <= index:
                self.buttons[i].background_normal = "star1.png"
                self.buttons[i].background_down = "star1.png"
            else:
                self.buttons[i].background_normal = "star0.png"
                self.buttons[i].background_down = "star0.png"
    
    def on_rate(self, btn):
        if self.current_image_id in None or self.current_rating == 0:
            print("no image or no rating")
            return
        data = {"image":self.current_image_id, "rating":self.current_rating}
        send_request("rate", data, self.on_rate_response)
    
    def on_rate_response(self, response):
        if response.get("status") == 'ok':
            print('rating sent')
        else:
            print("error", response.get('error'))

    def request_image(self, action):
        send_request(action, None, self.on_image_response)
    
    def on_prev(self, btn):
        self.request_image("get_prev")
    
    def on_next(self, btn):
        self.request_image("get_next")

    def on_image_response(self, response):
        if response.get("status") == 'ok':
            b64_data = response.get('image')
            image_bytes = base64.b64decode(b64_data)
            self.current_image_id = response.get('id')
            self.current_image_path = response.get('path')
            ext = "png"
            if self.current_image_path:
                ext = os.path.splitext(self.current_image_path)[1][1:].lower()
            data_stream = io.BytesIO(image_bytes)
            core_image = CoreImage(data_stream, ext=ext)
            self.img.texture = core_image.texture
            current_rating = response.get("current_rating", 0)
            self.current_rating = current_rating

            for i, star in enumerate(self.buttons):
                if i < current_rating:
                    star.background_normal = "star1.png"
                    star.background_down = "start1.png"
                else:
                    star.background_normal = "star0.png"
                    star.background_down = "start0.png"

    


class LikeApp(App):
    def build(self):
        self.mainBox = BoxLayout(orientation='vertical')
        rate=Rate()
        self.mainBox.add_widget(rate)
        return self.mainBox


LikeApp().run()