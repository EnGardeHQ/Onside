"""Brand Discovery Conversational AI Service.

This service implements a natural language chat interface for the En Garde
Setup Wizard brand discovery process. It uses LLM to conduct a conversational
interview, extract structured data, and guide users through brand analysis setup.
"""
import json
import re
import uuid
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from sqlalchemy.orm import Session

from src.models.brand_discovery_chat import BrandDiscoveryChatSession
from src.schemas.brand_discovery_chat import (
    ChatMessage,
    ExtractedData,
    ConversationState,
    ChatStartResponse,
    ChatMessageResponse,
    BrandAnalysisQuestionnaire,
    FinalizeResponse,
)
from src.services.ai.llm_service import LLMService
from src.services.llm_provider import FallbackManager
from src.models.llm_fallback import LLMProvider
from src.models.report import Report

logger = logging.getLogger(__name__)


# System prompts for the conversational AI
SYSTEM_PROMPT = """You are a friendly and professional brand consultant AI helping users discover their brand's digital footprint. Your role is to:

1. Ask natural, conversational questions to gather required information
2. Extract structured data from user responses
3. Guide users through the brand discovery process smoothly
4. Be concise - ask ONE question at a time
5. Acknowledge responses before moving to the next question
6. Handle corrections gracefully ("Actually, I meant...")
7. Extract information even when users provide multiple details at once

REQUIRED INFORMATION TO COLLECT:
- brand_name: The company/brand name
- website: Primary website URL
- industry: Business industry/sector
- products_services: What they offer

OPTIONAL INFORMATION:
- target_markets: Geographic markets (cities, regions, countries)
- target_audience: Customer demographics/psychographics
- competitors: Known competitors (domain names or company names)
- marketing_goals: SEO/marketing objectives
- keywords: Target keywords for SEO

CONVERSATION STYLE:
- Warm and professional, not robotic
- Brief acknowledgments ("Great!", "Perfect!", "Got it!")
- Use "we" language to build partnership
- Ask follow-up questions if responses are vague
- Confirm ambiguous information

EXTRACTION RULES:
- Automatically detect URLs and clean them (remove http/https, trailing slashes)
- Extract multiple items from comma-separated or natural lists
- Recognize when user answers multiple questions in one response
- Map industry terms to standard categories when possible

When you have all REQUIRED fields, inform the user you're ready to analyze their brand."""


FEW_SHOT_EXAMPLES = """
EXAMPLE 1 - Basic Flow:
User: "Acme Corp"
Assistant: {"response": "Great! And what's your primary website URL?", "extracted": {"brand_name": "Acme Corp"}}

User: "acmecorp.com"
Assistant: {"response": "Perfect! What industry is Acme Corp in?", "extracted": {"website": "acmecorp.com"}}

User: "We make email marketing software"
Assistant: {"response": "Excellent - so SaaS/Email Marketing. Could you describe your products or services in a bit more detail?", "extracted": {"industry": "SaaS/Email Marketing"}}

User: "Email automation, newsletter tools, and campaign analytics for small businesses"
Assistant: {"response": "Fantastic! Who are your main competitors, if you know any?", "extracted": {"products_services": "Email automation, newsletter tools, and campaign analytics for small businesses"}}

User: "Mailchimp and Constant Contact"
Assistant: {"response": "Got it! Any specific marketing goals or keywords you want to target?", "extracted": {"competitors": ["Mailchimp", "Constant Contact"]}}

User: "email marketing, marketing automation, newsletter software"
Assistant: {"response": "Perfect! I have everything I need. Let me analyze Acme Corp's digital footprint and competitive landscape.", "extracted": {"keywords": ["email marketing", "marketing automation", "newsletter software"]}}

EXAMPLE 2 - Multiple Details at Once:
User: "Hi, I'm setting up for my company DataViz Pro, we're at datavizpro.io and we do data visualization software"
Assistant: {"response": "Wonderful! I got that you're DataViz Pro (datavizpro.io) in the data visualization software space. What specific products or services do you offer?", "extracted": {"brand_name": "DataViz Pro", "website": "datavizpro.io", "industry": "Data Visualization Software"}}

EXAMPLE 3 - Handling Corrections:
User: "techstartup.com"
Assistant: {"response": "Great! What industry is your brand in?", "extracted": {"website": "techstartup.com"}}

User: "Actually, the website is techstartup.co, not .com"
Assistant: {"response": "No problem, updated to techstartup.co. Now, what industry are you in?", "extracted": {"website": "techstartup.co"}}

EXAMPLE 4 - Clarification Needed:
User: "We sell stuff online"
Assistant: {"response": "Could you be more specific? What type of products or services do you offer?", "extracted": {}}
"""


