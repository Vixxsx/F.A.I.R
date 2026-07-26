// ========== CONFIGURATION ==========
const API_BASE_URL = 'http://localhost:8000';
const QUESTION_TIME_LIMIT = 120; 
const COUNTDOWN_DURATION = 5; 

// ========== STATE ==========
let stream = null;
let mediaRecorder = null;
let recordedChunks = [];
let currentQuestionIndex = 0;
let questions = [];
let timerInterval = null;
let timeRemaining = QUESTION_TIME_LIMIT;
let isRecording = false;
let savedVideos = []; 

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', async () => {
    if (!sessionStorage.getItem('mediaReady')) {
        window.location.href = 'interview_test.html';
        return;
    }

    const settings = JSON.parse(sessionStorage.getItem('interviewPreferences') || '{}');

    await initializeCamera();

    await fetchQuestions(settings);

    startQuestion();
});

// ========== CAMERA SETUP ==========

async function initializeCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 1280 }, height: { ideal: 720 } },
            audio: true
        });

        const videoElement = document.getElementById('videoElement');
        videoElement.srcObject = stream;
       
        console.log('✅ Camera initialized');
    } catch (error) {
        console.error('❌ Camera error:', error);
        alert('Failed to access camera. Please check permissions.');
        window.location.href = 'home.html';
    }
}
// ========== FETCH QUESTIONS ==========
async function fetchQuestions(settings) {
    console.log('DEBUG 1: Settings path =', settings.path);
    console.log('DEBUG 2: Is manual?', settings.path === 'manual');
    console.log('🔍 DEBUG 3: Full settings object:', settings);
    console.log('🔍 DEBUG 4: settings.questions:', settings.questions);
    console.log('🔍 DEBUG 5: questions array length:', settings.questions?.length);
    showLoading('Generating Interview Questions', 'Please be patient...');
    
    try {
        if (settings.path === 'manual') {
            console.log('✅ ENTERED MANUAL MODE');
            
            const payload = {
                jobRole: settings.jobRole,
                education_lvl: settings.education_lvl,
                degree: settings.degree,
                company_type: settings.company_type,
                difficulty: settings.difficulty,
                interview_type: settings.interview_type,
                count: parseInt(settings.numQuestions) || 5
            };

            console.log('📤 Payload:', payload);

            const stringified = JSON.stringify(payload);
            console.log('📝 Stringified JSON:', stringified);  // ← ADD THIS

            const response = await fetch(`${API_BASE_URL}/api/questions/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: stringified  // ← USE stringified
            });

            if (response.ok) {
                const data = await response.json();
                questions = data.questions || [];
                console.log('✅ Questions generated:', questions);
            } else {
                console.error('❌ Backend error:', response.status, await response.text());
            }
        } else if (settings.path === 'resume') {
            console.log('Resume mode - skipping question generation');
            // For resume mode, questions come from backend after upload
            questions =settings.questions || [];
        }
    } catch (error) {
        console.error('❌ Failed to fetch questions:', error);
    }

    // Fallback demo questions
    if (questions.length === 0) {
        questions = [
            "Tell me about your experience with the technologies mentioned in your resume.",
            "Describe a challenging project you worked on and how you overcame obstacles.",
            "Where do you see yourself professionally in 5 years?",
            "How do you handle disagreements with team members?",
            "Why are you interested in this role and our company?"
        ];
    }

    hideLoading();
    updateProgress();
}

// ========== QUESTION FLOW ==========
async function startQuestion() {
    if (currentQuestionIndex >= questions.length) {
        await processAllAnswers();
        return;
    }
    updateProgress();
    displayQuestion();
    await showCountdown();
    startRecording();
}

function displayQuestion() {
    const questionNum = currentQuestionIndex + 1;
    const totalQuestions = questions.length;
   
    document.getElementById('questionNumber').textContent = `Question ${questionNum}`;
    document.getElementById('questionProgress').textContent = `Question ${questionNum} of ${totalQuestions}`;
    document.getElementById('questionText').textContent = questions[currentQuestionIndex];
}

function updateProgress() {
    const progress = ((currentQuestionIndex + 1) / questions.length) * 100;
    document.getElementById('progressBar').style.width = progress + '%';
}

// ========== COUNTDOWN - NEW DESIGN ==========
async function showCountdown() {
    const container = document.getElementById('countdownContainer');
    const numberEl = document.getElementById('countdownNumber');
   
    container.classList.add('active');
   
    for (let i = COUNTDOWN_DURATION; i > 0; i--) {
        numberEl.textContent = i;
        numberEl.style.animation = 'none';
        const ring = container.querySelector('.countdown-ring');
        if (ring) ring.style.animation = 'none';
        void numberEl.offsetWidth;
        numberEl.style.animation = 'numberBounce 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55)';
        if (ring) ring.style.animation = 'ringPulse 1s ease-in-out';
       
        await sleep(1000);
    }
   
    container.classList.remove('active');
}

// ========== RECORDING ==========
function startRecording() {
    recordedChunks = [];
    const options = { mimeType: 'video/webm;codecs=vp9,opus' };
    try {
        mediaRecorder = new MediaRecorder(stream, options);
    } catch (e) {
        console.warn('vp9 not supported, trying vp8');
        try {
            mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm;codecs=vp8,opus' });
        } catch (e2) {
            mediaRecorder = new MediaRecorder(stream);
        }
    }

    mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
            recordedChunks.push(event.data);
        }
    };

    mediaRecorder.onstop = () => {
        console.log('✅ Recording stopped');
        saveVideoLocally();
    };
    mediaRecorder.start();
    isRecording = true;
    document.getElementById('recordingIndicator').classList.add('active');
    document.getElementById('stopBtn').classList.add('show');
    startTimer();
   
    console.log('🎥 Recording started');
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        stopTimer();
        document.getElementById('recordingIndicator').classList.remove('active');
        document.getElementById('stopBtn').classList.remove('show');
    }
}

// ========== SAVE VIDEO LOCALLY (BATCH STRATEGY) ==========
function saveVideoLocally() {
    const blob = new Blob(recordedChunks, { type: 'video/webm' });
    savedVideos.push({
        questionNumber: currentQuestionIndex + 1,
        question: questions[currentQuestionIndex],
        videoBlob: blob,
        timestamp: new Date().toISOString()
    });
   
    console.log(`✅ Video ${currentQuestionIndex + 1} saved locally`);
   
    // Move to next question IMMEDIATELY (no backend call yet!)
    currentQuestionIndex++;
    startQuestion();
}
// ========== BATCH PROCESSING (AT THE END) ==========
async function processAllAnswers() {
    showLoading('Analyzing Answer', `Processing all ${savedVideos.length} answers...`);
   
    console.log('🔄 Starting batch upload and analysis...');
   
    const results = [];
   
    for (let i = 0; i < savedVideos.length; i++) {
        const video = savedVideos[i];
        showLoading('Analyzing Answer', `Analyzing answer ${i + 1} of ${savedVideos.length}...`);
       
        try {
            const formData = new FormData();
            formData.append('video', video.videoBlob, `question_${video.questionNumber}.webm`);
            formData.append('question', video.question);
            formData.append('questionNumber', video.questionNumber);
            const response = await fetch(`${API_BASE_URL}/api/interview/analyze-answer`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                results.push(result);
                console.log(`✅ Answer ${i + 1} analyzed`);
            } else {
                console.error(`❌ Failed to analyze answer ${i + 1}`);
                results.push({ error: 'Analysis failed', questionNumber: video.questionNumber });
            }
           
        } catch (error) {
            console.error(`❌ Error analyzing answer ${i + 1}:`, error);
            results.push({ error: error.message, questionNumber: video.questionNumber });
        }
    }
    sessionStorage.setItem('interviewResults', JSON.stringify(results));
   
    await finishInterview();
}

// ========== FINISH INTERVIEW ==========
async function finishInterview() {
    showLoading('Analyzing Answer', 'Preparing your scorecard...');
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
   
    await sleep(1500);
    window.location.href = 'scorecard.html';
}

// ========== TIMER ==========
function startTimer() {
    timeRemaining = QUESTION_TIME_LIMIT;
    updateTimerDisplay();
   
    timerInterval = setInterval(() => {
        timeRemaining--;
        updateTimerDisplay();
        updateTimerColor();
       
        if (timeRemaining <= 0) {
            stopRecording();
        }
    }, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function updateTimerDisplay() {
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;
    const display = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    document.getElementById('timer').textContent = display;
}

function updateTimerColor() {
    const timerEl = document.getElementById('timer');
    timerEl.classList.remove('warning', 'danger');
    if (timeRemaining <= 10) {
        timerEl.classList.add('danger');
    } else if (timeRemaining <= 30) {
        timerEl.classList.add('warning');
    }
}

// ========== UI HELPERS ==========
function showLoading(title, subtitle) {

    document.querySelector('.lo-title').textContent = title;
    document.getElementById('loadingText').textContent = subtitle;
    document.getElementById('loadingOverlay').classList.add('active');
}
function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ========== EVENT LISTENERS ==========
document.getElementById('stopBtn').addEventListener('click', () => {
    stopRecording();
});

window.addEventListener('beforeunload', () => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    stopTimer();
});

window.addEventListener('beforeunload', (e) => {
    if (currentQuestionIndex > 0 && currentQuestionIndex < questions.length) {
        e.preventDefault();
        e.returnValue = 'Interview in progress. Are you sure you want to leave?';
    }
});