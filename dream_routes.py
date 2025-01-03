from flask import Blueprint, jsonify, request
from sqlalchemy.orm import Session
from models import DreamEntry, db_session
from mood_analyzer import MoodAnalyzer
import nltk
import pandas as pd
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt

# Create Blueprint instead of APIRouter
dream_bp = Blueprint('dreams', __name__)

# Initialize NLTK data at startup
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')
    nltk.download('punkt')

# Create a single instance of MoodAnalyzer to be reused
mood_analyzer = MoodAnalyzer()

@dream_bp.route("/dreams/analysis/<int:dream_id>", methods=['GET'])
def get_dream_analysis(dream_id):
    try:
        dream = db_session.query(DreamEntry).filter(DreamEntry.dream_id == dream_id).first()
        if not dream:
            return jsonify({"error": "Dream not found"}), 404
            
        analysis = mood_analyzer.get_detailed_analysis(dream.dream_text)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

@dream_bp.route("/dreams/visualizations", methods=['GET'])
def get_dream_visualizations():
    try:
        # Convert matplotlib figures to base64 strings
        results = mood_analyzer.visualize_mood_patterns()
        
        # Save current figures as base64 strings
        visualizations = {}
        for fig_num in plt.get_fignums():
            fig = plt.figure(fig_num)
            visualizations[f'figure_{fig_num}'] = _figure_to_base64(fig)
        
        # Clear all figures to free memory
        plt.close('all')
        
        return jsonify({
            'visualizations': visualizations,
            'report': results.get('report', '')
        })
    except Exception as e:
        return jsonify({"error": f"Visualization failed: {str(e)}"}), 500

def _figure_to_base64(fig):
    """Convert matplotlib figure to base64 string"""
    buf = io.BytesIO()
    FigureCanvas(fig).print_png(buf)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

@dream_bp.route("/dreams/theme-visualization", methods=['GET'])
def get_theme_visualization():
    try:
        df, vectors = mood_analyzer.get_theme_visualization()
        
        # Convert the current figure to base64
        theme_viz = _figure_to_base64(plt.gcf())
        plt.close('all')
        
        return jsonify({
            'visualization': theme_viz,
            'theme_count': len(set(vectors.toarray().nonzero()[1]))
        })
    except Exception as e:
        return jsonify({"error": f"Theme visualization failed: {str(e)}"}), 500

# Error handling
@dream_bp.errorhandler(Exception)
def handle_error(error):
    return jsonify({
        "error": f"An unexpected error occurred: {str(error)}"
    }), 500