#!/usr/bin/env python
"""
Content Analysis Service for OnSide Reports

This service provides content analysis capabilities including:
- Sentiment analysis
- Topic modeling
- Entity recognition
- Content quality assessment
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
import aiohttp
import asyncio
from collections import Counter
import re
import os
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class ContentAnalyzer:
    """Service for analyzing content including news, articles, and web content."""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the content analyzer."""
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.openai_url = "https://api.openai.com/v1/chat/completions"
        
    async def analyze_news_articles(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a collection of news articles.
        
        Args:
            articles: List of article dictionaries with 'title', 'content', 'published_date'
            
        Returns:
            Analysis results including sentiment, topics, and key insights
        """
        if not articles:
            return {}
            
        logger.info(f"Analyzing {len(articles)} news articles")
        
        # Analyze sentiment and extract entities from each article
        analysis_tasks = [self._analyze_article(article) for article in articles[:20]]  # Limit to first 20 articles
        article_analyses = await asyncio.gather(*analysis_tasks)
        
        # Aggregate results
        return self._aggregate_analyses(article_analyses, articles)
    
    async def _analyze_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single news article."""
        try:
            # Extract text to analyze (title + first 2000 chars of content)
            text = f"{article.get('title', '')}\n\n{article.get('content', '')[:2000]}"
            
            # Get sentiment and entities in parallel
            sentiment_task = self._analyze_sentiment(text)
            entities_task = self._extract_entities(text)
            
            sentiment = await sentiment_task
            entities = await entities_task
            
            return {
                'sentiment': sentiment,
                'entities': entities,
                'published_date': article.get('published_date', datetime.utcnow().isoformat()),
                'source': article.get('source', {}).get('name', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Error analyzing article: {str(e)}")
            return {
                'sentiment': {'score': 0, 'label': 'neutral'},
                'entities': [],
                'error': str(e)
            }
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of the given text using OpenAI."""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.openai_api_key}'
            }
            
            payload = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are a sentiment analysis tool. Analyze the sentiment of the following text and respond with a JSON object containing a "score" from -1 (very negative) to 1 (very positive) and a "label" (positive, negative, or neutral).'
                    },
                    {
                        'role': 'user',
                        'content': f'Text: {text[:4000]}'
                    }
                ],
                'response_format': { 'type': 'json_object' },
                'temperature': 0.1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.openai_url, headers=headers, json=payload) as response:
                    result = await response.json()
                    
            # Parse the response
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                try:
                    sentiment = json.loads(content)
                    return {
                        'score': float(sentiment.get('score', 0)),
                        'label': sentiment.get('label', 'neutral').lower()
                    }
                except (json.JSONDecodeError, ValueError):
                    logger.warning("Failed to parse sentiment analysis response")
                    return {'score': 0, 'label': 'neutral'}
            
            return {'score': 0, 'label': 'neutral'}
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return {'score': 0, 'label': 'neutral'}
    
    async def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from the text using OpenAI."""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.openai_api_key}'
            }
            
            payload = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are an entity extraction tool. Extract the key entities (organizations, people, locations, products) from the following text and respond with a JSON array of objects, each with "entity", "type", and "relevance" (0-1) fields.'
                    },
                    {
                        'role': 'user',
                        'content': f'Text: {text[:4000]}'
                    }
                ],
                'response_format': { 'type': 'json_object' },
                'temperature': 0.1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.openai_url, headers=headers, json=payload) as response:
                    result = await response.json()
            
            # Parse the response
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                try:
                    data = json.loads(content)
                    if 'entities' in data:
                        return data['entities']
                except (json.JSONDecodeError, ValueError):
                    logger.warning("Failed to parse entity extraction response")
            
            return []
            
        except Exception as e:
            logger.error(f"Error in entity extraction: {str(e)}")
            return []
    
    def _aggregate_analyses(self, article_analyses: List[Dict[str, Any]], 
                          original_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate analyses of multiple articles into summary statistics."""
        if not article_analyses:
            return {}
        
        # Sentiment analysis
        sentiment_scores = [a['sentiment']['score'] for a in article_analyses if 'sentiment' in a]
        sentiment_labels = [a['sentiment']['label'] for a in article_analyses if 'sentiment' in a]
        
        # Entity analysis
        all_entities = []
        for analysis in article_analyses:
            if 'entities' in analysis:
                all_entities.extend(analysis['entities'])
        
        # Count entity frequencies
        entity_counter = Counter()
        for entity in all_entities:
            if isinstance(entity, dict) and 'entity' in entity:
                entity_counter[(entity['entity'], entity.get('type', 'OTHER'))] += 1
        
        # Get most common entities by type
        org_entities = [e for e, count in entity_counter.most_common() 
                       if e[1] == 'ORGANIZATION' and count > 1]
        person_entities = [e for e, count in entity_counter.most_common() 
                          if e[1] == 'PERSON' and count > 1]
        location_entities = [e for e, count in entity_counter.most_common() 
                           if e[1] == 'LOCATION' and count > 1]
        
        # Calculate sentiment distribution
        sentiment_dist = {
            'positive': sentiment_labels.count('positive') / len(sentiment_labels) if sentiment_labels else 0,
            'neutral': sentiment_labels.count('neutral') / len(sentiment_labels) if sentiment_labels else 0,
            'negative': sentiment_labels.count('negative') / len(sentiment_labels) if sentiment_labels else 0
        }
        
        # Calculate average sentiment
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        # Get most recent articles
        recent_articles = sorted(original_articles, 
                               key=lambda x: x.get('published_date', ''), 
                               reverse=True)[:5]
        
        return {
            'article_count': len(article_analyses),
            'avg_sentiment': avg_sentiment,
            'sentiment_distribution': sentiment_dist,
            'top_organizations': [e[0] for e in org_entities[:10]],
            'top_people': [e[0] for e in person_entities[:10]],
            'top_locations': [e[0] for e in location_entities[:10]],
            'recent_articles': [
                {
                    'title': a.get('title', ''),
                    'source': a.get('source', {}).get('name', 'unknown'),
                    'published_date': a.get('published_date', ''),
                    'url': a.get('url', '')
                }
                for a in recent_articles
            ]
        }
    
    def generate_content_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate human-readable insights from content analysis."""
        insights = []
        
        # Sentiment insights
        if 'avg_sentiment' in analysis:
            sentiment = analysis['avg_sentiment']
            if sentiment > 0.3:
                insights.append("Overall positive sentiment in recent coverage.")
            elif sentiment < -0.3:
                insights.append("Overall negative sentiment in recent coverage.")
            else:
                insights.append("Neutral to mixed sentiment in recent coverage.")
        
        # Top entities
        if 'top_organizations' in analysis and analysis['top_organizations']:
            orgs = ", ".join(analysis['top_organizations'][:3])
            insights.append(f"Frequently mentioned organizations: {orgs}.")
            
        if 'top_people' in analysis and analysis['top_people']:
            people = ", ".join(analysis['top_people'][:3])
            insights.append(f"Key people in the news: {people}.")
        
        # Content volume
        if 'article_count' in analysis:
            count = analysis['article_count']
            if count > 50:
                insights.append(f"High volume of coverage with {count} articles analyzed.")
            elif count > 10:
                insights.append(f"Moderate coverage with {count} articles analyzed.")
            else:
                insights.append(f"Limited coverage with only {count} articles analyzed.")
        
        return insights
