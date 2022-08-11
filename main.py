from time import sleep
from kivymd.app import MDApp
from kivymd.uix.boxlayout import BoxLayout
from kivymd.uix.gridlayout import GridLayout
from kivymd.uix.floatlayout import FloatLayout
from kivymd.uix.list import OneLineListItem
from kivy.properties import BooleanProperty, NumericProperty, ListProperty, StringProperty, DictProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.label import MDLabel
from kivy.clock import Clock
from colors import colors
from threading import Thread
from datetime import datetime, timedelta, timezone
from server import Connector
from exceptions import AccessError, CommonPasswordError, ShortPasswordError
from requests.exceptions import ConnectionError


class MainRootWidget(BoxLayout):
    pass
        

class SidebarWidget(BoxLayout):
    pass


class ContactsWidget(GridLayout):
    pass

class AppWindow(Screen):
    pass

class LoginWindow(Screen):
    pass

class SettingsWindow(Screen):
    pass

class WindowManager(ScreenManager):
    pass

class Row(RecycleDataViewBehavior, FloatLayout):
    text = StringProperty('')
    pos_hint = DictProperty({})
    halign = StringProperty('left')
    index = None
    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        print(rv, index, data)
        self.index = index
        return super(Row, self).refresh_view_attrs(
            rv, index, data)

