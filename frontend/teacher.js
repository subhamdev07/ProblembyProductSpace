let teacherData = null;

async function loadTeacherDashboard() {
  try {
    const res = await fetch('/api/teacher/dashboard?role=teacher', {
      headers: { 'X-Role': 'teacher' }
    });
    if (!res.ok) throw new Error('Educator authorization failed.');
    teacherData = await res.json();
    renderTeacherKPIs(teacherData);
    renderCohortAnalytics(teacherData);
    renderStudentsRoster(teacherData.students || []);
    loadTeacherActivityFeed();
    loadTeacherExamMetrics();
  } catch (err) {
    showToast(err.message, false);
  }
}

async function loadTeacherExamMetrics() {
  try {
    const res = await fetch('/api/teacher/examinations?role=teacher', {
      headers: { 'X-Role': 'teacher' }
    });
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById('t-exam-taken').innerText = data.total_examinations_taken || 0;
    document.getElementById('t-exam-avg-score').innerText = `${Math.round(data.average_score_marks || 0)} / 80`;
    document.getElementById('t-exam-avg-pct').innerText = `${Math.round(data.average_percentage || 0)}%`;
    document.getElementById('t-exam-pass-rate').innerText = `${Math.round(data.pass_rate_percentage || 0)}%`;
    document.getElementById('t-exam-high-score').innerText = `${data.highest_score_marks || 0} / 80`;
  } catch (e) {
    console.warn('Teacher exam metrics load error:', e);
  }
}

function renderTeacherKPIs(data) {
  document.getElementById('t-kpi-students').innerText = data.total_students || 3;
  const acc = data.average_accuracy_pct !== undefined ? data.average_accuracy_pct : (data.class_average_accuracy || 0) * 100;
  document.getElementById('t-kpi-accuracy').innerText = `${Math.round(acc)}%`;
  document.getElementById('t-kpi-interventions').innerText = (data.students_requiring_intervention ? data.students_requiring_intervention.length : 0);
}

