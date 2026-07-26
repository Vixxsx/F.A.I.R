const API_BASE_URL = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', function () {
    checkLoginStatus();
    loadInterviewHistory();
    initializeSplitScreen();
});

function getCurrentUser() {
    const sessionuser = sessionStorage.getItem('aira_user');
    if (sessionuser) return sessionuser;
    const localuser = localStorage.getItem('aira_user');
    return localuser;
}

function checkLoginStatus() {
    const currentUser = getCurrentUser();
    if (!currentUser) {
        window.location.href = 'Login.html';
        return;
    }
    document.getElementById('username').textContent = currentUser + '!';
}
function logout() {
    sessionStorage.removeItem('aira_user');
    localStorage.removeItem('aira_user');
    window.location.href = 'Login.html';
}

let splitState = {
    overlay: null,
    panelLeft: null,
    panelRight: null,
    formViewOverlay: null,
    formViewContainer: null,
    ringLeft: null,
    ringRight: null,
    
    splitPos: 50,
    targetSplitPos: 50,
    currentHover: null,
    isHolding: false,
    holdStartTime: null,
    holdAnimFrame: null,
    holdTimers: {},
    
    selectedPath: null,
};

function initializeSplitScreen() {
    splitState.overlay = document.getElementById('simulatorOverlay');
    splitState.panelLeft = document.getElementById('panelLeft');
    splitState.panelRight = document.getElementById('panelRight');
    splitState.formViewOverlay = document.getElementById('formViewOverlay');
    splitState.formViewContainer = document.getElementById('formViewContainer');
    splitState.ringLeft = document.getElementById('ringLeft');
    splitState.ringRight = document.getElementById('ringRight');

    const holdZones = document.querySelectorAll('.hold-confirm-zone');
    holdZones.forEach(zone => {
        zone.addEventListener('mousedown', handleHoldStart);
        zone.addEventListener('mouseup', handleHoldEnd);
        zone.addEventListener('mouseleave', handleHoldCancel);
    });

    splitState.panelLeft.addEventListener('mouseenter', () => setHover('left'));
    splitState.panelRight.addEventListener('mouseenter', () => setHover('right'));
    splitState.overlay.addEventListener('mouseleave', clearHover);
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeSplitScreen();
    });
}

function showSplitScreen() {
    if (!splitState.overlay) {
        console.error('Split screen overlay not initialized');
        return;
    }
    splitState.overlay.classList.add('active');
    applyVerticalSplit(50);
    updatePanelVisuals('none');
}

function closeSplitScreen() {
    splitState.overlay.classList.remove('active');
    splitState.formViewOverlay.classList.remove('active');
    cancelAllHolds();
}

function applyVerticalSplit(percentage) {
    splitState.panelLeft.style.clipPath = `polygon(0 0, ${percentage}% 0, ${percentage}% 100%, 0 100%)`;
    splitState.panelRight.style.clipPath = `polygon(${percentage}% 0, 100% 0, 100% 100%, ${percentage}% 100%)`;
}

function updatePanelVisuals(hoverSide) {
    const leftPreview = splitState.panelLeft.querySelector('.panel-preview');
    const rightPreview = splitState.panelRight.querySelector('.panel-preview');
    const leftDetails = splitState.panelLeft.querySelector('.perks-list');
    const rightDetails = splitState.panelRight.querySelector('.perks-list');
    
    if (hoverSide === 'left') {
        // Lighten left, darken right
        splitState.panelLeft.style.opacity = '1';
        splitState.panelRight.style.opacity = '0.4';
        splitState.panelLeft.style.filter = 'brightness(1.1)';
        splitState.panelRight.style.filter = 'brightness(0.6)';
        
        // Show details on left
        if (leftDetails) leftDetails.style.opacity = '1';
        if (rightDetails) rightDetails.style.opacity = '0';
    } else if (hoverSide === 'right') {
        // Lighten right, darken left
        splitState.panelLeft.style.opacity = '0.4';
        splitState.panelRight.style.opacity = '1';
        splitState.panelLeft.style.filter = 'brightness(0.6)';
        splitState.panelRight.style.filter = 'brightness(1.1)';
        
        // Show details on right
        if (leftDetails) leftDetails.style.opacity = '0';
        if (rightDetails) rightDetails.style.opacity = '1';
    } else {
        // Reset to neutral
        splitState.panelLeft.style.opacity = '1';
        splitState.panelRight.style.opacity = '1';
        splitState.panelLeft.style.filter = 'brightness(0.8)';
        splitState.panelRight.style.filter = 'brightness(0.8)';
        
        // Hide details
        if (leftDetails) leftDetails.style.opacity = '0.3';
        if (rightDetails) rightDetails.style.opacity = '0.3';
    }
}