class NetApp(MDApp):
    data = ListProperty([])
    input_color = ListProperty([])
    text_color = ListProperty([])
    refreshing = BooleanProperty(False)
    is_max_pool = BooleanProperty(False)
    text_size = NumericProperty(18)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.day = timedelta(days=1)
        self.two_days = self.day * 2
    
    def find_user(self, id):
        for i in self.users:
            if str(i['id']) == str(id):
                return i
        return None
    
    def render_contacts(self):
        
        self.contacts_widget = self.app.root.ids.app_window.ids.contacts
        self.contacts_widget.clear_widgets()
        print(self.contacts)
        for contact in self.contacts:
            frend = self.find_user(contact)
            i = OneLineListItem(text=frend['username'], on_press=self.on_select_chat, font_style="H6", divider=None)
            self.contacts_widget.add_widget(i)
            i.user_id = NumericProperty()
            i.user_id = contact
            i.chat_id = NumericProperty()
            i.chat_id = self.contacts[contact]
            i.chat_exist = BooleanProperty()
            i.chat_exist = True
    
    def refresh_contacts(self):
        self.render_contacts()
    
    def on_select_chat(self, item):
        self.is_max_pool = False
        self.messages_pool = 1
        if item.chat_exist:
            chat_id = item.chat_id
        else:
            chat = self.connector.createchat(item.user_id)['post']
            chat_id = chat['id']
            self.contacts[str(item.user_id)] = chat_id
            self.render_contacts()

        messages = self.render_messages(item.user_id, chat_id, "1")

        if len(messages) > 0:
            self.selected_chat = {'user_id': item.user_id, 'chat_id': chat_id, 'last_message_id': messages[-1]['id']}
        else:
            self.selected_chat = {'user_id': item.user_id, 'chat_id': chat_id, 'last_message_id': None}
    
    def get_message_string(self, timestamp, author_name, message):
        dt = datetime.fromisoformat(timestamp[:-1]+ "+00:00")
        now = datetime.now(tz=timezone.utc)
        if now - dt < self.day and now.day == dt.day:
            t = dt.astimezone().strftime("%H:%m")
        elif dt.day == (now - self.day).day and now - dt < self.two_days:
            t = "Вчера"
        elif dt.day == (now - self.two_days).day and now - dt < self.two_days + self.day:
            t = "Позавчера"
        else:
            t = dt.astimezone().strftime("%d:%m:%Y")
        return f"[size={self.text_size}]{t}[/size] [size={self.text_size + 4}]{author_name}[/size]: [size={self.text_size}]{message}[/size]"
        
        
    def render_messages(self, user, chat_id, part):
        self.data = []
        data = []
        
        messages = self.connector.getmessagelist(str(chat_id), part)['messages']
        frend = self.find_user(user)
        self.app.root.ids.app_window.ids.chatname.text = f"[b]{frend['username']}[/b]"
        for message in messages:
            if message['author_id'] == str(self.user['id']):
                author_name = "Вы"
            else:
                author_name = frend['username']
            ppos = {'center_y': 0.5, 'right': 0.97} if author_name == 'Вы' else {'center_y': 0.5, 'x': 0.03}
            halign = 'right' if author_name == 'Вы' else 'left'
            data.append({'text': self.get_message_string(message['created_at'], author_name, message['text']), 'pos_hint': ppos, 'halign': halign})
        self.data = data
        
        return messages
    
    def check_pull_refresh(self, view, grid):
        max_pixel = 200
        to_relative = max_pixel / (grid.height - view.height)
        if view.scroll_y < 1.0 + to_relative or self.refreshing:
            return

        self.refresh_data()
    
    def refresh_data(self):
        self.messages_pool += 1
        Thread(target=self._refresh_data).start()
    
    def _refresh_data(self):
        if not self.is_max_pool:
            self.refreshing = True
            sleep(0.5)
            messages = self.connector.getmessagelist(str(self.selected_chat['chat_id']), str(self.messages_pool))['messages']
            if len(messages) > 0:
                self.data = [{'text': self.get_message_string(i['created_at'], self.find_user(i['author_id'])['username'], i['text']), 'pos_hint': {'center_y': 0.5, 'right': 0.97} if str(i['author_id']) == str(self.user['id']) else {'center_y': 0.5, 'x': 0.03}, 'halign': 'right' if str(i['author_id']) == str(self.user['id']) else 'left'} for i in messages] + self.data
            else:
                self.is_max_pool = True
            self.refreshing = False
    
    def on_message(self, chat_id, message, author_username):
        if str(chat_id) == str(self.selected_chat['chat_id']):
            ppos = {'center_y': 0.5, 'right': 0.97} if message['author_id'] == self.user['id'] else {'center_y': 0.5, 'x': 0.03}
            halign = 'right' if message['author_id'] == self.user['id'] else 'left'
            print(message['author_id'], self.user['id'], type(message['author_id']), type(self.user['id']), halign)
            self.data = self.data + [{'text': self.get_message_string(message['created_at'], author_username, message['text']), 'pos_hint': ppos, 'halign': halign}]
            self.selected_chat['last_message_id'] = message['id']

    def bind_buttons(self):
        send_message_widget = self.app.root.ids.app_window.ids.send_message
        send_message_widget.bind(
            on_text_validate=self.send_message
        )
        
        search_users_widget = self.app.root.ids.app_window.ids.search_users
        search_users_widget.bind(
            on_text_validate=self.search_users
        )
        text_size = self.app.root.ids.settings_window.ids.text_size
        text_size.bind(
            on_touch_move=self.set_text_size,
            on_touch_up=lambda x, y: self.render_messages(self.selected_chat['user_id'], self.selected_chat['chat_id'], "1") if self.selected_chat else 0
        )
        print(self.text_size)
    
    def set_text_size(self, slider, mouse_motion_event):
        self.text_size = slider.value
    
    def search_users(self, instance_textfield):
        self.contacts_widget.clear_widgets()
        r = instance_textfield.text
        self.users = self.parse_users(self.connector.getuserlist())
        for user in self.users:
            if str(user['id']) == str(self.user['id']):
                continue
            if r in user['username']:
                i = OneLineListItem(text=user['username'], on_press=self.on_select_chat, font_style="H6", divider=None)
                
                i.user_id = NumericProperty()
                i.user_id = str(user['id'])
                i.chat_exist = BooleanProperty()
                if str(user['id']) in self.contacts.keys():
                    i.chat_exist = True
                    i.chat_id = NumericProperty()
                    i.chat_id = self.contacts[str(user['id'])]
                else:
                    i.chat_exist = False
                
                
                self.contacts_widget.add_widget(i)
    
    def send_message(self, instance_textfield):
        msg = instance_textfield.text
        if not self.selected_chat or self.selected_chat['chat_id'] is None or msg == '':
            return
        self.app.root.ids.app_window.ids.send_message.text = ''
        msg = self.connector.sendmessage(str(self.selected_chat['chat_id']), msg)['message']
        self.on_message(self.selected_chat['chat_id'], msg, 'Вы')
    
    def build(self):
        self.theme_cls.colors.update(colors)
        self.theme = 1
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.primary_hue = "500"
        self.theme_cls.accent_palette = "BlueGray"
        self.theme_cls.theme_style = 'Dark'
        self.input_color = (0.24, 0.27, 0.29, 1)
        self.text_color = (0.95, 0.95, 0.95, 1)
        return MainRootWidget()
    
    def change_theme_color(self):
        print(self.theme)
        if self.theme == 0:
            self.theme_cls.theme_style = "Dark"
            self.theme_cls.primary_palette = "Gray"
            self.theme_cls.accent_palette = "BlueGray"
            self.input_color = (0.24, 0.27, 0.29, 1)
            self.text_color = (0.95, 0.95, 0.95, 1)
            self.theme = 1
        else:
            self.theme_cls.theme_style = "Light"
            self.theme_cls.primary_palette = "DeepOrange"
            self.theme_cls.accent_palette = "Amber"
            self.input_color = (0.94, 0.94, 0.94, 1)
            self.text_color = (0.05, 0.05, 0.05, 1)
            self.theme = 0

    def aggregate_contacts(self, contacts):
        cont = {}
        for i in contacts:
            target_id = str(i['users'][0]) if str(i['users'][0]) != str(self.user['id']) else str(i['users'][1])
            cont[target_id] = i['id']
        return cont
    
    def logger(self):
        username_widget = self.app.root.ids.login_window.ids.username
        password_widget = self.app.root.ids.login_window.ids.password
        error_widget = self.app.root.ids.login_window.ids.error_widget
        
        try:
            self.connector.autorize(username_widget.text, password_widget.text)
        except AccessError:
            if isinstance(error_widget.children[0], MDLabel):
                error_widget.remove_widget(error_widget.children[0])
            error_widget.add_widget(
                MDLabel(text="Неправильное имя пользователя, или пароль", font_size=18, halign='center', theme_text_color="Custom", text_color=(1, 0, 0, 1), parent_background=(1, 0, 0, 1), pos_hint={"center_x": 0.5})
            )
        except ConnectionError:
            if isinstance(error_widget.children[0], MDLabel):
                error_widget.remove_widget(error_widget.children[0])
            error_widget.add_widget(
                MDLabel(text="Сервер недоступен", font_size=18, halign='center', theme_text_color="Custom", text_color=(0.9, 0.76, 0.25, 1), parent_background=(1, 0, 0, 1), pos_hint={"center_x": 0.5})
            )
        else:
            self.on_login()
    
    def open_settings_custom(self):
        self.app.root.ids.screen_manager.current = "settingsframe"
    
    def open_main_window(self):
        self.app.root.ids.screen_manager.current = "mainframe"

    def register(self):
        username_widget = self.app.root.ids.login_window.ids.username
        password_widget = self.app.root.ids.login_window.ids.password
        error_widget = self.app.root.ids.login_window.ids.error_widget
        
        try:
            self.connector.register(username_widget.text, password_widget.text)
            #self.connector.autorize("root", "123")
        except CommonPasswordError:
            if isinstance(error_widget.children[0], MDLabel):
                error_widget.remove_widget(error_widget.children[0])
            error_widget.add_widget(
                MDLabel(text="Слишком слабый пароль", font_size=18, halign='center', theme_text_color="Custom", text_color=(1, 0, 0, 1), parent_background=(1, 0, 0, 1), pos_hint={"center_x": 0.5})
            )
        except ShortPasswordError:
            if isinstance(error_widget.children[0], MDLabel):
                error_widget.remove_widget(error_widget.children[0])
            error_widget.add_widget(
                MDLabel(text="Пароль должен содержать не менее 8 символов", font_size=18, halign='center', theme_text_color="Custom", text_color=(1, 0, 0, 1), parent_background=(1, 0, 0, 1), pos_hint={"center_x": 0.5})
            )
        except ConnectionError:
            if isinstance(error_widget.children[0], MDLabel):
                error_widget.remove_widget(error_widget.children[0])
            error_widget.add_widget(
                MDLabel(text="Сервер недоступен", font_size=18, halign='center', theme_text_color="Custom", text_color=(0.9, 0.76, 0.25, 1), parent_background=(1, 0, 0, 1), pos_hint={"center_x": 0.5})
            )
        else:
            self.on_login()
    
    def parse_users(self, users):
        new_users = []
        for i in users:
            new_users.append({
                'id': i['id'],
                'username': i['user']['username']
            })
        return new_users
    
    def background_task(self, gt):
        if not self.selected_chat:
            return
        chat = self.selected_chat
        chat_id = str(chat['chat_id'])
        author = self.find_user(chat['user_id'])
        messages = self.connector.getmessagelist(chat_id, "1")['messages']
        for message in messages:
            if chat['last_message_id'] is None:
                self.on_message(chat_id, message, author['username'])
            elif message['id'] > chat['last_message_id']:
                self.on_message(chat_id, message, author['username'])


        if len(messages) > 0:
            self.selected_chat['last_message_id'] = messages[-1]['id']
    
    
    def on_login(self):
        self.load_main_screen()
        self.open_main_window()
    
    def load_main_screen(self):
        self.user = self.connector.getMe()
        self.user['id'] = str(self.user['id'])
        self.contacts = self.aggregate_contacts(self.connector.getcontacts()['chats']['chats'])
        self.users = self.parse_users(self.connector.getuserlist())
        self.render_contacts()
        if len(self.contacts) > 0:
            self.on_select_chat(self.contacts_widget.children[-1])
        else:
            self.data = [{'text': f'[color=#FF0000]Система[/color] У вас пока нет активных чатов! Чтобы начать переписку - используйте поиск контактов!', 'halign': 'left', 'pos_hint': {'x': 0.03, 'center_y': 0.5}},
                         {'text': f'[color=#FF0000]Система[/color] Поиск контактов: введите ник пользователя, или оставьте поле пустым и нажмите Enter. Выберите пользователя из списка. Готово!', 'halign': 'left', 'pos_hint': {'x': 0.03, 'center_y': 0.5}}]
            self.selected_chat = None
        self.messages_pool = 1
        self.refreshing = False
        self.is_max_pool = False
        self.bind_buttons()
        Clock.schedule_interval(self.background_task, 3)

    def on_start(self):
        self.app = MDApp.get_running_app()
        self.connector = Connector()
        


if __name__ == '__main__':
    NetApp().run()