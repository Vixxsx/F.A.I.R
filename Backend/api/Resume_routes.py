
"""
Resume upload and parsing routes.
Secondary path for interview setup - users can upload ATS-friendly resume
to get personalized questions based on their background.
"""
from urllib import request
from httpcore import request
from fastapi import Request, File, Form, UploadFile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import os

from Backend.Utilities.Resume_parse import ResumeParser
from Backend.Models.Question_Generator import QuestionGenerator

router = APIRouter(prefix="/api/resume", tags=["resume"])

# Initialize parser and question generator
resume_parser = ResumeParser()
question_generator = QuestionGenerator()


class ResumeParseResponse(BaseModel):
    success: bool
    is_ats_friendly: bool
    ats_score: int
    ats_issues: List[str]
    ats_warnings: List[str]
    extracted: Optional[Dict[str, Any]]
    masked: bool
    questions: List[str]
    message: str


@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(
    request: Request,
    resume: UploadFile = File(...),
    jobRole: str = Form(...),
    difficulty: str = Form(default="intermediate"),
    interviewType: str = Form(default="mixed"),
    maskPersonal: bool = Form(default=False),
    num_questions: int = Form(default=5)
):
    try:
        # Step 1: Read and validate file
        pdf_bytes = await resume.read()

        if not resume.filename or not resume.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF format is supported. Please upload an ATS-friendly PDF resume."
            )

        if len(pdf_bytes) > 5 * 1024 * 1024:  # 5MB limit
            raise HTTPException(
                status_code=400,
                detail="Resume file too large. Please upload a PDF under 5MB."
            )

        if len(pdf_bytes) < 1024:  # Less than 1KB is suspicious
            raise HTTPException(
                status_code=400,
                detail="Resume file appears to be empty or corrupted. Please upload a valid PDF."
            )

        # Step 2: Parse resume (validates ATS + extracts data)
        result = resume_parser.parse(pdf_bytes, mask_personal=maskPersonal)

        # Step 3: Gate on ATS-friendliness
        if not result['is_ats_friendly']:
            return ResumeParseResponse(
                success=False,
                is_ats_friendly=False,
                ats_score=result['ats_score'],
                ats_issues=result['ats_issues'],
                ats_warnings=result['ats_warnings'],
                extracted=None,
                masked=maskPersonal,
                questions=[],
                message="Resume is not ATS-friendly. Please fix the issues below or use manual setup."
            )

        # Step 4: Generate personalized questions
        profile = {
            "job_role": jobRole,
            "difficulty": difficulty,
            "interview_type": interviewType,
            "skills": result['extracted'].get('skills', []),
            "projects": result['extracted'].get('projects', []),
            "experience": result['extracted'].get('experience', []),
        }

        questions_result = question_generator.generate_questions_resume(
            profile=profile,
            num_questions=num_questions
        )
        questions = [q['question'] for q in questions_result]

        return ResumeParseResponse(
            success=True,
            is_ats_friendly=True,
            ats_score=result['ats_score'],
            ats_issues=result['ats_issues'],
            ats_warnings=result['ats_warnings'],
            extracted=result['extracted'],
            masked=maskPersonal,
            questions=questions,
            message=f"Resume parsed successfully. {len(questions)} personalized questions generated."
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Resume parsing endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Resume parsing failed: {str(e)}"
        )


@router.get("/format-guide")
async def get_format_guide():
    """
    Returns ATS-friendly resume format guide.
    Shown to users when their resume fails validation.
    """
    return {
        "title": "ATS-Friendly Resume Format Guide",
        "do": [
            "Use a single-column layout",
            "Use standard section headers: 'Education', 'Experience', 'Skills', 'Projects'",
            "Save as a text-based PDF (not scanned images)",
            "Use standard fonts: Arial, Calibri, Times New Roman",
            "Include your email address in the contact section",
            "Keep it to 1-2 pages (300-800 words)",
            "Use simple bullet points with • or -",
            "Include relevant keywords for your target role"
        ],
        "dont": [
            "Don't use multi-column layouts",
            "Don't use tables for layout (only for data)",
            "Don't include images, logos, or icons",
            "Don't use text boxes or shapes",
            "Don't use headers/footers for contact info",
            "Don't use fancy fonts, colors, or graphics",
            "Don't submit scanned PDFs (use text-based PDFs)"
        ],
        "tools": [
            {"name": "Canva ATS Resume Templates", "url": "https://www.canva.com/resumes/templates/ats/"},
            {"name": "Overleaf (LaTeX)", "url": "https://www.overleaf.com/gallery/tagged/cv"},
            {"name": "Google Docs Simple Resume Template", "url": "https://docs.google.com/document/"}
        ],
        "example_structure": {
            "header": "John Doe | john@email.com | (555) 123-4567 | linkedin.com/in/johndoe",
            "sections": [
                "EDUCATION",
                "B.S. Computer Science, XYZ University, 2024",
                "",
                "EXPERIENCE",
                "Software Engineering Intern, ABC Corp, Summer 2023",
                "• Built feature X using React and Node.js",
                "• Improved API response time by 40%",
                "",
                "PROJECTS",
                "ChatBot App | Python, TensorFlow, Flask",
                "• Built NLP chatbot with 90% intent accuracy",
                "",
                "SKILLS",
                "Languages: Python, JavaScript, TypeScript",
                "Frameworks: React, Node.js, Django",
                "Tools: Git, Docker, AWS"
            ]
        }
    }


@router.get("/test")
async def test_resume_api():
    """Test endpoint"""
    return {
        "message": "Resume API is working!",
        "endpoints": {
            "parse":       "POST /api/resume/parse",
            "format_guide": "GET  /api/resume/format-guide",
            "test":        "GET  /api/resume/test"
        }
    }