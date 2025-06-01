from config import constants
from services.formatter import format_profile


class MessageHandler:
    def __init__(self, bot):
        self.bot = bot

    def handle(self, event):
        if event.text.lower() == 'начать':
            self._send_welcome(event.user_id)
        elif event.text.lower() == 'найти':
            self._handle_search(event.user_id)

    def _send_welcome(self, user_id):
        self.bot.vk.send_message(
            user_id,
            constants.Messages.WELCOME
        )

    def _handle_search(self, user_id):
        matches = self.bot.matcher.find_matches(user_id)
        if not matches:
            self.bot.vk.send_message(
                user_id,
                constants.Messages.NO_MATCHES
            )
            return

        top_match = matches[0][1]
        profile_text = format_profile(top_match)
        photos = self.bot.vk.get_top_photos(top_match['id'])

        self.bot.vk.send_message(
            user_id,
            profile_text,
            attachments=photos
        )