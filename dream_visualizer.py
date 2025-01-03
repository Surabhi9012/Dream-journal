import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from collections import Counter

class DreamVisualizer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=1000,
            ngram_range=(1, 2)
        )
        self.kmeans = KMeans(n_clusters=3, random_state=42)
        
    def prepare_data(self, dreams_df):
        """
        Prepare dream data for visualization
        
        Parameters:
        dreams_df: DataFrame containing dream entries with columns:
            - dream_text: dream description
            - mood: mood after dream
            - created_at: timestamp of dream
        """
        # Ensure datetime
        df = dreams_df.copy()
        df['created_at'] = pd.to_datetime(df['created_at'])
        
        # Text vectorization and clustering
        dream_vectors = self.vectorizer.fit_transform(df['dream_text'])
        df['cluster'] = self.kmeans.fit_predict(dream_vectors)
        
        return df, dream_vectors
    
    def plot_mood_calendar(self, df):
        """Create a calendar heatmap of moods"""
        plt.figure(figsize=(15, 8))
        
        # Create pivot table for calendar
        mood_pivot = df.pivot_table(
            index=df['created_at'].dt.day_name(),
            columns=df['created_at'].dt.month,
            values='mood',
            aggfunc='count'
        )
        
        # Plot heatmap
        sns.heatmap(mood_pivot, cmap='YlOrRd', annot=True, fmt='g')
        plt.title('Dream Mood Calendar Heatmap')
        plt.xlabel('Month')
        plt.ylabel('Day of Week')
        plt.tight_layout()
        
    def plot_mood_distribution(self, df):
        """Plot distribution of moods over time"""
        plt.figure(figsize=(12, 6))
        
        # Group by week and mood
        weekly_moods = df.groupby([
            pd.Grouper(key='created_at', freq='W'),
            'mood'
        ]).size().unstack().fillna(0)
        
        # Create stacked bar plot
        weekly_moods.plot(kind='bar', stacked=True)
        plt.title('Weekly Mood Distribution')
        plt.xlabel('Week')
        plt.ylabel('Number of Dreams')
        plt.legend(title='Mood')
        plt.xticks(rotation=45)
        plt.tight_layout()
    
    def plot_theme_clusters(self, dream_vectors):
        """Visualize dream themes using cluster analysis"""
        feature_names = self.vectorizer.get_feature_names_out()
        cluster_centers = self.kmeans.cluster_centers_
        
        plt.figure(figsize=(15, 5))
        for idx, center in enumerate(cluster_centers):
            plt.subplot(1, 3, idx + 1)
            
            # Get top terms
            top_indices = center.argsort()[-10:][::-1]
            top_terms = [feature_names[i] for i in top_indices]
            top_weights = center[top_indices]
            
            # Create horizontal bar plot
            plt.barh(range(len(top_terms)), top_weights)
            plt.yticks(range(len(top_terms)), top_terms)
            plt.title(f'Cluster {idx} Themes')
            
        plt.tight_layout()
    
    def generate_report(self, df):
        """Generate a statistical report of dream patterns"""
        report = []
        
        # Mood statistics
        mood_stats = df['mood'].value_counts()
        report.append("Mood Distribution:")
        for mood, count in mood_stats.items():
            report.append(f"- {mood}: {count} dreams ({count/len(df)*100:.1f}%)")
            
        # Time patterns
        time_patterns = df.groupby(df['created_at'].dt.hour)['mood'].value_counts()
        report.append("\nPeak Dream Recording Times:")
        peak_hours = time_patterns.groupby(level=0).sum().nlargest(3)
        for hour, count in peak_hours.items():
            report.append(f"- {hour:02d}:00: {count} dreams")
            
        return "\n".join(report)

def main():
    # Example usage (commented out as you'll integrate with your existing data)
    """
    from models import Dream  # Import your Dream model
    from sqlalchemy.orm import Session
    from database import SessionLocal
    
    # Get dreams from database
    db = SessionLocal()
    dreams = db.query(Dream).all()
    
    # Convert to DataFrame
    dreams_df = pd.DataFrame([
        {
            'dream_text': dream.content,
            'mood': dream.mood,
            'created_at': dream.created_at
        } for dream in dreams
    ])
    
    visualizer = DreamVisualizer()
    df, vectors = visualizer.prepare_data(dreams_df)
    
    # Generate visualizations
    visualizer.plot_mood_calendar(df)
    visualizer.plot_mood_distribution(df)
    visualizer.plot_theme_clusters(vectors)
    
    # Generate report
    print(visualizer.generate_report(df))
    """

if __name__ == "__main__":
    main()