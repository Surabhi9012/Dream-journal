import logging
from datetime import datetime, timedelta
from sqlalchemy import func
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np
from models import DreamEntry, db_session

# Configure Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class MoodInsights:
    """Class to provide insights into user dreams, moods, and recurring themes."""
    
    def __init__(self, user_id):
        self.user_id = user_id

    def get_mood_trends(self, days=30):
        """
        Analyze mood trends for the past given days.
        :param days: Number of days to analyze (default: 30).
        :return: Dictionary with average mood, trend, and dominant mood.
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            dreams = db_session.query(DreamEntry).filter(
                DreamEntry.user_id == self.user_id,
                DreamEntry.timestamp >= start_date
            ).order_by(DreamEntry.timestamp).all()

            if not dreams:
                return {
                    'average_mood': None,
                    'trend': None,
                    'dominant_mood': "No data available"
                }

            mood_scores = [dream.mood_score for dream in dreams]

            # Calculate metrics
            average_mood = np.mean(mood_scores)
            trend = self._calculate_trend(mood_scores)
            dominant_mood = self._get_dominant_mood(mood_scores)

            logger.info(f"Mood Scores: {mood_scores}")
            logger.info(f"Average Mood: {average_mood}")
            logger.info(f"Trend: {trend}")
            logger.info(f"Dominant Mood: {dominant_mood}")

            return {
                'average_mood': float(average_mood),
                'trend': trend,
                'dominant_mood': dominant_mood
            }

        except Exception as e:
            logger.error(f"Error calculating mood trends: {str(e)}")
            return {
                'average_mood': None,
                'trend': "Error calculating trend",
                'dominant_mood': "Error determining dominant mood"
            }

    def _calculate_trend(self, scores):
        """Calculate mood trend using a linear regression slope."""
        if len(scores) < 2:
            return 'neutral'
        slope = np.polyfit(range(len(scores)), scores, 1)[0]
        if slope > 0.1:
            return 'improving'
        elif slope < -0.1:
            return 'declining'
        return 'stable'

    def _get_dominant_mood(self, scores):
        """Determine the dominant mood based on mood scores."""
        moods = [
            'negative' if s < -0.1 else 'positive' if s > 0.1 else 'neutral'
            for s in scores
        ]
        return Counter(moods).most_common(1)[0][0]

    def find_recurring_themes(self, min_dreams=3):
        """
        Identify recurring themes in user dreams.
        :param min_dreams: Minimum number of dreams required for analysis.
        :return: List of themes with keywords and frequency.
        """
        try:
            dreams = db_session.query(DreamEntry).filter(
                DreamEntry.user_id == self.user_id
            ).all()

            if len(dreams) < min_dreams:
                return None

            texts = [dream.dream_text for dream in dreams]
            vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
            X = vectorizer.fit_transform(texts)

            n_clusters = min(3, len(texts))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(X)

            themes = []
            for i in range(n_clusters):
                cluster_texts = [text for text, cluster in zip(texts, clusters) if cluster == i]
                if cluster_texts:
                    top_terms = self._get_top_terms(vectorizer, kmeans, i)
                    themes.append({
                        'theme': f"Theme {i + 1}",
                        'keywords': top_terms,
                        'frequency': len(cluster_texts)
                    })

            logger.info(f"Recurring themes found: {themes}")
            return themes

        except Exception as e:
            logger.error(f"Error finding recurring themes: {str(e)}")
            return None

    def _get_top_terms(self, vectorizer, kmeans, cluster_idx, top_n=3):
        """Get the top terms for a given cluster."""
        order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
        terms = vectorizer.get_feature_names_out()
        return [terms[i] for i in order_centroids[cluster_idx, :top_n]]

    def generate_feedback(self):
        """
        Generate personalized feedback based on mood trends and recurring themes.
        :return: Feedback string.
        """
        try:
            mood_data = self.get_mood_trends()
            themes = self.find_recurring_themes()

            if not mood_data:
                return "Not enough dream entries to generate insights."

            feedback = []

            # Mood feedback
            if mood_data['trend'] != 'stable':
                feedback.append(f"Your dream moods have been {mood_data['trend']} lately.")

            if mood_data['dominant_mood'] == 'negative' and mood_data['average_mood'] < -0.3:
                feedback.append("You've had several negative dreams recently. "
                                "Consider practicing relaxation techniques before bed.")
            elif mood_data['dominant_mood'] == 'positive' and mood_data['average_mood'] > 0.3:
                feedback.append("Your dreams have been notably positive lately. "
                                "This often indicates good emotional well-being.")

            # Theme feedback
            if themes:
                for theme in themes:
                    if theme['frequency'] >= 3:
                        feedback.append(f"You frequently dream about {', '.join(theme['keywords'])}.")

            return " ".join(feedback) if feedback else "Keep logging your dreams to receive personalized insights."

        except Exception as e:
            logger.error(f"Error generating feedback: {str(e)}")
            return "An error occurred while generating feedback. Please try again later."
