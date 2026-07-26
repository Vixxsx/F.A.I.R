# 🎯 AIRA - Automated Interview & Response Analyzer

**AI-powered interview practice platform that provides real-time feedback on your performance**

---

## 📖 About

**AIRA (Automated Interview & Response Analyzer)** is an AI-powered interview coaching platform that helps job seekers practice and improve their interview skills. Using advanced machine learning models, AIRA analyzes your video responses and provides detailed feedback on multiple aspects of your performance.

### Why AIRA?

- 🎥 **Practice Anywhere, Anytime** - No need to schedule mock interviews
- 🤖 **AI-Powered Analysis** - Get instant, objective feedback
- 📊 **Comprehensive Scoring** - Detailed breakdown across multiple dimensions
- 🎯 **Personalized Advice** - AI-generated tips tailored to your weaknesses
- 📈 **Track Progress** - Monitor improvement over time

---

## ✨ Features

### 🎤 **Multi-Dimensional Analysis**

AIRA evaluates your interview performance across 4 key dimensions:

| Dimension | Weight | What We Analyze |
|-----------|--------|-----------------|
| **Content Relevancy** | 30% | Answer quality, completeness, STAR method usage |
| **Audio Quality** | 25% | Filler words, speaking pace (WPM), clarity |
| **Eye Contact** | 25% | Gaze tracking, camera engagement |
| **Body Language** | 20% | Facial expressions, confidence, enthusiasm |

### 🧠 **AI-Powered Features**

- **Smart Question Generation** - GPT-4o-mini generates unique, role-specific questions
- **Speech-to-Text** - OpenAI Whisper transcribes your answers with high accuracy
- **Emotion Detection** - DeepFace analyzes facial expressions and confidence levels
- **Eye Tracking** - MediaPipe tracks eye contact and head pose
- **Personalized Feedback** - AI-generated actionable improvement tips

### 🎯 **Interview Types**

- **Technical Interviews** - Algorithm questions, system design, coding problems
- **Behavioral Interviews** - STAR method scenarios, past experiences
- **Mixed Interviews** - Combination of technical and behavioral questions

### 📊 **Grading System**

```
S Grade (90-100): Outstanding - Interview ready
A Grade (80-89):  Excellent - Minor improvements needed
B Grade (70-79):  Good - Practice specific areas
C Grade (60-69):  Average - More practice required
D Grade (50-59):  Below Average - Significant improvement needed
F Grade (0-49):   Poor - Extensive practice required
```

---

## 🚀 Installation

### Prerequisites

- Python 3.10+
- FFmpeg (for audio processing)
- Webcam (for video recording)
- Modern web browser (Chrome, Edge, Firefox)

### Quick Start

```bash
# Clone repository
git clone https://github.com/Vixxsx/A.I.R.A.git
cd A.I.R.A

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Create a .env file with your OpenAI API key
OPENAI_API_KEY=your-api-key-here

# Run the application
uvicorn Backend.main:app --reload --host 0.0.0.0 --port 8000
```

Open your browser and navigate to `http://localhost:8000`

---

## 🛠️ Tech Stack

### Frontend
- HTML5, CSS3, Vanilla JavaScript
- MediaRecorder API for video/audio recording
- LocalStorage API for data persistence

### Backend
- **Python 3.10+** - Core language
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server

### AI/ML Models

| Technology | Purpose |
|------------|---------|
| **OpenAI Whisper** | Speech-to-Text transcription |
| **GPT-4o-mini** | Question generation & feedback |
| **DeepFace** | Emotion detection |
| **MediaPipe** | Eye tracking (468 facial landmarks) |

### Data Processing
- **OpenCV** - Video frame extraction
- **MoviePy** - Audio extraction
- **NumPy** - Numerical computations
- **FFmpeg** - Media conversion

---

## 📁 Project Structure

```
A.I.R.A/
├── Backend/
│   ├── api/                      # FastAPI routes
│   ├── Models/                   # AI/ML models
│   └── Utilities/                # Helper functions
├── Frontend/
│   ├── Assets/                   # JavaScript files
│   ├── Components/               # CSS stylesheets
│   └── Pages/                    # HTML pages
├── .env                          # Environment variables (create this)
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
└── README.md
```

---

## 🎯 How It Works

```
1. Record your interview answer (video + audio)
2. AI analyzes multiple aspects:
   • Whisper converts speech to text
   • GPT evaluates answer quality
   • DeepFace detects emotions
   • MediaPipe tracks eye contact
3. Get instant feedback with detailed scores
4. Receive personalized improvement tips
```

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Ways to Contribute

1. 🐛 **Report Bugs** - Submit issues for bugs you find
2. 💡 **Suggest Features** - Share ideas for improvements
3. 📝 **Improve Documentation** - Help make docs clearer
4. 🔧 **Submit Pull Requests** - Fix bugs or add features

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/A.I.R.A.git
cd A.I.R.A

# Create a feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Add: your feature description"

# Push to your fork
git push origin feature/your-feature-name

# Open a Pull Request
```

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add comments for complex logic
- Write docstrings for functions
- Test your changes before submitting

---

## 📄 License

This project is licensed under the **MIT License**.

---

## 👥 Team

- **[@Vixxsx](https://github.com/Vixxsx)** - Project Lead & Backend Developer
- **[@Sadhika2005](https://github.com/Sadhika2005)** - Debug Engineer
- **[@nehaparnai](https://github.com/nehaparnai)** - Frontend Designer
- **[@nehasudheesh](https://github.com/nehasudheesh)** - Developer

---

## 🙏 Acknowledgments

- OpenAI - For Whisper and GPT models
- Google - For MediaPipe face tracking
- DeepFace - For emotion detection
- FastAPI - For excellent web framework

---

<div align="center">

**Made with ❤️ by the AIRA Team**
```
A.I.R.A
├─ .txt
├─ Backend
│  ├─ api
│  │  ├─ Auth_routes.py
│  │  ├─ Feedback_routes.py
│  │  ├─ History_routes.py
│  │  ├─ Interview_routes.py
│  │  ├─ Question_routes.py
│  │  ├─ Resume_routes.py
│  │  ├─ Video_routes.py
│  │  └─ __init__.py
│  ├─ Configuration
│  │  └─ dummy1.txt
│  ├─ main.py
│  ├─ Models
│  │  ├─ Content_Relevancy.py
│  │  ├─ emotion_detector.py
│  │  ├─ eye_tracker.py
│  │  ├─ face_landmarker.task
│  │  ├─ filler_word_detection.py
│  │  ├─ Question_Generator.py
│  │  ├─ whisper_stt.py
│  │  ├─ _registry.py
│  │  └─ __init__.py
│  ├─ Tests
│  │  ├─ Conftest.py
│  │  ├─ Questions.py
│  │  └─ __init__.py
│  └─ Utilities
│     ├─ audio_extract.py
│     ├─ database.py
│     ├─ Resume_parse.py
│     ├─ video_utils.py
│     └─ __init__.py
├─ Frontend
│  ├─ Assets
│  │  ├─ audio
│  │  └─ js
│  │     ├─ auth.js
│  │     ├─ home.js
│  │     └─ interview.js
│  ├─ Components
│  │  └─ theme.css
│  └─ Pages
│     ├─ home.html
│     ├─ interview.html
│     ├─ interview_test.html
│     ├─ Login.html
│     ├─ register.html
│     ├─ scorecard.html
│     └─ start.html
├─ pytest.ini
├─ README.md
└─ requirements.txt

```