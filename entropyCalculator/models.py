import nltk
import math
import re
from django.db import models
from textblob import TextBlob
from nltk.tokenize import sent_tokenize
from deep_translator import GoogleTranslator
from collections import Counter

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('vader_lexicon')

class ViralContentAnalyzer:
    """
    Enhanced semantic entropy calculator optimized for restaurant social media posts
    with translation capabilities
    """
    
    # Enhanced certainty indicators for marketing content
    CERTAINTY_WORDS = {
        'definitely': 0.95, 'certainly': 0.95, 'surely': 0.90, 'absolutely': 0.95,
        'undoubtedly': 0.95, 'clearly': 0.85, 'obviously': 0.85, 'guaranteed': 0.95,
        'always': 0.90, 'never': 0.90, 'perfect': 0.85, 'best': 0.80,
        'probably': 0.75, 'likely': 0.70, 'perhaps': 0.50, 'maybe': 0.50,
        'possibly': 0.40, 'unlikely': 0.30, 'doubtful': 0.20, 'might': 0.40,
        'could': 0.50, 'may': 0.50
    }
    
    # Viral content indicators (positive impact on virality)
    VIRAL_INDICATORS = {
        'emoji_density': 0.1,           # Positive impact of emojis
        'exclamation_density': 0.05,    # Positive impact of exclamations
        'question_density': -0.03,      # Questions might reduce certainty
        'emotional_words': 0.08,        # Emotional language
        'sensory_words': 0.07,          # Sensory descriptions
        'urgency_words': 0.06,          # Urgency/scarcity
        'social_proof': 0.09,           # Social validation words
        'curiosity_gaps': 0.08          # Creates curiosity
    }
    
    # Emotional and sensory words common in viral food content
    EMOTIONAL_WORDS = {
        'amazing', 'incredible', 'unforgettable', 'memorable', 'fantastic', 'wonderful',
        'delicious', 'mouthwatering', 'delectable', 'scrumptious', 'tasty', 'flavorful',
        'crave', 'addictive', 'irresistible', 'heavenly', 'divine', 'perfect'
    }
    
    SENSORY_WORDS = {
        'crispy', 'creamy', 'juicy', 'tender', 'flaky', 'buttery', 'aromatic',
        'fragrant', 'savory', 'sweet', 'spicy', 'tangy', 'zesty', 'fresh'
    }
    
    URGENCY_WORDS = {
        'limited', 'exclusive', 'special', 'now', 'today', 'hurry', 'quick',
        'before', 'ends', 'last chance', 'don\'t miss', 'hot'
    }
    
    SOCIAL_PROOF_WORDS = {
        'popular', 'favorite', 'loved', 'recommended', 'trending', 'viral',
        'everyone', 'customers', 'guests', 'fans'
    }
    
    @classmethod
    def translate_to_english(cls, text):
        """
        Translate Vietnamese text to English for better analysis
        """
        try:
            # Remove excessive emojis for translation (keep a few for context)
            clean_text = re.sub(r'([\U0001F600-\U0001F64F]){2,}', r'\1', text)
            
            translator = GoogleTranslator(source='vi', target='en')
            translated = translator.translate(clean_text)
            return translated
        except Exception as e:
            print(f"Translation error: {e}")
            return text  # Return original if translation fails
    
    @classmethod
    def extract_viral_features(cls, text):
        """
        Extract features that contribute to virality
        """
        features = {}
        
        # Emoji density
        emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', text))
        features['emoji_density'] = min(emoji_count / len(text.split()), 0.1)  # Normalize
        
        # Exclamation density
        exclamation_count = text.count('!')
        features['exclamation_density'] = min(exclamation_count / len(text.split()), 0.1)
        
        # Question density
        question_count = text.count('?')
        features['question_density'] = min(question_count / len(text.split()), 0.05)
        
        # Emotional words density
        words = text.lower().split()
        emotional_count = sum(1 for word in words if word in cls.EMOTIONAL_WORDS)
        features['emotional_words'] = min(emotional_count / len(words), 0.2)
        
        # Sensory words density
        sensory_count = sum(1 for word in words if word in cls.SENSORY_WORDS)
        features['sensory_words'] = min(sensory_count / len(words), 0.2)
        
        # Urgency words density
        urgency_count = sum(1 for word in words if word in cls.URGENCY_WORDS)
        features['urgency_words'] = min(urgency_count / len(words), 0.15)
        
        # Social proof density
        social_count = sum(1 for word in words if word in cls.SOCIAL_PROOF_WORDS)
        features['social_proof'] = min(social_count / len(words), 0.15)
        
        # Curiosity gaps (questions, mysterious phrases)
        curiosity_indicators = len(re.findall(r'\b(mystery|secret|discover|find out|what if|imagine)\b', text.lower()))
        features['curiosity_gaps'] = min(curiosity_indicators / len(words), 0.1)
        
        return features
    
    @classmethod
    def calculate_sentence_entropy(cls, sentence, viral_features=None):
        """
        Calculate semantic entropy for a single sentence with viral content optimization
        """
        blob = TextBlob(sentence.lower())
        words = [word for word in blob.words if word.isalpha()]
        
        # Base probability for neutral statements
        base_probability = 0.5
        
        # Check for certainty words
        certainty_found = False
        for word, prob in cls.CERTAINTY_WORDS.items():
            if word in sentence.lower():
                base_probability = prob
                certainty_found = True
                break
        
        # Adjust for sentiment (stronger impact for marketing content)
        sentiment = blob.sentiment.polarity
        sentiment_boost = sentiment * 0.3  # Increased impact for emotional content
        base_probability = max(0.1, min(0.95, base_probability + sentiment_boost))
        
        # Apply viral features adjustment if provided
        viral_adjustment = 0
        if viral_features:
            for feature, weight in cls.VIRAL_INDICATORS.items():
                viral_adjustment += viral_features.get(feature, 0) * weight
        
        base_probability = max(0.1, min(0.95, base_probability + viral_adjustment))
        
        # Calculate entropy
        p_event = base_probability
        p_no_event = 1 - p_event
        
        # Handle edge cases for log calculations
        entropy_event = p_event * math.log2(p_event) if p_event > 0 else 0
        entropy_no_event = p_no_event * math.log2(p_no_event) if p_no_event > 0 else 0
        
        entropy = - (entropy_event + entropy_no_event)
        
        return {
            'sentence': sentence,
            'probability': p_event,
            'entropy': entropy,
            'confidence': 1 - entropy,
            'sentiment': sentiment,
            'viral_adjustment': viral_adjustment
        }
    
    @classmethod
    def calculate_viral_potential(cls, paragraph):
        """
        Calculate semantic entropy with viral potential analysis
        """
        # First translate to English
        translated_paragraph = cls.translate_to_english(paragraph)
        
        sentences = sent_tokenize(translated_paragraph)
        
        if not sentences:
            return {
                'original_paragraph': paragraph,
                'translated_paragraph': translated_paragraph,
                'total_entropy': 0,
                'average_entropy': 0,
                'viral_score': 0,
                'sentence_details': [],
                'overall_confidence': 0,
                'viral_features': {}
            }
        
        # Extract viral features from the entire paragraph
        viral_features = cls.extract_viral_features(translated_paragraph)
        print("viral_features:::::", viral_features)
        sentence_entropies = []
        total_entropy = 0
        
        for sentence in sentences:
            sentence_data = cls.calculate_sentence_entropy(sentence.strip(), viral_features)
            sentence_entropies.append(sentence_data)
            total_entropy += sentence_data['entropy']
        
        average_entropy = total_entropy / len(sentences)
        overall_confidence = 1 - average_entropy
        
        # Calculate viral score (lower entropy + higher viral features = better)
        viral_score = (overall_confidence * 0.6) + (sum(viral_features.values()) * 0.4)
        
        # Compare with reference viral content if provided
        # viral_comparison = None
        # if reference_viral_entropy is not None:
        #     entropy_difference = reference_viral_entropy - average_entropy
        #     print("entropy_difference:::::", entropy_difference)
        #     viral_comparison = {
        #         'reference_entropy': reference_viral_entropy,
        #         'entropy_difference': entropy_difference,
        #         'is_more_viral_potential': entropy_difference > 0
        #     }
        
        return {
            'original_paragraph': paragraph,
            'translated_paragraph': translated_paragraph,
            'total_entropy': total_entropy,
            'average_entropy': average_entropy,
            'viral_score': viral_score,
            'sentence_details': sentence_entropies,
            'overall_confidence': overall_confidence,
            'viral_features': viral_features,
        }