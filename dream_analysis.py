from collections import defaultdict
import datetime

class DreamAnalyzer:
    def __init__(self, dream_entries):
        self.dream_entries = dream_entries

    def analyze_patterns(self):
        """Analyze patterns in dream entries"""
        if not self.dream_entries:
            return {"message": "No dreams recorded yet"}

        # Initialize analysis containers
        mood_trends = defaultdict(list)
        monthly_counts = defaultdict(int)
        theme_frequency = defaultdict(int)
        
        for dream in self.dream_entries:
            # Analyze mood trends
            month = dream.timestamp.strftime('%Y-%m')
            mood_trends[month].append(dream.mood_score)
            monthly_counts[month] += 1
            
        # Calculate averages and trends
        mood_averages = {
            month: sum(scores)/len(scores) 
            for month, scores in mood_trends.items()
        }
        
        # Get overall statistics
        total_dreams = len(self.dream_entries)
        avg_dreams_per_month = sum(monthly_counts.values()) / len(monthly_counts) if monthly_counts else 0
        
        return {
            'total_dreams': total_dreams,
            'mood_trends': mood_averages,
            'dreams_per_month': dict(monthly_counts),
            'average_dreams_per_month': round(avg_dreams_per_month, 2)
        }

    def get_mood_distribution(self):
        """Calculate distribution of mood categories"""
        mood_counts = defaultdict(int)
        total_dreams = len(self.dream_entries)
        
        for dream in self.dream_entries:
            if dream.mood_score >= 0.5:
                mood_counts['very_positive'] += 1
            elif dream.mood_score >= 0.1:
                mood_counts['positive'] += 1
            elif dream.mood_score > -0.1:
                mood_counts['neutral'] += 1
            elif dream.mood_score > -0.5:
                mood_counts['negative'] += 1
            else:
                mood_counts['very_negative'] += 1
        
        # Convert to percentages
        mood_distribution = {
            mood: (count/total_dreams) * 100 
            for mood, count in mood_counts.items()
        }
        
        return mood_distribution