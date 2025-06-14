import vk_api
from config.settings import settings


class VKClient:
    def __init__(self, token: str = None):
        self.token = token or settings.VK_GROUP_TOKEN
        self.session = vk_api.VkApi(token=self.token)
        self.api = self.session.get_api()

    def get_user_info(self, user_id: int) -> dict:
        return self.api.users.get(
            user_ids=user_id,
            fields='bdate,sex,city,interests,music,books,groups'
        )[0]