function setHover(side) {
    if (splitState.isHolding) return;
    splitState.currentHover = side;
    splitState.targetSplitPos = side === 'left' ? 60 : 40;
    updatePanelVisuals(side);
    animateSplitTo(splitState.targetSplitPos);
}

function clearHover() {
    if (splitState.isHolding) return;
    splitState.currentHover = null;
    splitState.targetSplitPos = 50;
    updatePanelVisuals('none');
    animateSplitTo(50);
}

function animateSplitTo(target) {
    const diff = target - splitState.splitPos;
    const step = diff * 0.12;  // Smoother animation
    splitState.splitPos += step;
    applyVerticalSplit(splitState.splitPos);
    
    if (Math.abs(splitState.splitPos - target) > 0.3) {
        requestAnimationFrame(() => animateSplitTo(target));
    } else {
        splitState.splitPos = target;
        applyVerticalSplit(target);
    }
}

function handleHoldStart(e) {
    const side = e.currentTarget.getAttribute('data-side');
    splitState.isHolding = true;
    splitState.holdStartTime = Date.now();
    splitState.selectedPath = side;

    splitState.holdTimers[side] = setInterval(() => {
        const elapsed = Date.now() - splitState.holdStartTime;
        const progress = Math.min(elapsed / 3000, 1);
        const ringOffset = 201 * (1 - progress);
        
        // Update split position while holding (morph to 100%)
        if (side === 'left') {
            splitState.splitPos = 50 + (progress * 50);  // 50 → 100
            applyVerticalSplit(splitState.splitPos);
            splitState.ringLeft.style.strokeDashoffset = ringOffset;
        } else {
            splitState.splitPos = 50 - (progress * 50);  // 50 → 0
            applyVerticalSplit(splitState.splitPos);
            splitState.ringRight.style.strokeDashoffset = ringOffset;
        }

        if (progress === 1) {
            clearInterval(splitState.holdTimers[side]);
            completeHold(side);
        }
    }, 16);
}

function handleHoldEnd(e) {
    const side = e.currentTarget.getAttribute('data-side');
    const elapsed = Date.now() - splitState.holdStartTime;
    
    if (elapsed < 3000) {
        handleHoldCancel();
    }
}

function handleHoldCancel() {
    cancelAllHolds();
    splitState.isHolding = false;
    splitState.targetSplitPos = 50;
    updatePanelVisuals('none');
    animateSplitTo(50);
}

function cancelAllHolds() {
    Object.values(splitState.holdTimers).forEach(timer => clearInterval(timer));
    splitState.holdTimers = {};
    splitState.ringLeft.style.strokeDashoffset = 201;
    splitState.ringRight.style.strokeDashoffset = 201;
}

function completeHold(side) {
    splitState.isHolding = false;
    splitState.overlay.classList.remove('active');
    showFormView(side);
}

function handleManualSubmit(e) {
    e.preventDefault();
    
    const prefs = {
        path: 'manual',
        jobRole: document.getElementById('manualJobSim').value,
        education_lvl: document.getElementById('manualEducationlvlSim').value,
        degree: document.getElementById('manualDegreeSim').value,
        company_type: document.getElementById('manualCompanySim').value,
        numQuestions: document.getElementById('manualNumQSim').value || 5,
        difficulty: document.getElementById('manualDiffSim').value,
        interview_type: document.getElementById('manualTypeSim').value,
        timestamp: new Date().toISOString()
    };
    
    sessionStorage.setItem('interviewPreferences', JSON.stringify(prefs));
    sessionStorage.setItem('jobRole', prefs.jobRole);
    
    showMessage('✅ Ready! Launching interview...', 'success');
    setTimeout(() => {
        window.location.href = './interview_test.html';  // ← Changed!
    }, 1500);
}

