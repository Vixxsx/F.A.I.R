from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    try:
        client = OpenAI(api_key=api_key)  # standard OpenAI, no base_url needed
        use_ai = True
        print("✅ OpenAI (gpt-4o-mini) initialized for feedback generation")
    except Exception as e:
        print(f"⚠️  OpenAI API unavailable: {e}")
        client = None
        use_ai = False
else:
    print("⚠️  OPENAI_API_KEY not found - using rule-based feedback")
    client = None
    use_ai = False


class FeedbackRequest(BaseModel):
    scores: Dict[str, float]  # content, audio, eye_contact, body_language, overall
    grade: str
    strengths: List[str]
    weaknesses: List[str]
    details: Dict[str, Any]  # filler_words, wpm, confidence, enthusiasm


@router.post("/generate")
async def generate_personalized_feedback(request: FeedbackRequest):
    """
    Generate personalized interview advice using AI
    
    Returns 3-5 actionable tips based on interview performance
    """
    
    try:
        print(f"\n{'='*60}")
        print(f"💡 Generating Personalized Feedback")
        print(f"   Overall Score: {request.scores.get('overall', 0)}/100 (Grade: {request.grade})")
        print(f"   Strengths: {len(request.strengths)}")
        print(f"   Weaknesses: {len(request.weaknesses)}")
        print(f"{'='*60}\n")
        
        if use_ai and client:
            # Use Grok for personalized advice
            advice = generate_with_grok(request)
        else:
            # Fallback to rule-based
            advice = generate_rule_based_advice(request)
        
        print(f"✅ Generated {len(advice)} personalized tips")
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "advice": advice,
            "method": "ai" if (use_ai and client) else "rule-based"
        }
    
    except Exception as e:
        print(f"❌ Feedback generation failed: {str(e)}")
        
        # Always have fallback
        fallback_advice = generate_rule_based_advice(request)
        
        return {
            "success": True,
            "advice": fallback_advice,
            "method": "fallback"
        }


def generate_with_grok(request: FeedbackRequest) -> List[str]:
    
    # Build context
    strengths_text = "\n".join(f"- {s}" for s in request.strengths) if request.strengths else "None identified"
    weaknesses_text = "\n".join(f"- {w}" for w in request.weaknesses) if request.weaknesses else "None identified"
    
    scores = request.scores
    details = request.details
    
    prompt = f"""You are an expert interview coach. Generate 3-5 specific, actionable tips to help this candidate improve their interview performance.

Interview Performance:
- Overall Score: {scores.get('overall', 0)}/100 (Grade {request.grade})
- Content Relevancy: {scores.get('content', 0)}/100
- Audio Quality: {scores.get('audio', 0)}/100
- Eye Contact: {scores.get('eye_contact', 0)}/100
- Body Language: {scores.get('body_language', 0)}/100

Details:
- Filler Words: {details.get('filler_words', 0)}
- Speaking Rate: {details.get('wpm', 0)} WPM
- Confidence Level: {details.get('confidence', 'Unknown')}
- Enthusiasm Level: {details.get('enthusiasm', 'Unknown')}

Strengths:
{strengths_text}

Areas for Improvement:
{weaknesses_text}

Provide 3-5 SPECIFIC, ACTIONABLE tips. Each tip should:
1. Be practical and immediately implementable
2. Focus on their weaknesses
3. Include a concrete action or technique
4. Be encouraging but honest

Return ONLY a JSON array of strings, no markdown:
["tip 1", "tip 2", "tip 3", ...]

No preamble, no explanation, just the JSON array."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert interview coach providing specific, actionable feedback. Return only valid JSON arrays with no markdown formatting."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up response
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
        
        content = content.strip()
        
        # Parse JSON
        advice_list = json.loads(content)
        
        # Validate it's a list of strings
        if isinstance(advice_list, list) and all(isinstance(item, str) for item in advice_list):
            print(f"✅ Grok generated {len(advice_list)} tips")
            return advice_list[:5]  # Max 5 tips
        else:
            print(f"⚠️  Grok returned invalid format, using fallback")
            return generate_rule_based_advice(request)
    
    except Exception as e:
        print(f"❌ Grok API error: {e}")
        return generate_rule_based_advice(request)


def generate_rule_based_advice(request: FeedbackRequest) -> List[str]:
    """Fallback rule-based advice generation"""
    
    advice = []
    scores = request.scores
    details = request.details
    
    # Content advice
    content_score = scores.get('content', 0)
    if content_score < 75:
        advice.append("Structure your answers using the STAR method (Situation, Task, Action, Result) to provide complete, relevant responses")
    elif content_score >= 85:
        advice.append("Excellent content relevancy! Continue using specific examples from your experience")
    
    # Audio advice
    filler_words = details.get('filler_words', 0)
    audio_score = scores.get('audio', 0)
    
    if filler_words > 5:
        advice.append(f"You used {filler_words} filler words. Practice pausing instead of saying 'um' or 'uh' - silence is better than fillers")
    elif audio_score >= 90:
        advice.append("Outstanding audio quality! Your clear communication is a strong asset")
    
    wpm = details.get('wpm', 0)
    if wpm > 0:
        if wpm < 120:
            advice.append(f"Your speaking rate ({wpm} WPM) is a bit slow. Try to speak at 130-160 WPM for optimal clarity and engagement")
        elif wpm > 170:
            advice.append(f"Your speaking rate ({wpm} WPM) is quite fast. Slow down to 130-160 WPM to ensure clarity")
    
    # Eye contact advice
    eye_score = scores.get('eye_contact', 0)
    if eye_score < 70:
        advice.append("Improve eye contact by placing a small photo or sticky note next to your camera lens - look at it while speaking")
    
    # Body language advice
    confidence = str(details.get('confidence', '')).lower()
    if confidence in ['low', 'moderate']:
        advice.append("Boost confidence with power poses before your interview - stand tall with hands on hips for 2 minutes")
    
    enthusiasm = str(details.get('enthusiasm', '')).lower()
    if enthusiasm in ['low', 'moderate']:
        advice.append("Show more enthusiasm by smiling naturally and using varied vocal tone when discussing your achievements")
    
    # Overall grade-based advice
    if request.grade in ['S', 'A']:
        advice.append("Exceptional performance! Consider mentoring others or recording a 'best practices' guide for future interviews")
    elif request.grade in ['D', 'F']:
        advice.append("Practice with mock interviews daily - consistency is key to improvement. Record yourself and review the footage")
    
    # Ensure we have at least 3 tips
    if len(advice) < 3:
        advice.append("Research the company thoroughly and prepare 2-3 questions to ask the interviewer")
        advice.append("Practice your answers out loud, not just in your head - muscle memory matters")
        advice.append("Get feedback from friends or use AI mock interview tools to identify blind spots")
    
    return advice[:5]  # Max 5 tips


@router.get("/test")
def test_feedback_api():
    """Test endpoint"""
    return {
        "message": "Feedback API is working!",
        "ai_enabled": use_ai,
        "endpoints": {
            "generate": "POST /api/feedback/generate"
        }
    }