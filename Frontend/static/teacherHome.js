// teacherHome.js - localStorage-based simple class/student manager
const STORAGE_KEY = "teacher_home_local_v1";
let classes = [];
let currentClassId = null;

function saveToStorage(){ try{ localStorage.setItem(STORAGE_KEY, JSON.stringify(classes)); }catch(e){console.error(e);} }
function loadFromStorage(){ try{ const raw = localStorage.getItem(STORAGE_KEY); classes = raw ? JSON.parse(raw) : []; }catch(e){ classes = []; } }
function generateId(prefix=''){ return (prefix ? prefix + '_' : '') + Math.random().toString(36).slice(2,9); }
function notify(msg, type='success'){ const c = document.getElementById('notif-container'); if(!c) return; const n = document.createElement('div'); n.className = 'notification' + (type==='error'?' error':''); n.textContent = msg; c.appendChild(n); setTimeout(()=>{ try{ n.remove(); }catch(e){} }, 3000); }
function escapeHtml(s){ if(s===null||s===undefined) return ''; return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;'); }

function computeAverage(grades){
  const a = grades && grades.attendance !== '' ? Number(grades.attendance) : 0;
  const m = grades && grades.mid !== '' ? Number(grades.mid) : 0;
  const f = grades && grades.final !== '' ? Number(grades.final) : 0;
  const avg = (a*0.2) + (m*0.3) + (f*0.5);
  return Math.round(avg*10)/10;
}

function renderClassCards(){
  const grid = document.getElementById('classes-grid'); if(!grid) return;
  if(!classes.length){ grid.innerHTML = '<div class="create-class-form" style="padding:1rem;"><em>Chưa có lớp học. Hãy tạo lớp mới.</em></div>'; return; }
  grid.innerHTML = classes.map(c => `
    <div class="class-card" data-id="${c.id}" onclick="openClassModal('${c.id}')">
      <h3>${escapeHtml(c.className)}</h3>
      <div class="class-meta"><strong>Mã lớp:</strong> ${escapeHtml(c.classCode)}</div>
      <div class="class-meta"><strong>SV:</strong> ${(c.students||[]).length} / ${c.maxStudents}</div>
    </div>
  `).join('');
}

function renderStudentTable(){
  const tbody = document.getElementById('student-tbody'); if(!tbody) return;
  const cls = classes.find(x=>x.id===currentClassId);
  if(!cls){ tbody.innerHTML = '<tr><td colspan="9">Lớp không tồn tại</td></tr>'; return; }
  const students = cls.students || [];
  if(!students.length){ tbody.innerHTML = '<tr><td colspan="9"><em>Chưa có sinh viên trong lớp.</em></td></tr>'; return; }
  tbody.innerHTML = students.map((s, idx) => {
    const att = s.grades && s.grades.attendance !== undefined ? s.grades.attendance : '';
    const mid = s.grades && s.grades.mid !== undefined ? s.grades.mid : '';
    const fin = s.grades && s.grades.final !== undefined ? s.grades.final : '';
    const avg = (att === '' && mid === '' && fin === '') ? '-' : computeAverage(s.grades);
    return `<tr data-stu-id="${s.id}">
      <td style="text-align:center;"><input type="checkbox" class="select-stu" data-id="${s.id}" onchange="onSelectChanged()"></td>
      <td>${idx+1}</td>
      <td>${escapeHtml(s.name)}</td>
      <td>${escapeHtml(s.studentId)}</td>
      <td><input class="input-grade" data-field="attendance" value="${att}" onchange="onGradeEdit('${s.id}', this)"></td>
      <td><input class="input-grade" data-field="mid" value="${mid}" onchange="onGradeEdit('${s.id}', this)"></td>
      <td><input class="input-grade" data-field="final" value="${fin}" onchange="onGradeEdit('${s.id}', this)"></td>
      <td>${avg}</td>
      <td><button class="create-btn small danger" onclick="removeStudent('${s.id}')">Xóa</button></td>
    </tr>`;
  }).join('');
}

function addClass(className, classCode, maxStudents){
  if(classes.some(c=>c.classCode===classCode)){ notify('Mã lớp đã tồn tại','error'); return false; }
  const obj = { id: generateId('class'), className, classCode, maxStudents: Number(maxStudents)||0, students: [], createdAt: new Date().toISOString() };
  classes.unshift(obj); saveToStorage(); renderClassCards(); notify('Tạo lớp thành công'); return true;
}

function openClassModal(classId){
  const cls = classes.find(x=>x.id===classId); if(!cls){ notify('Lớp không tìm thấy','error'); return; }
  currentClassId = classId;
  document.getElementById('modal-class-name').textContent = cls.className;
  document.getElementById('modal-class-code').textContent = cls.classCode;
  document.getElementById('modal-count').textContent = (cls.students||[]).length;
  document.getElementById('modal-max').textContent = cls.maxStudents;
  document.getElementById('student-name').value = '';
  document.getElementById('student-id').value = '';
  document.getElementById('add-student-warning').textContent = '';
  document.getElementById('select-all').checked = false;
  renderStudentTable();
  document.getElementById('class-modal').classList.remove('hidden');
}
function closeModal(){ currentClassId = null; document.getElementById('class-modal').classList.add('hidden'); }

function addStudentToCurrent(name, studentId){
  const cls = classes.find(x=>x.id===currentClassId); if(!cls){ notify('Chưa chọn lớp','error'); return; }
  if(!name || !studentId){ document.getElementById('add-student-warning').textContent = 'Vui lòng nhập họ tên và mã SV.'; return; }
  if((cls.students||[]).length >= Number(cls.maxStudents)){ document.getElementById('add-student-warning').textContent = 'Đã đạt tối đa sinh viên của lớp.'; return; }
  if((cls.students||[]).some(s=>s.studentId===studentId)){ document.getElementById('add-student-warning').textContent = 'Mã SV đã tồn tại trong lớp.'; return; }
  const student = { id: generateId('stu'), name, studentId, grades:{ attendance:'', mid:'', final:'' }, createdAt: new Date().toISOString() };
  cls.students.push(student); saveToStorage(); renderStudentTable(); document.getElementById('modal-count').textContent = cls.students.length; renderClassCards(); notify('Thêm sinh viên thành công'); document.getElementById('add-student-warning').textContent=''; }

function removeStudent(studentId){
  if(!currentClassId) return;
  const cls = classes.find(x=>x.id===currentClassId); if(!cls) return;
  const idx = (cls.students||[]).findIndex(s=>s.id===studentId); if(idx===-1){ notify('Sinh viên không tồn tại','error'); return; }
  if(!confirm('Bạn có chắc muốn xóa sinh viên này?')) return;
  cls.students.splice(idx,1); saveToStorage(); renderStudentTable(); document.getElementById('modal-count').textContent = (cls.students||[]).length; renderClassCards(); notify('Đã xóa sinh viên'); }

function onGradeEdit(studentId, inputElem){
  const field = inputElem.getAttribute('data-field'); if(!field) return;
  const raw = inputElem.value.trim(); if(raw===''){ updateStudentGrade(studentId, field, ''); return; }
  const num = Number(raw); if(Number.isNaN(num)){ inputElem.value=''; return; }
  const clamped = Math.max(0, Math.min(10, Math.round(num*10)/10)); inputElem.value = clamped;
  updateStudentGrade(studentId, field, clamped);
}
function updateStudentGrade(studentId, field, value){
  const cls = classes.find(x=>x.id===currentClassId); if(!cls) return;
  const student = (cls.students||[]).find(s=>s.id===studentId); if(!student) return;
  student.grades = student.grades || { attendance:'', mid:'', final:'' };
  student.grades[field] = value === '' ? '' : Number(value);
  saveToStorage(); renderStudentTable(); renderClassCards();
}

// Import/export CSV (simple)
function triggerImport(){ document.getElementById('import-file').click(); }
function importCSV(ev){
  const file = ev.target.files && ev.target.files[0]; if(!file) return;
  const reader = new FileReader(); reader.onload = function(e){
    const text = e.target.result; const rows = parseCSV(text);
    const cls = classes.find(x=>x.id===currentClassId); if(!cls){ notify('Lớp không tồn tại','error'); return; }
    let added=0, skipped=0;
    rows.forEach(r=>{
      const name = r.name || r['Họ tên'] || r['name'] || ''; const sid = r.studentId || r['Mã SV'] || r['studentId'] || '';
      if(!name || !sid){ skipped++; return; }
      if((cls.students||[]).some(s=>s.studentId===sid)){ skipped++; return; }
      if((cls.students||[]).length >= cls.maxStudents){ skipped++; return; }
      const att = r.attendance || r['attendance'] || ''; const mid = r.mid || r['mid'] || ''; const fin = r.final || r['final'] || '';
      const student = { id: generateId('stu'), name, studentId: sid, grades: { attendance: att===''? '': Math.max(0,Math.min(10,Number(att))), mid: mid===''? '': Math.max(0,Math.min(10,Number(mid))), final: fin===''? '': Math.max(0,Math.min(10,Number(fin))) } };
      cls.students.push(student); added++;
    });
    saveToStorage(); renderStudentTable(); renderClassCards(); notify(`Import xong: thêm ${added}, bỏ ${skipped}`); ev.target.value=''; };
  reader.readAsText(file,'utf-8');
}
function parseCSV(text){
  const lines = text.split(/\r?\n/).map(l=>l.trim()).filter(l=>l!==''); if(!lines.length) return [];
  const headers = lines[0].split(',').map(h=>h.replace(/^"|"$/g,'').trim());
  const rows = [];
  for(let i=1;i<lines.length;i++){
    const cols = lines[i].split(',').map(c=>c.replace(/^"|"$/g,'').trim());
    const obj = {}; headers.forEach((h,idx)=> obj[h]= cols[idx] !== undefined ? cols[idx] : '');
    rows.push(obj);
  }
  return rows;
}
function exportCSV(){
  const cls = classes.find(x=>x.id===currentClassId); if(!cls){ notify('Lớp ko tồn tại','error'); return; }
  const header = ['name','studentId','attendance','mid','final','average']; const lines = [header.join(',')];
  (cls.students||[]).forEach(s=>{
    const att = s.grades && s.grades.attendance !== undefined ? s.grades.attendance : ''; const mid = s.grades && s.grades.mid !== undefined ? s.grades.mid : ''; const fin = s.grades && s.grades.final !== undefined ? s.grades.final : '';
    const avg = (att==='' && mid==='' && fin==='') ? '' : computeAverage(s.grades);
    const row = [`"${(s.name||'').replace(/"/g,'""')}"`, `"${(s.studentId||'').replace(/"/g,'""')}"`, att, mid, fin, avg].join(',');
    lines.push(row);
  });
  const csv = lines.join('\n'); const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' }); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = (cls.classCode||cls.className||'class') + '_students.csv'; document.body.appendChild(a); a.click(); a.remove(); notify('Export CSV đã tải về');
}

function toggleSelectAll(el){ const ch = !!el.checked; document.querySelectorAll('.select-stu').forEach(cb=>cb.checked=ch); }
function onSelectChanged(){ const all = Array.from(document.querySelectorAll('.select-stu')); const selAll = document.getElementById('select-all'); if(!all.length) return; selAll.checked = all.every(cb=>cb.checked); }
function deleteSelectedStudents(){ const cls = classes.find(x=>x.id===currentClassId); if(!cls) return; const checked = Array.from(document.querySelectorAll('.select-stu')).filter(cb=>cb.checked).map(cb=>cb.getAttribute('data-id')); if(!checked.length){ notify('Chưa chọn SV nào','error'); return; } if(!confirm('Xóa các sinh viên đã chọn?')) return; cls.students = (cls.students||[]).filter(s=>!checked.includes(s.id)); saveToStorage(); renderStudentTable(); renderClassCards(); notify('Đã xóa sinh viên đã chọn'); }

function confirmDeleteClass(){ if(!currentClassId) return; const cls = classes.find(x=>x.id===currentClassId); if(!cls) return; if(!confirm(`Xóa lớp "${cls.className}"?`)) return; classes = classes.filter(c=>c.id!==currentClassId); saveToStorage(); closeModal(); renderClassCards(); notify('Đã xóa lớp'); }

// init
document.addEventListener('DOMContentLoaded', ()=>{
  loadFromStorage(); renderClassCards();
  const form = document.getElementById('create-class-form'); if(form) form.addEventListener('submit', (e)=>{ e.preventDefault(); const name = document.getElementById('class-name').value.trim(); const code = document.getElementById('class-code').value.trim(); const max = Number(document.getElementById('max-students').value) || 0; if(!name||!code||max<=0){ notify('Vui lòng nhập đầy đủ thông tin lớp hợp lệ','error'); return; } addClass(name,code,max); form.reset(); });
  const addBtn = document.getElementById('add-student-btn'); if(addBtn) addBtn.addEventListener('click', (ev)=>{ ev.preventDefault(); const name = document.getElementById('student-name').value.trim(); const sid = document.getElementById('student-id').value.trim(); addStudentToCurrent(name,sid); });
});

function logout(){ try{ localStorage.removeItem('token'); }catch(e){} window.location.href='/login'; }