function validateResumeUpload(e) {
    const file = document.getElementById('resumeFileSim').files[0];
    
    if (!file) {
        showMessage('⚠️ Please upload a resume PDF!', 'error');
        e.preventDefault();
        return false;
    }
    
    handleResumeSubmit(e);
}

async function handleResumeSubmit(e) {
    e.preventDefault();
    
    // Read current values from form
    const jobRole = document.getElementById('resumeJobSim').value.trim();
    const numQuestions = document.getElementById('numQuestionsSim').value || 5;
    const difficulty = document.getElementById('resumeDiffSim').value;
    const interviewType = document.getElementById('resumeTypeSim').value;
    
    // Check if we already parsed questions from autoUploadResume
    let existingPrefs = {};
    try {
        existingPrefs = JSON.parse(sessionStorage.getItem('interviewPreferences') || '{}');
    } catch(err) {}

    // Combine settings
    const prefs = {
        path: 'resume',
        jobRole: jobRole || existingPrefs.jobRole || 'Professional',
        numQuestions: numQuestions,
        difficulty: difficulty,
        interviewType: interviewType,
        questions: existingPrefs.questions || [],
        extractedData: existingPrefs.extractedData || {},
        timestamp: new Date().toISOString()
    };

    sessionStorage.setItem('interviewPreferences', JSON.stringify(prefs));
    sessionStorage.setItem('jobRole', prefs.jobRole);

    closeResumeOverlay();
    showMessage('🚀 Launching interview...', 'success');
    
    setTimeout(() => {
        window.location.href = './interview_test.html';
    }, 1000);
}


