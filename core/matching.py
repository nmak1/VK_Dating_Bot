from config import constants
from services.analyzer import InterestAnalyzer


class MatchFinder:
    def __init__(self, vk_client, user_vk_client):
        self.vk = vk_client
        self.user_vk = user_vk_client
        self.analyzer = InterestAnalyzer()

    def find_matches(self, user_id):
        user_info = self._get_user_info(user_id)
        candidates = self._search_candidates(user_info)
        return self._rank_candidates(user_info, candidates)

    def _get_user_info(self, user_id):
        return self.user_vk.get_user_info(user_id)

    def _search_candidates(self, user_info):
        params = {
            'age_from': max(user_info['age'] - constants.BotConstants.AGE_RANGE,
                            constants.BotConstants.MIN_AGE),
            'age_to': min(user_info['age'] + constants.BotConstants.AGE_RANGE,
                          constants.BotConstants.MAX_AGE),
            'sex': 1 if user_info['sex'] == 2 else 2,
            'city': user_info['city'],
            'has_photo': 1,
            'count': 100,
            'fields': constants.VkConstants.USER_FIELDS
        }
        return self.vk.search_users(params)

    def _rank_candidates(self, user_info, candidates):
        scored = []
        for candidate in candidates:
            score = self._calculate_match_score(user_info, candidate)
            if score > 0:
                scored.append((score, candidate))
        return sorted(scored, key=lambda x: x[0], reverse=True)

    def _calculate_match_score(self, user, candidate):
        score = 0
        # Логика расчета рейтинга
        return score