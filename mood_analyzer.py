from nltk.sentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import nltk
import re
from collections import Counter
from dream_visualizer import DreamVisualizer
import pandas as pd
from database import SessionLocal
from models import Dream

class MoodAnalyzer:
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('sentiment/vader_lexicon.zip')
        except LookupError:
            nltk.download('vader_lexicon')
            nltk.download('punkt')
            
        self.sia = SentimentIntensityAnalyzer()
        self.visualizer = DreamVisualizer()
        
        # Common dream themes and their associated emotions
        self.dream_themes = {
            'flying': 0.8,
            'falling': -0.4,
            'chase': -0.6,
            'water': 0.3,
            'family': 0.5,
            'death': -0.8,
            'school': -0.2,
            'work': -0.3,
            'love': 0.7
        }

    def analyze_mood(self, dream_text):
        """
        Analyze dream mood using multiple methods:
        1. VADER sentiment analysis
        2. TextBlob sentiment
        3. Theme-based analysis
        """
        # Clean text
        cleaned_text = self._clean_text(dream_text)
        
        # Get VADER sentiment
        vader_scores = self.sia.polarity_scores(dream_text)
        vader_compound = vader_scores['compound']
        
        # Get TextBlob sentiment
        blob = TextBlob(dream_text)
        textblob_score = blob.sentiment.polarity
        
        # Get theme-based score
        theme_score = self._analyze_themes(cleaned_text)
        
        # Combine scores (weighted average)
        final_score = (0.4 * vader_compound +
                      0.3 * textblob_score +
                      0.3 * theme_score)
        
        # Ensure score is between -1 and 1
        return max(min(final_score, 1.0), -1.0)

    def _clean_text(self, text):
        """Remove special characters and convert to lowercase"""
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        return text.lower()

    def _analyze_themes(self, text):
        """Analyze common dream themes and their emotional impact"""
        words = text.split()
        theme_scores = []
        
        for theme, score in self.dream_themes.items():
            if theme in words:
                theme_scores.append(score)
        
        return sum(theme_scores) / len(theme_scores) if theme_scores else 0.0

    def get_mood_label(self, mood_score):
        """Convert numerical score to mood category"""
        if mood_score >= 0.5:
            return "Very Positive"
        elif mood_score >= 0.1:
            return "Positive"
        elif mood_score > -0.1:
            return "Neutral"
        elif mood_score > -0.5:
            return "Negative"
        else:
            return "Very Negative"

    def get_detailed_analysis(self, dream_text):
        """Provide detailed mood analysis"""
        cleaned_text = self._clean_text(dream_text)
        vader_scores = self.sia.polarity_scores(dream_text)
        
        # Identify prominent themes
        themes = [theme for theme in self.dream_themes.keys() 
                 if theme in cleaned_text]
        
        # Word frequency analysis
        words = nltk.word_tokenize(cleaned_text)
        word_freq = Counter(words).most_common(5)
        
        return {
            'sentiment_scores': vader_scores,
            'identified_themes': themes,
            'common_words': word_freq,
            'mood_score': self.analyze_mood(dream_text),
            'mood_label': self.get_mood_label(self.analyze_mood(dream_text))
        }

    # New visualization methods
    def visualize_mood_patterns(self):
        """Generate visualizations for mood patterns"""
        db = SessionLocal()
        try:
            dreams = db.query(Dream).all()
            dreams_df = pd.DataFrame([
                {
                    'dream_text': dream.content,
                    'mood': dream.mood,
                    'created_at': dream.created_at,
                    'detailed_analysis': self.get_detailed_analysis(dream.content)
                } for dream in dreams
            ])
            
            # Add numerical mood scores to DataFrame
            dreams_df['mood_score'] = dreams_df['detailed_analysis'].apply(
                lambda x: x['mood_score']
            )
            
            # Prepare data for visualization
            df, vectors = self.visualizer.prepare_data(dreams_df)
            
            # Generate all visualizations
            self.visualizer.plot_mood_calendar(df)
            self.visualizer.plot_mood_distribution(df)
            self.visualizer.plot_theme_clusters(vectors)
            
            return {
                'dataframe': df,
                'vectors': vectors,
                'report': self.visualizer.generate_report(df)
            }
            
        finally:
            db.close()

    def get_theme_visualization(self):
        """Generate visualization for dream themes"""
        db = SessionLocal()
        try:
            dreams = db.query(Dream).all()
            dreams_df = pd.DataFrame([
                {
                    'dream_text': dream.content,
                    'mood': dream.mood,
                    'created_at': dream.created_at
                } for dream in dreams
            ])
            
            df, vectors = self.visualizer.prepare_data(dreams_df)
            self.visualizer.plot_theme_clusters(vectors)
            return df, vectors
            
        finally:
            db.close()

# Example usage
def main():
    analyzer = MoodAnalyzer()
    
    # Single dream analysis
    dream_text = "I was flying over mountains and felt very happy"
    analysis = analyzer.get_detailed_analysis(dream_text)
    print("Single Dream Analysis:", analysis)
    
    # Generate visualizations
    viz_results = analyzer.visualize_mood_patterns()
    print("Visualization Report:", viz_results['report'])

if __name__ == "__main__":
    main()