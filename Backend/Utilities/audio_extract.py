import os
import subprocess
from typing import Optional

class AudioExtractor:
    def __init__(self, output_dir: str = "Data/Audio"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        print(f"Audio Extractor initialized (output: {output_dir})")
    
    
    def extract_audio(self, video_path, output_filename, format="wav"):
        """Extract audio from video using FFmpeg (no fallbacks!)"""
        
        # FIRST: Check if video exists
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # SECOND: Check if FFmpeg exists (BEFORE we proceed)
        if not self._check_ffmpeg():
            raise RuntimeError(
                "FFmpeg not found in system PATH!\n")
        
        # Generate output filename if not provided
        if output_filename is None:
            video_basename = os.path.basename(video_path)
            video_name = os.path.splitext(video_basename)[0]
            output_filename = f"{video_name}_audio.{format}"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        print(f"Extracting audio from: {os.path.basename(video_path)}")
        
        try:
            # Extract with FFmpeg (no fallback!)
            self._extract_with_ffmpeg(video_path, output_path, format)
            
            # Verify file was created
            if not os.path.exists(output_path):
                raise Exception("Audio extraction failed - output file not created")
            
            # Verify file is not empty
            file_size = os.path.getsize(output_path)
            if file_size == 0:
                raise Exception("Audio extraction produced empty file")
            
            file_size_mb = file_size / (1024 * 1024)
            
            print(f"✅ Audio extracted: {output_filename}")
            print(f"   Size: {file_size_mb:.2f} MB")
            print(f"   Path: {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Audio extraction failed: {e}")
            raise
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    
    def _extract_with_ffmpeg(self, video_path: str, output_path: str, format: str):
        """Extract audio using FFmpeg"""
        print("   Using FFmpeg...")
        
        # FFmpeg command
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",  # No video
            "-acodec", "pcm_s16le" if format == "wav" else "libmp3lame",
            "-ar", "16000",  # 16kHz sample rate (good for Whisper)
            "-ac", "1",  # Mono
            "-y",  # Overwrite output file
            output_path
        ]
        
        # Run FFmpeg
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")