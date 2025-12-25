from typing import Dict, List
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

class SemanticService:
    def __init__(self):
        self.model_name = "sentence-transformers/all-mpnet-base-v2"
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the transformer model and tokenizer"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
        except Exception as e:
            logger.error(f"Error initializing semantic model: {str(e)}")
            raise

    def _get_embeddings(self, text: str) -> np.ndarray:
        """Get embeddings for input text"""
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            with torch.no_grad():
                outputs = self.model(**inputs)
            return outputs.last_hidden_state.mean(dim=1).numpy()
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return None

    async def analyze_content(self, content: str, keywords: List[str]) -> Dict:
        """Analyze content for semantic relevance"""
        try:
            content_embedding = self._get_embeddings(content)
            keyword_embeddings = [self._get_embeddings(keyword) for keyword in keywords]

            # Calculate keyword relevance
            keyword_similarities = [
                float(cosine_similarity(content_embedding, keyword_embedding)[0][0])
                for keyword_embedding in keyword_embeddings
            ]

            # Calculate topic coherence
            sentences = content.split('.')
            sentence_embeddings = [self._get_embeddings(sent) for sent in sentences if sent.strip()]
            coherence_scores = []
            
            for i in range(len(sentence_embeddings)-1):
                if sentence_embeddings[i] is not None and sentence_embeddings[i+1] is not None:
                    score = float(cosine_similarity(
                        sentence_embeddings[i],
                        sentence_embeddings[i+1]
                    )[0][0])
                    coherence_scores.append(score)

            # Calculate content depth
            unique_concepts = self._identify_unique_concepts(sentence_embeddings)
            depth_score = len(unique_concepts) / len(sentences)

            return {
                "keyword_relevance": np.mean(keyword_similarities),
                "topic_coherence": np.mean(coherence_scores) if coherence_scores else 0,
                "intent_alignment": self._calculate_intent_alignment(content_embedding, keyword_embeddings),
                "content_depth": depth_score,
                "detailed_scores": {
                    "keyword_similarities": dict(zip(keywords, keyword_similarities)),
                    "sentence_coherence": coherence_scores,
                    "unique_concepts": len(unique_concepts)
                }
            }
        except Exception as e:
            logger.error(f"Error in semantic analysis: {str(e)}")
            return None

    def _identify_unique_concepts(self, embeddings: List[np.ndarray]) -> List[np.ndarray]:
        """Identify unique concepts in the content"""
        unique_concepts = []
        
        for emb in embeddings:
            if emb is None:
                continue
                
            is_unique = True
            for concept in unique_concepts:
                similarity = float(cosine_similarity(emb, concept)[0][0])
                if similarity > 0.85:  # Threshold for considering concepts similar
                    is_unique = False
                    break
            
            if is_unique:
                unique_concepts.append(emb)
                
        return unique_concepts

    def _calculate_intent_alignment(self, content_embedding: np.ndarray, keyword_embeddings: List[np.ndarray]) -> float:
        """Calculate how well the content aligns with intended keywords"""
        try:
            keyword_space = np.mean(keyword_embeddings, axis=0)
            return float(cosine_similarity(content_embedding, keyword_space)[0][0])
        except Exception as e:
            logger.error(f"Error calculating intent alignment: {str(e)}")
            return 0.0
