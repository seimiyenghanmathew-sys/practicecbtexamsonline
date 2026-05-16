// ── State ──────────────────────────────────────────────────────────────────
let currentIdx = 0;
let answers = {};
let tabSwitches = 0;
let timerInterval = null;
let timeLeft = 180 * 60; // 180 minutes in seconds
let isSubmitting = false;

// ── Init ───────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadAnswers();
  restoreTimer();
  buildPalette();
  renderQuestion(currentIdx);
  startTimer();
  setupAntiCheat();
  updateTabCounts();
});

// ── Load / Save Answers ────────────────────────────────────────────────────
function loadAnswers() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) answers = JSON.parse(saved);
  } catch(e) { answers = {}; }
}

function saveAnswers() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(answers)); } catch(e) {}
}

// ── Timer ──────────────────────────────────────────────────────────────────
function restoreTimer() {
  const saved = localStorage.getItem(TIMER_KEY);
  if (saved) {
    const remaining = parseInt(saved);
    if (remaining > 0 && remaining <= 180 * 60) timeLeft = remaining;
  }
}

function startTimer() {
  const timerEl = document.getElementById('timer');
  timerInterval = setInterval(() => {
    timeLeft--;
    localStorage.setItem(TIMER_KEY, timeLeft);

    const h = Math.floor(timeLeft / 3600);
    const m = Math.floor((timeLeft % 3600) / 60);
    const s = timeLeft % 60;
    timerEl.textContent = `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;

    timerEl.className = 'timer';
    if (timeLeft <= 300) timerEl.classList.add('danger');
    else if (timeLeft <= 900) timerEl.classList.add('warn');

    if (timeLeft <= 0) {
      clearInterval(timerInterval);
      document.getElementById('autoModalTitle').textContent = "⏰ Time's Up!";
      document.getElementById('autoModalMsg').textContent = "Your 180 minutes are over. Exam will be submitted automatically.";
      document.getElementById('autoModal').classList.add('active');
      setTimeout(finalSubmit, 3000);
    }
  }, 1000);
}

// ── Render Question ────────────────────────────────────────────────────────
function renderQuestion(idx) {
  if (idx < 0 || idx >= QUESTIONS.length) return;
  const q = QUESTIONS[idx];
  const qNum = idx + 1;

  document.getElementById('questionNum').textContent = `Question ${qNum} of ${QUESTIONS.length} — ${q.subject}`;
  document.getElementById('currentQNum').textContent = qNum;
  document.getElementById('questionText').textContent = q.question;

  const optsList = document.getElementById('optionsList');
  optsList.innerHTML = '';
  const opts = ['A', 'B', 'C', 'D'];
  opts.forEach(letter => {
    const div = document.createElement('div');
    div.className = 'option-item' + (answers[q.id] === letter ? ' selected' : '');
    div.onclick = () => selectAnswer(idx, letter);
    div.innerHTML = `<div class="option-letter">${letter}</div><div>${q[letter] || ''}</div>`;
    optsList.appendChild(div);
  });

  // Update nav buttons
  document.getElementById('prevBtn').disabled = idx === 0;
  document.getElementById('nextBtn').disabled = idx === QUESTIONS.length - 1;

  // Update palette highlight
  updatePalette();

  // Update subject tab
  SUBS.forEach(sub => {
    const tab = document.querySelector(`.sub-tab[data-subject="${sub}"]`);
    if (tab) tab.classList.toggle('active', sub === q.subject);
  });
}

// ── Answer Selection ───────────────────────────────────────────────────────
function selectAnswer(idx, letter) {
  const q = QUESTIONS[idx];
  answers[q.id] = letter;
  saveAnswers();
  renderQuestion(idx);
  updateTabCounts();
  updateProgressBar();
}

// ── Navigation ─────────────────────────────────────────────────────────────
function navigate(dir) {
  const newIdx = currentIdx + dir;
  if (newIdx >= 0 && newIdx < QUESTIONS.length) {
    currentIdx = newIdx;
    renderQuestion(currentIdx);
  }
}

function jumpTo(idx) {
  currentIdx = idx;
  renderQuestion(currentIdx);
}

function switchSubject(subject) {
  const idx = QUESTIONS.findIndex(q => q.subject === subject);
  if (idx !== -1) jumpTo(idx);
}

// ── Palette ────────────────────────────────────────────────────────────────
function buildPalette() {
  const grid = document.getElementById('palette');
  grid.innerHTML = '';
  QUESTIONS.forEach((q, i) => {
    const btn = document.createElement('button');
    btn.className = 'pal-item';
    btn.textContent = i + 1;
    btn.id = `pal-${i}`;
    btn.onclick = () => jumpTo(i);
    grid.appendChild(btn);
  });
}

function updatePalette() {
  QUESTIONS.forEach((q, i) => {
    const btn = document.getElementById(`pal-${i}`);
    if (!btn) return;
    btn.className = 'pal-item';
    if (i === currentIdx) btn.classList.add('current');
    else if (answers[q.id]) btn.classList.add('answered');
  });
}

function updateTabCounts() {
  SUBS.forEach(sub => {
    const subQs = QUESTIONS.filter(q => q.subject === sub);
    const answered = subQs.filter(q => answers[q.id]).length;
    const el = document.getElementById(`tab-count-${sub}`);
    if (el) el.textContent = `(${answered}/${subQs.length})`;
  });

  const totalAnswered = Object.keys(answers).length;
  document.getElementById('answeredCount').textContent = totalAnswered;
  document.getElementById('unansweredCount').textContent = QUESTIONS.length - totalAnswered;
  updateProgressBar();
}

function updateProgressBar() {
  const pct = (Object.keys(answers).length / QUESTIONS.length) * 100;
  document.getElementById('progressBar').style.width = pct + '%';
}

// ── Submit Modals ──────────────────────────────────────────────────────────
function showSubmitModal() {
  const answered = Object.keys(answers).length;
  const unanswered = QUESTIONS.length - answered;
  document.getElementById('submitMsg').innerHTML =
    `You have answered <strong style="color:var(--green)">${answered}</strong> questions and 
     left <strong style="color:var(--red)">${unanswered}</strong> unanswered.<br><br>
     Are you sure you want to submit?`;
  document.getElementById('submitModal').classList.add('active');
}

function closeSubmitModal() {
  document.getElementById('submitModal').classList.remove('active');
}

function closeTabModal() {
  document.getElementById('tabModal').classList.remove('active');
}

// ── Final Submit ───────────────────────────────────────────────────────────
async function finalSubmit() {
  if (isSubmitting) return;
  isSubmitting = true;
  clearInterval(timerInterval);

  // Close modals
  document.getElementById('submitModal').classList.remove('active');
  document.getElementById('autoModal').classList.remove('active');

  // Show loading
  document.getElementById('autoModalTitle').textContent = '⏳ Submitting...';
  document.getElementById('autoModalMsg').textContent = 'Please wait while your exam is being submitted.';
  document.getElementById('autoModalBtn').style.display = 'none';
  document.getElementById('autoModal').classList.add('active');

  try {
    const response = await fetch('/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers })
    });
    const data = await response.json();

    // Clear localStorage
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(TIMER_KEY);

    // Redirect to result
    window.location.href = '/result';
  } catch(err) {
    document.getElementById('autoModalTitle').textContent = '❌ Submission Error';
    document.getElementById('autoModalMsg').textContent = 'Network error. Please try again.';
    document.getElementById('autoModalBtn').textContent = 'Retry';
    document.getElementById('autoModalBtn').style.display = 'inline-flex';
    document.getElementById('autoModalBtn').onclick = finalSubmit;
    isSubmitting = false;
  }
}

// ── Keyboard Shortcuts ─────────────────────────────────────────────────────
document.addEventListener('keydown', (e) => {
  // Prevent shortcuts when typing in input
  if (['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)) return;

  const key = e.key.toUpperCase();
  const submitModalActive = document.getElementById('submitModal').classList.contains('active');

  if (submitModalActive) {
    if (key === 'Y') finalSubmit();
    if (key === 'ESCAPE' || key === 'N') closeSubmitModal();
    return;
  }

  switch(key) {
    case 'A': selectAnswer(currentIdx, 'A'); break;
    case 'B': selectAnswer(currentIdx, 'B'); break;
    case 'C': selectAnswer(currentIdx, 'C'); break;
    case 'D': selectAnswer(currentIdx, 'D'); break;
    case 'N': navigate(1); break;
    case 'P': navigate(-1); break;
    case 'S': showSubmitModal(); break;
  }
});

// ── Anti-Cheating ──────────────────────────────────────────────────────────
function setupAntiCheat() {
  document.addEventListener('visibilitychange', () => {
    if (document.hidden && !isSubmitting) {
      tabSwitches++;
      if (tabSwitches >= 3) {
        document.getElementById('autoModalTitle').textContent = '🚨 Exam Terminated!';
        document.getElementById('autoModalMsg').textContent = 'You have switched tabs 3 times. Your exam is being auto-submitted.';
        document.getElementById('autoModalBtn').textContent = 'Submit Now';
        document.getElementById('autoModal').classList.add('active');
        setTimeout(finalSubmit, 3000);
      } else {
        document.getElementById('switchCount').textContent = tabSwitches;
        document.getElementById('tabModal').classList.add('active');
      }
    }
  });

  // Disable right click
  document.addEventListener('contextmenu', e => e.preventDefault());
  
  // Disable copy/paste
  document.addEventListener('copy', e => e.preventDefault());
  document.addEventListener('cut',  e => e.preventDefault());
}