function renderCohortAnalytics(data) {
  const weakContainer = document.getElementById('t-weakest-concepts-list');
  weakContainer.innerHTML = '';
  if (data.weakest_concepts && data.weakest_concepts.length) {
    data.weakest_concepts.forEach(c => {
      const el = document.createElement('div');
      el.className = 'flex items-center justify-between p-3 rounded-2xl bg-white border border-sandDark';
      const mVal = c.avg_mastery_pct !== undefined ? c.avg_mastery_pct : (c.average_mastery || 0) * 100;
      el.innerHTML = `
        <div>
          <span class="font-bold text-deepPurple block text-sm">${c.concept_name}</span>
          <span class="text-xs text-muted">${c.chapter_id || 'CH-01'} &bull; ${c.student_count || c.assessed_students || 1} students struggling</span>
        </div>
        <div class="text-right">
          <span class="text-sm font-bold text-errorRed">${Math.round(mVal)}%</span>
          <span class="text-[10px] text-muted block">Mastery</span>
        </div>
      `;
      weakContainer.appendChild(el);
    });
  } else {
    weakContainer.innerHTML = '<p class="text-xs text-muted text-center py-4">No critical cohort weaknesses flagged.</p>';
  }

  const miscContainer = document.getElementById('t-common-misc-list');
  miscContainer.innerHTML = '';
  if (data.common_misconceptions && data.common_misconceptions.length) {
    data.common_misconceptions.forEach(m => {
      const el = document.createElement('div');
      el.className = 'p-3 rounded-2xl bg-white border border-sandDark space-y-1';
      el.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-deepPurple">${m.concept_name}</span>
          <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-100 text-errorRed">${m.frequency || m.affected_students || 1} Occurrences</span>
        </div>
        <p class="text-xs text-muted">${m.description}</p>
      `;
      miscContainer.appendChild(el);
    });
  } else {
    miscContainer.innerHTML = '<p class="text-xs text-muted text-center py-4">No systemic misconceptions detected.</p>';
  }
}

function renderStudentsRoster(students) {
  const tbody = document.getElementById('t-students-table-body');
  tbody.innerHTML = '';

  if (!students || students.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-xs text-muted">No students enrolled yet.</td></tr>';
    return;
  }

  students.forEach(s => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-sandLight transition-colors';

    const masteryVal = s.mastery !== undefined ? (s.mastery > 1 ? s.mastery / 100 : s.mastery) : 0;
    const accVal = s.accuracy !== undefined ? (s.accuracy > 1 ? s.accuracy / 100 : s.accuracy) : (s.accuracy_pct ? s.accuracy_pct / 100 : 0);

    let statusBadge = '<span class="px-2 py-1 rounded-full text-xs font-bold bg-green-100 text-green-700">On Track</span>';
    if (s.status === 'Needs Support' || masteryVal < 0.4 || (s.misconceptions_count && s.misconceptions_count > 0)) {
      statusBadge = '<span class="px-2 py-1 rounded-full text-xs font-bold bg-red-100 text-red-700">Needs Support</span>';
    } else if (s.status === 'Developing' || masteryVal < 0.7) {
      statusBadge = '<span class="px-2 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-700">Developing</span>';
    }

    tr.innerHTML = `
      <td class="py-3 px-4 font-mono font-bold text-deepPurple text-xs">${s.student_id}</td>
      <td class="py-3 px-4 font-bold text-deepPurple">${s.name}</td>
      <td class="py-3 px-4 font-mono font-bold">${Math.round(accVal * 100)}%</td>
      <td class="py-3 px-4 font-mono font-bold">${Math.round(masteryVal * 100)}%</td>
      <td class="py-3 px-4">${statusBadge}</td>
      <td class="py-3 px-4 text-right">
        <button onclick="inspectStudent('${s.student_id}')" class="px-3 py-1.5 rounded-xl bg-deepPurple text-cream text-xs font-bold hover:bg-deepPurpleHover transition-all">
          Inspect
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function inspectStudent(studentId) {
  try {
    const res = await fetch(`/api/teacher/students/${studentId}?role=teacher`, {
      headers: { 'X-Role': 'teacher' }
    });
    if (!res.ok) throw new Error('Failed to fetch student details');
    const student = await res.json();

    const sName = (student.student && student.student.name) || student.name || 'Student';
    const sId = (student.student && student.student.student_id) || student.student_id || studentId;
    document.getElementById('t-drill-name').innerText = `${sName} (${sId})`;

    const notesContainer = document.getElementById('t-drill-notes');
    notesContainer.innerHTML = '';
    if (student.intervention_notes && student.intervention_notes.length) {
      student.intervention_notes.forEach(note => {
        const el = document.createElement('div');
        el.className = 'p-3 rounded-xl bg-sand border border-sandDark text-xs text-deepPurple font-medium';
        el.innerText = note;
        notesContainer.appendChild(el);
      });
    } else {
      notesContainer.innerHTML = '<p class="text-xs text-muted">No urgent teacher interventions required.</p>';
    }

    const miscContainer = document.getElementById('t-drill-misconceptions');
    miscContainer.innerHTML = '';
    if (student.active_misconceptions && student.active_misconceptions.length) {
      student.active_misconceptions.forEach(m => {
        const el = document.createElement('div');
        el.className = 'p-3 rounded-xl bg-red-50 border border-red-200 text-xs space-y-1';
        el.innerHTML = `
          <span class="font-bold text-errorRed block">${m.concept_name || 'Concept Error'}</span>
          <p class="text-ink">${m.description || m.misconception_tag || 'Misconception'}</p>
        `;
        miscContainer.appendChild(el);
      });
    } else {
      miscContainer.innerHTML = '<p class="text-xs text-muted">Zero active misconceptions recorded.</p>';
    }

    try {
      const actRes = await fetch(`/api/student/${studentId}/activity?limit=15`);
      if (actRes.ok) {
        const actData = await actRes.json();
        const actContainer = document.getElementById('t-drill-activity-list');
        if (actContainer) {
          actContainer.innerHTML = '';
          const activities = Array.isArray(actData) ? actData : (actData.activities || []);
          if (activities && activities.length) {
            activities.forEach(a => {
              const row = document.createElement('div');
              row.className = 'p-2.5 rounded-xl bg-sand border border-sandDark flex items-center justify-between text-xs';
              const timeStr = a.created_at ? new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
              row.innerHTML = `
                <div>
                  <span class="font-bold text-deepPurple block">${a.action_title}</span>
                  <span class="text-[10px] text-muted">${timeStr}</span>
                </div>
                <span class="font-mono text-[10px] bg-white px-2 py-0.5 rounded border border-sandDark">${a.event_type}</span>
              `;
              actContainer.appendChild(row);
            });
          } else {
            actContainer.innerHTML = '<p class="text-xs text-muted py-2">No recent telemetry logs.</p>';
          }
        }
      }
    } catch (e) {
      console.warn('Activity timeline error:', e);
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

async function loadTeacherActivityFeed() {
  try {
    const res = await fetch('/api/teacher/activity-stream?limit=30&role=teacher', {
      headers: { 'X-Role': 'teacher' }
    });
    if (!res.ok) return;
    const activities = await res.json();
    const container = document.getElementById('t-activity-feed-list');
    if (!container) return;
    container.innerHTML = '';

    if (!activities.length) {
      container.innerHTML = '<p class="text-xs text-muted text-center py-4">No live classroom telemetry recorded yet.</p>';
      return;
    }

    activities.forEach(a => {
      const item = document.createElement('div');
      item.className = 'flex items-start justify-between p-3 rounded-2xl bg-white border border-sandDark text-xs';
      const timeStr = a.created_at ? new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
      item.innerHTML = `
        <div class="space-y-0.5">
          <div class="flex items-center gap-2">
            <span class="font-bold text-deepPurple">${a.student_id}</span>
            <span class="text-sandDark">&bull;</span>
            <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-sand font-bold text-muted">${a.event_type}</span>
          </div>
          <p class="text-ink font-medium">${a.action_title}</p>
        </div>
        <span class="text-[10px] text-muted shrink-0">${timeStr}</span>
      `;
      container.appendChild(item);
    });
  } catch (err) {
    console.warn('Activity feed load error:', err);
  }
}

function showToast(msg, isSuccess = true) {
  const toast = document.getElementById('toast');
  const msgEl = document.getElementById('toast-msg');
  msgEl.innerText = msg;
  toast.className = `fixed top-6 right-6 z-50 px-5 py-3 rounded-xl shadow-lg flex items-center gap-3 text-sm font-medium transition-all ${
    isSuccess ? 'bg-deepPurple text-cream' : 'bg-errorRed text-white'
  }`;
  toast.classList.remove('hidden');
  setTimeout(() => toast.classList.add('hidden'), 3500);
}

function logoutTeacher() {
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
  try {
    const user = JSON.parse(stored);
    if (user.role !== 'teacher') {
      window.location.replace('/dashboard');
      return;
    }
  } catch (e) {
    window.location.replace('/login');
    return;
  }
  loadTeacherDashboard();
});
