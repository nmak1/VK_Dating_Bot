from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from core import VKAPIClient
from handlers.message import MessageHandler
from handlers.callback import CallbackHandler
from config import settings

class DatingBot:
    def __init__(self):

        self.vk = VKAPIClient(settings.VK_GROUP_TOKEN)
        self.user_vk = VKAPIClient(settings.VK_USER_TOKEN)
        self.message_handler = MessageHandler(self.vk, self.user_vk)
        self.callback_handler = CallbackHandler(self.vk, self.user_vk)

    def run(self):
        longpoll = VkBotLongPoll(self.vk.api, settings.VK_GROUP_ID)
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                self.message_handler.handle(event)
            elif event.type == VkBotEventType.MESSAGE_EVENT:
                self.callback_handler.handle(event)