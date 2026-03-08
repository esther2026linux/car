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
        self.spacing = dp(5)
        self.size_hint_y = None
        self.adaptive_height = True
        self.radius = [dp(12), dp(12), dp(12), dp(12)]

        # Responsive width for phone screens
        self.size_hint_x = None
        self.width = Window.width * 0.75

        # Bubble color
        self.md_bg_color = get_color_from_hex(
            "#D0E6FF" if is_user else "#F3F3F3"
        )

        # Alignment
        self.pos_hint = {"right": 0.98} if is_user else {"x": 0.02}

        self.label = MDLabel(
            text=text,
            adaptive_height=True,
            halign="left",
        )

        self.label.bind(
            width=lambda *x:
            self.label.setter("text_size")(self.label, (self.label.width, None))
        )

        self.add_widget(self.label)

        Clock.schedule_once(self.update_height)

    def update_height(self, *args):
        self.height = self.label.texture_size[1] + dp(30)

    def update_text(self, new_text):
        self.label.text = new_text
        Clock.schedule_once(self.update_height)


class ChatBotMobileApp(MDApp):

    def build(self):

        self.theme_cls.primary_palette = "BlueGray"
        self.theme_cls.material_style = "M3"

        self.ai_manager = AIConversationManager()

        screen = MDScreen()

        main_layout = MDBoxLayout(orientation="vertical")

        # Top toolbar
        toolbar = MDTopAppBar(
            title="Cardia Vehicle AI",
            elevation=2,
            right_action_items=[
                ["delete", lambda x: self.clear_chat()]
            ]
        )

        main_layout.add_widget(toolbar)

        # Scroll area
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

        main_layout.add_widget(self.scroll)

        # Input area
        input_box = MDBoxLayout(
            adaptive_height=True,
            padding=dp(8),
            spacing=dp(8)
        )

        self.text_input = MDTextField(
            hint_text="Describe the vehicle problem...",
            mode="rectangle",
            size_hint_x=1
        )

        self.text_input.bind(on_text_validate=self.send_message)

        send_btn = MDIconButton(
            icon="send",
            on_release=self.send_message
        )

        input_box.add_widget(self.text_input)
        input_box.add_widget(send_btn)

        main_layout.add_widget(input_box)

        screen.add_widget(main_layout)

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

        if self.chat_list.children:
            self.scroll.scroll_to(self.chat_list.children[0])

    def clear_chat(self):

        self.chat_list.clear_widgets()


if __name__ == "__main__":

    ChatBotMobileApp().run()
