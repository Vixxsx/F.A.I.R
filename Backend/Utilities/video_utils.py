import os
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional
import json

os.environ["DISPLAY"] = ""
os.environ["MPLBACKEND"] = "Agg"

try:
    import cv2
    CV2_AVAILABLE = True
    print("✅ cv2 loaded successfully")
except ImportError as e:
    CV2_AVAILABLE = False
    print(f"⚠️ cv2 not available: {e} - video processing disabled")


class VideoProcessor():
    def __init__(self, base_path: str = "Data/Video"):
        self.base_path      = base_path
        self.raw_path       = os.path.join(base_path, "Raw")
        self.processed_path = os.path.join(base_path, "Processed")
        self.frames_path    = os.path.join(base_path, "Frames")

        os.makedirs(self.raw_path,       exist_ok=True)
        os.makedirs(self.processed_path, exist_ok=True)
        os.makedirs(self.frames_path,    exist_ok=True)

    def _check_cv2(self):
        if not CV2_AVAILABLE:
            raise Exception("cv2 is not available in this environment")

    def test_webcam(self, camera_index: int = 0) -> bool:
        self._check_cv2()
        try:
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                return False
            ret, frame = cap.read()
            cap.release()
            return ret and frame is not None
        except Exception as e:
            print(f"Camera test failed: {e}")
            return False

    def get_available_cameras(self) -> List[int]:
        self._check_cv2()
        available = []
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available.append(i)
                cap.release()
        return available

    def capture_video(self, duration: int = 10, camera_index: int = 0, filename: Optional[str] = None, fps: int = 30) -> str:
        self._check_cv2()
        if filename is None:
            filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

        output_path = os.path.join(self.raw_path, filename)
        cap         = cv2.VideoCapture(camera_index)

        if not cap.isOpened():
            raise Exception(f"Camera {camera_index} not accessible")

        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out    = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame_count  = 0
        total_frames = duration * fps

        try:
            while frame_count < total_frames:
                ret, frame = cap.read()
                if ret:
                    out.write(frame)
                    frame_count += 1
                else:
                    break
        finally:
            cap.release()
            out.release()

        return output_path

    def get_video_info(self, video_path: str) -> Dict[str, any]:
        self._check_cv2()
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception(f"Could not open video file: {video_path}")

        try:
            fps         = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width       = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height      = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration    = frame_count / fps if fps > 0 else 0
            file_size   = os.path.getsize(video_path)

            return {
                "path":               video_path,
                "filename":           os.path.basename(video_path),
                "fps":                fps,
                "frame_count":        frame_count,
                "width":              width,
                "height":             height,
                "resolution":         f"{width}x{height}",
                "duration_seconds":   duration,
                "duration_formatted": self._format_duration(duration),
                "file_size_bytes":    file_size,
                "file_size_mb":       round(file_size / (1024 * 1024), 2)
            }
        finally:
            cap.release()

    def extract_frames(self, video_path, output_folder, every_nth=None, max_frames=None, return_arrays=False):
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_seconds = total_frames / fps if fps > 0 else 0
        
        if every_nth is None:
            every_nth = int(fps * 6)
        if max_frames is None:
            max_frames = min(20, max(5, int(duration_seconds / 6)))
        
        frame_paths = []
        frame_count = 0
        extracted_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # ← ADD INDENTATION HERE!
            if frame is None or frame.size == 0:  # ← Validate frame
                frame_count += 1
                continue
            
            if frame_count % every_nth == 0 and extracted_count < max_frames:  # ← CORRECT INDENT
                filename = f"frame_{extracted_count:03d}.jpg"
                filepath = os.path.join(output_folder, filename)
                
                success = cv2.imwrite(filepath, frame)  # ← Check success
                if success:
                    frame_paths.append(filepath)
                    extracted_count += 1
            
            frame_count += 1
        
        cap.release()
        print(f"✅ Extracted {extracted_count} frames")
        if return_arrays:
            arrays = []
            for path in frame_paths:
                frame = cv2.imread(path)
                if frame is not None:
                    arrays.append(frame)
            print(f"✅ Converted {len(arrays)} frames to arrays")
            return arrays
        else:
            return frame_paths
        

    def extract_frames_by_time(self, video_path: str, timestamps: List[float], output_folder: Optional[str] = None) -> List[np.ndarray]:
        self._check_cv2()
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception(f"Could not open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if output_folder:
            os.makedirs(output_folder, exist_ok=True)

        frames = []
        try:
            for timestamp in timestamps:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(timestamp * fps))
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
                    if output_folder:
                        cv2.imwrite(os.path.join(output_folder, f"frame_at_{int(timestamp * 1000)}ms.jpg"), frame)
            return frames
        finally:
            cap.release()

    def _format_duration(self, seconds: float) -> str:
        return f"{int(seconds // 60)}:{int(seconds % 60):02d}"

    def cleanup_temp_files(self, older_than_hours: int = 24):
        import time
        cutoff     = time.time() - (older_than_hours * 3600)
        deleted    = 0
        skip_files = {'.gitkeep', 'readme.md', '.gitignore'}

        for folder in [self.raw_path, self.processed_path]:
            if not os.path.exists(folder):
                continue
            for filename in os.listdir(folder):
                if filename in skip_files:
                    continue
                filepath = os.path.join(folder, filename)
                if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff:
                    os.remove(filepath)
                    deleted += 1

        print(f"Cleaned up {deleted} file(s)")


def quick_capture(duration: int = 10, output_name: str = "test_video.mp4") -> str:
    return VideoProcessor().capture_video(duration=duration, filename=output_name)


def quick_extract_frames(video_path: str, every_n: int = 10) -> List[np.ndarray]:
    return VideoProcessor().extract_frames(video_path, every_nth=every_n)