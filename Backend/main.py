from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
import os
import warnings
REQUIRED_MODELS = ["Backend/Models/face_landmarker.task"]
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
warnings.filterwarnings('ignore')
import shutil
from datetime import datetime

# Import routes
from Backend.api.Video_routes     import router as video_router
from Backend.api.Question_routes  import router as question_router
from Backend.api.Interview_routes import router as interview_router
from Backend.api.Feedback_routes  import router as feedback_router
from Backend.api.History_routes   import router as history_router

# Import models
from Backend.Models.whisper_stt           import WhisperSTT
from Backend.Models.filler_word_detection import FillerDetector
from Backend.Models.emotion_detector      import EmotionDetector
from Backend.Models.Content_Relevancy     import ContentRelevancyAnalyzer
from Backend.Models.eye_tracker           import EyeTracker
from Backend.Utilities.video_utils        import VideoProcessor
from Backend.Utilities.audio_extract      import AudioExtractor
from Models                               import _registry as ModelRegistry


UPLOAD_DIR = "Data/Video/Raw"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ========== APPLICATION CONSTANTS ==========
APP_NAME = "AIRA"
APP_VERSION = "2.0.0"

def checkfile():
    missing=[]
    for file_path in REQUIRED_MODELS:
        if not os.path.exists(file_path):
            missing.append(file_path)   
    if missing:
        print("Required model files missing:")
        for file_path in missing:
            print(f"  - {file_path}")

# ========== CREATE FASTAPI APP ==========

app = FastAPI(
    title="AIRA - Automated Interview & Response Analyzer",
    description="Backend API for AI-Powered Interview & Response Analyzer",
    version="2.0.0"
)

# ========== CORS MIDDLEWARE ==========

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== LOAD AI MODELS ==========
@app.on_event("startup")
async def startup_event():
    """Initialize on server startup"""
    print("\n" + "="*70)
    print(f"🚀 {APP_NAME} v{APP_VERSION} Starting...")
    print("="*70)
    
    # Step 1: Check required files
    print("\n📁 Step 1: Checking required files...")
    try:
        checkfile()
        print("✅ All required files present")
    except RuntimeError as e:
        print(str(e))
        raise
    
    # Step 2: Load models
    print("\n📦 Step 2: Loading AI models...")
    try:
        ModelRegistry.load_all_models()
        print("✅ Models loaded successfully")
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        raise
    
    # Step 3: Ready
    print("\n" + "="*70)
    print(f"✅ {APP_NAME} v{APP_VERSION} is READY!")
    print("="*70 + "\n")
async def load_models():
    global stt, filler_detector, emotion_detector, relevancy_analyzer, eye_tracker, video_processor, audio_extractor
    print("\nInitializing MySQL Database...")
    try:
        from Backend.Utilities.database import db
        print("MySQL Database connected and tables ready!")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        print("⚠️  Check your .env file for MySQL credentials")

    print("Loading Whisper model...")
    ModelRegistry.stt = WhisperSTT(model_size="small")
    print("✅ Whisper loaded!")

    print("Loading Filler Detector...")
    ModelRegistry.filler_detector = FillerDetector(strictness="medium")
    print("✅ Filler Detector loaded!")

    print("Loading Emotion Detector...")
    ModelRegistry.emotion_detector = EmotionDetector()
    print("✅ Emotion Detector loaded!")

    print("Loading Content Relevancy Analyzer...")
    ModelRegistry.relevancy_analyzer = ContentRelevancyAnalyzer()
    print("✅ Content Relevancy Analyzer loaded!")

    print("Loading Eye Tracker...")
    ModelRegistry.eye_tracker = EyeTracker()
    print("✅ Eye Tracker loaded!")

    print("Loading Video Processor...")
    ModelRegistry.video_processor = VideoProcessor()
    print("✅ Video Processor loaded!")

    print("Loading Audio Extractor...")
    ModelRegistry.audio_extractor = AudioExtractor()
    print("✅ Audio Extractor loaded!")


