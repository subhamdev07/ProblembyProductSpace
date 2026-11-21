    let currentStudentId = 'STU-001';
    let currentRole = 'student'; // 'student' or 'teacher'
    let currentAssessment = null;
    let currentQuestionIndex = 0;
    let selectedAnswers = {};
    let allMasteryItems = [];
    let currentAdaptiveRec = null;
    let currentRemediation = null;

    function initAuthSession() {
      const stored = localStorage.getItem('bodhai_user');
      if (stored) {
        try {
          const user = JSON.parse(stored);
          if (user.role === 'teacher') {
            window.location.replace('/teacher');
            return;
          }
          if (user.user_id) currentStudentId = user.user_id;
          currentRole = 'student';
          const nameEl = document.getElementById('sidebar-user-name');
          if (nameEl) nameEl.innerText = user.name || 'Aarav Sharma';
          const roleEl = document.getElementById('sidebar-user-role');
          if (roleEl) roleEl.innerText = `Student (Grade ${user.grade || 10})`;
          const avatarEl = document.getElementById('role-avatar');
          if (avatarEl) avatarEl.innerText = user.avatar || 'AS';
        } catch (e) {
          console.warn('Session parse error:', e);
        }
      }
    }

    async function trackStudentActivity(eventType, actionTitle, details = {}, durationSeconds = 0) {
      try {
        await fetch('/api/student/activity', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            student_id: currentStudentId,
            event_type: eventType,
            action_title: actionTitle,
            details: details,
            duration_seconds: durationSeconds
          })
        });
      } catch (e) {
        console.warn('Telemetry tracking warning:', e);
      }
    }

    function switchView(viewName) {
      if (viewName === 'teacher' && currentRole !== 'teacher') {
        showToast('Access restricted: Educator Portal is accessible to verified teachers only.');
        switchView('dashboard');
        return;
      }

      document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.nav-btn').forEach(b => {
        b.classList.remove('bg-deepPurple', 'text-cream', 'shadow-sm');
        b.classList.add('text-muted');
      });

      const targetView = document.getElementById(`view-${viewName}`);
      const targetNav = document.getElementById(`nav-${viewName}`);

      if (targetView) targetView.classList.add('active');
      if (targetNav) {
        targetNav.classList.remove('text-muted');
        targetNav.classList.add('bg-deepPurple', 'text-cream', 'shadow-sm');
      }

      window.scrollTo({ top: 0, behavior: 'smooth' });

      const pathMap = {
        'dashboard': '/dashboard',
        'assessment': '/diagnostic',
        'examination-hub': '/exam',
        'mastery': '/mastery',
        'adaptive': '/practice',
        'remediation': '/remediation',
        'revision': '/revision',
        'misconceptions': '/misconceptions',
        'doubt-solver': '/doubt-solver',
        'concept-graph': '/concept-graph',
        'teacher': '/teacher'
      };
      const newPath = pathMap[viewName] || '/' + viewName;
      if (window.location.pathname !== newPath && !(window.location.pathname === '/' && viewName === 'dashboard')) {
        try { history.pushState({ view: viewName }, '', newPath); } catch (e) {}
      }

      trackStudentActivity('VIEW_NAVIGATION', 'Viewed ' + viewName.replace(/-/g, ' ').toUpperCase(), { view: viewName }, 5);

      const bc = document.getElementById('breadcrumb-current-view');
      if (bc) {
        const viewTitles = {
          'dashboard': 'Dashboard',
          'assessment': 'Diagnostic Test',
          'examination-hub': 'Board Exam Simulation',
          'examination-workspace': 'Live Exam Session',
          'mastery': 'Concept Mastery',
          'concept-graph': 'Concept Graph DAG',
          'adaptive': 'Adaptive Practice',
          'remediation': 'Targeted Learning',
          'revision': 'Revision Center',
          'misconceptions': 'Misconceptions Review',
          'doubt-solver': 'AI Doubt Solver',
          'teacher': 'Teacher Dashboard'
        };
        bc.innerText = viewTitles[viewName] || viewName;
      }

      if (viewName === 'dashboard') loadDashboard();
      if (viewName === 'mastery') loadMasteryView();
      if (viewName === 'concept-graph') loadConceptGraphView();
      if (viewName === 'examination-hub') loadExaminationHub();
    }

    function toggleSidebar() {
      const sb = document.getElementById('app-sidebar');
      const openTab = document.getElementById('sidebar-open-tab');
      if (!sb) return;
      const isClosed = sb.classList.contains('sidebar-closed');
      if (isClosed) {
        sb.classList.remove('sidebar-closed');
        if (openTab) openTab.classList.add('hidden');
        localStorage.setItem('bodhai_sidebar_state', 'open');
      } else {
        sb.classList.add('sidebar-closed');
        if (openTab) openTab.classList.remove('hidden');
        localStorage.setItem('bodhai_sidebar_state', 'closed');
      }
    }

    (function initSidebarState() {
      const savedState = localStorage.getItem('bodhai_sidebar_state');
      if (savedState === 'closed') {
        window.addEventListener('DOMContentLoaded', () => {
          document.getElementById('app-sidebar')?.classList.add('sidebar-closed');
          document.getElementById('sidebar-open-tab')?.classList.remove('hidden');
        });
      }
    })();

    function showToast(message, isSuccess = true) {
      const toast = document.getElementById('toast');
      const icon = document.getElementById('toast-icon');
      const msg = document.getElementById('toast-msg');

      icon.innerText = isSuccess ? '✓' : '⚠️';
      msg.innerText = message;
      toast.classList.remove('hidden');

      setTimeout(() => {
        toast.classList.add('hidden');
      }, 3500);
    }

    let currentExamSession = null;
    let currentExamQIndex = 0;
    let examTimerInterval = null;
    let examRemainingSeconds = 0;
    let currentExamResult = null;

    async function loadExaminationHub() {
      switchView('examination-hub');
      try {
        const bpRes = await fetch('/api/examinations/blueprints');
        if (bpRes.ok) {
          const blueprints = await bpRes.json();
          const grid = document.getElementById('available-blueprints-grid');
          grid.innerHTML = '';
          blueprints.forEach(bp => {
            const card = document.createElement('div');
            card.className = 'p-6 rounded-3xl bg-white border-2 border-sandDark hover:border-deepPurple transition-all space-y-4 shadow-sm';
            card.innerHTML = `
              <div class="flex items-center justify-between">
                <span class="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase ${bp.is_official ? 'bg-amber-100 text-amber-900' : 'bg-purple-100 text-purple-900'}">
                  ${bp.is_official ? '★ Official CBSE Pattern' : 'Diagnostic Unit Mock'}
                </span>
                <span class="text-xs font-mono text-muted">${bp.blueprint_id}</span>
              </div>
              <h4 class="text-lg font-bold text-deepPurple leading-snug">${bp.title}</h4>
              <div class="flex items-center gap-4 text-xs text-muted font-medium">
                <span>⏱️ ${bp.duration_minutes} Mins (${Math.round(bp.duration_minutes/60)} Hours)</span>
                <span>📝 ${bp.question_count} Questions</span>
                <span>🎯 ${bp.total_marks} Marks</span>
              </div>
              <p class="text-xs text-muted leading-relaxed">
                Full syllabus simulation encompassing Sections A to E with multi-typology questions and server-authoritative timer.
              </p>
              <div class="pt-2">
                <button onclick="startBoardExam('${bp.blueprint_id}')" class="w-full py-3 rounded-xl bg-brandYellow hover:bg-brandYellowDark text-deepPurple font-extrabold text-sm shadow transition-all flex items-center justify-center gap-2">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                  Begin Examination
                </button>
              </div>
            `;
            grid.appendChild(card);
          });
        }

        const actRes = await fetch(`/api/examinations/active?student_id=${currentStudentId}`);
        const activeBanner = document.getElementById('exam-active-banner');
        if (actRes.ok) {
          const activeSess = await actRes.json();
          if (activeSess && activeSess.status === 'IN_PROGRESS') {
            currentExamSession = activeSess;
            document.getElementById('active-banner-title').innerText = activeSess.paper_title;
            const mins = Math.floor(activeSess.remaining_time_seconds / 60);
            const secs = activeSess.remaining_time_seconds % 60;
            const hrs = Math.floor(mins / 60);
            document.getElementById('active-banner-timer').innerText = 
              `${String(hrs).padStart(2,'0')}:${String(mins%60).padStart(2,'0')}:${String(secs).padStart(2,'0')}`;
            activeBanner.classList.remove('hidden');
          } else {
            activeBanner.classList.add('hidden');
          }
        }

        const pastRes = await fetch(`/api/student/examinations?student_id=${currentStudentId}`);
        if (pastRes.ok) {
          const pastExams = await pastRes.json();
          const tableBody = document.getElementById('past-exams-table-body');
          tableBody.innerHTML = '';
          if (pastExams.length > 0) {
            pastExams.forEach(pe => {
              const tr = document.createElement('tr');
              tr.className = 'hover:bg-sandLight transition-colors font-medium';
              const isDone = (pe.status === 'SUBMITTED' || pe.status === 'EVALUATED' || pe.status === 'TIMED_OUT');
              tr.innerHTML = `
                <td class="py-3 px-3 font-bold text-deepPurple">${pe.paper_title}</td>
                <td class="py-3 px-3 font-mono text-muted text-[11px]">${pe.session_id || '—'}</td>
                <td class="py-3 px-3 text-muted">${pe.completed_at ? new Date(pe.completed_at).toLocaleDateString() : '—'}</td>
                <td class="py-3 px-3 text-center font-bold text-deepPurple">${pe.score !== null ? pe.score + ' / ' + pe.total_marks : '—'}</td>
                <td class="py-3 px-3 text-center font-bold ${pe.percentage >= 70 ? 'text-green-700' : 'text-amber-700'}">${pe.percentage !== null ? pe.percentage + '%' : '—'}</td>
                <td class="py-3 px-3 text-center">
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${isDone ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'}">
                    ${pe.status}
                  </span>
                </td>
                <td class="py-3 px-3 text-right">
                  ${isDone ? `<button onclick="loadExamResultFromHistory('${pe.session_id}')" class="font-bold text-deepPurple hover:underline">View Report &rarr;</button>` : `<button onclick="resumeActiveExamination()" class="font-bold text-brandYellowDark hover:underline">Resume &rarr;</button>`}
                </td>
              `;
              tableBody.appendChild(tr);
            });
          } else {
            tableBody.innerHTML = '<tr><td colspan="7" class="py-6 text-center text-muted">No examination attempts yet. Start your first CBSE simulation above!</td></tr>';
          }
        }

      } catch (err) {
        showToast(err.message, false);
      }
    }

    async function startBoardExam(blueprintId) {
      if (!confirm('You are about to start a timed Board Examination Simulation (180 Minutes). The countdown will be authoritatively synchronized with the server. Ensure you have an uninterrupted workspace. Proceed?')) {
        return;
      }
      try {
        const res = await fetch('/api/examinations/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ student_id: currentStudentId, blueprint_id: blueprintId })
        });
        if (!res.ok) throw new Error('Failed to start examination');
        const sessionState = await res.json();
        renderExamWorkspace(sessionState);
        showToast('Examination session initialized! Best of luck.');
      } catch (err) {
        showToast(err.message, false);
      }
    }

    function resumeActiveExamination() {
      if (currentExamSession) {
        renderExamWorkspace(currentExamSession);
      } else {
        loadExaminationHub();
      }
    }

    function renderExamWorkspace(session) {
      currentExamSession = session;
      currentExamQIndex = 0;

      switchView('examination-workspace');
      document.getElementById('workspace-paper-title').innerText = session.paper_title;
      document.getElementById('workspace-paper-code').innerText = `${session.paper_code} • ${session.total_marks} Marks (${session.duration_minutes}m)`;

      startAuthoritativeTimer(session.remaining_time_seconds);

      buildPaletteGrid();

      renderExamQuestion(0);
    }

    function startAuthoritativeTimer(initialSeconds) {
      if (examTimerInterval) clearInterval(examTimerInterval);
      examRemainingSeconds = initialSeconds;

      function updateDisplay() {
        if (examRemainingSeconds <= 0) {
          clearInterval(examTimerInterval);
          document.getElementById('exam-timer-display').innerText = '00:00:00';
          submitBoardExam(true); // Auto-submit on timeout
          return;
        }

        const hrs = Math.floor(examRemainingSeconds / 3600);
        const mins = Math.floor((examRemainingSeconds % 3600) / 60);
        const secs = examRemainingSeconds % 60;
        const timeStr = `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

        const displayEl = document.getElementById('exam-timer-display');
        displayEl.innerText = timeStr;

        if (examRemainingSeconds < 900) { // Under 15 mins
          displayEl.classList.add('text-red-600');
        } else {
          displayEl.classList.remove('text-red-600');
        }

        examRemainingSeconds--;
      }

      updateDisplay();
      examTimerInterval = setInterval(updateDisplay, 1000);
    }

    function buildPaletteGrid() {
      const palette = document.getElementById('exam-palette-grid');
      palette.innerHTML = '';
      const questions = currentExamSession.questions || [];

      questions.forEach((q, idx) => {
        const btn = document.createElement('button');
        btn.id = `palette-btn-${idx}`;
        btn.className = 'palette-bubble w-full aspect-square rounded-xl text-xs font-bold transition-all border flex items-center justify-center';
        btn.onclick = () => jumpToExamQuestion(idx);
        btn.innerText = idx + 1;
        palette.appendChild(btn);
      });

      updatePaletteUI();
    }

    function updatePaletteUI() {
      if (!currentExamSession) return;
      const questions = currentExamSession.questions || [];
      const saved = currentExamSession.saved_answers || {};
      const marked = currentExamSession.marked_for_review || [];

      let answeredCount = 0;

      questions.forEach((q, idx) => {
        const btn = document.getElementById(`palette-btn-${idx}`);
        if (!btn) return;

        const isAnswered = Boolean(saved[q.question_id] && Object.keys(saved[q.question_id]).length > 0);
        const isMarked = marked.includes(q.question_id);
        const isActive = (idx === currentExamQIndex);

        if (isAnswered) answeredCount++;

        btn.className = 'palette-bubble w-full aspect-square rounded-xl text-xs font-bold transition-all flex items-center justify-center';

        if (isAnswered && isMarked) {
          btn.classList.add('bg-brandYellow', 'text-deepPurple', 'border-2', 'border-brandPurple');
        } else if (isMarked) {
          btn.classList.add('bg-brandPurple', 'text-cream');
        } else if (isAnswered) {
          btn.classList.add('bg-successGreen', 'text-white');
        } else {
          btn.classList.add('bg-sandDark', 'text-muted', 'hover:bg-sand');
        }

        if (isActive) {
          btn.classList.add('ring-4', 'ring-deepPurple');
        }
      });

      document.getElementById('palette-status-count').innerText = `${answeredCount} / ${questions.length} Answered`;
    }

    function renderExamQuestion(index) {
      if (!currentExamSession || !currentExamSession.questions.length) return;
      if (index < 0 || index >= currentExamSession.questions.length) return;

      currentExamQIndex = index;
      const q = currentExamSession.questions[index];

      document.getElementById('exam-q-num').innerText = index + 1;
      document.getElementById('exam-q-section').innerText = q.section_name;
      document.getElementById('exam-q-chapter').innerText = q.chapter_name || q.chapter_id;
      document.getElementById('exam-q-marks').innerText = `${q.marks} Mark${q.marks > 1 ? 's' : ''}`;
      document.getElementById('exam-q-type').innerText = q.question_type;

      document.querySelectorAll('.exam-sec-tab').forEach(t => {
        if (t.getAttribute('data-sec') === q.section_name) {
          t.className = 'exam-sec-tab px-4 py-2 rounded-xl font-bold text-xs bg-deepPurple text-cream transition-all whitespace-nowrap';
        } else {
          t.className = 'exam-sec-tab px-4 py-2 rounded-xl font-bold text-xs bg-sand text-muted hover:bg-sandDark transition-all whitespace-nowrap';
        }
      });

      const qTextEl = document.getElementById('exam-q-text');
      qTextEl.innerHTML = q.question_text;

      const passageBox = document.getElementById('exam-case-passage-box');
      if (q.question_type === 'CASE_BASED' && q.passage) {
        passageBox.classList.remove('hidden');
        document.getElementById('exam-case-passage-text').innerHTML = q.passage;
      } else {
        passageBox.classList.add('hidden');
      }

      const arBox = document.getElementById('exam-ar-box');
      if (q.question_type === 'ASSERTION_REASON') {
        if (!q.options || Object.keys(q.options).length === 0) {
          q.options = {
            "A": "Both Assertion (A) and Reason (R) are true and Reason (R) is the correct explanation of Assertion (A).",
            "B": "Both Assertion (A) and Reason (R) are true but Reason (R) is not the correct explanation of Assertion (A).",
            "C": "Assertion (A) is true but Reason (R) is false.",
            "D": "Assertion (A) is false but Reason (R) is true."
          };
        }
        if (q.assertion || q.reason) {
          arBox.classList.remove('hidden');
          document.getElementById('exam-ar-assertion').innerHTML = q.assertion || '';
          document.getElementById('exam-ar-reason').innerHTML = q.reason || '';
        } else {
          arBox.classList.add('hidden');
        }
      } else {
        arBox.classList.add('hidden');
      }

      const inputContainer = document.getElementById('exam-input-container');
      inputContainer.innerHTML = '';

      const savedAns = (currentExamSession.saved_answers || {})[q.question_id] || {};

      const opts = (q.options && Object.keys(q.options).length > 0) ? q.options : {
        "A": "Option A (Select to record your response)",
        "B": "Option B (Select to record your response)",
        "C": "Option C (Select to record your response)",
        "D": "Option D (Select to record your response)"
      };

      const selectedOpt = savedAns.selected_option || '';
      for (const [optKey, optText] of Object.entries(opts)) {
        const card = document.createElement('div');
        const isSelected = (selectedOpt === optKey);
        card.className = `option-card p-4 rounded-2xl border-2 cursor-pointer flex items-center gap-4 transition-all ${isSelected ? 'border-deepPurple bg-sandLight font-semibold shadow-sm' : 'border-sandDark bg-white hover:border-sand'}`;
        card.onclick = () => selectExamOption(optKey);
        card.innerHTML = `
          <div class="w-8 h-8 rounded-xl font-bold flex items-center justify-center text-sm ${isSelected ? 'bg-deepPurple text-brandYellow' : 'bg-sandDark text-muted'}">
            ${optKey}
          </div>
          <div class="text-sm text-deepPurple flex-1 leading-snug">
            ${optText}
          </div>
        `;
        inputContainer.appendChild(card);
      }

      document.getElementById('btn-exam-prev').disabled = (index === 0);

      if (window.renderMathInElement) {
        try {
          renderMathInElement(document.getElementById('view-examination-workspace'), {
            delimiters: [
              { left: '$$', right: '$$', display: true },
              { left: '$', right: '$', display: false },
              { left: '\\(', right: '\\)', display: false },
              { left: '\\[', right: '\\]', display: true },
            ],
            throwOnError: false,
          });
        } catch (e) {
          console.warn('KaTeX render warning:', e);
        }
      }

      updatePaletteUI();
    }

    function selectExamOption(optKey) {
      if (!currentExamSession) return;
      const q = currentExamSession.questions[currentExamQIndex];
      if (!currentExamSession.saved_answers) currentExamSession.saved_answers = {};
      currentExamSession.saved_answers[q.question_id] = { selected_option: optKey };
      renderExamQuestion(currentExamQIndex);
    }

    function updateWordCount(textarea) {
      const counter = document.getElementById('exam-word-counter');
      if (!counter) return;
      const text = textarea.value.trim();
      const words = text ? text.split(/\s+/).length : 0;
      counter.innerText = `${words} words`;
    }

    function switchExamSection(sectionName) {
      if (!currentExamSession) return;
      const questions = currentExamSession.questions || [];
      const idx = questions.findIndex(q => q.section_name === sectionName);
      if (idx !== -1) {
        jumpToExamQuestion(idx);
      }
    }

    function jumpToExamQuestion(targetIndex) {
      saveExamAnswer(false, false);
      renderExamQuestion(targetIndex);
    }

    function navigateExamQuestion(delta) {
      saveExamAnswer(false, false);
      renderExamQuestion(currentExamQIndex + delta);
    }

    async function saveExamAnswer(isMarkedForReview = false, moveNext = false) {
      if (!currentExamSession) return;
      const q = currentExamSession.questions[currentExamQIndex];
      let submitted = {};
      const existing = (currentExamSession.saved_answers || {})[q.question_id];
      if (existing && existing.selected_option) {
        submitted = { selected_option: existing.selected_option };
      }

      if (Object.keys(submitted).length > 0) {
        currentExamSession.saved_answers[q.question_id] = submitted;
      }

      if (isMarkedForReview) {
        if (!currentExamSession.marked_for_review.includes(q.question_id)) {
          currentExamSession.marked_for_review.push(q.question_id);
        }
      } else {
        currentExamSession.marked_for_review = currentExamSession.marked_for_review.filter(id => id !== q.question_id);
      }

      try {
        await fetch(`/api/examinations/${currentExamSession.session_id}/answer?student_id=${currentStudentId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question_id: q.question_id,
            submitted_answer: submitted,
            is_marked_for_review: isMarkedForReview,
            time_spent_seconds: 30
          })
        });
      } catch (err) {
        console.warn('Answer persistence warning:', err);
      }

      updatePaletteUI();

      if (moveNext) {
        if (currentExamQIndex < currentExamSession.questions.length - 1) {
          renderExamQuestion(currentExamQIndex + 1);
        } else {
          confirmSubmitExam();
        }
      }
    }

    function saveAndNextExamQuestion() {
      saveExamAnswer(false, true);
    }

    function saveAndMarkForReview() {
      saveExamAnswer(true, true);
    }

    function clearCurrentExamAnswer() {
      if (!currentExamSession) return;
      const q = currentExamSession.questions[currentExamQIndex];
      delete currentExamSession.saved_answers[q.question_id];
      currentExamSession.marked_for_review = currentExamSession.marked_for_review.filter(id => id !== q.question_id);
      renderExamQuestion(currentExamQIndex);
      showToast('Response cleared for this question.');
    }

    function confirmSubmitExam() {
      saveExamAnswer(false, false);
      const answered = Object.keys(currentExamSession.saved_answers || {}).length;
      const total = currentExamSession.questions.length;
      const unanswered = total - answered;

      const msg = `You have answered ${answered} of ${total} questions (${unanswered} unanswered).\n\nAre you sure you want to finish and submit your CBSE Board Examination paper? This will finalize your responses and calculate your official score.`;
      if (confirm(msg)) {
        submitBoardExam(false);
      }
    }

    async function submitBoardExam(isTimeout = false) {
      if (examTimerInterval) clearInterval(examTimerInterval);
      try {
        showToast(isTimeout ? 'Time limit reached! Auto-submitting paper...' : 'Evaluating all 39 questions against CBSE marking schemes...');
        const res = await fetch(`/api/examinations/${currentExamSession.session_id}/submit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ student_id: currentStudentId, is_timeout: isTimeout })
        });

        if (!res.ok) throw new Error('Failed to evaluate examination');
        const summary = await res.json();
        currentExamResult = summary;
        renderExamResult(summary);
      } catch (err) {
        showToast(err.message, false);
      }
    }

    async function loadExamResultFromHistory(sessionId) {
      try {
        const res = await fetch(`/api/examinations/${sessionId}/result?student_id=${currentStudentId}`);
        if (!res.ok) throw new Error('Failed to load past result');
        const summary = await res.json();
        currentExamResult = summary;
        renderExamResult(summary);
      } catch (err) {
        showToast(err.message, false);
      }
    }

    function renderExamResult(summary) {
      switchView('examination-result');

      document.getElementById('result-paper-title').innerText = summary.paper_title;
      document.getElementById('result-meta-info').innerText = `Candidate: ${summary.student_name} (${summary.student_id}) • Code: ${summary.paper_code} • ${new Date(summary.completed_at).toLocaleString()}`;
      document.getElementById('result-score-display').innerText = `${summary.score} / ${summary.total_marks}`;
      document.getElementById('result-pct-display').innerText = `${summary.percentage}%`;

      let grade = 'A1 (Outstanding)';
      let passStatus = 'DISTINCTION';
      if (summary.percentage >= 91) { grade = 'A1 (Outstanding)'; passStatus = 'EXEMPLARY'; }
      else if (summary.percentage >= 81) { grade = 'A2 (Excellent)'; passStatus = 'DISTINCTION'; }
      else if (summary.percentage >= 71) { grade = 'B1 (Very Good)'; passStatus = 'FIRST CLASS'; }
      else if (summary.percentage >= 61) { grade = 'B2 (Good)'; passStatus = 'SECOND CLASS'; }
      else if (summary.percentage >= 51) { grade = 'C1 (Average)'; passStatus = 'PASS'; }
      else if (summary.percentage >= 33) { grade = 'D (Pass)'; passStatus = 'PASS'; }
      else { grade = 'E (Essential Repeat)'; passStatus = 'NEEDS REMEDIATION'; }

      document.getElementById('result-grade-display').innerText = grade;
      document.getElementById('result-pass-status').innerText = passStatus;
      document.getElementById('result-time-spent-display').innerText = `${Math.round(summary.time_spent_seconds / 60)}m`;
      document.getElementById('result-q-count-display').innerText = `${summary.question_reviews.length} / ${summary.question_reviews.length}`;

      const secContainer = document.getElementById('result-section-cards');
      secContainer.innerHTML = '';
      for (const [secName, sData] of Object.entries(summary.section_scores)) {
        const card = document.createElement('div');
        card.className = 'p-5 rounded-2xl bg-white border border-sandDark shadow-sm space-y-2';
        card.innerHTML = `
          <span class="text-xs font-bold uppercase tracking-wider text-muted block">${secName}</span>
          <div class="flex items-baseline justify-between">
            <span class="text-2xl font-black text-deepPurple">${sData.marks_obtained}</span>
            <span class="text-xs font-bold text-muted">/ ${sData.total_marks} Marks</span>
          </div>
          <div class="w-full bg-sandDark h-2 rounded-full overflow-hidden">
            <div class="bg-brandPurple h-full rounded-full" style="width: ${sData.percentage}%"></div>
          </div>
          <div class="flex justify-between text-[11px] text-muted font-medium pt-1">
            <span>${sData.correct_count} / ${sData.questions_count} Correct</span>
            <span class="font-bold text-deepPurple">${sData.percentage}%</span>
          </div>
        `;
        secContainer.appendChild(card);
      }

      const unitContainer = document.getElementById('result-unit-bars');
      unitContainer.innerHTML = '';
      for (const [unitName, uData] of Object.entries(summary.unit_scores)) {
        const row = document.createElement('div');
        row.className = 'space-y-1';
        row.innerHTML = `
          <div class="flex justify-between text-xs font-bold">
            <span class="text-deepPurple">${unitName}</span>
            <span class="text-muted">${uData.marks_obtained} / ${uData.total_marks} Marks (${uData.percentage}%)</span>
          </div>
          <div class="w-full bg-sandDark h-3 rounded-full overflow-hidden">
            <div class="bg-brandYellow h-full rounded-full transition-all duration-500" style="width: ${uData.percentage}%"></div>
          </div>
        `;
        unitContainer.appendChild(row);
      }

      const recReason = document.getElementById('result-rec-reason');
      if (summary.recommended_next_action && summary.recommended_next_action.reason) {
        recReason.innerText = summary.recommended_next_action.reason;
      } else {
        recReason.innerText = 'Review all marked responses to strengthen overall syllabus mastery.';
      }

      const revContainer = document.getElementById('result-question-reviews-list');
      revContainer.innerHTML = '';
      summary.question_reviews.forEach((rev, idx) => {
        const card = document.createElement('div');
        const isCorrect = rev.is_correct;
        card.className = `p-6 rounded-2xl border-2 space-y-4 ${isCorrect ? 'bg-green-50/50 border-green-200' : 'bg-red-50/50 border-red-200'}`;

        const studentAnsStr = typeof rev.submitted_answer === 'object' && rev.submitted_answer !== null ?
          (rev.submitted_answer.selected_option || rev.submitted_answer.numerical_value || rev.submitted_answer.text_answer || 'No Answer Provided') :
          String(rev.submitted_answer || 'No Answer Provided');

        const correctAnsStr = typeof rev.correct_answer === 'object' ? JSON.stringify(rev.correct_answer) : String(rev.correct_answer);

        card.innerHTML = `
          <div class="flex flex-wrap items-center justify-between gap-2 border-b border-sandDark pb-3">
            <div class="flex items-center gap-2">
              <span class="w-7 h-7 rounded-lg font-extrabold text-xs flex items-center justify-center ${isCorrect ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}">
                ${rev.question_number}
              </span>
              <span class="text-xs font-bold uppercase ${isCorrect ? 'text-green-900' : 'text-red-900'}">
                ${rev.section_name} • ${isCorrect ? 'CORRECT (+' + rev.marks_awarded + ' marks)' : 'INCORRECT (0 / ' + rev.marks + ' marks)'}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs font-semibold px-2 py-0.5 rounded-md bg-white border border-sandDark text-muted">${rev.chapter_name || rev.chapter_id}</span>
              <span class="text-xs font-mono text-muted">${rev.question_id}</span>
            </div>
          </div>

          <div class="text-sm font-semibold text-deepPurple leading-relaxed">
            ${rev.question_text}
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div class="p-3 rounded-xl bg-white/80 border border-sandDark space-y-1">
              <span class="font-bold text-muted uppercase block text-[10px]">Your Response:</span>
              <span class="font-bold ${isCorrect ? 'text-green-800' : 'text-red-800'}">${studentAnsStr}</span>
            </div>
            <div class="p-3 rounded-xl bg-white/80 border border-sandDark space-y-1">
              <span class="font-bold text-muted uppercase block text-[10px]">Verified Marking Scheme / Answer Key:</span>
              <span class="font-bold text-deepPurple">${correctAnsStr}</span>
            </div>
          </div>

          <div class="bg-white p-4 rounded-xl border border-sandDark text-xs space-y-1.5">
            <span class="font-extrabold text-deepPurple uppercase tracking-wider block">NCERT Step-by-Step Pedagogical Explanation:</span>
            <p class="text-muted leading-relaxed">${rev.explanation}</p>
            ${rev.evaluation_feedback ? `<p class="text-deepPurple font-medium pt-1"><strong>Rubric Feedback:</strong> ${rev.evaluation_feedback}</p>` : ''}
            ${rev.misconception_tags && rev.misconception_tags.length ? `<p class="text-amber-800 font-semibold pt-1">⚠️ <strong>Detected Misconception Pattern:</strong> ${rev.misconception_tags.join(', ')}</p>` : ''}
          </div>
        `;
        revContainer.appendChild(card);
      });

      if (window.renderMathInElement) {
        try {
          renderMathInElement(document.getElementById('view-examination-result'), {
            delimiters: [
              { left: '$$', right: '$$', display: true },
              { left: '$', right: '$', display: false },
              { left: '\\(', right: '\\)', display: false },
              { left: '\\[', right: '\\]', display: true },
            ],
            throwOnError: false,
          });
        } catch (e) {
          console.warn('KaTeX render warning:', e);
        }
      }
    }

    function executeResultRecommendation() {
      if (currentExamResult && currentExamResult.recommended_next_action && currentExamResult.recommended_next_action.concept_id) {
        loadRemediationForConcept(currentExamResult.recommended_next_action.concept_id);
      } else {
        loadRemediationView();
      }
    }

    async function loadDashboard() {
      try {
        const res = await fetch(`/api/student/dashboard?student_id=${currentStudentId}`);
        if (!res.ok) throw new Error('Failed to load dashboard data');
        const data = await res.json();

        document.getElementById('dash-welcome-name').innerText = data.student.name.split(' ')[0];
        document.getElementById('sidebar-user-name').innerText = data.student.name;
        document.getElementById('kpi-mastery-score').innerText = `${Math.round(data.overall_mastery_pct)}%`;
        document.getElementById('kpi-mastery-bar').style.width = `${Math.round(data.overall_mastery_pct)}%`;
        document.getElementById('kpi-assessments-count').innerText = data.total_assessments_taken;
        document.getElementById('kpi-accuracy-rate').innerText = `${Math.round(data.overall_accuracy_pct)}%`;

        const miscRes = await fetch(`/api/student/misconceptions?student_id=${currentStudentId}`);
        if (miscRes.ok) {
          const miscs = await miscRes.json();
          const activeCount = miscs.filter(m => m.status !== 'RESOLVED').length;
          document.getElementById('kpi-misconceptions-count').innerText = activeCount;
        }

        const weakList = document.getElementById('weak-concepts-list');
        weakList.innerHTML = '';
        document.getElementById('weak-concepts-count').innerText = `${data.weak_concepts.length} concepts`;
        if (data.weak_concepts.length > 0) {
          data.weak_concepts.slice(0, 3).forEach(c => {
            const row = document.createElement('div');
            row.className = 'p-3 rounded-2xl bg-sandLight border border-sandDark flex items-center justify-between text-sm';
            row.innerHTML = `
              <div>
                <span class="font-bold text-deepPurple block">${c.concept_name}</span>
                <span class="text-xs text-muted">Mastery: ${Math.round(c.mastery_score * 100)}%</span>
              </div>
              <button onclick="loadRemediationForConcept('${c.concept_id}')" class="text-xs font-bold text-deepPurple px-3 py-1.5 rounded-lg bg-sandDark hover:bg-brandYellow transition-colors">
                Remediate &rarr;
              </button>
            `;
            weakList.appendChild(row);
          });
        } else {
          weakList.innerHTML = '<p class="text-xs text-muted text-center py-4">No weak concepts detected!</p>';
        }

        const strongList = document.getElementById('strong-concepts-list');
        strongList.innerHTML = '';
        document.getElementById('strong-concepts-count').innerText = `${data.strong_concepts.length} concepts`;
        if (data.strong_concepts.length > 0) {
          data.strong_concepts.slice(0, 3).forEach(c => {
            const row = document.createElement('div');
            row.className = 'p-3 rounded-2xl bg-sandLight border border-sandDark flex items-center justify-between text-sm';
            row.innerHTML = `
              <div>
                <span class="font-bold text-deepPurple block">${c.concept_name}</span>
                <span class="text-xs text-successGreen font-semibold">Mastery: ${Math.round(c.mastery_score * 100)}%</span>
              </div>
              <span class="text-xs font-bold px-2 py-0.5 rounded-full bg-green-100 text-green-800">STRONG</span>
            `;
            strongList.appendChild(row);
          });
        } else {
          strongList.innerHTML = '<p class="text-xs text-muted text-center py-4">Complete diagnostics to verify strengths.</p>';
        }

        const recentList = document.getElementById('recent-assessments-list');
        recentList.innerHTML = '';
        if (data.recent_assessments.length > 0) {
          data.recent_assessments.slice(0, 4).forEach(asm => {
            const row = document.createElement('div');
            const pct = asm.total_marks > 0 ? Math.round((asm.score / asm.total_marks) * 100) : 0;
            row.className = 'p-3 rounded-2xl bg-sandLight border border-sandDark flex items-center justify-between text-sm';
            row.innerHTML = `
              <div>
                <span class="font-bold text-deepPurple block">${asm.assessment_type}</span>
                <span class="text-xs text-muted">${new Date(asm.started_at).toLocaleDateString()}</span>
              </div>
              <span class="px-2.5 py-1 rounded-full text-xs font-bold ${pct >= 70 ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'}">
                ${asm.score} / ${asm.total_marks} (${pct}%)
              </span>
            `;
            recentList.appendChild(row);
          });
        } else {
          recentList.innerHTML = '<p class="text-xs text-muted text-center py-4">No assessments completed yet.</p>';
        }

        await loadStudentActivityTimeline();

      } catch (err) {
        console.error(err);
      }
    }

    async function loadStudentActivityTimeline() {
      try {
        const [actRes, telRes] = await Promise.all([
          fetch(`/api/student/${currentStudentId}/activity?limit=25`),
          fetch(`/api/student/${currentStudentId}/telemetry`)
        ]);

        if (telRes.ok) {
          const tel = await telRes.json();
          const elActions = document.getElementById('tel-total-actions');
          const elStudy = document.getElementById('tel-study-time');
          const elExams = document.getElementById('tel-exams-count');
          const elRemed = document.getElementById('tel-remed-count');
          if (elActions) elActions.innerText = tel.total_activities;
          if (elStudy) elStudy.innerText = `${tel.total_study_minutes}m`;
          if (elExams) elExams.innerText = tel.board_exams_count + tel.diagnostic_tests_count;
          if (elRemed) elRemed.innerText = tel.remediations_completed;
        }

        const container = document.getElementById('student-activity-timeline');
        if (!container) return;

        if (!actRes.ok) {
          container.innerHTML = '<p class="text-xs text-muted text-center py-4">Telemetry tracking initializing...</p>';
          return;
        }

        const acts = await actRes.json();
        container.innerHTML = '';
        if (acts.length === 0) {
          container.innerHTML = '<p class="text-xs text-muted text-center py-4">No student telemetry logged yet. Start practicing or take a test!</p>';
          return;
        }

        acts.forEach(item => {
          const el = document.createElement('div');
          el.className = 'p-3.5 rounded-2xl bg-white border border-sandDark flex items-start justify-between gap-3 shadow-2xs hover:border-deepPurple/30 transition-all';
          
          let icon = '⚡';
          let badgeBg = 'bg-sandDark text-deepPurple';
          if (item.event_type.includes('LOGIN')) { icon = '🔑'; badgeBg = 'bg-blue-100 text-blue-900'; }
          else if (item.event_type.includes('BOARD_EXAM')) { icon = '🏆'; badgeBg = 'bg-amber-100 text-amber-900'; }
          else if (item.event_type.includes('DIAGNOSTIC')) { icon = '📝'; badgeBg = 'bg-purple-100 text-purple-900'; }
          else if (item.event_type.includes('REMEDIATION')) { icon = '🎯'; badgeBg = 'bg-green-100 text-green-900'; }
          else if (item.event_type.includes('SPACED')) { icon = '🔄'; badgeBg = 'bg-indigo-100 text-indigo-900'; }
          else if (item.event_type.includes('MISCONCEPTION')) { icon = '⚠️'; badgeBg = 'bg-red-100 text-red-900'; }

          const dateObj = new Date(item.created_at);
          const timeStr = isNaN(dateObj.getTime()) ? item.created_at : `${dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}, ${dateObj.toLocaleDateString()}`;

          let detailsSub = '';
          if (item.details) {
            if (item.details.score !== undefined) {
              detailsSub = `<span class="text-[11px] font-semibold text-deepPurple">Score: ${item.details.score}</span>`;
            } else if (item.details.concept_id) {
              detailsSub = `<span class="text-[11px] font-semibold text-muted font-mono">${item.details.concept_id}</span>`;
            }
          }

          el.innerHTML = `
            <div class="flex items-start gap-3">
              <span class="w-8 h-8 rounded-xl ${badgeBg} flex items-center justify-center text-sm font-bold shrink-0">${icon}</span>
              <div>
                <span class="font-bold text-deepPurple text-xs block leading-tight">${item.action_title}</span>
                <div class="flex flex-wrap items-center gap-2 mt-1">
                  <span class="text-[10px] text-muted">${timeStr}</span>
                  ${item.duration_seconds > 0 ? `<span class="text-[10px] font-semibold text-muted bg-sand px-1.5 py-0.5 rounded">${item.duration_seconds}s active</span>` : ''}
                  ${detailsSub}
                </div>
              </div>
            </div>
            <span class="text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${badgeBg} shrink-0">
              ${item.event_type.replace(/_/g, ' ')}
            </span>
          `;
          container.appendChild(el);
        });

      } catch (err) {
        console.error('Failed to load activity timeline:', err);
      }
    }

    async function loadTeacherActivityFeed() {
      try {
        const res = await fetch('/api/teacher/activity-stream?role=teacher&limit=40');
        const container = document.getElementById('t-activity-feed-list');
        if (!container) return;

        if (!res.ok) {
          container.innerHTML = '<p class="text-xs text-muted text-center py-4">Live telemetry feed requires teacher credentials.</p>';
          return;
        }

        const events = await res.json();
        container.innerHTML = '';
        if (events.length === 0) {
          container.innerHTML = '<p class="text-xs text-muted text-center py-4">No student telemetry events recorded in classroom feed.</p>';
          return;
        }

        events.forEach(ev => {
          const el = document.createElement('div');
          el.className = 'p-3.5 rounded-2xl bg-white border border-sandDark flex items-start justify-between gap-3 shadow-2xs hover:border-deepPurple/40 transition-all';

          let icon = '⚡';
          let badgeBg = 'bg-sandDark text-deepPurple';
          if (ev.event_type.includes('LOGIN')) { icon = '🔑'; badgeBg = 'bg-blue-100 text-blue-900'; }
          else if (ev.event_type.includes('BOARD_EXAM')) { icon = '🏆'; badgeBg = 'bg-amber-100 text-amber-900'; }
          else if (ev.event_type.includes('DIAGNOSTIC')) { icon = '📝'; badgeBg = 'bg-purple-100 text-purple-900'; }
          else if (ev.event_type.includes('REMEDIATION')) { icon = '🎯'; badgeBg = 'bg-green-100 text-green-900'; }
          else if (ev.event_type.includes('SPACED')) { icon = '🔄'; badgeBg = 'bg-indigo-100 text-indigo-900'; }

          const dateObj = new Date(ev.created_at);
          const timeStr = isNaN(dateObj.getTime()) ? ev.created_at : `${dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}, ${dateObj.toLocaleDateString()}`;

          el.innerHTML = `
            <div class="flex items-start gap-3">
              <span class="w-8 h-8 rounded-xl ${badgeBg} flex items-center justify-center text-sm font-bold shrink-0">${icon}</span>
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-extrabold text-deepPurple text-xs">${ev.student_name}</span>
                  <span class="text-[10px] font-mono text-muted">(${ev.student_id})</span>
                </div>
                <p class="text-xs font-semibold text-deepPurple/90 mt-0.5">${ev.action_title}</p>
                <span class="text-[10px] text-muted block mt-1">${timeStr}</span>
              </div>
            </div>
            <span class="text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${badgeBg} shrink-0">
              ${ev.event_type.replace(/_/g, ' ')}
            </span>
          `;
          container.appendChild(el);
        });

      } catch (err) {
        console.error('Failed to load teacher activity feed:', err);
      }
    }

    let diagTimerInterval = null;
    let diagRemainingSeconds = 900;

    function startDiagnosticTimer(initialSeconds = 900) {
      if (diagTimerInterval) clearInterval(diagTimerInterval);
      diagRemainingSeconds = initialSeconds;

      function updateDiagDisplay() {
        if (diagRemainingSeconds <= 0) {
          clearInterval(diagTimerInterval);
          const displayEl = document.getElementById('diag-timer-display');
          if (displayEl) displayEl.innerText = '00:00';
          showToast('Diagnostic assessment time limit reached! Auto-finalizing test...');
          finalizeAssessment();
          return;
        }
        const mins = Math.floor(diagRemainingSeconds / 60);
        const secs = diagRemainingSeconds % 60;
        const timeStr = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
        const displayEl = document.getElementById('diag-timer-display');
        if (displayEl) displayEl.innerText = timeStr;
        diagRemainingSeconds--;
      }

      updateDiagDisplay();
      diagTimerInterval = setInterval(updateDiagDisplay, 1000);
    }

    async function startDiagnosticTest() {
      try {
        switchView('assessment');
        document.getElementById('q-text-content').innerText = 'Initializing diagnostic session...';
        startDiagnosticTimer(900);
        
        const res = await fetch('/api/assessments/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            student_id: currentStudentId,
            chapter_id: 'CH-01',
            question_count: 10
          })
        });

        if (!res.ok) throw new Error('Failed to start test');
        currentAssessment = await res.json();
        currentQuestionIndex = 0;
        selectedAnswers = {};
        
        renderCurrentQuestion();
        showToast('Diagnostic assessment initialized with 10 questions (Q1-4 Easy, Q5-7 Medium, Q8-10 Hard).');
      } catch (err) {
        showToast(err.message, false);
      }
    }

    function renderCurrentQuestion() {
      if (!currentAssessment || !currentAssessment.questions.length) return;

      const q = currentAssessment.questions[currentQuestionIndex];
      const total = currentAssessment.questions.length;

      document.getElementById('q-current-num').innerText = currentQuestionIndex + 1;
      document.getElementById('q-total-num').innerText = total;
      document.getElementById('test-progress-bar').style.width = `${((currentQuestionIndex + 1) / total) * 100}%`;

      document.getElementById('badge-qtype').innerText = q.question_type;
      document.getElementById('badge-difficulty').innerText = q.difficulty;
      document.getElementById('badge-marks').innerText = `Marks: ${q.marks}`;
      document.getElementById('q-id-display').innerText = q.question_id;

      document.getElementById('q-text-content').innerText = q.question_text;

      const arContainer = document.getElementById('ar-container');
      if (q.question_type === 'ASSERTION_REASON') {
        if (!q.options || Object.keys(q.options).length === 0) {
          q.options = {
            "A": "Both Assertion (A) and Reason (R) are true and Reason (R) is the correct explanation of Assertion (A).",
            "B": "Both Assertion (A) and Reason (R) are true but Reason (R) is not the correct explanation of Assertion (A).",
            "C": "Assertion (A) is true but Reason (R) is false.",
            "D": "Assertion (A) is false but Reason (R) is true."
          };
        }
        if (q.assertion || q.reason) {
          arContainer.classList.remove('hidden');
          document.getElementById('ar-assertion-text').innerText = q.assertion || '';
          document.getElementById('ar-reason-text').innerText = q.reason || '';
        } else {
          arContainer.classList.add('hidden');
        }
      } else {
        arContainer.classList.add('hidden');
      }

      const optsContainer = document.getElementById('options-container');
      const textContainer = document.getElementById('text-input-container');

      optsContainer.innerHTML = '';

      if (q.options && Object.keys(q.options).length > 0) {
        optsContainer.classList.remove('hidden');
        textContainer.classList.add('hidden');

        const currentSelection = selectedAnswers[q.question_id]?.selected_option;

        for (const [optKey, optText] of Object.entries(q.options)) {
          const card = document.createElement('div');
          const isSelected = (currentSelection === optKey);
          card.className = `option-card p-4 rounded-2xl border-2 cursor-pointer flex items-center gap-4 ${isSelected ? 'selected' : 'border-sandDark bg-sandLight'}`;
          card.onclick = () => selectOption(q.question_id, optKey);
          card.innerHTML = `
            <div class="w-8 h-8 rounded-xl font-bold flex items-center justify-center text-sm ${isSelected ? 'bg-deepPurple text-cream' : 'bg-sandDark text-muted'}">
              ${optKey}
            </div>
            <div class="text-sm font-medium text-deepPurple flex-1">
              ${optText}
            </div>
          `;
          optsContainer.appendChild(card);
        }
      } else {
        optsContainer.classList.add('hidden');
        textContainer.classList.remove('hidden');
        const existingText = selectedAnswers[q.question_id]?.text_answer || '';
        document.getElementById('student-text-input').value = existingText;
      }

      document.getElementById('btn-prev-q').disabled = (currentQuestionIndex === 0);

      if (window.renderMathInElement) {
        renderMathInElement(document.getElementById('view-assessment'), {
          delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$', right: '$', display: false }
          ]
        });
      }
    }

    function selectOption(questionId, optionKey) {
      selectedAnswers[questionId] = { selected_option: optionKey };
      renderCurrentQuestion();
    }

    async function saveCurrentAnswer() {
      if (!currentAssessment) return;
      const q = currentAssessment.questions[currentQuestionIndex];
      
      if (document.getElementById('text-input-container').classList.contains('hidden') === false) {
        const textVal = document.getElementById('student-text-input').value.trim();
        if (textVal) {
          selectedAnswers[q.question_id] = { text_answer: textVal, numerical_value: parseFloat(textVal) || null };
        }
      }

      const ansPayload = selectedAnswers[q.question_id];
      if (ansPayload) {
        try {
          await fetch(`/api/assessments/${currentAssessment.assessment_id}/answers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              student_id: currentStudentId,
              question_id: q.question_id,
              submitted_answer: ansPayload,
              time_spent_seconds: 30
            })
          });
        } catch (e) {
          console.warn('Auto-save error:', e);
        }
      }
    }

    async function navigateQuestion(direction) {
      await saveCurrentAnswer();
      currentQuestionIndex += direction;
      renderCurrentQuestion();
    }

    async function saveAndNext() {
      await saveCurrentAnswer();
      if (currentQuestionIndex < currentAssessment.questions.length - 1) {
        currentQuestionIndex++;
        renderCurrentQuestion();
      } else {
        showSubmitConfirmModal();
      }
    }

    async function showSubmitConfirmModal() {
      await saveCurrentAnswer();
      if (confirm('Are you ready to submit your diagnostic assessment and view your evaluated results?')) {
        finalizeAssessment();
      }
    }

    async function finalizeAssessment() {
      if (diagTimerInterval) clearInterval(diagTimerInterval);
      try {
        await saveCurrentAnswer();
        const res = await fetch(`/api/assessments/${currentAssessment.assessment_id}/submit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ student_id: currentStudentId })
        });

        if (!res.ok) throw new Error('Failed to finalize assessment');
        const summary = await res.json();
        renderAssessmentResult(summary);
      } catch (err) {
        showToast(err.message, false);
      }
    }

    function renderAssessmentResult(summary) {
      document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
      document.getElementById('results-view').classList.add('active');

      document.getElementById('res-score-display').innerText = `${summary.score} / ${summary.total_marks}`;
      document.getElementById('res-pct-display').innerText = `${summary.percentage}%`;

      const reviewsList = document.getElementById('question-reviews-list');
      reviewsList.innerHTML = '';

      summary.question_reviews.forEach((rev, idx) => {
        const card = document.createElement('div');
        card.className = `p-6 rounded-2xl border-2 space-y-4 ${rev.is_correct ? 'bg-green-50/50 border-green-200' : 'bg-red-50/50 border-red-200'}`;

        const subChoice = rev.submitted_answer?.selected_option || rev.submitted_answer?.text_answer || 'None';
        const correctChoice = rev.correct_answer || 'N/A';

        card.innerHTML = `
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider ${rev.is_correct ? 'text-green-800' : 'text-red-800'}">
              Question ${idx + 1} • ${rev.is_correct ? 'CORRECT (+ ' + rev.marks_awarded + ' marks)' : 'INCORRECT (0 marks)'}
            </span>
            <span class="text-xs font-mono text-muted">${rev.question_id}</span>
          </div>

          <p class="font-semibold text-deepPurple text-base">${rev.question_text}</p>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div class="p-3 rounded-xl bg-white/70 border border-sandDark">
              <span class="text-xs text-muted block font-semibold">Your Answer:</span>
              <span class="font-bold ${rev.is_correct ? 'text-green-800' : 'text-red-800'}">${subChoice}</span>
            </div>
            <div class="p-3 rounded-xl bg-white/70 border border-sandDark">
              <span class="text-xs text-muted block font-semibold">Correct Answer:</span>
              <span class="font-bold text-deepPurple">${correctChoice}</span>
            </div>
          </div>

          <div class="bg-white p-4 rounded-xl border border-sandDark text-sm space-y-1">
            <span class="text-xs font-bold text-deepPurple uppercase tracking-wider block">NCERT Step-by-Step Explanation:</span>
            <p class="text-muted leading-relaxed">${rev.explanation}</p>
          </div>
        `;
        reviewsList.appendChild(card);
      });

      if (window.renderMathInElement) {
        renderMathInElement(reviewsList, {
          delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$', right: '$', display: false }
          ]
        });
      }

      showToast('Assessment evaluated and learner mastery updated!');
    }

    async function loadMasteryView() {
      try {
        const res = await fetch(`/api/student/mastery?student_id=${currentStudentId}&chapter_id=CH-01`);
        if (!res.ok) throw new Error('Failed to load mastery profile');
        allMasteryItems = await res.json();
        renderMasteryGrid(allMasteryItems);
      } catch (err) {
        console.error(err);
      }
    }

    function renderMasteryGrid(items) {
      const grid = document.getElementById('full-mastery-grid');
      grid.innerHTML = '';

      items.forEach(c => {
        const card = document.createElement('div');
        card.className = 'bg-sand p-5 rounded-2xl border border-sandDark shadow-sm flex flex-col justify-between';
        
        let statusBadge = '';
        if (c.status === 'STRONG') statusBadge = '<span class="bg-green-100 text-green-800 text-xs font-bold px-2.5 py-0.5 rounded-full">STRONG</span>';
        else if (c.status === 'IMPROVING') statusBadge = '<span class="bg-purple-100 text-purple-800 text-xs font-bold px-2.5 py-0.5 rounded-full">IMPROVING</span>';
        else if (c.status === 'DEVELOPING') statusBadge = '<span class="bg-red-100 text-red-800 text-xs font-bold px-2.5 py-0.5 rounded-full">DEVELOPING</span>';
        else statusBadge = '<span class="bg-sandDark text-muted text-xs font-bold px-2.5 py-0.5 rounded-full">UNASSESSED</span>';

        const pct = Math.round(c.mastery_score * 100);

        card.innerHTML = `
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-mono text-muted">${c.concept_id}</span>
              ${statusBadge}
            </div>
            <h4 class="font-bold text-deepPurple text-base mb-1">${c.concept_name}</h4>
            <p class="text-xs text-muted mb-4">Topic: ${c.topic_id}</p>
          </div>
          <div>
            <div class="flex items-center justify-between text-xs font-semibold mb-1">
              <span>Mastery Score</span>
              <span>${pct}%</span>
            </div>
            <div class="w-full bg-sandDark h-2 rounded-full overflow-hidden mb-3">
              <div class="bg-brandYellow h-full" style="width: ${pct}%"></div>
            </div>
            <div class="flex items-center justify-between text-xs text-muted">
              <span>Attempts: ${c.total_attempts}</span>
              <button onclick="loadRemediationForConcept('${c.concept_id}')" class="font-bold text-deepPurple hover:underline">Remediate &rarr;</button>
            </div>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    function filterMastery(status) {
      document.querySelectorAll('.mastery-filter-btn').forEach(b => {
        b.classList.remove('bg-deepPurple', 'text-cream');
        b.classList.add('bg-sand', 'text-muted');
      });
      event.target.classList.remove('bg-sand', 'text-muted');
      event.target.classList.add('bg-deepPurple', 'text-cream');

      if (status === 'ALL') {
        renderMasteryGrid(allMasteryItems);
      } else {
        const filtered = allMasteryItems.filter(item => item.status === status);
        renderMasteryGrid(filtered);
      }
    }

    async function loadAdaptiveQuestion() {
      switchView('adaptive');
      document.getElementById('adapt-feedback-box').classList.add('hidden');
      document.getElementById('btn-submit-adapt').disabled = false;

      try {
        const res = await fetch(`/api/questions/next?student_id=${currentStudentId}&chapter_id=CH-01`);
        if (!res.ok) throw new Error('Failed to fetch adaptive question');
        currentAdaptiveRec = await res.json();

        const rec = currentAdaptiveRec;
        document.getElementById('adapt-concept-name').innerText = `Concept: ${rec.target_concept_name} (${rec.target_concept_id})`;
        document.getElementById('adapt-rationale').innerText = rec.selection_rationale;

        const q = rec.question;
        document.getElementById('adapt-qtype').innerText = q.question_type;
        document.getElementById('adapt-diff').innerText = rec.difficulty;
        document.getElementById('adapt-qtext').innerText = q.question_text;

        const optsContainer = document.getElementById('adapt-options-container');
        optsContainer.innerHTML = '';

        if (!q.options || Object.keys(q.options).length === 0) {
          if (q.question_type === 'ASSERTION_REASON') {
            q.options = {
              "A": "Both Assertion (A) and Reason (R) are true and Reason (R) is the correct explanation of Assertion (A).",
              "B": "Both Assertion (A) and Reason (R) are true but Reason (R) is not the correct explanation of Assertion (A).",
              "C": "Assertion (A) is true but Reason (R) is false.",
              "D": "Assertion (A) is false but Reason (R) is true."
            };
          }
        }

        const opts = (q.options && Object.keys(q.options).length > 0) ? q.options : {
          "A": "Option A (Select to record your response)",
          "B": "Option B (Select to record your response)",
          "C": "Option C (Select to record your response)",
          "D": "Option D (Select to record your response)"
        };

        for (const [key, text] of Object.entries(opts)) {
          const card = document.createElement('div');
          card.className = 'option-card p-4 rounded-2xl border-2 border-sandDark bg-sandLight cursor-pointer flex items-center gap-4';
          card.onclick = () => {
            optsContainer.querySelectorAll('.option-card').forEach(el => el.classList.remove('selected'));
            card.classList.add('selected');
            card.dataset.selectedKey = key;
          };
          card.innerHTML = `
            <div class="w-8 h-8 rounded-xl font-bold bg-sandDark text-muted flex items-center justify-center text-sm">
              ${key}
            </div>
            <div class="text-sm font-medium text-deepPurple flex-1">
              ${text}
            </div>
          `;
          optsContainer.appendChild(card);
        }

        if (window.renderMathInElement) {
          renderMathInElement(document.getElementById('view-adaptive'), {
            delimiters: [
              { left: '$$', right: '$$', display: true },
              { left: '$', right: '$', display: false }
            ]
          });
        }

      } catch (err) {
        showToast(err.message, false);
      }
    }

    async function submitAdaptiveAnswer() {
      if (!currentAdaptiveRec) return;
      const q = currentAdaptiveRec.question;
      const selected = document.querySelector('#adapt-options-container .option-card.selected');
      if (!selected) {
        showToast('Please select an option before submitting.', false);
        return;
      }

      const chosenKey = selected.dataset.selectedKey;
      try {
        const res = await fetch(`/api/assessments/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            student_id: currentStudentId,
            chapter_id: 'CH-01',
            question_count: 1
          })
        });
        const asm = await res.json();

        const evalRes = await fetch(`/api/assessments/${asm.assessment_id}/answers`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            student_id: currentStudentId,
            question_id: q.question_id,
            submitted_answer: { selected_option: chosenKey },
            time_spent_seconds: 45
          })
        });
        const evalData = await evalRes.json();

        const fb = document.getElementById('adapt-feedback-box');
        fb.classList.remove('hidden');
        if (evalData.is_correct) {
          fb.className = 'p-5 rounded-2xl border text-sm leading-relaxed space-y-2 bg-green-50 border-green-300 text-green-900';
          fb.innerHTML = `
            <div class="flex items-center gap-2 font-bold text-base text-green-800">
              <span>✓ Correct Answer!</span>
            </div>
            <p>${evalData.feedback}</p>
          `;
        } else {
          fb.className = 'p-5 rounded-2xl border text-sm leading-relaxed space-y-2 bg-red-50 border-red-300 text-red-900';
          fb.innerHTML = `
            <div class="flex items-center gap-2 font-bold text-base text-red-800">
              <span>✗ Incorrect</span>
            </div>
            <p>${evalData.feedback}</p>
          `;
        }

        document.getElementById('btn-submit-adapt').disabled = true;
        showToast(evalData.is_correct ? 'Correct! Mastery updated.' : 'Answer evaluated.');

      } catch (err) {
        showToast(err.message, false);
      }
    }

    async function loadRemediationView(conceptId = null) {
      switchView('remediation');
      document.getElementById('rem-feedback-box').classList.add('hidden');
      document.getElementById('btn-submit-rem').disabled = false;

      try {
        let url = `/api/student/remediation?student_id=${currentStudentId}`;
        if (conceptId) url += `&concept_id=${conceptId}`;

        const res = await fetch(url);
        if (!res.ok) throw new Error('Failed to load remediation');
        currentRemediation = await res.json();

        const r = currentRemediation;
        document.getElementById('rem-target-concept-title').innerText = `${r.concept_name} (${r.concept_id})`;
        document.getElementById('rem-mastery-badge').innerText = `Mastery: ${Math.round(r.current_mastery * 100)}%`;
        
        if (r.prerequisite_concept_id) {
          document.getElementById('rem-prereq-text').innerText = `Prerequisite Foundation Gap: ${r.prerequisite_concept_name || r.prerequisite_concept_id}`;
          document.getElementById('rem-gap-summary').innerText = r.gap_summary;
        } else {
          document.getElementById('rem-prereq-text').innerText = 'Direct Remediation Focus';
          document.getElementById('rem-gap-summary').innerText = r.gap_summary;
        }

        document.getElementById('rem-ncert-ref').innerText = r.ncert_reference;
        document.getElementById('rem-explanation').innerText = r.explanation;
        document.getElementById('rem-example').innerText = r.example_activity;

        const qCard = document.getElementById('rem-practice-card');
        const optsContainer = document.getElementById('rem-options-container');
        optsContainer.innerHTML = '';

        if (r.practice_question) {
          qCard.classList.remove('hidden');
          const pq = r.practice_question;
          document.getElementById('rem-q-id').innerText = pq.question_id;
          document.getElementById('rem-q-text').innerText = pq.question_text;

          if (pq.options) {
            for (const [key, text] of Object.entries(pq.options)) {
              const card = document.createElement('div');
              card.className = 'option-card p-4 rounded-2xl border-2 border-sandDark bg-sandLight cursor-pointer flex items-center gap-4';
              card.onclick = () => {
                optsContainer.querySelectorAll('.option-card').forEach(el => el.classList.remove('selected'));
                card.classList.add('selected');
                card.dataset.selectedKey = key;
              };
              card.innerHTML = `
                <div class="w-8 h-8 rounded-xl font-bold bg-sandDark text-muted flex items-center justify-center text-sm">
                  ${key}
                </div>
                <div class="text-sm font-medium text-deepPurple flex-1">
                  ${text}
                </div>
              `;
              optsContainer.appendChild(card);
            }
          }
        } else {
          qCard.classList.add('hidden');
        }

        if (window.renderMathInElement) {
          renderMathInElement(document.getElementById('view-remediation'), {
            delimiters: [
              { left: '$$', right: '$$', display: true },
              { left: '$', right: '$', display: false }
            ]
          });
        }

      } catch (err) {
        showToast(err.message, false);
      }
    }

    function loadRemediationForConcept(conceptId) {
      loadRemediationView(conceptId);
    }

    async function submitRemediationPractice() {
      if (!currentRemediation || !currentRemediation.practice_question) return;
      const selected = document.querySelector('#rem-options-container .option-card.selected');
      if (!selected) {
        showToast('Please select an option before submitting.', false);
        return;
      }

      const chosenKey = selected.dataset.selectedKey;
      try {
        const res = await fetch('/api/student/remediation/complete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            remediation_id: currentRemediation.remediation_id,
            student_id: currentStudentId,
            question_id: currentRemediation.practice_question.question_id,
            student_answer: { selected_option: chosenKey }
          })
        });

        if (!res.ok) throw new Error('Remediation submission failed');
        const data = await res.json();

        const fb = document.getElementById('rem-feedback-box');
        fb.classList.remove('hidden');
        if (data.is_correct) {
          fb.className = 'p-5 rounded-2xl border text-sm leading-relaxed space-y-2 bg-green-50 border-green-300 text-green-900';
          fb.innerHTML = `
            <div class="flex items-center gap-2 font-bold text-base text-green-800">
              <span>✓ Remediation Successful!</span>
            </div>
            <p>${data.feedback}</p>
            <p class="text-xs text-green-950 font-bold">Mastery increased from ${Math.round(data.mastery_before * 100)}% to ${Math.round(data.mastery_after * 100)}% (+${Math.round(data.mastery_delta * 100)}%).</p>
            <p class="text-xs text-muted">Next spaced repetition scheduled for: ${new Date(data.next_revision_date).toLocaleDateString()}</p>
          `;
        } else {
          fb.className = 'p-5 rounded-2xl border text-sm leading-relaxed space-y-2 bg-red-50 border-red-300 text-red-900';
          fb.innerHTML = `
            <div class="flex items-center gap-2 font-bold text-base text-red-800">
              <span>✗ Keep Reviewing</span>
            </div>
            <p>${data.feedback}</p>
            <p class="text-xs text-muted">Interval reset to 1 day for reinforcement.</p>
          `;
        }

        document.getElementById('btn-submit-rem').disabled = true;
        showToast('Remediation practice completed!');

      } catch (err) {
        showToast(err.message, false);
      }
    }

    let allRevisionItems = [];

    async function loadRevisionView() {
      switchView('revision');
      try {
        const [dueRes, upRes] = await Promise.all([
          fetch(`/api/student/revision-due?student_id=${currentStudentId}`),
          fetch(`/api/student/revision-upcoming?student_id=${currentStudentId}`)
        ]);

        const dueItems = dueRes.ok ? await dueRes.json() : [];
        const upItems = upRes.ok ? await upRes.json() : [];

        document.getElementById('rev-due-count').innerText = dueItems.length;
        document.getElementById('rev-upcoming-count').innerText = upItems.length;

        allRevisionItems = [...dueItems, ...upItems];
        renderRevisionList(dueItems.length > 0 ? dueItems : upItems);

      } catch (err) {
        showToast(err.message, false);
      }
    }

    function renderRevisionList(items) {
      const container = document.getElementById('revision-items-list');
      container.innerHTML = '';

      if (items.length === 0) {
        container.innerHTML = '<p class="text-sm text-muted text-center py-8">No revision items scheduled. Complete a diagnostic test to auto-schedule concept reviews!</p>';
        return;
      }

      items.forEach(item => {
        const card = document.createElement('div');
        const isDue = (item.review_status === 'DUE' || item.review_status === 'OVERDUE');
        card.className = `p-6 rounded-2xl border-2 bg-sand flex flex-col md:flex-row items-start md:items-center justify-between gap-4 ${isDue ? 'border-errorRed/40 bg-red-50/20' : 'border-sandDark'}`;

        card.innerHTML = `
          <div>
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs font-mono text-muted">${item.concept_id}</span>
              <span class="px-2 py-0.5 rounded-full text-xs font-bold ${isDue ? 'bg-red-100 text-red-800' : 'bg-sandDark text-muted'}">
                ${item.review_status}
              </span>
            </div>
            <h4 class="font-bold text-deepPurple text-lg">${item.concept_name}</h4>
            <div class="flex items-center gap-4 text-xs text-muted mt-2">
              <span>Interval: <strong>${item.interval_days} days</strong></span>
              <span>Reviews Completed: <strong>${item.review_count}</strong></span>
              <span>Current Mastery: <strong>${Math.round(item.current_mastery * 100)}%</strong></span>
            </div>
          </div>
          <div class="flex items-center gap-2 w-full md:w-auto">
            <button onclick="executeRevisionCheck('${item.concept_id}', true)" class="flex-1 md:flex-initial px-4 py-2 rounded-xl bg-successGreen hover:bg-green-700 text-cream font-bold text-xs shadow transition-all">
              Mark Correct
            </button>
            <button onclick="executeRevisionCheck('${item.concept_id}', false)" class="flex-1 md:flex-initial px-4 py-2 rounded-xl bg-sandDark hover:bg-errorRed hover:text-cream text-deepPurple font-bold text-xs transition-all">
              Needs Practice
            </button>
          </div>
        `;
        container.appendChild(card);
      });
    }

    async function executeRevisionCheck(conceptId, isCorrect) {
      try {
        const res = await fetch('/api/student/revision/complete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            student_id: currentStudentId,
            concept_id: conceptId,
            is_correct: isCorrect,
            difficulty_rating: isCorrect ? 'NORMAL' : 'HARD'
          })
        });

        if (!res.ok) throw new Error('Failed to record revision');
        const data = await res.json();
        showToast(data.message, isCorrect);
        loadRevisionView();
      } catch (err) {
        showToast(err.message, false);
      }
    }

    function filterRevisions(type) {
      document.querySelectorAll('.rev-tab-btn').forEach(b => {
        b.classList.remove('bg-deepPurple', 'text-cream');
        b.classList.add('bg-sand', 'text-muted');
      });
      event.target.classList.remove('bg-sand', 'text-muted');
      event.target.classList.add('bg-deepPurple', 'text-cream');

      if (type === 'DUE') {
        const due = allRevisionItems.filter(i => i.review_status === 'DUE' || i.review_status === 'OVERDUE');
        renderRevisionList(due);
      } else {
        const upcoming = allRevisionItems.filter(i => i.review_status === 'PENDING');
        renderRevisionList(upcoming);
      }
    }

    async function loadMisconceptionsView() {
      switchView('misconceptions');
      try {
        const res = await fetch(`/api/student/misconceptions?student_id=${currentStudentId}`);
        if (!res.ok) throw new Error('Failed to load misconceptions');
        const items = await res.json();

        const container = document.getElementById('misconception-items-list');
        container.innerHTML = '';

        if (items.length === 0) {
          container.innerHTML = '<p class="text-sm text-muted text-center py-8">No misconceptions detected! Student demonstrates verified conceptual understanding.</p>';
          return;
        }

        items.forEach(item => {
          const card = document.createElement('div');
          let badgeClass = 'bg-amber-100 text-amber-900 border-amber-300';
          if (item.status === 'CONFIRMED') badgeClass = 'bg-red-100 text-red-900 border-red-300';
          if (item.status === 'RESOLVED') badgeClass = 'bg-green-100 text-green-900 border-green-300';

          card.className = 'bg-sand p-6 rounded-2xl border border-sandDark shadow-sm space-y-3';
          card.innerHTML = `
            <div class="flex items-center justify-between">
              <span class="text-xs font-mono font-bold text-muted">${item.misconception_tag}</span>
              <span class="px-2.5 py-0.5 rounded-full text-xs font-extrabold border ${badgeClass}">
                ${item.status} (Evidence: ${item.evidence_count}x)
              </span>
            </div>
            <h4 class="font-bold text-deepPurple text-lg">${item.concept_name}</h4>
            <div class="bg-sandLight p-3.5 rounded-xl border border-sandDark text-xs text-muted leading-relaxed">
              <span class="font-bold text-deepPurple block mb-1">Diagnostic Evidence:</span>
              ${item.evidence_text || 'Demonstrated conceptual ambiguity on reaction stoichiometry.'}
            </div>
            <div class="flex justify-end pt-1">
              <button onclick="loadRemediationForConcept('${item.concept_id}')" class="text-xs font-bold text-deepPurple hover:underline">
                Resolve via Targeted Remediation &rarr;
              </button>
            </div>
          `;
          container.appendChild(card);
        });

      } catch (err) {
        showToast(err.message, false);
      }
    }

    async function loadTeacherDashboard() {
      switchView('teacher');
      try {
        const [dashRes, stuRes, miscRes] = await Promise.all([
          fetch('/api/teacher/dashboard?role=teacher'),
          fetch('/api/teacher/students?role=teacher'),
          fetch('/api/teacher/misconceptions?role=teacher')
        ]);

        if (!dashRes.ok) throw new Error('Teacher authorization required');
        const dash = await dashRes.json();
        const students = await stuRes.json();
        const miscList = await miscRes.json();

        document.getElementById('t-kpi-students').innerText = dash.total_students;
        document.getElementById('t-kpi-accuracy').innerText = `${Math.round(dash.average_accuracy_pct)}%`;
        document.getElementById('t-kpi-interventions').innerText = dash.students_requiring_intervention.length;

        try {
          const examRes = await fetch('/api/teacher/examinations?role=teacher');
          if (examRes.ok) {
            const es = await examRes.json();
            document.getElementById('t-exam-taken').innerText = es.total_examinations_taken;
            document.getElementById('t-exam-avg-score').innerText = `${es.cohort_average_score} / 80`;
            document.getElementById('t-exam-avg-pct').innerText = `${es.cohort_average_percentage}%`;
            document.getElementById('t-exam-pass-rate').innerText = `${es.pass_rate_percentage}%`;
            document.getElementById('t-exam-high-score').innerText = `${es.highest_score} / 80`;
          }
        } catch (e) {
          console.warn('Teacher exam metrics error:', e);
        }

        const weakContainer = document.getElementById('t-weakest-concepts-list');
        weakContainer.innerHTML = '';
        if (dash.weakest_concepts.length > 0) {
          dash.weakest_concepts.forEach(c => {
            const row = document.createElement('div');
            row.className = 'p-3 rounded-xl bg-sandLight border border-sandDark flex items-center justify-between text-xs';
            row.innerHTML = `
              <div>
                <span class="font-bold text-deepPurple block">${c.concept_name}</span>
                <span class="text-muted">Attempts: ${c.assessed_students}</span>
              </div>
              <span class="font-extrabold text-errorRed">${c.avg_mastery_pct}% avg</span>
            `;
            weakContainer.appendChild(row);
          });
        } else {
          weakContainer.innerHTML = '<p class="text-xs text-muted text-center py-4">No cohort weaknesses below 60%.</p>';
        }

        const miscContainer = document.getElementById('t-common-misc-list');
        miscContainer.innerHTML = '';
        if (miscList.length > 0) {
          miscList.slice(0, 4).forEach(m => {
            const row = document.createElement('div');
            row.className = 'p-3 rounded-xl bg-sandLight border border-sandDark flex items-center justify-between text-xs';
            row.innerHTML = `
              <div>
                <span class="font-bold text-deepPurple block">${m.misconception_tag}</span>
                <span class="text-muted">${m.concept_name || m.concept_id}</span>
              </div>
              <span class="px-2 py-0.5 rounded-full font-bold bg-amber-100 text-amber-800">${m.affected_students} students</span>
            `;
            miscContainer.appendChild(row);
          });
        } else {
          miscContainer.innerHTML = '<p class="text-xs text-muted text-center py-4">No recurring misconceptions found.</p>';
        }

        const tableBody = document.getElementById('t-students-table-body');
        tableBody.innerHTML = '';
        students.forEach(s => {
          const tr = document.createElement('tr');
          tr.className = 'hover:bg-sandLight transition-colors';
          tr.innerHTML = `
            <td class="py-3 px-4 font-mono text-xs text-muted">${s.student_id}</td>
            <td class="py-3 px-4 font-bold text-deepPurple">${s.name}</td>
            <td class="py-3 px-4 font-semibold">${Math.round(s.accuracy_pct)}%</td>
            <td class="py-3 px-4 font-semibold">${Math.round(s.mastery_pct)}%</td>
            <td class="py-3 px-4">
              <span class="px-2.5 py-0.5 rounded-full text-xs font-bold ${s.needs_intervention ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}">
                ${s.needs_intervention ? 'Intervention Needed' : 'On Track'}
              </span>
            </td>
            <td class="py-3 px-4 text-right">
              <button onclick="drilldownStudent('${s.student_id}')" class="font-bold text-deepPurple text-xs hover:underline">
                Drill-Down &rarr;
              </button>
            </td>
          `;
          tableBody.appendChild(tr);
        });

        await loadTeacherActivityFeed();

      } catch (err) {
        showToast(err.message, false);
      }
    }

    async function drilldownStudent(studentId) {
      try {
        const res = await fetch(`/api/teacher/students/${studentId}?role=teacher`);
        if (!res.ok) throw new Error('Failed to load student details');
        const detail = await res.json();

        document.getElementById('t-drill-name').innerText = `${detail.student.name} (${detail.student.student_id})`;

        const notesContainer = document.getElementById('t-drill-notes');
        notesContainer.innerHTML = '';
        detail.intervention_notes.forEach(note => {
          const p = document.createElement('p');
          p.className = 'p-3 rounded-xl bg-sand text-xs text-deepPurple font-medium leading-relaxed border border-sandDark';
          p.innerText = `• ${note}`;
          notesContainer.appendChild(p);
        });

        const miscContainer = document.getElementById('t-drill-misconceptions');
        miscContainer.innerHTML = '';
        if (detail.active_misconceptions.length > 0) {
          detail.active_misconceptions.forEach(m => {
            const p = document.createElement('div');
            p.className = 'p-3 rounded-xl bg-red-50 text-xs text-red-900 border border-red-200';
            p.innerHTML = `<strong>${m.concept_name}:</strong> ${m.misconception_tag} (${m.status})`;
            miscContainer.appendChild(p);
          });
        } else {
          miscContainer.innerHTML = '<p class="text-xs text-muted">No active misconceptions.</p>';
        }

        try {
          const actRes = await fetch(`/api/student/${studentId}/activity?limit=15`);
          const actContainer = document.getElementById('t-drill-activity-list');
          if (actContainer && actRes.ok) {
            const acts = await actRes.json();
            actContainer.innerHTML = '';
            if (acts.length > 0) {
              acts.forEach(a => {
                const row = document.createElement('div');
                row.className = 'p-2.5 rounded-xl bg-sandLight border border-sandDark flex items-center justify-between text-xs';
                const timeStr = new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ', ' + new Date(a.created_at).toLocaleDateString();
                row.innerHTML = `
                  <div>
                    <span class="font-bold text-deepPurple block">${a.action_title}</span>
                    <span class="text-[10px] text-muted">${timeStr}</span>
                  </div>
                  <span class="font-mono text-[9px] px-2 py-0.5 rounded-full bg-white text-deepPurple border border-sandDark uppercase font-bold">${a.event_type.replace(/_/g, ' ')}</span>
                `;
                actContainer.appendChild(row);
              });
            } else {
              actContainer.innerHTML = '<p class="text-xs text-muted text-center py-2">No activity records for this student.</p>';
            }
          }
        } catch (e) {
          console.warn('Drilldown activity warning:', e);
        }

        document.getElementById('t-drilldown-panel').classList.remove('hidden');
        document.getElementById('t-drilldown-panel').scrollIntoView({ behavior: 'smooth' });

      } catch (err) {
        showToast(err.message, false);
      }
    }

    function closeDrilldown() {
      document.getElementById('t-drilldown-panel').classList.add('hidden');
    }

    let conceptGraphData = null;
    let selectedConceptNode = null;

    async function loadConceptGraphView(chapterId = '') {
      switchView('concept-graph');
      const svg = document.getElementById('concept-graph-svg');
      if (svg) svg.innerHTML = '<text x="50%" y="50%" text-anchor="middle" fill="#777487" font-size="14">Loading Concept Dependency DAG...</text>';

      try {
        const url = `/api/concept-graph?student_id=${currentStudentId}${chapterId ? '&chapter_id=' + encodeURIComponent(chapterId) : ''}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error('Failed to load concept graph');
        conceptGraphData = await res.json();
        renderConceptGraphSVG(conceptGraphData);
      } catch (err) {
        if (svg) svg.innerHTML = `<text x="50%" y="50%" text-anchor="middle" fill="#dc2626" font-size="14">${err.message}</text>`;
        showToast(err.message, false);
      }
    }

    function filterConceptGraph(chapterId) {
      loadConceptGraphView(chapterId);
    }

    function renderConceptGraphSVG(data) {
      const svg = document.getElementById('concept-graph-svg');
      if (!svg || !data || !data.nodes || !data.nodes.length) {
        if (svg) svg.innerHTML = '<text x="50%" y="50%" text-anchor="middle" fill="#777487" font-size="14">No concepts found for this selection.</text>';
        return;
      }

      const nodes = data.nodes;
      const edges = data.edges || [];
      const cols = { EASY: [], MEDIUM: [], HARD: [] };
      nodes.forEach(n => {
        const diff = (n.difficulty || 'MEDIUM').toUpperCase();
        if (cols[diff]) cols[diff].push(n);
        else cols['MEDIUM'].push(n);
      });

      const colX = { EASY: 110, MEDIUM: 360, HARD: 610 };
      const nodePositions = {};
      const maxColLen = Math.max(cols.EASY.length, cols.MEDIUM.length, cols.HARD.length, 6);
      const svgHeight = Math.max(500, maxColLen * 68 + 80);
      const svgWidth = 760;

      svg.setAttribute('viewBox', `0 0 ${svgWidth} ${svgHeight}`);
      svg.setAttribute('width', '100%');
      svg.setAttribute('height', svgHeight);

      ['EASY', 'MEDIUM', 'HARD'].forEach(tier => {
        const list = cols[tier];
        const gap = (svgHeight - 80) / Math.max(list.length, 1);
        list.forEach((n, idx) => {
          nodePositions[n.id] = {
            x: colX[tier],
            y: 50 + idx * Math.min(gap, 68),
            data: n
          };
        });
      });

      let svgHTML = `
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#cbd5e1"/>
          </marker>
        </defs>
      `;

      edges.forEach(e => {
        const src = nodePositions[e.source];
        const tgt = nodePositions[e.target];
        if (src && tgt) {
          svgHTML += `<path d="M ${src.x} ${src.y} C ${(src.x + tgt.x)/2} ${src.y}, ${(src.x + tgt.x)/2} ${tgt.y}, ${tgt.x} ${tgt.y}" fill="none" stroke="#cbd5e1" stroke-width="1.8" marker-end="url(#arrow)" />`;
        }
      });

      svgHTML += `
        <text x="110" y="24" text-anchor="middle" font-size="12" font-weight="bold" fill="#7868C7">FOUNDATIONAL (EASY)</text>
        <text x="360" y="24" text-anchor="middle" font-size="12" font-weight="bold" fill="#7868C7">DEVELOPING (MEDIUM)</text>
        <text x="610" y="24" text-anchor="middle" font-size="12" font-weight="bold" fill="#7868C7">ADVANCED (HARD)</text>
      `;

      nodes.forEach(n => {
        const pos = nodePositions[n.id];
        if (!pos) return;
        let color = '#94a3b8';
        if (n.has_misconception || n.status === 'NEEDS_REMEDIATION') {
          color = '#ef4444';
        } else if (n.mastery_score >= 0.8 || n.status === 'MASTERED') {
          color = '#10b981';
        } else if (n.mastery_score >= 0.4 || n.status === 'DEVELOPING') {
          color = '#f59e0b';
        }

        const safeName = n.name.length > 22 ? n.name.substring(0, 20) + '...' : n.name;
        svgHTML += `
          <g class="cursor-pointer group" onclick="selectConceptNode('${n.id}')">
            <rect x="${pos.x - 90}" y="${pos.y - 20}" width="180" height="40" rx="10" fill="#ffffff" stroke="${color}" stroke-width="2.5"/>
            <circle cx="${pos.x - 72}" cy="${pos.y}" r="6" fill="${color}"/>
            <text x="${pos.x - 58}" y="${pos.y + 4}" font-size="11" font-weight="600" fill="#242235">${safeName}</text>
            <text x="${pos.x + 80}" y="${pos.y + 4}" text-anchor="end" font-size="10" font-family="monospace" font-weight="bold" fill="${color}">${Math.round(n.mastery_score * 100)}%</text>
          </g>
        `;
      });

      svg.innerHTML = svgHTML;
    }

    function selectConceptNode(conceptId) {
      if (!conceptGraphData) return;
      const node = conceptGraphData.nodes.find(n => n.id === conceptId);
      if (!node) return;
      selectedConceptNode = node;

      const badge = document.getElementById('cg-status-badge');
      const details = document.getElementById('cg-node-details');
      const actions = document.getElementById('cg-actions');

      let statusColor = 'bg-slate-100 text-slate-700';
      if (node.has_misconception || node.status === 'NEEDS_REMEDIATION') statusColor = 'bg-red-100 text-red-700';
      else if (node.mastery_score >= 0.8) statusColor = 'bg-emerald-100 text-emerald-700';
      else if (node.mastery_score >= 0.4) statusColor = 'bg-amber-100 text-amber-700';

      badge.className = `px-2.5 py-1 rounded-full text-[10px] font-bold ${statusColor}`;
      badge.innerText = node.has_misconception ? 'MISCONCEPTION' : node.status.replace(/_/g, ' ');

      details.innerHTML = `
        <div>
          <span class="text-[10px] font-mono font-bold text-muted uppercase">${node.id} &bull; ${node.chapter_id}</span>
          <h4 class="text-base font-extrabold text-deepPurple">${node.name}</h4>
        </div>
        <p class="text-xs text-muted leading-relaxed">${node.description || 'Core concept node in NCERT Science.'}</p>
        <div class="bg-sandDark/60 p-3 rounded-xl space-y-1 text-xs">
          <div class="flex justify-between"><span class="text-muted">Mastery Score:</span><span class="font-bold font-mono text-deepPurple">${Math.round(node.mastery_score * 100)}%</span></div>
          <div class="flex justify-between"><span class="text-muted">Tier:</span><span class="font-bold text-deepPurple">${node.difficulty}</span></div>
          <div class="flex justify-between"><span class="text-muted">Misconceptions:</span><span class="font-bold ${node.has_misconception ? 'text-errorRed' : 'text-emerald-600'}">${node.has_misconception ? 'Active' : 'None Detected'}</span></div>
        </div>
      `;

      if (actions) actions.classList.remove('hidden');

      const btnAsk = document.getElementById('btn-cg-ask-doubt');
      if (btnAsk) {
        btnAsk.onclick = () => {
          quickAskDoubt(`Can you clarify my doubts and misconceptions about ${node.name}?`);
        };
      }
      const btnRem = document.getElementById('btn-cg-remediate');
      if (btnRem) {
        btnRem.onclick = () => {
          loadAdaptiveQuestion();
        };
      }
    }

    async function sendDoubt() {
      const input = document.getElementById('doubt-input-box');
      const text = input ? input.value.trim() : '';
      if (!text) return;
      input.value = '';

      const feed = document.getElementById('doubt-chat-feed');
      const stuBubble = document.createElement('div');
      stuBubble.className = 'flex items-start justify-end gap-3';
      stuBubble.innerHTML = `
        <div class="bg-deepPurple text-cream p-4 rounded-2xl rounded-tr-none shadow-sm max-w-2xl text-sm leading-relaxed">
          <p class="text-xs font-bold text-brandYellow mb-1">You (Student)</p>
          <p>${text.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</p>
        </div>
        <div class="w-8 h-8 rounded-full bg-brandYellow flex items-center justify-center font-bold text-deepPurple shadow-sm text-xs shrink-0">AS</div>
      `;
      feed.appendChild(stuBubble);
      feed.scrollTop = feed.scrollHeight;

      const thinkBubble = document.createElement('div');
      thinkBubble.className = 'flex items-start gap-3';
      thinkBubble.id = 'bot-thinking-bubble';
      thinkBubble.innerHTML = `
        <div class="w-8 h-8 rounded-full bg-brandYellow flex items-center justify-center font-bold text-deepPurple shadow-sm text-sm shrink-0">ब</div>
        <div class="bg-white p-4 rounded-2xl rounded-tl-none border border-sandDark shadow-sm text-sm text-muted animate-pulse">
          Resolving scientific doubt against NCERT curriculum & checking learner misconceptions...
        </div>
      `;
      feed.appendChild(thinkBubble);
      feed.scrollTop = feed.scrollHeight;

      try {
        const res = await fetch('/api/ai/doubt-solver', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question: text,
            student_id: currentStudentId,
            chapter_id: 'CH-01'
          })
        });
        if (!res.ok) throw new Error('Failed to resolve doubt');
        const data = await res.json();

        thinkBubble.remove();

        const botBubble = document.createElement('div');
        botBubble.className = 'flex items-start gap-3';

        let citationsHTML = '';
        if (data.ncert_citations && data.ncert_citations.length) {
          citationsHTML = `
            <div class="mt-3 pt-3 border-t border-sandDark text-xs text-muted">
              <span class="font-bold text-deepPurple block mb-1">NCERT Textual References:</span>
              ${data.ncert_citations.map(c => `<span class="inline-block bg-sand px-2 py-0.5 rounded mr-1.5 mb-1 font-mono">${c.section} (P.${c.page})</span>`).join('')}
            </div>
          `;
        }

        botBubble.innerHTML = `
          <div class="w-8 h-8 rounded-full bg-brandYellow flex items-center justify-center font-bold text-deepPurple shadow-sm text-sm shrink-0">ब</div>
          <div class="bg-white p-5 rounded-2xl rounded-tl-none border border-sandDark shadow-sm max-w-2xl text-sm leading-relaxed text-ink">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-bold text-deepPurple">BodhAI Science Tutor</span>
              <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-sand font-bold text-muted">${data.model || 'Groq Llama-3.3-70B'}</span>
            </div>
            <div class="space-y-2 whitespace-pre-line">${data.answer}</div>
            ${citationsHTML}
          </div>
        `;
        feed.appendChild(botBubble);
        feed.scrollTop = feed.scrollHeight;

        if (window.renderMathInElement) {
          renderMathInElement(botBubble, {
            delimiters: [
              { left: '$$', right: '$$', display: true },
              { left: '$', right: '$', display: false }
            ]
          });
        }
      } catch (err) {
        thinkBubble.remove();
        showToast(err.message, false);
      }
    }

    function quickAskDoubt(questionText) {
      switchView('doubt-solver');
      const input = document.getElementById('doubt-input-box');
      if (input) input.value = questionText;
      sendDoubt();
    }

    function logoutUser() {
      try {
        localStorage.clear();
        sessionStorage.clear();
      } catch (e) {}
      window.location.replace('/login?logout=1');
    }

    window.addEventListener('DOMContentLoaded', () => {
      const stored = localStorage.getItem('bodhai_user');
      if (!stored) {
        window.location.replace('/login');
        return;
      }

      initAuthSession();

      const currentPath = window.location.pathname.toLowerCase().replace(/\/$/, '');
      if (currentPath === '/diagnostic') {
        startDiagnosticTest();
      } else if (currentPath === '/exam' || currentPath === '/board-exam' || currentPath === '/examination-hub') {
        switchView('examination-hub');
      } else if (currentPath === '/mastery') {
        switchView('mastery');
      } else if (currentPath === '/practice' || currentPath === '/adaptive') {
        loadAdaptiveQuestion();
      } else if (currentPath === '/remediation') {
        loadRemediationView();
      } else if (currentPath === '/revision') {
        loadRevisionView();
      } else if (currentPath === '/misconceptions') {
        loadMisconceptionsView();
      } else if (currentPath === '/concept-graph') {
        loadConceptGraphView();
      } else if (currentPath === '/doubt-solver') {
        switchView('doubt-solver');
      } else if (currentPath === '/teacher') {
        window.location.replace('/teacher');
      } else {
        loadDashboard();
      }
      trackStudentActivity('VIEW_DASHBOARD', 'Active Session Initialized');
    });

    window.addEventListener('popstate', () => {
      const p = window.location.pathname.toLowerCase().replace(/\/$/, '');
      if (p === '/diagnostic') switchView('assessment');
      else if (p === '/exam' || p === '/board-exam' || p === '/examination-hub') switchView('examination-hub');
      else if (p === '/mastery') switchView('mastery');
      else if (p === '/practice' || p === '/adaptive') loadAdaptiveQuestion();
      else if (p === '/remediation') loadRemediationView();
      else if (p === '/revision') loadRevisionView();
      else if (p === '/misconceptions') loadMisconceptionsView();
      else if (p === '/concept-graph') loadConceptGraphView();
      else if (p === '/doubt-solver') switchView('doubt-solver');
      else if (p === '/teacher') window.location.replace('/teacher');
      else loadDashboard();
    });