function showFormView(path) {
    const isResume = path === 'left';
    
    if (isResume) {
        splitState.formViewContainer.innerHTML = `
            <h3>📄 Resume Optimization</h3>
            <p>Upload your resume and we'll generate tailored interview questions</p>
            
            <form id="resumeFormSim" onsubmit="handleResumeSubmit(event)">
                <!-- JOB ROLE FIRST -->
                <div class="sim-form-group">
                    <label>💼 Target Job Role *</label>
                    <input type="text" id="resumeJobSim" placeholder="e.g., Software Engineer" 
                        oninput="enableResumeUpload()" required>
                    <small style="color: #6a6d8c;">What position are you interviewing for?</small>
                </div>

                <!-- RESUME UPLOAD SECOND -->
                <div class="sim-form-group">
                    <label>📝 Upload Resume (PDF)</label>
                    <div class="upload-zone" onclick="document.getElementById('resumeFileSim').click()" 
                        id="resumeUploadZone" style="opacity: 0.5; cursor: not-allowed;">
                        <input type="file" id="resumeFileSim" accept=".pdf" 
                            onchange="autoUploadResume(event)" style="display:none;" disabled>
                        <p>Enter job role first to upload resume</p>
                        <small>Max 5MB • PDF only</small>
                    </div>
                    <p style="font-size: 12px; color: #6a6d8c; margin-top: 12px;">
                        ℹ️ <a href="https://www.jobscan.co/blog/ats-resume/" target="_blank" style="color: #00f2fe; text-decoration: none;">What is an ATS-friendly resume?</a>
                    </p>
                </div>

                <!-- OPTIONS -->
                <div class="sim-form-group">
                    <label>🔢 Number of Questions</label>
                    <input type="number" id="numQuestionsSim" min="1" max="20" value="5" required>
                </div>
                
                <div class="sim-row-flex">
                    <div class="sim-form-group">
                        <label>⚡ Difficulty</label>
                        <select id="resumeDiffSim" required>
                            <option value="beginner">Beginner</option>
                            <option value="intermediate" selected>Intermediate</option>
                            <option value="advanced">Advanced</option>
                        </select>
                    </div>
                    <div class="sim-form-group">
                        <label>🎤 Interview Type</label>
                        <select id="resumeTypeSim" required>
                            <option value="technical">Technical</option>
                            <option value="behavioral">Behavioral</option>
                            <option value="mixed" selected>Mixed</option>
                        </select>
                    </div>
                </div>
                
                <button type="submit" class="sim-launch-btn">🚀 LAUNCH INTERVIEW</button>
            </form>
        `;
    } else {
        splitState.formViewContainer.innerHTML = `
            <h3>⚡ Manual Configuration</h3>
            <p>Customize every parameter for targeted practice</p>
            
            <form id="manualFormSim" onsubmit="handleManualSubmit(event)">
                <div class="sim-form-group">
                    <label>💼 Job Role</label>
                    <input type="text" id="manualJobSim" placeholder="Software Engineer" required>
                </div>
                
                <div class="sim-form-group">
                    <label>📚 Education Lvl</label>
                    <select id="manualEducationlvlSim" required>
                    <option value="None">None's</option>
                    <option value="Sec or HSec">Secondary or High Secondary</option>
                    <option value="Diploma">Diploma</option>
                    <option value="Undergraduate's">Bachelor's</option>
                    <option value="PostGraduate's">Master's</option>
                    <option value="Doctrate">Doctrate</option>
                    </select>
                </div>

                <div class="sim-form-group">
                    <label>🎓 Degree</label>
                    <input type="text" id="manualDegreeSim" placeholder="B.Tech Computer Science" required>
                </div>

                <div class="sim-form-group">
                    <label>🏢 Company Type</label>
                    <input type="text" id="manualCompanySim" placeholder="Tech Company" required>
                </div>
                
                <div class="sim-form-group">
                    <label>🔢 Number of Questions</label>
                    <input type="number" id="manualNumQSim" min="1" max="20" value="5" required>
                </div>
                
                <div class="sim-row-flex">
                    <div class="sim-form-group">
                        <label>⚡ Difficulty</label>
                        <select id="manualDiffSim" required>
                            <option value="beginner">Beginner</option>
                            <option value="intermediate" selected>Intermediate</option>
                            <option value="advanced">Advanced</option>
                        </select>
                    </div>
                    <div class="sim-form-group">
                        <label>🎤 Interview Type</label>
                        <select id="manualTypeSim" required>
                            <option value="technical">Technical</option>
                            <option value="behavioral">Behavioral</option>
                            <option value="mixed" selected>Mixed</option>
                        </select>
                    </div>
                </div>
                
                <button type="submit" class="sim-launch-btn">🚀 LAUNCH INTERVIEW</button>
            </form>
        `;
    }
    
    splitState.formViewOverlay.classList.add('active');
}
function enableResumeUpload() {
    const jobRole = document.getElementById('resumeJobSim').value.trim();
    const uploadZone = document.getElementById('resumeUploadZone');
    const fileInput = document.getElementById('resumeFileSim');
    
    if (jobRole.length > 0) {
        uploadZone.style.opacity = '1';
        uploadZone.style.cursor = 'pointer';
        fileInput.disabled = false;
        uploadZone.querySelector('p').textContent = 'Click to upload or drag file here';
    } else {
        uploadZone.style.opacity = '0.5';
        uploadZone.style.cursor = 'not-allowed';
        fileInput.disabled = true;
        uploadZone.querySelector('p').textContent = 'Enter job role first to upload resume';
    }
}
//========== INTERVIEW HISTORY ==========
async function loadInterviewHistory() {
    const username = getCurrentUser();
    const section = document.getElementById('historySection');
    
    if (!username) {
        section.innerHTML = '<p>Please log in to view history</p>';
        return;
    }
    
    try {
        const response = await fetch(`http://localhost:8000/api/interviews/recent?username=${username}&limit=5`);
        
        if (response.ok) {
            const data = await response.json();
            if (data.interviews && data.interviews.length > 0) {
                section.innerHTML = data.interviews.map(buildHistoryCard).join('');
            } else {
                section.innerHTML = `
                    <div style="text-align:center; padding:40px; color:rgba(255,251,150,0.3);">
                        <div style="font-size:48px; margin-bottom:16px;">🎯</div>
                        <p>No interviews yet</p>
                    </div>`;
            }
        }
    } catch (error) {
        console.error('Error loading history:', error);
        section.innerHTML = '<p>Unable to load history</p>';
    }
}

