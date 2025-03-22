from kivy.app import App

from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

class LikeApp(App):
    def build(self):
        self.mainBox = BoxLayout(orientation='vertical')
        btnBox=BoxLayout()
        lbl_title = Label(text="Оцініть фото", font_size=32, halign="center", size_hint=[1,0.1])

        btn_like = Button(text='Like', font_size=24, size_hint=[0.5, 0.3])
        btn_dislike = Button(text='dislike', font_size=24, size_hint=[0.5, 0.3])

        self.img = Image(source="photos/photo_2025-03-22_12-47-05.jpg", size_hint=[1, 0.6])

        self.mainBox.add_widget(lbl_title)
        self.mainBox.add_widget(self.img)

        btnBox.add_widget(btn_like)
        btnBox.add_widget(btn_dislike)

        self.mainBox.add_widget(btnBox)
        return self.mainBox

LikeApp().run()