from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from config import settings, constants
from core.db.repositories import UserRepository
from core.vk_api.client import VKClient
from core.matching import MatchFinder
from handlers.callback import CallbackHandler
from handlers.message import MessageHandler


class DatingBot:
    def __init__(self):
        self.vk = VKClient(settings.VK_GROUP_TOKEN)
        self.user_vk = VKClient(settings.VK_USER_TOKEN)
        self.matcher = MatchFinder(self.vk, self.user_vk)
        self.handler = MessageHandler(self)
        self.callback_handler = CallbackHandler(self.vk, UserRepository())



    def run(self):
        longpoll = VkBotLongPoll(self.vk.api, settings.VK_GROUP_ID)
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                self.handler.handle(event)

    async def handle_callback(self, event):
            return await self.callback_handler.handle(event)