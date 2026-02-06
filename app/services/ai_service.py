import os
import json
from typing import Dict, Any
from openai import AzureOpenAI
from app.models import AreaEnum


class AIService:
    """Service for AI-powered rumor validation and moderation using Azure OpenAI"""
    
    def __init__(self):
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        api_key = os.getenv('AZURE_OPENAI_API_KEY')
        
        if endpoint and api_key:
            self.client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version="2024-02-15-preview"
            )
            self.model = os.getenv('AZURE_OPENAI_MODEL', 'gpt-4')
        else:
            self.client = None
            self.model = None
    
    def validate_rumor(self, content: str) -> Dict[str, Any]:
        """
        Validate if content is a rumor worthy of voting
        
        Returns:
            {
                'isValid': bool,
                'isRumor': bool,
                'reason': str,
                'suggestedArea': str
            }
        """
        if not self.client:
            # Fallback validation when AI is not configured
            return self._fallback_validation(content)
        
        try:
            return self._validate_with_azure_openai(content)
        except Exception as e:
            print(f"AI validation error: {str(e)}")
            return self._fallback_validation(content)
    
    def _validate_with_azure_openai(self, content: str) -> Dict[str, Any]:
        """Validate using Azure OpenAI"""
        system_prompt = """You are a rumor validator for a university community platform. 
Analyze if the given text is:
1. An unverified claim (rumor) - ACCEPT
2. A known fact that can be easily verified - REJECT
3. Nonsense/spam/inappropriate content - REJECT

Also suggest which area this rumor belongs to from: SEECS, NBS, ASAB, SINES, SCME, S3H, General

Return a JSON object with:
- isValid (boolean): whether this should be accepted
- isRumor (boolean): whether this is actually a rumor
- reason (string): explanation of the decision
- suggestedArea (string): one of the valid areas

Be strict: only accept genuine rumors that need community verification."""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this text:\n\n{content}"}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return self._normalize_response(result)
    
    def _fallback_validation(self, content: str) -> Dict[str, Any]:
        """Fallback validation when AI is not available"""
        # Basic validation rules
        content = content.strip()
        
        # Reject very short content
        if len(content) < 20:
            return {
                'isValid': False,
                'isRumor': False,
                'reason': 'Content too short to be a meaningful rumor',
                'suggestedArea': 'General'
            }
        
        # Check for spam patterns
        spam_patterns = ['click here', 'buy now', 'limited offer', 'www.', 'http']
        if any(pattern.lower() in content.lower() for pattern in spam_patterns):
            return {
                'isValid': False,
                'isRumor': False,
                'reason': 'Content appears to be spam',
                'suggestedArea': 'General'
            }
        
        # Accept by default in fallback mode
        return {
            'isValid': True,
            'isRumor': True,
            'reason': 'Content appears to be a rumor (AI validation disabled)',
            'suggestedArea': 'General'
        }
    
    def _normalize_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize AI response to expected format"""
        # Validate suggested area
        suggested_area = result.get('suggestedArea', 'General')
        valid_areas = [e.value for e in AreaEnum]
        
        if suggested_area not in valid_areas:
            suggested_area = 'General'
        
        return {
            'isValid': bool(result.get('isValid', False)),
            'isRumor': bool(result.get('isRumor', False)),
            'reason': str(result.get('reason', 'No reason provided')),
            'suggestedArea': suggested_area
        }
    
    def moderate_decision(self, rumor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI moderation to detect anomalies and decide if voting should be extended
        
        Returns:
            {
                'isAmbiguous': bool,
                'shouldExtend': bool,
                'reason': str
            }
        """
        if not self.client:
            return self._fallback_moderation(rumor_data)
        
        try:
            total_votes = rumor_data.get('total_votes', 0)
            fact_weight = rumor_data.get('fact_weight', 0)
            lie_weight = rumor_data.get('lie_weight', 0)
            under_area_votes = rumor_data.get('under_area_votes', 0)
            content = rumor_data.get('content', '')
            
            # Check for obvious extension cases first
            if total_votes == 0:
                return {
                    'isAmbiguous': True,
                    'shouldExtend': True,
                    'reason': 'No votes received'
                }
            
            # Use Azure OpenAI for intelligent moderation
            total_weight = fact_weight + lie_weight
            fact_percentage = (fact_weight / total_weight * 100) if total_weight > 0 else 0
            within_area_ratio = (under_area_votes / total_votes) if total_votes > 0 else 0
            
            system_prompt = """You are an AI moderator for a university rumor verification platform.
Analyze voting patterns to determine if the decision is clear or if voting should be extended.

Extend voting if:
- Votes are nearly tied (within 5-10% difference)
- Very low participation from the relevant area (< 20%)
- Voting pattern seems suspicious or manipulated
- Total votes are too low for a reliable decision (< 5 votes)

Do NOT extend if:
- Clear majority (> 60%)
- Good participation from relevant area (> 30%)
- Voting pattern looks natural and decisive

Return JSON with:
- isAmbiguous (boolean): whether the result is unclear
- shouldExtend (boolean): whether to extend voting by 24 hours
- reason (string): brief explanation for the decision"""
            
            user_prompt = f"""Analyze this voting result:

Rumor: {content[:200]}...

Voting Statistics:
- Total Votes: {total_votes}
- Fact Weight: {fact_weight:.1f} ({fact_percentage:.1f}%)
- Lie Weight: {lie_weight:.1f} ({100-fact_percentage:.1f}%)
- Votes from Relevant Area: {under_area_votes} ({within_area_ratio*100:.1f}%)

Should voting be extended?"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return {
                'isAmbiguous': bool(result.get('isAmbiguous', False)),
                'shouldExtend': bool(result.get('shouldExtend', False)),
                'reason': str(result.get('reason', 'AI moderation complete'))
            }
            
        except Exception as e:
            print(f"AI moderation error: {str(e)}")
            return self._fallback_moderation(rumor_data)
    
    def _fallback_moderation(self, rumor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback moderation logic"""
        total_votes = rumor_data.get('total_votes', 0)
        fact_weight = rumor_data.get('fact_weight', 0)
        lie_weight = rumor_data.get('lie_weight', 0)
        
        if total_votes == 0:
            return {
                'isAmbiguous': True,
                'shouldExtend': True,
                'reason': 'No votes received'
            }
        
        total_weight = fact_weight + lie_weight
        if total_weight > 0:
            fact_percentage = (fact_weight / total_weight) * 100
            if 45 <= fact_percentage <= 55:
                return {
                    'isAmbiguous': True,
                    'shouldExtend': True,
                    'reason': 'Votes are nearly tied'
                }
        
        return {
            'isAmbiguous': False,
            'shouldExtend': False,
            'reason': 'Clear voting pattern'
        }


# Singleton instance
ai_service = AIService()