function buildHistoryCard(interview) {
    const GRADE_COLOURS = {
        S: 'linear-gradient(135deg,#fbe238,#f49829)',
        A: 'linear-gradient(135deg,#05FFA1,#01CDFE)',
        B: 'linear-gradient(135deg,#01CDFE,#B967FF)',
        C: 'linear-gradient(135deg,#FFFB96,#f49829)',
        D: 'linear-gradient(135deg,#f49829,#FF71CE)',
        F: 'linear-gradient(135deg,#FF71CE,#764ba2)',
    };
    
    const GRADE_SHADOWS = {
        S: 'rgba(251,226,56,0.5)',
        A: 'rgba(5,255,161,0.5)',
        B: 'rgba(1,205,254,0.5)',
        C: 'rgba(255,251,150,0.4)',
        D: 'rgba(244,152,41,0.5)',
        F: 'rgba(255,113,206,0.5)',
    };
    const grade = interview.grade || 'B';
    const score = interview.overall_score || 0;
    const role = interview.job_role || 'Interview';
    
    const date = interview.timestamp
        ? new Date(interview.timestamp).toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric' 
          })
        : 'Unknown date';
    
    return `
    <div class="history-card">
        <div class="history-grade" style="
            background: ${GRADE_COLOURS[grade] || GRADE_COLOURS['B']};
            box-shadow: 0 4px 20px ${GRADE_SHADOWS[grade] || 'rgba(1,205,254,0.4)'};
        ">${grade}</div>

        <div class="history-info">
            <div class="history-role">${role}</div>
            <div class="history-date">
                <span>📅 ${date}</span>
            </div>
        </div>

        <div class="history-score">
            <div class="score-value">${score}</div>
            <div class="score-label">/ 100</div>
        </div>
    </div>`;
}

function getInterviewHistory() {
    try {
        const raw = localStorage.getItem('aira_interview_history');
        if (raw) return JSON.parse(raw);
    } catch(e) {}

    try {
        const raw = sessionStorage.getItem('interviewResults');
        const prefs = sessionStorage.getItem('interviewPreferences');
        if (raw && prefs) {
            const results  = JSON.parse(raw);
            const p        = JSON.parse(prefs);
            const overall  = calcOverall(results);
            const grade    = scoreToGrade(overall);
            return [{
                jobRole:       p.jobRole,
                difficulty:    p.difficulty,
                interviewType: p.interviewType,
                numQuestions:  p.numQuestions,
                overall,
                grade,
                timestamp:     p.timestamp || new Date().toISOString()
            }];
        }
    } catch(e) {}

    return [];
}

function calcOverall(results) {
    if (!results || !results.length) return 0;
    let tC=0,tA=0,tE=0,tB=0, cC=0,aC=0,eC=0,bC=0;
    results.forEach(r => {
        if (!r.success) return;
        if (r.content_relevancy) { tC += r.content_relevancy.score; cC++; }
        else if (r.transcript) {
            const wc = r.transcript.word_count||0, dur = r.transcript.duration_seconds||1;
            let s=70; if(wc>=50&&wc<=250) s+=15; if(dur>=30&&dur<=120) s+=15;
            tC+=s; cC++;
        }
        if (r.audio_quality)  { tA += r.audio_quality.overall_score;  aC++; }
        tE += 70; eC++;
        if (r.body_language)  { tB += r.body_language.score;          bC++; }
    });
    const c=cC>0?tC/cC:70, a=aC>0?tA/aC:75, e=eC>0?tE/eC:70, b=bC>0?tB/bC:75;
    return Math.round(c*0.30 + a*0.25 + e*0.25 + b*0.20);
}

function scoreToGrade(s) {
    if(s>=90) return 'S'; if(s>=80) return 'A';
    if(s>=70) return 'B'; if(s>=60) return 'C';
    if(s>=50) return 'D'; return 'F';
}

function saveInterviewToHistory(entry) {
    try {
        const raw     = localStorage.getItem('aira_interview_history');
        const history = raw ? JSON.parse(raw) : [];
        history.push(entry);
        if (history.length > 20) history.splice(0, history.length - 20);
        localStorage.setItem('aira_interview_history', JSON.stringify(history));
    } catch(e) {
        console.warn('Could not save history:', e);
    }
}

