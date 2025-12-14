from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 

app = FastAPI(
    title="AI Interview Analyzer",
    description="Backend API for Automated Interview Feedback Analyzer",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
async def root():
    return {"message": "Welcome to the AI Interview Analyzer Backend!",
            "status": "running",
            "version": "1.0.0"}

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
                "whisper": "available",
                "filler_detector": "available",
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
            "transcribe": "/api/transcribe ",
            "analyze_fillers": "/api/analyze/fillers"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0",port=8000,reload=True)
