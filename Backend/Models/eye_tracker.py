import os
import numpy as np
import urllib.request
from typing import List, Dict

os.environ["DISPLAY"] = ""
os.environ["MPLBACKEND"] = "Agg"

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️ cv2 not available - eye tracker will use fallback")


class EyeTracker:
    def __init__(self):
        self.model_path = "Backend/Models/face_landmarker.task"
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}\n"
                                    "File Required and should be in Repo")

        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        base_options = mp.tasks.BaseOptions(model_asset_path=self.model_path)
        options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=True,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.landmarker = mp.tasks.vision.FaceLandmarker.create_from_options(options)

        self.LEFT_IRIS         = 468
        self.RIGHT_IRIS        = 473
        self.LEFT_EYE          = [33, 133, 160, 159, 158, 157, 173, 144]
        self.RIGHT_EYE         = [362, 263, 385, 386, 387, 388, 398, 373]
        self.NOSE_TIP          = 1
        self.CHIN              = 152
        self.LEFT_EYE_CORNER   = 33
        self.RIGHT_EYE_CORNER  = 263
        self.LEFT_MOUTH        = 61
        self.RIGHT_MOUTH       = 291

        print("✅ Eye Tracker initialized (MediaPipe 0.10.32) - Enhanced Accuracy")

    def analyze_frame(self, frame: np.ndarray) -> Dict:
        try:
            import mediapipe as mp

            if CV2_AVAILABLE:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                rgb = frame

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result   = self.landmarker.detect(mp_image)

            if not result.face_landmarks:
                return self._no_face_result()

            landmarks = result.face_landmarks[0]
            h, w      = frame.shape[:2]
            head_pose = self._calculate_head_pose(landmarks, w, h)
            score     = self._eye_contact_score_improved(landmarks, w, h, head_pose)

            return {
                "face_detected":    True,
                "eye_contact_score":round(score, 3),
                "looking_at_camera":score > 0.65,
                "gaze_direction":   self._gaze_direction(score),
                "head_pose": {
                    "pitch":        round(head_pose['pitch'], 1),
                    "yaw":          round(head_pose['yaw'], 1),
                    "facing_camera":head_pose['facing_camera']
                }
            }

        except Exception as e:
            return self._no_face_result(str(e))

    def _calculate_head_pose(self, landmarks, w, h) -> Dict:
        def get_3d(idx):
            return np.array([landmarks[idx].x * w, landmarks[idx].y * h, landmarks[idx].z * w])

        nose      = get_3d(self.NOSE_TIP)
        chin      = get_3d(self.CHIN)
        left_eye  = get_3d(self.LEFT_EYE_CORNER)
        right_eye = get_3d(self.RIGHT_EYE_CORNER)

        left_dist  = np.linalg.norm(left_eye[:2]  - nose[:2])
        right_dist = np.linalg.norm(right_eye[:2] - nose[:2])
        yaw_ratio  = (left_dist - right_dist) / (left_dist + right_dist)
        yaw        = yaw_ratio * 90

        nose_chin_angle = np.arctan2(chin[1] - nose[1], chin[0] - nose[0])
        pitch           = (nose_chin_angle - np.pi/2) * 180 / np.pi

        return {
            'yaw':          yaw,
            'pitch':        pitch,
            'facing_camera':abs(yaw) < 25 and abs(pitch) < 20
        }

    def _eye_contact_score_improved(self, landmarks, w, h, head_pose) -> float:
        def get_point(idx):
            return np.array([landmarks[idx].x * w, landmarks[idx].y * h])

        left_eye_inner  = get_point(133)
        left_eye_outer  = get_point(33)
        right_eye_inner = get_point(362)
        right_eye_outer = get_point(263)
        left_iris       = get_point(self.LEFT_IRIS)
        right_iris      = get_point(self.RIGHT_IRIS)

        def iris_ratio(iris, inner, outer):
            eye_width = np.linalg.norm(outer - inner)
            if eye_width < 1:
                return 0.5
            return np.linalg.norm(iris - inner) / eye_width

        avg_ratio   = (iris_ratio(left_iris, left_eye_inner, left_eye_outer) +
                       iris_ratio(right_iris, right_eye_inner, right_eye_outer)) / 2
        deviation   = abs(avg_ratio - 0.5)
        ratio_score = max(0.0, 1.0 - (deviation / 0.25))

        yaw_penalty   = 1.0 - (abs(head_pose['yaw'])   / 90.0)
        pitch_penalty = 1.0 - (abs(head_pose['pitch'])  / 60.0)
        pose_factor   = max(0.2, yaw_penalty * 0.7 + pitch_penalty * 0.3)

        return ratio_score * 0.7 + pose_factor * 0.3

    def _gaze_direction(self, score: float) -> str:
        if score > 0.80:   return "Excellent - Direct eye contact"
        elif score > 0.65: return "Good - Looking at camera"
        elif score > 0.50: return "Fair - Slightly off-center"
        elif score > 0.35: return "Poor - Looking away"
        else:              return "Very poor - Not looking at camera"

    def analyze_frames_list(self, frames: List[np.ndarray]) -> Dict:
        print(f"👁️ Analyzing eye contact in {len(frames)} frames...")
        results = []

        for i, frame in enumerate(frames):
            results.append(self.analyze_frame(frame))
            if (i + 1) % 10 == 0:
                print(f"   Processed {i + 1}/{len(frames)} frames")

        valid = [r for r in results if r['face_detected']]

        if not valid:
            return {
                "success": False,
                "summary": {
                    "eye_contact_percentage": 65.0,
                    "avg_score":              0.65,
                    "frames_with_face":       0,
                    "total_frames":           len(results),
                    "feedback":               "Unable to detect face consistently"
                }
            }

        eye_contact_frames = sum(1 for r in valid if r['looking_at_camera'])
        eye_contact_pct    = (eye_contact_frames / len(valid)) * 100
        avg_score          = sum(r['eye_contact_score'] for r in valid) / len(valid)

        excellent_pct = sum(1 for r in valid if r['eye_contact_score'] > 0.80) / len(valid) * 100
        good_pct      = sum(1 for r in valid if 0.65 < r['eye_contact_score'] <= 0.80) / len(valid) * 100
        fair_pct      = sum(1 for r in valid if 0.50 < r['eye_contact_score'] <= 0.65) / len(valid) * 100
        poor_pct      = sum(1 for r in valid if r['eye_contact_score'] <= 0.50) / len(valid) * 100

        head_poses        = [r['head_pose'] for r in valid if 'head_pose' in r]
        facing_camera_pct = sum(1 for hp in head_poses if hp['facing_camera']) / len(head_poses) * 100 if head_poses else 0

        feedback = self._generate_feedback(eye_contact_pct, avg_score, excellent_pct, facing_camera_pct)

        return {
            "success": True,
            "summary": {
                "eye_contact_percentage": round(eye_contact_pct, 1),
                "avg_score":              round(avg_score, 3),
                "frames_with_face":       len(valid),
                "total_frames":           len(results),
                "face_detection_rate":    round(len(valid) / len(results) * 100, 1),
                "distribution": {
                    "excellent": round(excellent_pct, 1),
                    "good":      round(good_pct, 1),
                    "fair":      round(fair_pct, 1),
                    "poor":      round(poor_pct, 1)
                },
                "head_pose": {"facing_camera_percentage": round(facing_camera_pct, 1)},
                "feedback":  feedback
            }
        }

    def _generate_feedback(self, eye_contact_pct, avg_score, excellent_pct, facing_camera_pct) -> str:
        if avg_score > 0.75 and eye_contact_pct > 80:
            return "Excellent eye contact! You maintained strong camera focus throughout."
        elif avg_score > 0.65 and eye_contact_pct > 70:
            return "Good eye contact overall. Try to maintain focus on the camera more consistently."
        elif avg_score > 0.55 and eye_contact_pct > 60:
            return "Fair eye contact. Focus on looking directly at the camera lens, not the screen."
        elif facing_camera_pct < 60:
            return "Head position needs improvement. Face the camera more directly and maintain posture."
        else:
            return "Eye contact needs significant improvement. Practice looking at the camera lens consistently."

    def _no_face_result(self, error: str = None) -> Dict:
        result = {
            "face_detected":    False,
            "eye_contact_score":0.0,
            "looking_at_camera":False,
            "gaze_direction":   "No face detected",
            "head_pose":        {"pitch": 0, "yaw": 0, "facing_camera": False}
        }
        if error:
            result["error"] = error
        return result


def quick_eye_analysis(video_path: str) -> Dict:
    tracker = EyeTracker()
    if not CV2_AVAILABLE:
        raise Exception("cv2 not available")
    cap    = cv2.VideoCapture(video_path)
    frames = []
    count  = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if count % 30 == 0:
            frames.append(frame)
        count += 1
    cap.release()
    return tracker.analyze_frames_list(frames)