"""
Multilingual NLU (Natural Language Understanding) Engine
Supports English, Hindi, and regional languages
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, Optional
from openai import OpenAI
import json
import re


class MultilingualNLU:
    """
    Natural Language Understanding for multilingual educational queries
    Supports: English, Hindi, and regional Indian languages
    """
    
    # Language detection patterns
    LANGUAGE_PATTERNS = {
        'hi': re.compile(r'[\u0900-\u097F]'),  # Devanagari script
        'ta': re.compile(r'[\u0B80-\u0BFF]'),  # Tamil
        'te': re.compile(r'[\u0C00-\u0C7F]'),  # Telugu
        'kn': re.compile(r'[\u0C80-\u0CFF]'),  # Kannada
        'ml': re.compile(r'[\u0D00-\u0D7F]'),  # Malayalam
        'gu': re.compile(r'[\u0A80-\u0AFF]'),  # Gujarati
        'pa': re.compile(r'[\u0A00-\u0A7F]'),  # Punjabi
        'bn': re.compile(r'[\u0980-\u09FF]'),  # Bengali
    }
    
    LANGUAGE_NAMES = {
        'en': 'English',
        'hi': 'Hindi',
        'ta': 'Tamil',
        'te': 'Telugu',
        'kn': 'Kannada',
        'ml': 'Malayalam',
        'gu': 'Gujarati',
        'pa': 'Punjabi',
        'bn': 'Bengali'
    }
    
    def __init__(self, openai_api_key: str):
        self.openai_client = OpenAI(api_key=openai_api_key)
    
    def detect_language(self, text: str) -> str:
        """Detect language of input text"""
        
        # Check for Indic scripts
        for lang_code, pattern in self.LANGUAGE_PATTERNS.items():
            if pattern.search(text):
                return lang_code
        
        # Default to English
        return 'en'
    
    def translate_to_english(self, text: str, source_language: str) -> str:
        """
        Translate non-English text to English for processing
        """
        
        if source_language == 'en':
            return text
        
        lang_name = self.LANGUAGE_NAMES.get(source_language, source_language)
        
        try:
            completion = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a translator. Translate the following {lang_name} text to English. Preserve the meaning and intent. Respond only with the English translation."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.3
            )
            
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Translation error: {e}")
            return text  # Return original if translation fails
    
    def translate_from_english(self, text: str, target_language: str) -> str:
        """
        Translate English response back to target language
        """
        
        if target_language == 'en':
            return text
        
        lang_name = self.LANGUAGE_NAMES.get(target_language, target_language)
        
        try:
            completion = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a translator. Translate the following English text to {lang_name}. Maintain a respectful, educational tone appropriate for academic contexts. Respond only with the {lang_name} translation."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.3
            )
            
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Translation error: {e}")
            return text  # Return original if translation fails
    
    def extract_intent(self, text: str, language: str = 'en') -> Dict[str, Any]:
        """
        Extract intent from multilingual query
        """
        
        # Common intents across languages
        intents = {
            'risk_check': [
                'risk', 'danger', 'fail', 'problem', 'issue',
                'जोखिम', 'खतरा', 'समस्या'  # Hindi
            ],
            'performance': [
                'performance', 'grade', 'marks', 'cgpa', 'gpa',
                'प्रदर्शन', 'अंक', 'ग्रेड'  # Hindi
            ],
            'attendance': [
                'attendance', 'absent', 'classes', 'present',
                'उपस्थिति', 'कक्षा'  # Hindi
            ],
            'advice': [
                'help', 'improve', 'suggestion', 'advice', 'guidance',
                'सहायता', 'सुधार', 'सलाह', 'मार्गदर्शन'  # Hindi
            ],
            'career': [
                'career', 'job', 'placement', 'future', 'profession',
                'करियर', 'नौकरी', 'भविष्य'  # Hindi
            ]
        }
        
        # Convert text to lowercase for matching
        text_lower = text.lower()
        
        # Check for intent keywords
        detected_intents = []
        for intent, keywords in intents.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_intents.append(intent)
        
        # If no clear intent, default to general query
        if not detected_intents:
            detected_intents = ['general']
        
        return {
            'primary_intent': detected_intents[0],
            'all_intents': detected_intents,
            'language': language,
            'confidence': 0.8 if detected_intents != ['general'] else 0.5
        }
    
    def process_multilingual_query(self, query: str) -> Dict[str, Any]:
        """
        Complete multilingual query processing pipeline
        """
        
        # Step 1: Detect language
        detected_lang = self.detect_language(query)
        
        # Step 2: Translate to English if needed
        english_query = query
        if detected_lang != 'en':
            english_query = self.translate_to_english(query, detected_lang)
        
        # Step 3: Extract intent
        intent_data = self.extract_intent(english_query, detected_lang)
        
        return {
            'original_query': query,
            'detected_language': detected_lang,
            'language_name': self.LANGUAGE_NAMES.get(detected_lang, 'English'),
            'english_translation': english_query if detected_lang != 'en' else None,
            'intent': intent_data,
            'processed_query': english_query
        }
    
    def format_response(self, response: str, target_language: str) -> str:
        """
        Format response in target language
        """
        
        if target_language == 'en':
            return response
        
        return self.translate_from_english(response, target_language)


# Example usage and testing
if __name__ == "__main__":
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if api_key:
        nlu = MultilingualNLU(api_key)
        
        # Test queries in different languages
        test_queries = [
            "What is my risk level?",
            "मेरा जोखिम स्तर क्या है?",  # Hindi
            "How can I improve my attendance?",
            "मैं अपनी उपस्थिति कैसे सुधार सकता हूं?"  # Hindi
        ]
        
        print("\n" + "="*60)
        print("MULTILINGUAL NLU TESTING")
        print("="*60)
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            result = nlu.process_multilingual_query(query)
            print(f"Language: {result['language_name']}")
            print(f"Intent: {result['intent']['primary_intent']}")
            if result['english_translation']:
                print(f"Translation: {result['english_translation']}")
            print("-" * 60)
    else:
        print("❌ OPENAI_API_KEY not found!")