class BrandDiscoveryChatService:
    """Service for managing conversational brand discovery."""

    # Required fields that must be collected
    REQUIRED_FIELDS = ['brand_name', 'website', 'industry', 'products_services']

    # Field weights for progress calculation
    FIELD_WEIGHTS = {
        'brand_name': 15,
        'website': 15,
        'industry': 15,
        'products_services': 15,
        'target_markets': 8,
        'target_audience': 8,
        'competitors': 12,
        'marketing_goals': 6,
        'keywords': 6,
    }

    def __init__(self, db: Session):
        """Initialize the chat service.

        Args:
            db: Database session
        """
        self.db = db
        self.llm_service = LLMService()
        self.fallback_manager = FallbackManager()

    def start_conversation(self, user_id: str) -> ChatStartResponse:
        """Start a new brand discovery chat session.

        Args:
            user_id: User identifier

        Returns:
            ChatStartResponse with session_id and first message
        """
        # Create new session
        session = BrandDiscoveryChatSession(
            user_id=user_id,
            messages=[],
            extracted_data={},
            status='active'
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        # First AI message
        first_message = (
            "Hi! I'm here to help you discover your brand's digital footprint. "
            "Let's start with the basics - what's your brand or company name?"
        )

        # Store first message
        self._add_message(session, "assistant", first_message)

        logger.info(f"Started new brand discovery chat session: {session.session_id} for user: {user_id}")

        return ChatStartResponse(
            session_id=session.session_id,
            first_message=first_message
        )

    async def send_message(self, session_id: uuid.UUID, user_message: str) -> ChatMessageResponse:
        """Process user message and generate AI response.

        Args:
            session_id: Chat session ID
            user_message: User's message

        Returns:
            ChatMessageResponse with AI response and extracted data

        Raises:
            ValueError: If session not found or not active
        """
        # Get session
        session = self._get_session(session_id)

        if session.status != 'active':
            raise ValueError(f"Session {session_id} is not active (status: {session.status})")

        # Add user message
        self._add_message(session, "user", user_message)

        # Get AI response with extraction
        ai_response, updated_data = await self._generate_response(session, user_message)

        # Update extracted data
        session.extracted_data.update(updated_data)

        # Add AI response
        self._add_message(session, "assistant", ai_response)

        # Calculate progress
        progress_pct = self._calculate_progress(session.extracted_data)
        is_complete = self._is_complete(session.extracted_data)

        # Mark as completed if done
        if is_complete:
            session.status = 'completed'

        session.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(session)

        logger.info(f"Processed message for session {session_id}, progress: {progress_pct}%")

        return ChatMessageResponse(
            ai_response=ai_response,
            progress_pct=progress_pct,
            extracted_data=ExtractedData(**session.extracted_data),
            is_complete=is_complete,
            session_id=session.session_id
        )

    def get_conversation_state(self, session_id: uuid.UUID) -> ConversationState:
        """Get current state of conversation.

        Args:
            session_id: Chat session ID

        Returns:
            ConversationState with progress and extracted data
        """
        session = self._get_session(session_id)

        progress_pct = self._calculate_progress(session.extracted_data)
        missing_fields = self._get_missing_required_fields(session.extracted_data)
        is_complete = self._is_complete(session.extracted_data)

        return ConversationState(
            session_id=session.session_id,
            extracted_data=ExtractedData(**session.extracted_data),
            progress_pct=progress_pct,
            missing_fields=missing_fields,
            is_complete=is_complete
        )

    def finalize_conversation(self, session_id: uuid.UUID) -> FinalizeResponse:
        """Finalize conversation and create brand analysis questionnaire.

        Args:
            session_id: Chat session ID

        Returns:
            FinalizeResponse with questionnaire

        Raises:
            ValueError: If required fields are missing
        """
        session = self._get_session(session_id)

        # Validate required fields
        missing_fields = self._get_missing_required_fields(session.extracted_data)
        if missing_fields:
            raise ValueError(f"Cannot finalize: missing required fields: {', '.join(missing_fields)}")

        # Build questionnaire
        questionnaire_data = {
            'brand_name': session.extracted_data.get('brand_name'),
            'website': session.extracted_data.get('website'),
            'industry': session.extracted_data.get('industry'),
            'products_services': session.extracted_data.get('products_services'),
            'target_markets': session.extracted_data.get('target_markets'),
            'target_audience': session.extracted_data.get('target_audience'),
            'competitors': session.extracted_data.get('competitors'),
            'marketing_goals': session.extracted_data.get('marketing_goals'),
            'keywords': session.extracted_data.get('keywords'),
        }

        questionnaire = BrandAnalysisQuestionnaire(**questionnaire_data)

        # Mark session as completed
        session.status = 'completed'
        session.updated_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Finalized brand discovery chat session: {session_id}")

        return FinalizeResponse(
            questionnaire=questionnaire,
            message=f"Brand discovery complete! Ready to analyze {questionnaire.brand_name}."
        )

    # Private helper methods

    def _get_session(self, session_id: uuid.UUID) -> BrandDiscoveryChatSession:
        """Get session by ID or raise error."""
        session = self.db.query(BrandDiscoveryChatSession).filter(
            BrandDiscoveryChatSession.session_id == session_id
        ).first()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        return session

    def _add_message(self, session: BrandDiscoveryChatSession, role: str, content: str):
        """Add a message to the session."""
        if session.messages is None:
            session.messages = []

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        session.messages.append(message)

    async def _generate_response(self, session: BrandDiscoveryChatSession, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Generate AI response and extract data from user message.

        Args:
            session: Chat session
            user_message: User's message

        Returns:
            Tuple of (AI response text, extracted data dict)
        """
        # Build conversation history
        conversation_history = self._build_conversation_context(session)

        # Build prompt for LLM
        prompt = self._build_extraction_prompt(
            conversation_history=conversation_history,
            current_data=session.extracted_data,
            user_message=user_message
        )

        try:
            # Use LLM service for chat completion with JSON mode
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]

            result = await self.llm_service.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            # Parse response (should be JSON)
            content = result.get('content', '{}')
            response_data = json.loads(content)

            ai_response = response_data.get('response', 'Could you tell me more?')
            extracted = response_data.get('extracted', {})

            # Clean extracted data
            extracted = self._clean_extracted_data(extracted)

            return ai_response, extracted

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")

            # Fallback to simple rule-based extraction
            ai_response, extracted = self._fallback_extraction(session.extracted_data, user_message)
            return ai_response, extracted

    def _build_conversation_context(self, session: BrandDiscoveryChatSession) -> str:
        """Build conversation history for context."""
        if not session.messages:
            return ""

        # Take last 10 messages for context
        recent_messages = session.messages[-10:]

        context = []
        for msg in recent_messages:
            role = msg['role'].capitalize()
            content = msg['content']
            context.append(f"{role}: {content}")

        return "\n".join(context)

    def _build_extraction_prompt(
        self,
        conversation_history: str,
        current_data: Dict[str, Any],
        user_message: str
    ) -> str:
        """Build prompt for LLM to extract data and generate response."""

        missing_required = self._get_missing_required_fields(current_data)

        prompt = f"""{SYSTEM_PROMPT}

{FEW_SHOT_EXAMPLES}

CURRENT CONVERSATION:
{conversation_history}

ALREADY COLLECTED DATA:
{json.dumps(current_data, indent=2)}

MISSING REQUIRED FIELDS:
{', '.join(missing_required) if missing_required else 'None - all required fields collected'}

USER'S LATEST MESSAGE:
{user_message}

INSTRUCTIONS:
1. Extract any new information from the user's message
2. Update the extracted data with new findings
3. Generate a natural follow-up question or acknowledgment
4. If all required fields are collected, let the user know you're ready to analyze their brand

Respond in JSON format:
{{
    "response": "Your conversational response to the user",
    "extracted": {{
        "field_name": "extracted value",
        ...
    }}
}}

Focus on collecting: {missing_required[0] if missing_required else 'optional information like competitors or keywords'}
"""
        return prompt

    def _clean_extracted_data(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize extracted data."""
        cleaned = {}

        for field, value in extracted.items():
            if value is None or value == '':
                continue

            # Clean website URLs
            if field == 'website' and isinstance(value, str):
                value = self._clean_url(value)

            # Ensure lists for multi-value fields
            if field in ['target_markets', 'competitors', 'keywords']:
                if isinstance(value, str):
                    # Split by commas or 'and'
                    value = [item.strip() for item in re.split(r',|\sand\s', value) if item.strip()]
                elif not isinstance(value, list):
                    value = [value]

            cleaned[field] = value

        return cleaned

    def _clean_url(self, url: str) -> str:
        """Clean and normalize URL."""
        # Remove protocol
        url = re.sub(r'^https?://', '', url)
        # Remove www
        url = re.sub(r'^www\.', '', url)
        # Remove trailing slash
        url = url.rstrip('/')
        # Remove path (keep only domain)
        url = url.split('/')[0]
        return url.lower()

    def _fallback_extraction(
        self,
        current_data: Dict[str, Any],
        user_message: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Simple rule-based extraction when LLM fails.

        This is a backup extraction mechanism using regex and pattern matching.
        """
        extracted = {}

        # Try to extract URL
        url_pattern = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})'
        url_match = re.search(url_pattern, user_message)
        if url_match and 'website' not in current_data:
            extracted['website'] = self._clean_url(url_match.group(0))

        # Try to extract brand name (if it's the first message and no brand name yet)
        if 'brand_name' not in current_data and len(user_message.split()) <= 5:
            # Likely a brand name if short
            extracted['brand_name'] = user_message.strip()

        # Generate next question based on what's missing
        missing = self._get_missing_required_fields({**current_data, **extracted})

        if 'brand_name' in missing:
            response = "What's your brand or company name?"
        elif 'website' in missing:
            response = "What's your primary website URL?"
        elif 'industry' in missing:
            response = "What industry are you in?"
        elif 'products_services' in missing:
            response = "What products or services do you offer?"
        else:
            response = "Great! Do you know any competitors?"

        return response, extracted

    def _calculate_progress(self, extracted_data: Dict[str, Any]) -> int:
        """Calculate completion progress percentage."""
        total_weight = sum(self.FIELD_WEIGHTS.values())
        earned_weight = 0

        for field, weight in self.FIELD_WEIGHTS.items():
            value = extracted_data.get(field)
            if value is not None and value != '' and value != []:
                earned_weight += weight

        progress = int((earned_weight / total_weight) * 100)
        return min(progress, 100)

    def _get_missing_required_fields(self, extracted_data: Dict[str, Any]) -> List[str]:
        """Get list of missing required fields."""
        missing = []

        for field in self.REQUIRED_FIELDS:
            value = extracted_data.get(field)
            if value is None or value == '' or value == []:
                missing.append(field)

        return missing

    def _is_complete(self, extracted_data: Dict[str, Any]) -> bool:
        """Check if all required fields are collected."""
        return len(self._get_missing_required_fields(extracted_data)) == 0
