import socket
import json
import threading
import base64
import io
import os

from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage

# Встановлюємо адресу сервера (за потребою змініть)
HOST, PORT = "127.0.0.1", 9999

def send_request(action, data, callback):
    """
    Встановлює з'єднання з сервером, надсилає запит та викликає callback з отриманою відповіддю.
    """
    def worker():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            request = {"action": action}
            if data:
                request.update(data)
            s.send(json.dumps(request).encode())
            response_data = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            response = json.loads(response_data.decode())
        except Exception as e:
            response = {"status": "error", "error": str(e)}
        finally:
            s.close()
        Clock.schedule_once(lambda dt: callback(response))
    threading.Thread(target=worker, daemon=True).start()

class Rate(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.current_image_id = None
        self.current_image_path = None
        self.current_rating = 0

        lbl_title = Label(text="Оцініть фото", font_size=32, halign="center", size_hint=(1, 0.1))
        self.img = Image(source="")

        self.add_widget(lbl_title)
        self.add_widget(self.img)

        # Панель для оцінювання (відображення зірочок)
        stars_layout = BoxLayout(size_hint=(1, 0.1))
        self.star_buttons = []
        for i in range(5):
            btn = Button(text=str(i+1), background_normal="star0.png", background_down="star0.png")
            btn.bind(on_press=self.on_star_press)
            self.star_buttons.append(btn)
            stars_layout.add_widget(btn)
        self.add_widget(stars_layout)

        # Панель навігації: Назад, Оцінити, Вперед
        nav_layout = BoxLayout(size_hint=(1, 0.1))
        btn_prev = Button(text="Назад")
        btn_prev.bind(on_press=self.on_prev)
        btn_rate = Button(text="Оцінити")
        btn_rate.bind(on_press=self.on_rate)
        btn_next = Button(text="Вперед")
        btn_next.bind(on_press=self.on_next)
        nav_layout.add_widget(btn_prev)
        nav_layout.add_widget(btn_rate)
        nav_layout.add_widget(btn_next)
        self.add_widget(nav_layout)

        # Завантажуємо перше зображення при старті
        self.request_image("get_next")

    def on_star_press(self, btn):
        """
        При натисканні на зірочку оновлюється поточний рейтинг та змінюється вигляд кнопок.
        """
        rating_value = int(btn.text)
        self.current_rating = rating_value
        for i, star in enumerate(self.star_buttons):
            if i < rating_value:
                star.background_normal = "star1.png"
                star.background_down = "star1.png"
            else:
                star.background_normal = "star0.png"
                star.background_down = "star0.png"

    def on_prev(self, instance):
        self.request_image("get_prev")

    def on_next(self, instance):
        self.request_image("get_next")

    def on_rate(self, instance):
        if self.current_image_id is None or self.current_rating == 0:
            print("Спочатку виберіть рейтинг та переконайтесь, що зображення завантажено!")
            return
        data = {"image": self.current_image_id, "rating": self.current_rating}
        send_request("rate", data, self.on_rate_response)

    def on_rate_response(self, response):
        if response.get("status") == "ok":
            print("Оцінку збережено!")
        else:
            print("Помилка:", response.get("error"))

    def request_image(self, action):
        send_request(action, None, self.on_image_response)

    def on_image_response(self, response):
        if response.get("status") == "ok":
            b64_data = response.get("image")
            image_bytes = base64.b64decode(b64_data)
            self.current_image_id = response.get("id")
            self.current_image_path = response.get("path")
            ext = "png"
            if self.current_image_path:
                ext = os.path.splitext(self.current_image_path)[1][1:].lower()
            data_stream = io.BytesIO(image_bytes)
            core_image = CoreImage(data_stream, ext=ext)
            self.img.texture = core_image.texture

            # Встановлення поточної оцінки від сервера
            current_rating = response.get("current_rating", 0)
            self.current_rating = current_rating
            print(current_rating)
            for i, star in enumerate(self.star_buttons):
                if i < current_rating:
                    star.background_normal = "star1.png"
                    star.background_down = "star1.png"
                else:
                    star.background_normal = "star0.png"
                    star.background_down = "star0.png"
        else:
            print("Помилка завантаження зображення:", response.get("error"))

class LikeApp(App):
    def build(self):
        return Rate()

if __name__ == '__main__':
    LikeApp().run()
