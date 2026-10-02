from flask import Flask, render_template, request, jsonify
import sqlite3, json, urllib.request
from datetime import datetime

app = Flask(__name__)
DB = 'student_success.db'


def init_db():
    with sqlite3.connect(DB) as c:
        c.execute('''CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, attendance REAL, cgpa REAL, weak_subject TEXT,
            study_hours REAL, created_at TEXT)''')
        c.commit()


def analyze(att, cgpa, weak, hours):
    score = round(min(100, max(0, att * 0.35 + cgpa * 10 * 0.45 + min(hours, 6) / 6 * 100 * 0.20)))
    priority = 'High' if score < 60 or att < 75 or cgpa < 6 else ('Medium' if score < 75 or att < 85 or cgpa < 7.5 else 'Low')
    risk = 'Needs attention' if priority == 'High' else ('On track' if priority == 'Medium' else 'Strong position')
    recs = []
    if att < 75:
        recs.append(('Attendance', 'Prioritize classes and avoid unnecessary absences.', 'urgent'))
    elif att < 85:
        recs.append(('Attendance', f'Your {att:.1f}% attendance is workable. Aim for an 85%+ safety margin.', 'focus'))
    else:
        recs.append(('Attendance', 'Your attendance is in a healthy range. Keep it consistent.', 'good'))
    if cgpa < 6:
        recs.append(('Academics', 'Strengthen core concepts, class notes, and previous exam questions.', 'urgent'))
    elif cgpa < 7.5:
        recs.append(('Academics', 'Prioritize weaker subjects and practice previous exam questions regularly.', 'focus'))
    else:
        recs.append(('Academics', 'Maintain your performance while adding advanced topics and projects.', 'good'))
    weak_name = weak or 'your weakest subject'
    recs.append(('Weak subject', f'Give extra attention to {weak_name}; start with its hardest topics.', 'focus'))
    if hours < 2:
        recs.append(('Study routine', 'Build toward at least 2 focused hours a day using short sessions.', 'urgent'))
    elif hours < 4:
        recs.append(('Study routine', 'A consistent 3–4 hour focused routine can create steady progress.', 'focus'))
    else:
        recs.append(('Study routine', 'Your study-time target is strong. Use breaks to protect focus.', 'good'))

    plan = [
        ('MON', 'Concept Sprint', f'Learn the core concepts of {weak_name}. Finish one small topic.', 60, 'Learn'),
        ('TUE', 'Practice Lab', 'Solve 10–15 questions and write down every mistake.', 60, 'Practice'),
        ('WED', 'Recall Day', 'Close your notes and create a one-page summary from memory.', 45, 'Recall'),
        ('THU', 'Exam Mode', 'Attempt previous exam questions under a timer.', 60, 'Test'),
        ('FRI', 'Gap Fix', 'Review mistakes and relearn the two weakest areas.', 45, 'Improve'),
        ('SAT', 'Mock Sprint', 'Take a short mock test, check answers, and track accuracy.', 75, 'Measure'),
        ('SUN', 'Reset & Plan', 'Review the week and choose the next seven-day priority.', 30, 'Plan'),
    ]
    study_pct = round(min(hours / 6 * 100, 100))
    return score, priority, risk, recs, plan, study_pct


@app.route('/')
def home():
    return render_template('index.html')


@app.post('/api/analyze')
def api_analyze():
    try:
        d = request.get_json(force=True)
        name = (d.get('name') or 'Student').strip() or 'Student'
        att = float(d['attendance'])
        cgpa = float(d['cgpa'])
        weak = (d.get('weak_subject') or '').strip()
        hours = float(d['study_hours'])
        if not (0 <= att <= 100 and 0 <= cgpa <= 10 and 0 <= hours <= 24):
            raise ValueError('Please enter valid values.')
        score, priority, risk, recs, plan, study_pct = analyze(att, cgpa, weak, hours)
        with sqlite3.connect(DB) as c:
            c.execute('INSERT INTO students(name,attendance,cgpa,weak_subject,study_hours,created_at) VALUES(?,?,?,?,?,?)',
                      (name, att, cgpa, weak, hours, datetime.now().isoformat(timespec='seconds')))
            c.commit()
        return jsonify(name=name, attendance=att, cgpa=cgpa, weak_subject=weak,
                       study_hours=hours, score=score, priority=priority, risk=risk,
                       recommendations=recs, plan=plan, study_pct=study_pct)
    except Exception as e:
        return jsonify(error=str(e)), 400


@app.post('/api/coach')
def coach():
    d = request.get_json(force=True)
    q = (d.get('question') or '').strip()
    p = d.get('profile') or {}
    if not q:
        return jsonify(answer='Ask me about your study plan, subjects, exams, or time management.', source='local coach')
    prompt = f'''You are a concise college study coach. Student profile: attendance={p.get('attendance')}%, CGPA={p.get('cgpa')}/10, weak subject={p.get('weak_subject')}, study hours={p.get('study_hours')}/day. Question: {q}. Give practical, specific advice in 4-6 short bullets. Do not invent academic facts.''' 
    try:
        body = json.dumps({'model': 'qwen3:8b', 'prompt': prompt, 'stream': False}).encode()
        req = urllib.request.Request('http://127.0.0.1:11434/api/generate', data=body, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=12) as r:
            out = json.loads(r.read().decode()).get('response', '').strip()
        if out:
            return jsonify(answer=out, source='Ollama • Qwen 3 8B')
    except Exception:
        pass
    weak = p.get('weak_subject') or 'your weakest subject'
    return jsonify(answer=f'''Start with {weak} for your first focused session.\nBreak the topic into one small concept at a time.\nSolve practice questions immediately after learning it.\nKeep a mistake list and review it before the next session.\nEnd the day by writing your next two tasks.''', source='Built-in study coach')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
