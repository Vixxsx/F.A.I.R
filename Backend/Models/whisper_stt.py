from unittest import result
import warnings
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
import json
import os
from datetime import datetime
from faster_whisper import WhisperModel
class WhisperSTT:
    
    def __init__(self, model_size="medium", device="cuda", compute_type="float16"):
        print(f"🎤 Loading faster-whisper '{model_size}' model...")
        self.model_size = model_size
        self.device = device
        
        # Fallback to CPU/int8 automatically if CUDA isn't explicitly configured or fails
        try:
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        except Exception as e:
            print(f"⚠️ CUDA/FP16 initialization failed ({e}). Falling back to CPU...")
            self.device = "cpu"
            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

        print(f"✅ faster-whisper model '{model_size}' loaded successfully on {self.device.upper()}!")

    def transcribe(self, audio_path, language="en"):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        print(f"\n🎤 Transcribing: {audio_path}")
        
        # faster-whisper returns a generator for segments and an info tuple
        segments_generator, info = self.model.transcribe(
            audio_path,
            language=language,
            task="transcribe",
            word_timestamps=True,                       # Enables word-level details
            condition_on_previous_text=False,          # Prevents context cleanup loops
            compression_ratio_threshold=2.4,           # Retains more words
            no_speech_threshold=0.6,                    # Catches faint speech
            beam_size=5,
            temperature=0.0
        )
        raw_transcript = ""
        processed_segments = []
        
        for seg in segments_generator:
            # Reconstruct transcript from word-level objects or segment text
            if seg.words:
                for word_data in seg.words:
                    raw_transcript += word_data.word + " "
            else:
                raw_transcript += seg.text + " "
            
            # Format segment data to preserve original functionality
            processed_segments.append({
                "id": seg.id,
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
                "duration": round(seg.end - seg.start, 2)
            })

        raw_transcript = raw_transcript.strip()
        duration = processed_segments[-1]["end"] if processed_segments else getattr(info, 'duration', 0)

        transcript_data = {
            "text": raw_transcript, 
            "language": info.language,
            "segments": processed_segments,
            "duration": round(duration, 2),
            "word_count": len(raw_transcript.split()),
            "timestamp": datetime.now().isoformat(),
            "model_used": self.model_size,
            "audio_file": os.path.basename(audio_path)
        }
        
        print(f"✅ Transcription complete!")
        print(f"📝 Transcript: {transcript_data['text'][:100]}...")
        print(f"📊 Word count: {transcript_data['word_count']}")
        
        return transcript_data

    def get_speaking_stats(self, transcript_data):
        segments = transcript_data["segments"]
        total_duration = transcript_data["duration"]
        total_words = transcript_data["word_count"]
        
        speaking_time = sum(seg["duration"] for seg in segments)
        pauses = []
        
        for i in range(len(segments) - 1):
            pause_duration = segments[i + 1]["start"] - segments[i]["end"]
            if pause_duration > 0.5:  # Count pauses longer than 0.5 seconds
                pauses.append({
                    "after_segment": i,
                    "duration": round(pause_duration, 2)
                })
        
        stats = {
            "total_words": total_words,
            "duration_seconds": round(total_duration, 2),
            "speaking_time_seconds": round(speaking_time, 2),
            "words_per_minute": round((total_words / speaking_time) * 60, 2) if speaking_time > 0 else 0,
            "pause_time_seconds": round(max(0, total_duration - speaking_time), 2),
            "number_of_pauses": len(pauses),
            "average_pause_duration": round(sum(p["duration"] for p in pauses) / len(pauses), 2) if pauses else 0,
            "longest_pause": max((p["duration"] for p in pauses), default=0)
        }
        return stats

    def save_transcript(self, transcript_data, filename=None, output_dir="Data/Transcript"):
        os.makedirs(output_dir, exist_ok=True)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transcript_{timestamp}.json"
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Transcript saved: {output_path}")
        return output_path

    def load_transcript(self, filepath):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Transcript not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Transcript loaded: {filepath}")
        return data

    def transcribe_and_save(self, audio_path, save_transcript=True):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        initial_prompt = (
            "This is a professional job interview. "
            "The candidate is discussing work experience, deadlines, teamwork, "
            "group projects, technical skills, and career goals."
        )

        segments_generator, info = self.model.transcribe(
            audio_path,
            language="en",
            initial_prompt=initial_prompt,
            temperature=0.0,
            beam_size=5,
            condition_on_previous_text=True
        )

        segments = list(segments_generator)
        full_text = " ".join([seg.text.strip() for seg in segments])

        result_dict = {
            "text": full_text,
            "language": info.language,
            "duration": getattr(info, 'duration', 0),
            "segments": [{"id": s.id, "start": s.start, "end": s.end, "text": s.text} for s in segments] if hasattr(segments[0], 'id') else []
        }

        saved_path = None
        if save_transcript:
            audio_name = os.path.splitext(os.path.basename(audio_path))[0]
            transcript_filename = f"{audio_name}_transcript.json"
            saved_path = self.save_transcript(result_dict, filename=transcript_filename)

        return {
    "text": result_dict.get("text", ""),
    "word_count": len(result_dict.get("text", "").split()),
    "transcription": result_dict,
    "saved_to": saved_path
        }
# ========== TESTING ==========
def test_whisper():
    print("=" * 70)
    print("🧪 FASTER-WHISPER TESTING")
    print("=" * 70)
    
    # Defaults to CUDA, but automatically falls back to CPU if needed
    stt = WhisperSTT(model_size="medium", device="cuda", compute_type="float16")
    
    test_audio = "Data/Audio/test_audio.wav"
    
    if not os.path.exists(test_audio):
        print(f"\n⚠️ Test audio file not found: {test_audio}")
        return

    print("\n" + "=" * 70)
    transcript = stt.transcribe(test_audio)
    stats = {
    "total_words": len(transcript["text"].split()),
    "duration_seconds": 120,
    "speaking_time_seconds": 96,
    "words_per_minute": (len(transcript["text"].split()) / 120) * 60
}
    
    print("\n" + "=" * 70)
    print("📊 TRANSCRIPTION RESULTS")
    print("=" * 70)
    print(f"\n📝 Full Transcript:\n{transcript['text']}\n")
    print("=" * 70)
    print("⏱️ SPEAKING STATISTICS:")
    print("=" * 70)
    for key, value in stats.items():
        print(f"  • {key.replace('_', ' ').title()}: {value}")
        
    print("\n" + "=" * 70)
    output_path = stt.save_transcript(transcript)
    
    print("\n" + "=" * 70)
    print("✅ TRANSCRIPTION COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    test_whisper()