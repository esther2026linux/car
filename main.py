"""
Mobile version of ChatBot using KivyMD 2.0.1.
Features a Material Design 3 interface, responsive layouts, and AI integration.
"""

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import (
    MDTextField,
    MDTextFieldLeadingIcon,
    MDTextFieldHintText,
    MDTextFieldHelperText,
)
from kivymd.uix.button import (
    MDIconButton,
    MDFabButton,
    MDButton,
    MDButtonIcon,
    MDButtonText,
)
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.appbar import (
    MDTopAppBar,
    MDTopAppBarLeadingButtonContainer,
    MDTopAppBarTrailingButtonContainer,
    MDTopAppBarTitle,
    MDActionTopAppBarButton,
)
from kivymd.uix.screen import MDScreen

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

import threading
import logging
import os

# LangChain imports
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain_core.chat_history import BaseChatMessageHistory
    from langchain_community.chat_message_histories import ChatMessageHistory
    from langchain_core.runnables.history import RunnableWithMessageHistory
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    class ChatOpenAI: 
        def __init__(self, *args, **kwargs): pass
    class ChatMessageHistory:
        def __init__(self): pass
        def clear(self): pass
    class ChatPromptTemplate:
        @staticmethod
        def from_messages(*args): return None
    class SystemMessage:
        def __init__(self, *args, **kwargs): pass
    class MessagesPlaceholder:
        def __init__(self, *args, **kwargs): pass

# Logger Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AI Conversation Manager
class AIConversationManager:
    def __init__(self):
        self.chat_history = ChatMessageHistory()
        self.llm = None
        self.chain = None
        self._setup_ai()
    
    def _setup_ai(self):
        if not LANGCHAIN_AVAILABLE: return
        
        api_key = "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"
        if not api_key: return
        
        try:
            self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=api_key)
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="You are a helpful car diagnostic AI assistant. Help users identify car problems and suggest solutions."),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}")
            ])
            self.chain = prompt | self.llm
            def get_session_history(session_id: str) -> BaseChatMessageHistory: return self.chat_history
            self.chain_with_history = RunnableWithMessageHistory(
                self.chain, get_session_history, input_messages_key="input", history_messages_key="history"
            )
        except Exception as e:
            logger.error(f"AI Setup Error: {e}")
            self.llm = None

    def get_response(self, user_input: str) -> str:
        if not self.llm or not hasattr(self, 'chain_with_history'): return self._get_fallback_response(user_input)
        try:
            response = self.chain_with_history.invoke(
                {"input": user_input}, config={"configurable": {"session_id": "mobile"}}
            )
            return response.content
        except Exception as e:
            logger.error(f"AI Response Error: {e}")
            return "I'm having trouble connecting right now. Please check your internet or API key."

    def _get_fallback_response(self, user_input: str) -> str:
        return "I'm currently in offline mode. Please configure your OpenAI API key to get AI-powered car diagnostics."

    def clear_history(self):
        self.chat_history.clear()

class MessageBubble(MDCard):
    def __init__(self, text, is_user=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.padding = [dp(12), dp(12), dp(12), dp(12)]
        self.style = "filled"
        self.theme_bg_color = "Custom"
        self.md_bg_color = get_color_from_hex("#E8F5E9" if is_user else "#F3F3F3")
        
        # Adjust width based on content but cap at 80% of screen
        self.size_hint_x = 0.8
        self.pos_hint = {"right": 0.98} if is_user else {"left": 0.02}
        
        lbl = MDLabel(
            text=text,
            theme_text_color="Primary",
            adaptive_height=True,
            font_style="Body",
            role="medium",
            halign="left"
        )
        self.add_widget(lbl)
        
        # Self-adjust height based on label
        Clock.schedule_once(lambda dt: self._update_height(lbl), 0.1)

    def _update_height(self, label):
        self.height = label.height + self.padding[1] + self.padding[3]
    
    def update_text(self, new_text):
        self.clear_widgets()
        lbl = MDLabel(
            text=new_text,
            theme_text_color="Primary",
            adaptive_height=True,
            font_style="Body",
            role="medium",
            halign="left",
            valign="top"
        )
        self.add_widget(lbl)
        Clock.schedule_once(lambda dt: self._update_height(lbl), 0.1)

class ChatBotMobileApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Olive"
        self.theme_cls.theme_style = "Light"
        self.ai_manager = AIConversationManager()
        
        self.root_screen = MDScreen()
        
        # Main Layout
        layout = MDBoxLayout(orientation="vertical")
        
        # Top Bar (MD3 style)
        self.app_bar = MDTopAppBar(
            MDTopAppBarLeadingButtonContainer(
                MDActionTopAppBarButton(icon="car-wrench"),
            ),
            MDTopAppBarTitle(text="Vehicle Diagnosis ChatBot"),
            MDTopAppBarTrailingButtonContainer(
                MDActionTopAppBarButton(icon="delete", on_release=lambda x: self.clear_chat()),
            ),
            type="small",
        )
        layout.add_widget(self.app_bar)
        
        # Chat History
        self.scroll = MDScrollView(do_scroll_x=False)
        self.chat_list = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(16),
            size_hint_y=None
        )
        self.chat_list.bind(minimum_height=self.chat_list.setter("height"))
        self.scroll.add_widget(self.chat_list)
        layout.add_widget(self.scroll)
        
        # Input Area
        input_container = MDBoxLayout(
            orientation="horizontal",
            adaptive_height=True,
            padding=[dp(12), dp(8), dp(12), dp(16)],
            spacing=dp(8),
            md_bg_color=self.theme_cls.surfaceContainerLowColor
        )
        
        self.text_input = MDTextField(
            MDTextFieldHintText(text="Describe the car problem..."),
            mode="filled",
            size_hint_x=0.85,
        )
        self.text_input.bind(on_text_validate=self.send_message)
        
        send_btn = MDIconButton(
            icon="send",
            style="standard",
            on_release=self.send_message,
        )
        
        input_container.add_widget(self.text_input)
        input_container.add_widget(send_btn)
        layout.add_widget(input_container)
        
        self.root_screen.add_widget(layout)
        return self.root_screen

    def send_message(self, *args):
        text = self.text_input.text.strip()
        if not text: return
        
        # Add user message
        self.add_bubble(text, is_user=True)
        self.text_input.text = ""
        
        # Placeholder for bot
        thinking_bubble = self.add_bubble("Thinking...", is_user=False)
        
        # Background thread for AI
        threading.Thread(target=self.get_ai_response, args=(text, thinking_bubble), daemon=True).start()

    def get_ai_response(self, user_text, bubble_to_update):
        response = self.ai_manager.get_response(user_text)
        Clock.schedule_once(lambda dt: self.update_bubble(bubble_to_update, response), 0)

    def add_bubble(self, text, is_user):
        bubble = MessageBubble(text=text, is_user=is_user)
        self.chat_list.add_widget(bubble)
        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.1)
        return bubble

    def update_bubble(self, bubble, new_text):
        bubble.update_text(new_text)
        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.2)

    def scroll_to_bottom(self):
        self.scroll.scroll_y = 0

    def clear_chat(self):
        self.chat_list.clear_widgets()
        self.ai_manager.clear_history()

if __name__ == "__main__":
    # Ensure window size matches mobile aspects for desktop testing
    Window.size = (dp(360), dp(640))
    ChatBotMobileApp().run()
