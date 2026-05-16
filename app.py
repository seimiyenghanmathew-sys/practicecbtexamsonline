from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
import sqlite3, os, random, string, csv, io
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'leesmart2026secretkey'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'gif'}

SUBJECTS = [
    "English", "Accounting", "Agricultural Science", "Arabic", "Art",
    "Biology", "Chemistry", "Christian Religious Studies", "Commerce", "Economics",
    "French", "Geography", "Government", "Hausa", "History",
    "Home Economics", "Igbo", "Islamic Religious Studies", "Literature in English", "Mathematics",
    "Music", "Physical and Health Education", "Physics", "Principles of Accounts", "Yoruba"
]

def get_db():
    db = sqlite3.connect('cbt.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            email TEXT,
            phone TEXT,
            receipt TEXT,
            reg_no TEXT UNIQUE NOT NULL,
            login_code TEXT,
            payment_status TEXT DEFAULT 'Pending',
            sub1 TEXT,
            sub2 TEXT,
            sub3 TEXT
        );
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            question TEXT NOT NULL,
            A TEXT, B TEXT, C TEXT, D TEXT,
            answer TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            score REAL,
            answers TEXT,
            submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    ''')
    db.commit()
    db.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def gen_reg_no():
    chars = string.ascii_uppercase + string.digits
    return 'CANDMOCK' + ''.join(random.choices(chars, k=6))

def gen_login_code():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=6))

# ─── HOME ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

# ─── REGISTRATION ───────────────────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        age = request.form.get('age','').strip()
        email = request.form.get('email','').strip()
        phone = request.form.get('phone','').strip()
        subjects = request.form.getlist('subjects')

        # Validate
        if not name or not phone:
            flash('Name and Phone are required.', 'error')
            return render_template('register.html', subjects=SUBJECTS)

        # English always included
        if 'English' not in subjects:
            subjects.insert(0, 'English')
        other = [s for s in subjects if s != 'English']
        if len(other) != 3:
            flash('You must select exactly 3 subjects in addition to English.', 'error')
            return render_template('register.html', subjects=SUBJECTS)

        # Receipt upload
        receipt_filename = None
        if 'receipt' in request.files:
            file = request.files['receipt']
            if file and file.filename and allowed_file(file.filename):
                receipt_filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename))

        reg_no = gen_reg_no()
        db = get_db()
        # Ensure unique
        while db.execute('SELECT id FROM users WHERE reg_no=?', (reg_no,)).fetchone():
            reg_no = gen_reg_no()

        db.execute('''INSERT INTO users (name,age,email,phone,receipt,reg_no,payment_status,sub1,sub2,sub3)
                      VALUES (?,?,?,?,?,?,?,?,?,?)''',
                   (name, age or None, email, phone, receipt_filename, reg_no, 'Pending',
                    other[0], other[1], other[2]))
        db.commit()
        db.close()
        return render_template('reg_success.html', reg_no=reg_no, name=name)

    return render_template('register.html', subjects=SUBJECTS)

# ─── CANDIDATE LOGIN ─────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        reg_no = request.form.get('reg_no','').strip().upper()
        login_code = request.form.get('login_code','').strip().upper()
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE reg_no=? AND login_code=?', (reg_no, login_code)).fetchone()
        db.close()
        if user:
            if user['payment_status'] != 'Approved':
                flash('Your payment has not been approved yet. Contact admin.', 'error')
                return render_template('login.html')
            # Check if already submitted
            db = get_db()
            existing = db.execute('SELECT id FROM results WHERE user_id=?', (user['id'],)).fetchone()
            db.close()
            if existing:
                flash('You have already taken this exam.', 'error')
                return render_template('login.html')
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['reg_no'] = user['reg_no']
            session['sub1'] = user['sub1']
            session['sub2'] = user['sub2']
            session['sub3'] = user['sub3']
            return redirect(url_for('exam'))
        else:
            flash('Invalid Registration Number or Login Code.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ─── EXAM ────────────────────────────────────────────────────────────────────
@app.route('/exam')
def exam():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    db = get_db()
    # Check already submitted
    existing = db.execute('SELECT id FROM results WHERE user_id=?', (user_id,)).fetchone()
    if existing:
        db.close()
        return redirect(url_for('result'))

    subs = ['English', session['sub1'], session['sub2'], session['sub3']]
    counts = {'English': 60, session['sub1']: 40, session['sub2']: 40, session['sub3']: 40}

    all_questions = []
    for sub in subs:
        rows = db.execute('SELECT * FROM questions WHERE subject=?', (sub,)).fetchall()
        selected = random.sample(rows, min(counts[sub], len(rows)))
        for q in selected:
            all_questions.append({
                'id': q['id'], 'subject': q['subject'],
                'question': q['question'],
                'A': q['A'], 'B': q['B'], 'C': q['C'], 'D': q['D'],
                'answer': q['answer']
            })
    db.close()

    # Store correct answers in session (server side)
    session['correct_answers'] = {str(q['id']): q['answer'] for q in all_questions}
    # Strip answer before sending to client
    for q in all_questions:
        del q['answer']

    return render_template('exam.html',
                           questions=all_questions,
                           subs=subs,
                           user_name=session['user_name'])

# ─── SUBMIT EXAM ─────────────────────────────────────────────────────────────
@app.route('/submit', methods=['POST'])
def submit():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    data = request.get_json()
    answers = data.get('answers', {})  # {qid: chosen_option}
    correct_answers = session.get('correct_answers', {})

    correct = 0
    total = len(correct_answers)
    for qid, correct_ans in correct_answers.items():
        if answers.get(qid, '').upper() == correct_ans.upper():
            correct += 1

    score = (correct / 180) * 400 if total > 0 else 0
    score = round(score, 2)

    import json
    db = get_db()
    # Check duplicate
    existing = db.execute('SELECT id FROM results WHERE user_id=?', (session['user_id'],)).fetchone()
    if not existing:
        db.execute('INSERT INTO results (user_id, score, answers) VALUES (?,?,?)',
                   (session['user_id'], score, json.dumps(answers)))
        db.commit()
    db.close()

    session['last_score'] = score
    session['last_answers'] = answers
    session['last_correct'] = correct
    session['last_total'] = total
    return jsonify({'score': score, 'correct': correct, 'total': total})

# ─── RESULT ──────────────────────────────────────────────────────────────────
@app.route('/result')
def result():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    res = db.execute('SELECT * FROM results WHERE user_id=?', (session['user_id'],)).fetchone()
    db.close()
    if not res:
        if 'last_score' in session:
            score = session['last_score']
            correct = session['last_correct']
            total = session['last_total']
        else:
            return redirect(url_for('exam'))
    else:
        score = res['score']
        correct = None
        total = None
    return render_template('result.html', score=score, correct=correct, total=total,
                           name=session.get('user_name',''))

# ─── RESULT REVIEW ───────────────────────────────────────────────────────────
@app.route('/review')
def review():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    import json
    db = get_db()
    res = db.execute('SELECT * FROM results WHERE user_id=?', (session['user_id'],)).fetchone()
    db.close()
    if not res:
        return redirect(url_for('result'))
    answers = json.loads(res['answers']) if res['answers'] else {}
    correct_answers = session.get('correct_answers', {})
    if not correct_answers:
        return redirect(url_for('result'))

    db = get_db()
    review_data = []
    for qid, correct_ans in correct_answers.items():
        q = db.execute('SELECT * FROM questions WHERE id=?', (qid,)).fetchone()
        if q:
            user_ans = answers.get(qid, '')
            review_data.append({
                'question': q['question'], 'subject': q['subject'],
                'A': q['A'], 'B': q['B'], 'C': q['C'], 'D': q['D'],
                'correct': correct_ans, 'user_answer': user_ans,
                'is_correct': user_ans.upper() == correct_ans.upper()
            })
    db.close()
    return render_template('review.html', review_data=review_data, name=session.get('user_name',''))

# ─── ADMIN LOGIN ──────────────────────────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('username') == 'admin' and request.form.get('password') == 'admin123':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ─── ADMIN DASHBOARD ─────────────────────────────────────────────────────────
@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()
    candidates = db.execute('SELECT * FROM users ORDER BY id DESC').fetchall()
    total = len(candidates)
    scores = db.execute('SELECT score FROM results').fetchall()
    scores_list = [r['score'] for r in scores]
    avg_score = round(sum(scores_list)/len(scores_list), 2) if scores_list else 0
    highest = max(scores_list) if scores_list else 0
    lowest = min(scores_list) if scores_list else 0
    pass_rate = round(len([s for s in scores_list if s >= 200])/len(scores_list)*100, 1) if scores_list else 0
    q_count = db.execute('SELECT COUNT(*) as c FROM questions').fetchone()['c']
    db.close()
    return render_template('admin_dashboard.html',
                           candidates=candidates, total=total,
                           avg_score=avg_score, highest=highest,
                           lowest=lowest, pass_rate=pass_rate, q_count=q_count)

# ─── APPROVE/REJECT ───────────────────────────────────────────────────────────
@app.route('/admin/approve/<int:uid>')
@admin_required
def approve(uid):
    code = gen_login_code()
    db = get_db()
    db.execute("UPDATE users SET payment_status='Approved', login_code=? WHERE id=?", (code, uid))
    db.commit()
    db.close()
    flash(f'Approved! Login code: {code}', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<int:uid>')
@admin_required
def reject(uid):
    db = get_db()
    db.execute("UPDATE users SET payment_status='Rejected' WHERE id=?", (uid,))
    db.commit()
    db.close()
    flash('Payment rejected.', 'error')
    return redirect(url_for('admin_dashboard'))

# ─── BULK UPLOAD ──────────────────────────────────────────────────────────────
@app.route('/admin/bulk_upload', methods=['POST'])
@admin_required
def bulk_upload():
    if 'csv_file' not in request.files:
        flash('No file uploaded.', 'error')
        return redirect(url_for('admin_dashboard'))
    file = request.files['csv_file']
    content = file.read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(content))
    db = get_db()
    count = 0
    for row in reader:
        reg_no = gen_reg_no()
        login_code = gen_login_code()
        try:
            db.execute('''INSERT INTO users (name,email,phone,reg_no,login_code,payment_status,sub1,sub2,sub3)
                          VALUES (?,?,?,?,?,?,?,?,?)''',
                       (row['name'], row.get('email',''), row.get('phone',''),
                        reg_no, login_code, 'Approved',
                        row.get('sub1',''), row.get('sub2',''), row.get('sub3','')))
            count += 1
        except:
            pass
    db.commit()
    db.close()
    flash(f'{count} candidates uploaded successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

# ─── QUESTION MANAGEMENT ─────────────────────────────────────────────────────
@app.route('/admin/questions', methods=['GET'])
@admin_required
def questions():
    subject_filter = request.args.get('subject', '')
    db = get_db()
    if subject_filter:
        qs = db.execute('SELECT * FROM questions WHERE subject=? ORDER BY id DESC LIMIT 100', (subject_filter,)).fetchall()
    else:
        qs = db.execute('SELECT * FROM questions ORDER BY id DESC LIMIT 100').fetchall()
    counts = db.execute('SELECT subject, COUNT(*) as c FROM questions GROUP BY subject').fetchall()
    db.close()
    return render_template('questions.html', questions=qs, subjects=SUBJECTS,
                           counts=counts, selected_subject=subject_filter)

@app.route('/admin/questions/add', methods=['POST'])
@admin_required
def add_question():
    subject = request.form.get('subject')
    question = request.form.get('question','').strip()
    a = request.form.get('A','').strip()
    b = request.form.get('B','').strip()
    c = request.form.get('C','').strip()
    d = request.form.get('D','').strip()
    answer = request.form.get('answer','').strip().upper()
    if not all([subject, question, a, b, c, d, answer]):
        flash('All fields required.', 'error')
        return redirect(url_for('questions'))
    db = get_db()
    db.execute('INSERT INTO questions (subject,question,A,B,C,D,answer) VALUES (?,?,?,?,?,?,?)',
               (subject, question, a, b, c, d, answer))
    db.commit()
    db.close()
    flash('Question added.', 'success')
    return redirect(url_for('questions'))

@app.route('/admin/questions/upload', methods=['POST'])
@admin_required
def upload_questions():
    if 'csv_file' not in request.files:
        flash('No file.', 'error')
        return redirect(url_for('questions'))
    file = request.files['csv_file']
    content = file.read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(content))
    db = get_db()
    count = 0
    for row in reader:
        try:
            db.execute('INSERT INTO questions (subject,question,A,B,C,D,answer) VALUES (?,?,?,?,?,?,?)',
                       (row['subject'], row['question'], row['A'], row['B'], row['C'], row['D'], row['answer']))
            count += 1
        except Exception as e:
            pass
    db.commit()
    db.close()
    flash(f'{count} questions uploaded.', 'success')
    return redirect(url_for('questions'))

@app.route('/admin/questions/delete/<int:qid>')
@admin_required
def delete_question(qid):
    db = get_db()
    db.execute('DELETE FROM questions WHERE id=?', (qid,))
    db.commit()
    db.close()
    flash('Question deleted.', 'success')
    return redirect(url_for('questions'))

# ─── UPLOADS ─────────────────────────────────────────────────────────────────
@app.route('/uploads/<filename>')
@admin_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    init_db()
    app.run(debug=True)
