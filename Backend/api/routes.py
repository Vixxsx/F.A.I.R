from fastapi import APIRouter,UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api", tags=["API"])
class TranscriptionResponse(BaseModel):
    text: str
    word_count: int
    duration: float
    language: str

class FillerAnalysisResponse(BaseModel):
    total_fillers: int
    filler_density: float
    score: int
    fillers_list: list

@router.get("test")
def test_endpoint():
    return {
        "message": "API routes are working!",
        "status": "success"
    }
@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe audio to text using Whisper
    
    Week 2: Will implement full functionality
    """

    return {
        "text": "Placeholder - will implement in Week 2",
        "word_count": 0,
        "duration": 0.0,
        "language": "en"
    }

# Placeholder 
@router.post("/analyze/fillers", response_model=FillerAnalysisResponse)
async def analyze_fillers(text: str):
#inniyum und cheyan 
    # TODO: Implement filler detection
    return {
        "total_fillers": 0,
        "filler_density": 0.0,
        "score": 100,
        "fillers_list": []
    }
