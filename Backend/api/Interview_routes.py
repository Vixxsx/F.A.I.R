from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import os
import shutil
try:
    import cv2
except ImportError:
    cv2 = None
from datetime import datetime
# Import models
import numpy as np

def convert_numpy_types(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

router = APIRouter(prefix="/api/interview", tags=["interview"])

# Initialize models
from Models._registry import (stt, filler_detector, emotion_detector, relevancy_analyzer, eye_tracker, video_processor, audio_extractor)

UPLOAD_DIR = "Data/Video/Raw"
FRAMES_DIR = "Data/Video/Frames"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)


@router.post("/analyze-answer")
async def analyze_answer(
    video:          UploadFile = File(...),
    question:       str        = Form(...),
    questionNumber: int        = Form(...),
    jobRole:        str        = Form(default="Professional")  # ← NEW: pass from frontend
):
    try:
        # ── Step 1: Save uploaded video ──
        timestamp      = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"question_{questionNumber}_{timestamp}.webm"
        video_path     = os.path.join(UPLOAD_DIR, video_filename)

        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        print(f"\n{'='*60}")
        print(f"🎯 Analyzing Question {questionNumber}")
        print(f"📁 Video saved: {video_path}")
        print(f"❓ Question: {question}")
        print(f"{'='*60}\n")

        # ── Step 2: Extract audio and transcribe ──
        print("🎤 Step 1: Extracting audio and transcribing...")
        audio_path= audio_extractor.extract_audio(video_path)
        transcript_result = stt.transcribe_audio(audio_path)
        transcript_text = transcript_result["text"]
        stats           = stt.get_speaking_stats(transcript_result)

        print(f"✅ Transcription: {stats['total_words']} words @ {stats['words_per_minute']} WPM")

        # ── Step 3: Content Relevancy Analysis (NEW) ──
        print("\n🧠 Step 2: Analyzing content relevancy...")
        relevancy_result = relevancy_analyzer.analyze(
            question=question,
            answer=transcript_text,
            job_role=jobRole
        )

        print(f"✅ Relevancy: {relevancy_result['relevancy_score']}/100 ({relevancy_result['relevancy_label']})")
        if relevancy_result['cant_answer']:
            print("   ⚠️  Candidate indicated they couldn't answer")
        if relevancy_result['gibberish']:
            print("   ⚠️  Answer detected as incoherent/gibberish")

        # ── Step 4: Filler word analysis ──
        print("\n🔍 Step 3: Analyzing filler words...")
        filler_result = filler_detector.detect_fillers(transcript_text)

        print(f"✅ Fillers: {filler_result['total_fillers']} ({filler_result['filler_density_percentage']}%) — Score: {filler_result['score']}/100")

        # ── Step 5: Extract frames ──
        print("\n📸 Step 4: Extracting frames from video...")
        frames_output_dir = os.path.join(FRAMES_DIR, f"question_{questionNumber}_{timestamp}")
        os.makedirs(frames_output_dir, exist_ok=True)
        
        video_info    = video_processor.get_video_info(video_path)
        duration      = video_info.get("duration_seconds", 0)
        sample_every  = max(1, int(duration))
        max_frames    = min(60, max(30, int(duration)))

        frame_paths = video_processor.extract_frames(
            video_path,
            output_folder=frames_output_dir,
            every_nth=sample_every,
            max_frames=max_frames,
            return_arrays=True
        )
        print(f"✅ Extracted {len(frame_paths)} frames (1fps from {duration}s video) | Saved to: {frames_output_dir}")

        print("\n👁️ Step 5: Analyzing eye contact...")
        eye_result    = eye_tracker.analyze_frames_list(frame_paths)
        eye_summary   = eye_result["summary"]
        eye_score_100 = round(eye_summary["avg_score"] * 100)
        print(f"✅ Eye contact score: {eye_score_100}/100 | detection rate: {eye_summary['face_detection_rate']}%")

        # ── Step 6: Emotion analysis ──
        print("\n😊 Step 6: Analyzing emotions...")
        emotion_results = emotion_detector.analyze_frames_list(frame_paths)
        print("✅ Emotion analysis complete")

        # ── Step 7: Calculate scores ──
        print("\n📊 Step 7: Calculating scores...")

        # Speaking rate score
        wpm = stats["words_per_minute"]
        if 130 <= wpm <= 160:
            speaking_rate_score = 100
        elif 120 <= wpm < 130 or 160 < wpm <= 170:
            speaking_rate_score = 85
        elif 110 <= wpm < 120 or 170 < wpm <= 180:
            speaking_rate_score = 70
        else:
            speaking_rate_score = 50

        # Audio quality score
        audio_quality_score = round(
            (filler_result["score"] * 0.6) + (speaking_rate_score * 0.4)
        )

        # Content score — now uses real relevancy instead of word count heuristic
        content_score = relevancy_result["relevancy_score"]

        # Body language score
        emotion_summary    = emotion_results['summary']
        emotion_distribution = emotion_summary['emotion_distribution']
        dominant_emotion   = max(emotion_distribution, key=emotion_distribution.get)

        body_language_score = round(
            (emotion_summary['confidence_score']    * 0.4) +
            (emotion_summary['professionalism_score'] * 0.4) +
            ((100 - emotion_summary['nervousness_score']) * 0.2)
        )

        print(f"✅ Scores:")
        print(f"   Content Relevancy: {content_score}/100")
        print(f"   Eye Contact:       {eye_score_100}/100")
        print(f"   Audio Quality:     {audio_quality_score}/100")
        print(f"   Body Language:     {body_language_score}/100")

        print(f"\n{'='*60}")
        print(f"✅ Question {questionNumber} analysis complete!")
        print(f"{'='*60}\n")

        result = {
            "success":         True,
            "question_number": questionNumber,
            "question":        question,
            "video_path":      video_path,
            "frames_dir":      frames_output_dir,

            "transcript": {
                "text":             transcript_text,
                "word_count":       stats["total_words"],
                "duration_seconds": stats["duration_seconds"],
                "words_per_minute": round(wpm, 1),
                "speaking_time":    stats["speaking_time_seconds"]
            },

            # ── NEW: full relevancy block ──
            "content_relevancy": {
                "score":             content_score,
                "label":             relevancy_result["relevancy_label"],
                "cant_answer":       relevancy_result["cant_answer"],
                "gibberish":         relevancy_result["gibberish"],
                "feedback":          relevancy_result["feedback"],
                "key_points_hit":    relevancy_result["key_points_hit"],
                "key_points_missed": relevancy_result["key_points_missed"],
                "suggestion":        relevancy_result["suggestion"]
            },

            "filler_analysis": {
                "total_fillers":   filler_result["total_fillers"],
                "filler_density":  filler_result["filler_density_percentage"],
                "filler_frequency": filler_result["filler_frequency"],
                "score":           filler_result["score"]
            },

            "audio_quality": {
                "speaking_rate_score": speaking_rate_score,
                "filler_score":        filler_result["score"],
                "overall_score":       audio_quality_score
            },

            "eye_contact": {
                "score":                eye_score_100,
                "avg_score":            eye_summary["avg_score"],
                "eye_contact_percentage": eye_summary["eye_contact_percentage"],
                "face_detection_rate":  eye_summary["face_detection_rate"],
                "feedback":             eye_summary["feedback"]
            },
            "emotion_analysis": {
                "dominant_emotion":            dominant_emotion,
                "dominant_emotion_confidence": round(emotion_distribution[dominant_emotion], 1),
                "emotion_distribution":        emotion_distribution,
                "confidence_score":            emotion_summary['confidence_score'],
                "enthusiasm_score":            emotion_summary['enthusiasm_score'],
                "nervousness_score":           emotion_summary['nervousness_score'],
                "professionalism_score":       emotion_summary['professionalism_score'],
                "emotional_tone":              emotion_summary['emotional_tone'],
                "feedback":                    emotion_summary['interview_feedback']
            },

            "body_language": {
                "score":               body_language_score,
                "appears_confident":   emotion_summary['appeared_confident_percentage'] > 50,
                "appears_nervous":     emotion_summary['appeared_nervous_percentage'] > 30,
                "appears_enthusiastic": emotion_summary['appeared_enthusiastic_percentage'] > 40
            },

            "overall_assessment": {
                "content_score":       content_score,
                "audio_quality_score": audio_quality_score,
                "body_language_score": body_language_score,
                "eye_contact_score":   eye_score_100,
                "emotional_tone":      emotion_summary['emotional_tone'],
                "cant_answer":         relevancy_result["cant_answer"]
            }
        }

        return convert_numpy_types(result)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n{'='*60}")
        print(f"❌ ANALYSIS FAILED: {str(e)}")
        print(f"{'='*60}")
        print(error_details)
        print(f"{'='*60}\n")

        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/test")
def test_interview_api():
    return {
        "message": "Interview API is working!",
        "models": {
            "whisper":    "small",
            "relevancy":  "gpt-4o-mini",
            "emotion":    "deepface",
            "fillers":    "custom",
            "eye_tracker": "mediapipe"
        }
    }