# backend/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
from datetime import datetime

# ✅ FIXED: Correct import paths (lowercase 'models')
from models.whisper_stt import WhisperSTT
from models.filler_word_detection import FillerDetector

# Create FastAPI app
app = FastAPI(
    title="AI Interview Analyzer",
    description="Backend API for Automated Interview Feedback Analyzer",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI models at startup
print("🎤 Loading Whisper model...")
stt = WhisperSTT(model_size="base")
print("✅ Whisper loaded!")

print("🔍 Loading Filler Detector...")
filler_detector = FillerDetector(strictness="medium")
print("✅ Filler Detector loaded!")

# ✅ FIXED: Create required directories
UPLOAD_DIR = "temp_audio"
TRANSCRIPT_DIR = "data/Report"  # Where transcripts are saved
AUDIO_TEST_DIR = "data/Audio"   # Where test audio files are

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
os.makedirs(AUDIO_TEST_DIR, exist_ok=True)

# Response models
class TranscriptResponse(BaseModel):
    success: bool
    transcript: str
    word_count: int
    duration: float
    speaking_time: float
    words_per_minute: float
    language: str
    timestamp: str
    saved_path: str  # ✅ Added: Path where transcript was saved

class FillerAnalysisResponse(BaseModel):
    success: bool
    total_fillers: int
    filler_density: float
    filler_score: int
    filler_frequency: dict
    categories: dict

class CompleteAnalysisResponse(BaseModel):
    success: bool
    transcript: TranscriptResponse
    filler_analysis: FillerAnalysisResponse

# Basic endpoints
@app.get("/")
async def root():
    return {
        "message": "Welcome to the AI Interview Analyzer Backend!",
        "status": "running",
        "version": "1.0.0",
        "docs": "Visit /docs for API documentation"
    }

@app.get("/api/test")
def api_test():
    return {
        "message": "API is working!",
        "status": "success"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "api": "Operational",
        "models": {
            "whisper": "loaded",
            "filler_detector": "loaded",
        }
    }

@app.get("/status")
def status():
    return {
        "api_name": "AI Mock Interview API",
        "version": "1.0.0",
        "endpoints": {
            "root": "/",
            "health": "/health",
            "status": "/status",
            "test": "/api/test",
            "transcribe": "/api/transcribe",
            "analyze_fillers": "/api/analyze/fillers",
            "complete_analysis": "/api/analyze/complete"
        }
    }

# ========== ACTUAL API ENDPOINTS ==========

@app.post("/api/transcribe", response_model=TranscriptResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe audio file to text using Whisper
    """
    try:
        # Save uploaded file temporarily
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(audio.filename)[1]
        temp_file_path = os.path.join(UPLOAD_DIR, f"audio_{timestamp}{file_extension}")
        
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        print(f"📁 Saved audio to: {temp_file_path}")
        
        # Transcribe with Whisper
        print("🎤 Transcribing...")
        transcript_data = stt.transcribe_audio(temp_file_path)
        
        # Get speaking statistics
        stats = stt.get_speaking_stats(transcript_data)
        
        # ✅ FIXED: Save transcript to Report folder
        output_filename = f"transcript_{timestamp}.json"
        output_path = os.path.join(TRANSCRIPT_DIR, output_filename)
        stt.save_transcript(transcript_data, output_path)
        
        # Clean up temp audio file
        os.remove(temp_file_path)
        print("✅ Transcription complete!")
        
        return TranscriptResponse(
            success=True,
            transcript=transcript_data["text"],
            word_count=stats["total_words"],
            duration=stats["duration_seconds"],
            speaking_time=stats["speaking_time_seconds"],
            words_per_minute=stats["words_per_minute"],
            language=transcript_data["language"],
            timestamp=transcript_data["timestamp"],
            saved_path=output_path  # ✅ Return where it was saved
        )
    
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/api/analyze/fillers", response_model=FillerAnalysisResponse)
async def analyze_fillers(text: str):
    """
    Analyze text for filler words
    """
    try:
        print("Analyzing fillers...")
        result = filler_detector.detect_fillers(text)
        
        return FillerAnalysisResponse(
            success=True,
            total_fillers=result["total_fillers"],
            filler_density=result["filler_density_percentage"],
            filler_score=result["score"],
            filler_frequency=result["filler_frequency"],
            categories=result["categories"]
        )
    
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Filler analysis failed: {str(e)}")

@app.post("/api/analyze/complete", response_model=CompleteAnalysisResponse)
async def complete_analysis(audio: UploadFile = File(...)):
    """
    Complete analysis: Transcribe audio + Analyze fillers + Save report
    """
    try:
        # Save uploaded file temporarily
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(audio.filename)[1]
        temp_file_path = os.path.join(UPLOAD_DIR, f"audio_{timestamp}{file_extension}")
        
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        print(f"Saved audio to: {temp_file_path}")
        
        # Transcribe
        print("Transcribing...")
        transcript_data = stt.transcribe_audio(temp_file_path)
        stats = stt.get_speaking_stats(transcript_data)
        
        # Analyze fillers
        print("Analyzing fillers...")
        filler_result = filler_detector.detect_fillers(transcript_data["text"])
        
        # ✅ FIXED: Save complete report to Report folder
        output_filename = f"complete_analysis_{timestamp}.json"
        output_path = os.path.join(TRANSCRIPT_DIR, output_filename)
        
        import json
        complete_report = {
            "timestamp": timestamp,
            "audio_file": audio.filename,
            "transcript": transcript_data,
            "speaking_stats": stats,
            "filler_analysis": filler_result
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(complete_report, f, indent=2, ensure_ascii=False)
        
        print(f"Complete report saved to: {output_path}")
        
        # Clean up temp audio
        os.remove(temp_file_path)
        print("Complete analysis done!")
        
        return CompleteAnalysisResponse(
            success=True,
            transcript=TranscriptResponse(
                success=True,
                transcript=transcript_data["text"],
                word_count=stats["total_words"],
                duration=stats["duration_seconds"],
                speaking_time=stats["speaking_time_seconds"],
                words_per_minute=stats["words_per_minute"],
                language=transcript_data["language"],
                timestamp=transcript_data["timestamp"],
                saved_path=output_path
            ),
            filler_analysis=FillerAnalysisResponse(
                success=True,
                total_fillers=filler_result["total_fillers"],
                filler_density=filler_result["filler_density_percentage"],
                filler_score=filler_result["score"],
                filler_frequency=filler_result["filler_frequency"],
                categories=filler_result["categories"]
            )
        )
    
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Complete analysis failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)