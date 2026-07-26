"""
Question Generation Routes
Uses the Question_Generator model to generate interview questions
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

# Import your existing Question Generator
from Models.Question_Generator import QuestionGenerator

router = APIRouter(prefix="/api/questions", tags=["questions"])

# Initialize the generator
question_generator = QuestionGenerator()

class QuestionRequest(BaseModel):
    jobRole: str
    degree : str
    education_lvl: str
    difficulty: str
    company_type: str
    count: int
    interview_type: str

@router.post("/generate")
async def generate_questions(request: QuestionRequest):
    try:
        print(f"\n{'='*60}")
        print(f"📝 Generating Questions (Manual Mode)")
        print(f"   Job Role: {request.jobRole}")
        print(f"   Degree: {request.degree}")
        print(f"   Difficulty: {request.difficulty}")
        print(f"{'='*60}\n")
        
        profile = {
            "job_role": request.jobRole,
            "degree": request.degree, 
            "education_lvl": request.education_lvl,
            "difficulty": request.difficulty,
            "company_type": request.company_type,
            "interview_type": request.interview_type
        }
        
        # Use OpenAI generation if available
        if question_generator.use_ai and question_generator.client:
            raw_questions = question_generator._generate_with_openai(
                profile=profile,
                num_questions=request.count
            )
            questions = [q['question'] if isinstance(q, dict) else str(q) for q in raw_questions]
        else:
            raw_questions = question_generator._generate_from_templates(
                profile=profile,
                num_questions=request.count
            )
            questions = [q['question'] for q in raw_questions]
        
        print(f"✅ Successfully generated {len(questions)} questions")
        
        return {
            "success": True,
            "questions": questions,
            "profile": profile
        }
    
    except Exception as e:
        print(f"❌ Question generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback
        fallback_questions = [
            f"Tell me about your experience related to {request.jobRole}.",
            "Describe a challenging project you worked on recently.",
            "How do you handle working under tight deadlines?",
            "What are your core strengths relevant to this role?",
            "Where do you see yourself in 3 to 5 years?"
        ]
        
        return {
            "success": True,
            "questions": fallback_questions[:request.count],
            "fallback": True
        }

@router.get("/test")
def test_questions_api():
    """Test endpoint"""
    return {
        "message": "Questions API is working!",
        "endpoints": {
            "generate": "POST /api/questions/generate"
        }
    }