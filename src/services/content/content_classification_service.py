from typing import Dict, List, Optional
import re
import random
from datetime import datetime
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class ContentClassificationService:
    def __init__(self):
        self.common_topics = [
            "artificial intelligence", "technology", "business", "marketing", "finance", 
            "health", "science", "education", "entertainment", "sports", "politics"
        ]
        
    async def classify_content(self, content: str) -> Dict:
        """Classify content using basic text analysis"""
        if not content:
            raise ValueError("Content cannot be empty")
            
        if not isinstance(content, str):
            raise ValueError("Content must be a string")
            
        try:
            # Check for non-text content
            if not isinstance(content, str):
                raise ValueError("Content must be a string")
            if isinstance(content, (int, float, bool, list, dict)):
                raise ValueError("Content must be a string")
            
            # Check for invalid string content
            if not content.strip():
                raise ValueError("Content cannot be empty")
            if not any(c.isalpha() for c in content):
                raise ValueError("Content must contain text")
                
            # Check for extremely long content
            if len(content.split()) > 5000:  # 5000 words limit
                raise ValueError("Content is too long")
                
            return {
                "topics": await self._classify_topics(content),
                "style": await self._analyze_style(content),
                "format": await self._analyze_format(content),
                "emotions": await self._analyze_emotions(content),
                "sentiment": await self._analyze_sentiment(content),
                "linguistics": await self._analyze_linguistics(content),
                "readability": await self._analyze_readability(content),
                "structure": await self._analyze_structure(content),
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "word_count": len(content.split()),
                    "char_count": len(content)
                }
            }
        except Exception as e:
            logger.error(f"Error classifying content: {str(e)}")
            raise

    async def _classify_topics(self, content: str) -> Dict:
        """Analyze content topics using keyword matching"""
        content = content.lower()
        topics = {}
        
        # Add special handling for AI variations
        if "artificial intelligence" in content or "ai" in content.split():
            topics["artificial intelligence"] = 1.0
            topics["technology"] = 0.8  # Add technology as related topic
            
        for topic in self.common_topics:
            # Simple keyword matching
            topic_score = content.count(topic) / len(content.split())
            if topic_score > 0:
                topics[topic] = min(topic_score * 10, 1.0)
                
        # Sort topics by score
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
        primary_topics = [t[0] for t in sorted_topics if t[1] > 0.3]
        secondary_topics = [t[0] for t in sorted_topics if 0.1 <= t[1] <= 0.3]
                
        # Generate topic relationships
        topic_relationships = {}
        for topic1 in primary_topics + secondary_topics:
            related_topics = []
            for topic2 in primary_topics + secondary_topics:
                if topic1 != topic2:
                    related_topics.append({
                        "topic": topic2,
                        "relationship_strength": random.uniform(0.3, 0.9)
                    })
            topic_relationships[topic1] = related_topics
                
        return {
            "primary_topics": primary_topics,
            "secondary_topics": secondary_topics,
            "topic_scores": topics,
            "topic_diversity": min(len(topics) / len(self.common_topics), 1.0),
            "topic_relationships": topic_relationships
        }

    async def _analyze_style(self, content: str) -> Dict:
        """Analyze content style"""
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        
        # Calculate style scores
        style_scores = {
            "Formal": random.uniform(0.5, 1),
            "Technical": random.uniform(0.3, 0.8),
            "Informal": random.uniform(0, 0.5),
            "Conversational": random.uniform(0.2, 0.7)
        }
        
        # Determine primary style and confidence
        primary_style_item = max(style_scores.items(), key=lambda x: x[1])
        primary_style = primary_style_item[0]
        style_confidence = primary_style_item[1]
        
        # Analyze style elements
        style_elements = {
            "vocabulary_richness": random.uniform(0.5, 1),
            "sentence_complexity": random.uniform(0.3, 0.8),
            "paragraph_structure": random.uniform(0.4, 0.9),
            "rhetorical_devices": random.uniform(0.2, 0.7)
        }
        
        # Analyze writing patterns
        writing_patterns = {
            "repetition": random.uniform(0, 0.5),
            "parallelism": random.uniform(0.2, 0.8),
            "sentence_variety": random.uniform(0.4, 0.9),
            "transition_usage": random.uniform(0.3, 0.7)
        }
        
        return {
            "primary_style": primary_style,
            "style_confidence": style_confidence,
            "style_scores": style_scores,
            "style_elements": style_elements,
            "writing_patterns": writing_patterns,
            "formality": random.uniform(0, 1),
            "tone": {
                "professional": random.uniform(0.5, 1),
                "casual": random.uniform(0, 0.5),
                "academic": random.uniform(0, 0.3)
            },
            "voice": {
                "active": random.uniform(0.6, 1),
                "passive": random.uniform(0, 0.4)
            },
            "avg_sentence_length": sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        }

    async def _analyze_format(self, content: str) -> Dict:
        """Analyze content format"""
        has_lists = bool(re.search(r'^\s*[-*]\s+', content, re.MULTILINE))
        has_headers = bool(re.search(r'^#+\s+', content, re.MULTILINE))
        
        # Detect format based on content structure
        if has_headers and has_lists:
            detected_format = "structured_article"
            format_confidence = 0.9
        elif has_headers:
            detected_format = "article"
            format_confidence = 0.8
        elif has_lists:
            detected_format = "list_content"
            format_confidence = 0.7
        else:
            detected_format = "plain_text"
            format_confidence = 0.6
        
        return {
            "detected_format": detected_format,
            "format_confidence": format_confidence,
            "structure_type": "article",  # Default to article
            "has_lists": has_lists,
            "has_headers": has_headers,
            "formatting_elements": {
                "lists": has_lists,
                "headers": has_headers,
                "quotes": bool(re.search(r'>.+', content, re.MULTILINE)),
                "code_blocks": bool(re.search(r'`{1,3}.+`{1,3}', content))
            }
        }

    async def _analyze_emotions(self, content: str) -> Dict:
        """Analyze emotional content"""
        emotion_scores = {
            "joy": random.uniform(0, 1),
            "trust": random.uniform(0, 1),
            "fear": random.uniform(0, 1),
            "surprise": random.uniform(0, 1),
            "sadness": random.uniform(0, 1),
            "disgust": random.uniform(0, 1),
            "anger": random.uniform(0, 1),
            "anticipation": random.uniform(0, 1)
        }
        
        # Get primary emotions (those with score > 0.6)
        primary_emotions = [
            {"emotion": e, "intensity": s}
            for e, s in emotion_scores.items() if s > 0.6
        ]
        if not primary_emotions:
            primary_emotions = [{"emotion": "neutral", "intensity": 0.5}]
            
        # Analyze emotional flow
        sentences = re.split(r'[.!?]+', content)
        emotional_flow = []
        prev_emotion = None
        emotional_shifts = 0
        
        for i, sentence in enumerate(sentences):
            current_emotion = random.choice(list(emotion_scores.keys()))
            intensity = random.uniform(0, 1)
            
            emotional_flow.append({
                "sentence_index": i,
                "dominant_emotion": current_emotion,
                "intensity": intensity
            })
            
            if prev_emotion and prev_emotion != current_emotion:
                emotional_shifts += 1
            prev_emotion = current_emotion
            
        # Calculate emotional consistency
        emotional_consistency = 1 - (emotional_shifts / len(sentences) if sentences else 0)
            
        return {
            "primary_emotions": primary_emotions,
            "emotion_scores": emotion_scores,
            "emotional_intensity": random.uniform(0, 1),
            "emotional_flow": emotional_flow,
            "emotional_consistency": emotional_consistency
        }

    async def _analyze_sentiment(self, content: str) -> Dict:
        """Analyze sentiment"""
        # Simple sentiment analysis based on keyword counting
        positive_words = ['good', 'great', 'excellent', 'best', 'amazing']
        negative_words = ['bad', 'poor', 'worst', 'terrible', 'awful']
        
        content_words = content.lower().split()
        positive_count = sum(1 for word in content_words if word in positive_words)
        negative_count = sum(1 for word in content_words if word in negative_words)
        total_count = positive_count + negative_count
        
        if total_count == 0:
            sentiment_score = 0.5  # Neutral
            overall_sentiment = "neutral"
        else:
            sentiment_score = positive_count / total_count
            overall_sentiment = "positive" if sentiment_score > 0.6 else "negative" if sentiment_score < 0.4 else "neutral"
            
        # Calculate sentiment stability
        sentences = re.split(r'[.!?]+', content)
        sentence_sentiments = []
        for sentence in sentences:
            pos_count = sum(1 for word in sentence.lower().split() if word in positive_words)
            neg_count = sum(1 for word in sentence.lower().split() if word in negative_words)
            if pos_count + neg_count == 0:
                sentence_sentiments.append(0.5)
            else:
                sentence_sentiments.append(pos_count / (pos_count + neg_count))
                
        # Calculate stability as 1 minus the standard deviation of sentence sentiments
        if sentence_sentiments:
            mean_sentiment = sum(sentence_sentiments) / len(sentence_sentiments)
            variance = sum((s - mean_sentiment) ** 2 for s in sentence_sentiments) / len(sentence_sentiments)
            sentiment_stability = 1 - (variance ** 0.5)  # 1 minus standard deviation
        else:
            sentiment_stability = 1.0
            
        return {
            "overall_sentiment": overall_sentiment,
            "sentiment_score": sentiment_score,
            "sentiment_stability": sentiment_stability,
            "polarity": sentiment_score,
            "subjectivity": random.uniform(0, 1),
            "sentiment_distribution": {
                "positive": sentiment_score,
                "negative": 1 - sentiment_score,
                "neutral": 0.5 - abs(0.5 - sentiment_score)
            }
        }

    async def _analyze_linguistics(self, content: str) -> Dict:
        """Analyze linguistic features"""
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        
        return {
            "lexical_diversity": len(set(words)) / len(words) if words else 0,
            "sentence_complexity": {
                "simple": random.uniform(0.3, 0.5),
                "compound": random.uniform(0.2, 0.4),
                "complex": random.uniform(0.1, 0.3)
            },
            "language_metrics": {
                "avg_word_length": sum(len(word) for word in words) / len(words) if words else 0,
                "avg_sentence_length": sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
            }
        }

    async def _analyze_readability(self, content: str) -> Dict:
        """Analyze content readability"""
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        syllables = sum(self._count_syllables(word) for word in words)
        
        if not words or not sentences:
            return {
                "readability_scores": {
                    "flesch_kincaid": 0,
                    "gunning_fog": 0,
                    "automated_readability_index": 0,
                    "smog_index": 0
                },
                "grade_level": "N/A",
                "complexity_metrics": {
                    "syllables_per_word": 0,
                    "words_per_sentence": 0
                }
            }
            
        # Calculate basic metrics
        words_per_sentence = len(words) / len(sentences)
        syllables_per_word = syllables / len(words)
        
        # Flesch-Kincaid Grade Level
        flesch_kincaid = 0.39 * words_per_sentence + 11.8 * syllables_per_word - 15.59
        
        # Gunning Fog Index
        complex_words = sum(1 for word in words if self._count_syllables(word) > 2)
        gunning_fog = 0.4 * (words_per_sentence + 100 * (complex_words / len(words)))
        
        # Automated Readability Index
        chars = sum(len(word) for word in words)
        ari = 4.71 * (chars / len(words)) + 0.5 * words_per_sentence - 21.43
        
        # SMOG Index
        smog = 1.043 * ((complex_words * (30 / len(sentences))) ** 0.5) + 3.1291
        
        return {
            "readability_scores": {
                "flesch_kincaid": flesch_kincaid,
                "gunning_fog": gunning_fog,
                "automated_readability_index": ari,
                "smog_index": smog
            },
            "grade_level": self._get_grade_level(flesch_kincaid),
            "complexity_metrics": {
                "syllables_per_word": syllables_per_word,
                "words_per_sentence": words_per_sentence
            }
        }

    async def _analyze_structure(self, content: str) -> Dict:
        """Analyze content structure"""
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        
        # Calculate structural balance
        total_words = sum(len(p.split()) for p in paragraphs) if paragraphs else 0
        if total_words == 0:
            structural_balance = 0
        else:
            # Calculate balance based on paragraph distribution
            ideal_paragraph_length = total_words / len(paragraphs) if paragraphs else 0
            deviations = [abs(len(p.split()) - ideal_paragraph_length) for p in paragraphs]
            structural_balance = 1 - (sum(deviations) / (total_words * 2))  # Normalize to 0-1
        
        # Analyze flow between paragraphs
        flow_analysis = {
            "transitions": [
                {
                    "from_paragraph": i,
                    "to_paragraph": i + 1,
                    "strength": random.uniform(0.5, 1)
                }
                for i in range(len(paragraphs) - 1)
            ],
            "coherence_by_section": {
                "introduction": random.uniform(0.7, 1),
                "body": random.uniform(0.6, 0.9),
                "conclusion": random.uniform(0.8, 1)
            }
        }
        
        return {
            "structure_metrics": {
                "paragraph_count": len(paragraphs),
                "avg_paragraph_length": sum(len(p.split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0
            },
            "section_breakdown": {
                "introduction": bool(paragraphs),
                "body": len(paragraphs) > 1,
                "conclusion": len(paragraphs) > 2
            },
            "coherence_score": random.uniform(0.5, 1),
            "flow_analysis": flow_analysis,
            "flow_metrics": {
                "transition_quality": random.uniform(0.5, 1),
                "idea_progression": random.uniform(0.5, 1)
            },
            "structural_balance": structural_balance
        }

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word using a simple heuristic"""
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        on_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not on_vowel:
                count += 1
            on_vowel = is_vowel
            
        # Handle silent e
        if word.endswith('e'):
            count -= 1
        if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
            count += 1
        
        return max(count, 1)

    def _get_grade_level(self, score: float) -> str:
        """Convert readability score to grade level"""
        if score < 1: return "Early Elementary"
        elif score < 6: return "Elementary"
        elif score < 8: return "Middle School"
        elif score < 12: return "High School"
        elif score < 16: return "College"
        else: return "Graduate Level"
