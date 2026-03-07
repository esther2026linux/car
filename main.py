

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

# LangChain imports
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage
    from langchain_core.chat_history import BaseChatMessageHistory
    from langchain_community.chat_message_histories import ChatMessageHistory
    from langchain_core.runnables.history import RunnableWithMessageHistory
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIConversationManager:
    def __init__(self):
        self.chat_history = ChatMessageHistory()
        self.llm = None
        self.chain = None
        self._setup_ai()

    def _setup_ai(self):
        if not LANGCHAIN_AVAILABLE:
            return

        api_key = "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"

        try:
            self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=api_key)

            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="You are a helpful car diagnostic AI assistant."),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}")
            ])

            self.chain = prompt | self.llm

            def get_session_history(session_id: str) -> BaseChatMessageHistory:
                return self.chat_history

            self.chain_with_history = RunnableWithMessageHistory(
                self.chain,
                get_session_history,
                input_messages_key="input",
                history_messages_key="history",
            )

        except Exception as e:
            logger.error(f"AI Setup Error: {e}")
            self.llm = None

    def get_response(self, user_input: str) -> str:
        if not self.llm:
            return "AI not configured."

        try:
            response = self.chain_with_history.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": "mobile"}},
            )
            return response.content

        except Exception as e:
            logger.error(f"AI Response Error: {e}")
            return "Error contacting AI."


class MessageBubble(MDCard):

    def __init__(self, text, is_user=False, **kwargs):
        super().__init__(**kwargs)

        self.orientation = "vertical"
        self.padding = dp(12)
        self.size_hint_y = None

        self.md_bg_color = get_color_from_hex("#E8F5E9" if is_user else "#F3F3F3")

        self.size_hint_x = 0.8
        self.pos_hint = {"right": 0.98} if is_user else {"x": 0.02}

        self.label = MDLabel(
            text=text,
            adaptive_height=True,
            halign="left",
        )

        self.label.bind(
            width=lambda *x: self.label.setter("text_size")(self.label, (self.label.width, None))
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
            title="Vehicle Diagnosis ChatBot",
            elevation=10
        )

        layout.add_widget(toolbar)

        self.scroll = MDScrollView()

        self.chat_list = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(16),
            size_hint_y=None
        )

        self.chat_list.bind(minimum_height=self.chat_list.setter("height"))

        self.scroll.add_widget(self.chat_list)

        layout.add_widget(self.scroll)

        input_box = MDBoxLayout(
            size_hint_y=None,
            height=dp(60),
            padding=dp(8),
            spacing=dp(8)
        )

        self.text_input = MDTextField(
            hint_text="Describe the car problem...",
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

        Clock.schedule_once(lambda dt: self.update_bubble(bubble, response))

    def add_bubble(self, text, is_user):

        bubble = MessageBubble(text=text, is_user=is_user)

        self.chat_list.add_widget(bubble)

        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.1)

        return bubble

    def update_bubble(self, bubble, text):

        bubble.update_text(text)

        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.1)

    def scroll_to_bottom(self):

        self.scroll.scroll_y = 0


if __name__ == "__main__":

    Window.size = (360, 640)

    ChatBotMobileApp().run()
