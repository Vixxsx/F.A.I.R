import warnings
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
"""
USAGE:
from models.whisper_stt import WhisperSTT

stt = WhisperSTT(model_size="base")
result = stt.transcribe_audio("audio.wav")
print(result["text"])
"""

import whisper
import json
import os
from datetime import datetime

class WhisperSTT:
    """
    Whisper Speech-to-Text Pipeline
    Week 1-2: Core transcription module
    """
    
    def __init__(self, model_size="base"):

        print(f"🎤 Loading Whisper '{model_size}' model...")
        self.model = whisper.load_model(model_size)
        self.model_size = model_size
        print(f"✅ Whisper model '{model_size}' loaded successfully!")
    
    def transcribe_audio(self, audio_path, language="en"):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        print(f"\n🎤 Transcribing: {audio_path}")
        
        result = self.model.transcribe(
            audio_path,
            language=language,
            task="transcribe",
            verbose=False
        )
        
        transcript_data = {
            "text": result["text"].strip(),
            "language": result["language"],
            "segments": self._process_segments(result["segments"]),
            "duration": result["segments"][-1]["end"] if result["segments"] else 0,
            "word_count": len(result["text"].strip().split()),
            "timestamp": datetime.now().isoformat(),
            "model_used": self.model_size
        }
        
        print(f"✅ Transcription complete!")
        print(f"📝 Preview: {transcript_data['text'][:100]}...")
        print(f"📊 Word count: {transcript_data['word_count']}")
        
        return transcript_data
    
    def _process_segments(self, segments):

        processed = []
        for seg in segments:
            processed.append({
                "id": seg["id"],
                "start": round(seg["start"], 2),
                "end": round(seg["end"], 2),
                "text": seg["text"].strip(),
                "duration": round(seg["end"] - seg["start"], 2)
            })
        return processed
    
    def get_speaking_stats(self, transcript_data):
        """
        Calculate basic speaking statistics
        Useful for Week 5 fluency analysis
        
        Args:
            transcript_data: Output from transcribe_audio()
        
        Returns:
            dict: Speaking statistics
        """
        segments = transcript_data["segments"]
        total_duration = transcript_data["duration"]
        total_words = transcript_data["word_count"]
        
        # Calculate speaking time
        speaking_time = sum(seg["duration"] for seg in segments)
        
        # Calculate pause information
        pauses = []
        for i in range(len(segments) - 1):
            pause_duration = segments[i + 1]["start"] - segments[i]["end"]
            if pause_duration > 0.5:  # Only count pauses > 0.5 seconds
                pauses.append({
                    "after_segment": i,
                    "duration": round(pause_duration, 2)
                })
        
        stats = {
            "total_words": total_words,
            "duration_seconds": round(total_duration, 2),
            "speaking_time_seconds": round(speaking_time, 2),
            "words_per_minute": round((total_words / speaking_time) * 60, 2) if speaking_time > 0 else 0,
            "pause_time_seconds": round(total_duration - speaking_time, 2),
            "number_of_pauses": len(pauses),
            "average_pause_duration": round(sum(p["duration"] for p in pauses) / len(pauses), 2) if pauses else 0,
            "longest_pause": max((p["duration"] for p in pauses), default=0)
        }
        
        return stats
    
    def save_transcript(self, transcript_data, output_path):
        """
        Save transcript to JSON file
        
        Args:
            transcript_data: Output from transcribe_audio()
            output_path: Path to save JSON file
        """

    
    def transcribe_and_save(self, audio_path, output_dir="data/transcripts", language="en"):
        """
        Convenience method: Transcribe audio and save results
        
        Args:
            audio_path: Path to audio file
            output_dir: Directory to save transcript
            language: Language code
        
        Returns:
            tuple: (transcript_data, saved_file_path)
        """
        # Transcribe
        transcript_data = self.transcribe_audio(audio_path, language)
        
        # Generate output filename
        audio_filename = os.path.basename(audio_path)
        output_filename = f"{os.path.splitext(audio_filename)[0]}_transcript.json"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save
        saved_path = self.save_transcript(transcript_data, output_path)
        
        return transcript_data, saved_path


# ========== TESTING SCRIPT ==========

def test_whisper():
    """
    Test Whisper with sample audio
    """
    print("="*70)
    print("🧪 WHISPER TESTING")
    print("="*70)
    
    # Initialize Whisper
    stt = WhisperSTT(model_size="base")
    
    # Test audio file path
    test_audio = "data/Audio/test_audio.wav"
    
    if not os.path.exists(test_audio):
        print(f"\n⚠️ Test audio file not found: {test_audio}")

    
    # Transcribe
    print("\n" + "="*70)
    transcript = stt.transcribe_audio(test_audio)
    
    # Get stats
    stats = stt.get_speaking_stats(transcript)
    
    # Display results
    print("\n" + "="*70)
    print("📊 TRANSCRIPTION RESULTS")
    print("="*70)
    print(f"\n📝 Full Transcript:\n{transcript['text']}\n")
    
    print("="*70)
    print("⏱️ SPEAKING STATISTICS:")
    print("="*70)
    for key, value in stats.items():
        print(f"  • {key.replace('_', ' ').title()}: {value}")
    
    # Save to file
    print("\n" + "="*70)
    output_file = "data/Transcript/test_transcript.json"
    stt.save_transcript(transcript, output_file)
    
    print("\n" + "="*70)
    print("TRANSCRIPTION COMPLETE!")
    print("="*70)

def save_transcript(self, transcript_data, output_path):
    """
    Save transcript to JSON file
    
    Args:
        transcript_data: Output from transcribe_audio()
        output_path: Path to save JSON file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    import json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(transcript_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Transcript saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    test_whisper()