const GRADE_COLOURS = {
    S: 'linear-gradient(135deg,#fbe238,#f49829)',
    A: 'linear-gradient(135deg,#05FFA1,#01CDFE)',
    B: 'linear-gradient(135deg,#01CDFE,#B967FF)',
    C: 'linear-gradient(135deg,#FFFB96,#f49829)',
    D: 'linear-gradient(135deg,#f49829,#FF71CE)',
    F: 'linear-gradient(135deg,#FF71CE,#764ba2)',
};

const GRADE_SHADOWS = {
    S: 'rgba(251,226,56,0.5)',
    A: 'rgba(5,255,161,0.5)',
    B: 'rgba(1,205,254,0.5)',
    C: 'rgba(255,251,150,0.4)',
    D: 'rgba(244,152,41,0.5)',
    F: 'rgba(255,113,206,0.5)',
};

// ========== MODAL ==========
function openModal() {
    document.getElementById('aboutModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('aboutModal').style.display = 'none';
}

window.onclick = function (event) {
    const modal = document.getElementById('aboutModal');
    if (event.target === modal) closeModal();
};
window.showSplitScreen = showSplitScreen;
window.handleResumeSubmit = handleResumeSubmit;
window.handleManualSubmit = handleManualSubmit;

async function autoUploadResume(event) {
    const file = event.target.files[0];
    
    const jobRole = document.getElementById('resumeJobSim').value.trim();
    if (!jobRole) {
        console.error('❌ Job role is empty!');
        showMessage('⚠️ Please enter a job role first!', 'error');
        return;
    }
    console.log('✅ Job role confirmed:', jobRole);
    
    if (!file) {
        console.error('❌ No file selected');
        showMessage('⚠️ Please select a resume file', 'error');
        return;
    }
    
    // Validation
    if (!file.name.endsWith('.pdf')) {
        showMessage('⚠️ Only PDF files accepted', 'error');
        return;
    }
    
    if (file.size > 5 * 1024 * 1024) {
        showMessage('⚠️ File too large (max 5MB)', 'error');
        return;
    }

    console.log('📤 Starting upload with job role:', jobRole);
    showMessage('⏳ Parsing resume...', 'success');    
    // Show overlay and uploading state
    showResumeOverlay('uploading');
    document.getElementById('uploadProgress').textContent = `Uploading ${file.name}...`;
    
    try {
        // Upload to backend
        const formData = new FormData();
        formData.append('resume', file);
        formData.append('jobRole', document.getElementById('resumeJobSim').value);
        formData.append('difficulty', document.getElementById('resumeDiffSim').value);
        formData.append('interviewType', document.getElementById('resumeTypeSim').value);
        
        // Show parsing state
        setTimeout(() => {
            showResumeOverlay('parsing');
        }, 800);
        
        const numQuestions = document.getElementById('numQuestionsSim').value || 5;  // ← GET THIS FIRST
        const response = await fetch(`http://localhost:8000/api/resume/parse?num_questions=${numQuestions}`, {
            method: 'POST',
            body: formData
        });
        console.log('📥 Response status:', response.status);
        const data = await response.json();
        console.log('📥 Response data:', data);
        
        // SUCCESS
        if (response.ok && data.success) {
            console.log('✅ Resume parsed successfully with job role:', jobRole);
            
            const prefs = {
                path: 'resume',
                jobRole: document.getElementById('resumeJobSim').value || data.extracted.name || 'Professional',
                numQuestions: document.getElementById('numQuestionsSim').value || 5,
                difficulty: document.getElementById('resumeDiffSim').value,
                interviewType: document.getElementById('resumeTypeSim').value,
                questions: data.questions,
                extractedData: data.extracted,
                timestamp: new Date().toISOString()
            };
            
            sessionStorage.setItem('interviewPreferences', JSON.stringify(prefs));
            console.log('✅ Data saved to sessionStorage:', prefs);
            showMessage('✅ Resume parsed! Job role confirmed: ' + jobRole, 'success');
            
            // Show success
            document.getElementById('detectedRole').textContent = `${data.extracted.name || 'Candidate'}`;
            document.getElementById('atsScore').textContent = data.ats_score || '--';
            document.getElementById('extractedSkills').textContent = 
                (data.extracted.skills || []).slice(0, 5).join(', ') || 'Multiple skills detected';
            const extractedDiv = document.querySelector('.success-details');
            extractedDiv.innerHTML = `
            <p><strong>✓ ATS Score:</strong> <span style="color: #00ffaa; font-size: 18px;">${data.ats_score || 0}/100</span></p>
            <p><strong>✓ Candidate Name:</strong> ${data.extracted.name || 'Professional'}</p>
            <p><strong>✓ Top Skills:</strong> ${(data.extracted.skills || []).slice(0, 8).join(', ') || 'Multiple skills'}</p>
            <p><strong>✓ Experience Entries:</strong> ${(data.extracted.experience || []).length || 0}</p>
            <p><strong>✓ Education Entries:</strong> ${(data.extracted.education || []).length || 0}</p>
            <p><strong>✓ Projects Found:</strong> ${(data.extracted.projects || []).length || 0}</p>
        `;
            setTimeout(() => {
                showResumeOverlay('success');
            }, 1500);
            
        } 
        // ERROR - ATS NOT FRIENDLY or PARSING FAILED
        else {
            const issues = data.ats_issues || [];
            const parseError = data.parse_error || null;
            
            // Set error message
            let errorMsg = data.message || 'Your resume needs formatting improvements';
            if (parseError) {
                errorMsg = `Parsing Error: ${parseError}`;
            }
            document.getElementById('errorMessage').textContent = errorMsg;
            
            // Populate issues list
            const issuesList = document.getElementById('issuesList');
            issuesList.innerHTML = '';
            
            if (issues.length === 0 && parseError) {
                // Show parsing error
                const li = document.createElement('li');
                li.textContent = `❌ ${parseError}`;
                issuesList.appendChild(li);
            } else if (issues.length === 0) {
                // Generic issue if no specific issues
                const li = document.createElement('li');
                li.textContent = 'Resume formatting needs improvement';
                issuesList.appendChild(li);
            } else {
                // Show all issues
                issues.forEach(issue => {
                    const li = document.createElement('li');
                    li.textContent = issue;
                    issuesList.appendChild(li);
                });
            }
            
            setTimeout(() => {
                showResumeOverlay('error');
            }, 1500);
        }
        
    } catch (error) {
        console.error('Resume upload error:', error);
        
        // Set error message
        const errorMsg = error.message || 'Unknown error occurred';
        document.getElementById('errorMessage').textContent = 
            'Upload Failed: ' + errorMsg;
        
        // Show error details in issues list
        const issuesList = document.getElementById('issuesList');
        issuesList.innerHTML = '';
        
        const li = document.createElement('li');
        li.textContent = `❌ ${errorMsg}`;
        issuesList.appendChild(li);
        
        setTimeout(() => {
            showResumeOverlay('error');
        }, 500);
    }
}

// Show/hide overlay with state
function showResumeOverlay(state) {
    const overlay = document.getElementById('resumeUploadOverlay');
    overlay.classList.add('active');
    
    document.getElementById('uploadingState').style.display = 'none';
    document.getElementById('parsingState').style.display = 'none';
    document.getElementById('successState').style.display = 'none';
    document.getElementById('errorState').style.display = 'none';
    
    if (state === 'uploading') {
        document.getElementById('uploadingState').style.display = 'block';
    } else if (state === 'parsing') {
        document.getElementById('parsingState').style.display = 'block';
    } else if (state === 'success') {
        document.getElementById('successState').style.display = 'block';
    } else if (state === 'error') {
        document.getElementById('errorState').style.display = 'block';
    }
}

function closeResumeOverlay() {
    document.getElementById('resumeUploadOverlay').classList.remove('active');
}

function switchToManual() {
    closeResumeOverlay();
    // Switch to manual path
    document.querySelectorAll('.mode-btn')[1].click();
}


// ========== MESSAGE HELPER ==========
function showMessage(text, type) {
    const el = document.getElementById('message');
    el.textContent   = text;
    el.className     = 'message ' + type;
    el.style.display = 'block';
    setTimeout(() => { el.style.display = 'none'; }, 5000);
}
