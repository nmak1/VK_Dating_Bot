from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class InterestAnalyzer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()

    def calculate_similarity(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0

        vectors = self.vectorizer.fit_transform([text1, text2])
        return cosine_similarity(vectors[0:1], vectors[1:2])[0][0]