# ========== CREATE DIRECTORIES ==========

TRANSCRIPT_DIR = "Data/Transcript"
AUDIO_TEST_DIR = "Data/Audio"

os.makedirs(UPLOAD_DIR,     exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
os.makedirs(AUDIO_TEST_DIR, exist_ok=True)

# ========== INCLUDE ROUTERS ==========

app.include_router(video_router)
app.include_router(interview_router)
print("✅ Interview routes loaded")
app.include_router(question_router)
print("✅ Question routes loaded")
app.include_router(feedback_router)
print("✅ Feedback routes loaded")
app.include_router(history_router)
print("✅ History routes loaded")

# Auth routes
try:
    from Backend.api.Auth_routes import router as auth_router
    app.include_router(auth_router)
    print("✅ Auth routes loaded from Backend/api/")
except ImportError:
    try:
        import sys
        sys.path.append(os.path.dirname(__file__))
        from Backend.api.Auth_routes import router as auth_router
        app.include_router(auth_router)
        print("✅ Auth routes loaded (development mode)")
    except ImportError:
        print("⚠️  Auth routes not found - authentication endpoints not available")

# ========== SERVE FRONTEND STATIC FILES ==========

app.mount("/Assets",     StaticFiles(directory="Frontend/Assets"),          name="assets")
app.mount("/Components", StaticFiles(directory="Frontend/Components"),       name="components")
app.mount("/Pages",      StaticFiles(directory="Frontend/Pages", html=True), name="pages")

print("✅ Frontend static files mounted")

# ========== RESPONSE MODELS ==========

class TranscriptResponse(BaseModel):
    success: bool
    transcript: str
    word_count: int
    duration: float
    speaking_time: float
    words_per_minute: float
    language: str
    timestamp: str
    saved_path: str

class FillerAnalysisResponse(BaseModel):
    success: bool
    total_fillers: int
    filler_density: float
    filler_score: int
    filler_frequency: dict
    categories: dict

# ========== HELPER FUNCTIONS ==========

def get_speaking_rate_feedback(wpm: float) -> str:
    if wpm < 110:
        return "Speaking too slowly. Try to increase pace slightly."
    elif 110 <= wpm < 130:
        return "Speaking a bit slow. Slightly faster would be better."
    elif 130 <= wpm <= 160:
        return "Excellent speaking pace - clear and natural."
    elif 160 < wpm <= 180:
        return "Speaking a bit fast. Slow down slightly for clarity."
    else:
        return "Speaking too fast. Take your time and breathe."

def calculate_overall_audio_score(filler_score: int, speaking_rate_score: int) -> int:
    overall = (filler_score * 0.6) + (speaking_rate_score * 0.4)
    return round(overall)

# ========== BASIC ENDPOINTS ==========

@app.get("/")
async def root():
    return RedirectResponse(url="/Pages/start.html")

@app.get("/api")
async def api_root():
    return {
        "message": "Welcome to AIRA - AI Interview Analyzer Backend!",
        "status":  "running",
        "version": "1.0.0",
        "docs":    "Visit /docs for API documentation",
        "features": {
            "authentication":     "✅ Enabled",
            "audio_analysis":     "✅ Enabled",
            "video_processing":   "✅ Enabled",
            "interview_analysis": "✅ Enabled",
            "database":           "✅ MySQL"
        }
    }

@app.get("/api/test")
def api_test():
    return {"message": "API is working!", "status": "success"}

@app.get("/health")
def health_check():
    return {
        "status":   "healthy",
        "api":      "Operational",
        "database": "MySQL",
        "Models": {
            "whisper":          "loaded",
            "filler_detector":  "loaded"
        }
    }

@app.get("/status")
def status():
    return {
        "api_name": "AIRA - AI Interview Analyzer API",
        "version":  "1.0.0",
        "endpoints": {
            "root":   "/",
            "health": "/health",
            "status": "/status",
            "test":   "/api/test",
            "history": {
                "save":   "POST   /api/interviews/save",
                "recent": "GET    /api/interviews/recent",
                "stats":  "GET    /api/interviews/stats",
                "clear":  "DELETE /api/interviews/clear"
            }
        }
    }

# ========== AUDIO ANALYSIS ENDPOINTS ==========

@app.post("/api/transcribe", response_model=TranscriptResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    try:
        timestamp      = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(audio.filename)[1]
        temp_file_path = os.path.join(UPLOAD_DIR, f"audio_{timestamp}{file_extension}")

        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        transcript_data = stt.transcribe_audio(temp_file_path)
        stats           = stt.get_speaking_stats(transcript_data)
        saved_path      = stt.save_transcript(transcript_data, filename=f"transcript_{timestamp}.json")
        os.remove(temp_file_path)

        return TranscriptResponse(
            success=True,
            transcript=transcript_data["text"],
            word_count=stats["total_words"],
            duration=stats["duration_seconds"],
            speaking_time=stats["speaking_time_seconds"],
            words_per_minute=stats["words_per_minute"],
            language=transcript_data["language"],
            timestamp=transcript_data["timestamp"],
            saved_path=saved_path
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/api/analyze/fillers", response_model=FillerAnalysisResponse)
async def analyze_fillers(text: str):
    try:
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
        raise HTTPException(status_code=500, detail=f"Filler analysis failed: {str(e)}")


@app.post("/api/analyze/complete")
async def analyze_complete(audio: UploadFile = File(...)):
    try:
        timestamp      = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(audio.filename)[1]
        temp_path      = os.path.join(UPLOAD_DIR, f"audio_{timestamp}{file_extension}")

        with open(temp_path, "wb") as f:
            f.write(await audio.read())

        transcription_result = stt.transcribe_audio(temp_path)
        transcript_text      = transcription_result["text"]
        language             = transcription_result.get("language", "unknown")
        stats                = stt.get_speaking_stats(transcription_result)
        filler_result        = filler_detector.detect_fillers(transcript_text)
        words_per_minute     = stats["words_per_minute"]

        if   130 <= words_per_minute <= 160: speaking_rate_score = 100
        elif 120 <= words_per_minute < 130 or 160 < words_per_minute <= 170: speaking_rate_score = 85
        elif 110 <= words_per_minute < 120 or 170 < words_per_minute <= 180: speaking_rate_score = 70
        else: speaking_rate_score = 50

        saved_path = stt.save_transcript(transcription_result, filename=f"transcript_{timestamp}.json")
        os.remove(temp_path)

        return {
            "success": True,
            "audio_file": audio.filename,
            "transcription": {
                "text":             transcript_text,
                "word_count":       stats["total_words"],
                "duration_seconds": stats["duration_seconds"],
                "language":         language,
                "saved_to":         saved_path
            },
            "filler_analysis": {
                "filler_words":      filler_result["filler_frequency"],
                "total_fillers":     filler_result["total_fillers"],
                "filler_percentage": filler_result["filler_density_percentage"],
                "score":             filler_result["score"],
                "feedback":          f"Filler word score: {filler_result['score']}/100"
            },
            "audio_metrics": {
                "words_per_minute":       round(words_per_minute, 1),
                "speaking_time":          stats["speaking_time_seconds"],
                "pause_time":             stats["pause_time_seconds"],
                "number_of_pauses":       stats["number_of_pauses"],
                "speaking_rate_score":    speaking_rate_score,
                "speaking_rate_feedback": get_speaking_rate_feedback(words_per_minute)
            },
            "overall_audio_score": calculate_overall_audio_score(
                filler_result["score"], speaking_rate_score
            )
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Complete analysis failed: {str(e)}")


# ========== RUN SERVER ==========

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting AIRA Backend Server...")
    print("📍 Server:   http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🌐 Frontend: http://localhost:8000/")
    print("\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)