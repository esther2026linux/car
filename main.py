from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.screen import MDScreen

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

import threading
import logging
import requests


# YOUR BACKEND API
SERVER_URL = "https://esther2026linux.pythonanywhere.com/api/chat/"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIConversationManager:

    def get_response(self, user_input):

        try:
            payload = {"message": user_input}

            response = requests.post(
                SERVER_URL,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                return response.json().get("response", "Empty response from server")

            return f"Server error {response.status_code}"

        except requests.exceptions.ConnectionError:
            return "Cannot connect to server."

        except Exception as e:
            logger.error(e)
            return "Error contacting server."


class MessageBubble(MDCard):

    def __init__(self, text, is_user=False, **kwargs):
        super().__init__(**kwargs)

        self.orientation = "vertical"
        self.padding = dp(12)
        self.size_hint_y = None

        self.md_bg_color = get_color_from_hex(
            "#D0E6FF" if is_user else "#F3F3F3"
        )

        self.size_hint_x = 0.8
        self.pos_hint = {"right": 0.98} if is_user else {"x": 0.02}

        self.label = MDLabel(
            text=text,
            adaptive_height=True,
            halign="left"
        )

        self.label.bind(
            width=lambda *x:
            self.label.setter("text_size")(self.label, (self.label.width, None))
        )

        self.add_widget(self.label)

        Clock.schedule_once(self.update_height)

    def update_height(self, *args):
        self.height = self.label.texture_size[1] + dp(24)

    def update_text(self, new_text):
        self.label.text = new_text
        Clock.schedule_once(self.update_height)


class ChatBotMobileApp(MDApp):

    def build(self):

        self.theme_cls.primary_palette = "BlueGray"

        self.ai_manager = AIConversationManager()

        screen = MDScreen()

        layout = MDBoxLayout(orientation="vertical")

        toolbar = MDTopAppBar(
            title="Cardia Vehicle AI",
            right_action_items=[
                ["delete", lambda x: self.clear_chat()]
            ]
        )

        layout.add_widget(toolbar)

        self.scroll = MDScrollView()

        self.chat_list = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(16),
            size_hint_y=None
        )

        self.chat_list.bind(
            minimum_height=self.chat_list.setter("height")
        )

        self.scroll.add_widget(self.chat_list)

        layout.add_widget(self.scroll)

        input_box = MDBoxLayout(
            size_hint_y=None,
            height=dp(60),
            padding=dp(8),
            spacing=dp(8)
        )

        self.text_input = MDTextField(
            hint_text="Describe the vehicle problem...",
            size_hint_x=0.85
        )

        self.text_input.bind(on_text_validate=self.send_message)

        send_btn = MDIconButton(
            icon="send",
            on_release=self.send_message
        )

        input_box.add_widget(self.text_input)
        input_box.add_widget(send_btn)

        layout.add_widget(input_box)

        screen.add_widget(layout)

        return screen

    def send_message(self, *args):

        text = self.text_input.text.strip()

        if not text:
            return

        self.add_bubble(text, True)

        self.text_input.text = ""

        thinking = self.add_bubble("Thinking...", False)

        threading.Thread(
            target=self.get_ai_response,
            args=(text, thinking),
            daemon=True
        ).start()

    def get_ai_response(self, text, bubble):

        response = self.ai_manager.get_response(text)

        Clock.schedule_once(
            lambda dt: self.update_bubble(bubble, response)
        )

    def add_bubble(self, text, is_user):

        bubble = MessageBubble(text=text, is_user=is_user)

        self.chat_list.add_widget(bubble)

        Clock.schedule_once(
            lambda dt: self.scroll_to_bottom(),
            0.1
        )

        return bubble

    def update_bubble(self, bubble, text):

        bubble.update_text(text)

        Clock.schedule_once(
            lambda dt: self.scroll_to_bottom(),
            0.1
        )

    def scroll_to_bottom(self):

        self.scroll.scroll_y = 0

    def clear_chat(self):

        self.chat_list.clear_widgets()


if __name__ == "__main__":

    Window.size = (360, 640)

    ChatBotMobileApp().run()
