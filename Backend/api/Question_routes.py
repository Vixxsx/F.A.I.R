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
        print(f"📝 Generating Questions")
        print(f"   Job Role: {request.jobRole}")
        print(f"   Degree: {request.degree}")
        print(f"   Company Type: {request.company_type}")
        print(f"   Difficulty: {request.difficulty}")
        print(f"   Type: {request.interview_type}")
        print(f"   Count: {request.count}")
        print(f"{'='*60}\n")
        
        # Generate questions using your model
        profile={
            "job_role": request.jobRole,
            "degree": request.degree,
            "difficulty": request.difficulty,
            "company_type": request.company_type,
            "interview_type": request.interview_type
        }
        result=question_generator.generate_questions(
            profile=profile,
            num_questions=request.count
        )
        questions=[q['question'] for q in result]
        
        print(f"✅ Generated {len(questions)} questions")
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "questions": questions,
            "profile": profile,
            "metadata": {
                "job_role": request.jobRole,
                "degree": request.degree,
                "company_type": request.company_type,
                "difficulty": request.difficulty,
                "interview_type": request.interview_type,
                "count": len(questions)
            }
        }
    
    except Exception as e:
        print(f"❌ Question generation failed: {str(e)}")
        
        # Fallback to basic questions if generation fails
        fallback_questions = {
            "behavioral": [
                "Tell me about a time when you faced a significant challenge at work. How did you handle it?",
                "Describe a situation where you had to work with a difficult team member.",
                "Give me an example of a goal you set and how you achieved it.",
                "Tell me about a time you failed. What did you learn from it?",
                "Describe a time when you had to adapt to a major change at work."
            ],
            "technical": [
                f"Explain your experience with the main technologies used in a {request.jobRole} role.",
                "Walk me through how you would approach a complex technical problem.",
                "What's the most challenging technical project you've worked on?",
                "How do you stay updated with the latest developments in your field?",
                "Describe your development process from requirements to deployment."
            ],
            "mixed": [
                f"Tell me about your experience as a {request.jobRole}.",
                "Describe a challenging project you worked on and how you overcame obstacles.",
                "Where do you see yourself professionally in 5 years?",
                "How do you handle disagreements with team members?",
                f"Why are you interested in working as a {request.jobRole}?"
            ]
        }
        
        question_type = request.type if request.type in fallback_questions else "mixed"
        fallback = fallback_questions[question_type][:request.count]
        
        return {
            "success": True,
            "questions": fallback,
            "fallback": True,
            "metadata": {
                "job_role": request.jobRole,
                "degree": request.degree,
                "company_type": request.company_type,
                "difficulty": request.difficulty,
                "count": len(fallback),
                "interview_type": request.interview_type
            }
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