# 📝 ONLINE CBT MOCK EXAM SYSTEM
**Powered by LEE SMART TECH 2026**

A full-featured Computer-Based Testing (CBT) system built with Flask, SQLite, HTML, CSS, and JavaScript.

---

## 🚀 Quick Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the application
```bash
python app.py
```
Then visit: `http://localhost:5000`

The SQLite database (`cbt.db`) and all tables are **auto-created** on first run.

---

## 🔑 Default Admin Credentials
- **Username:** `admin`
- **Password:** `admin123`

Admin Login URL: `http://localhost:5000/admin/login`

---

## 📁 Project Structure
```
cbt_system/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── Procfile               # For deployment (Heroku/Railway)
├── cbt.db                 # SQLite database (auto-created)
├── uploads/               # Payment receipt uploads
├── static/
│   ├── css/style.css      # Main stylesheet
│   └── js/exam.js         # Exam engine JavaScript
└── templates/
    ├── base.html           # Base layout
    ├── index.html          # Homepage
    ├── register.html       # Candidate registration
    ├── reg_success.html    # Registration success page
    ├── login.html          # Candidate login
    ├── admin_login.html    # Admin login
    ├── admin_dashboard.html # Admin control panel
    ├── questions.html      # Question management
    ├── exam.html           # Exam interface
    ├── result.html         # Score display
    └── review.html         # Answer review
```

---

## 📋 Features

### Candidates
- Register with personal info + receipt upload
- Select English (compulsory) + 3 other subjects from 25 available
- Auto-generated Registration Number (CANDMOCK + 6 chars)
- Login with Reg No + Login Code
- JAMB-style exam interface with subject tabs
- 180-minute countdown timer with auto-submit
- Question palette (green=answered, red=unanswered, yellow=current)
- Keyboard shortcuts: A/B/C/D (answer), N (next), P (prev), S (submit), Y (confirm)
- Auto-save answers in localStorage (survives page reload)
- Anti-cheating: tab-switch detection, auto-submit after 3 switches
- Score on 400-point JAMB scale
- Full answer review with correct/wrong highlighting

### Admin
- Dashboard with candidate table and analytics
- Approve/Reject payments (generates login code on approval)
- View uploaded payment receipts
- Bulk candidate upload via CSV
- Add questions manually or via CSV upload
- Question counts per subject (target: 100 each)

---

## 📊 CSV Formats

### Bulk Candidate Upload
```csv
name,email,phone,sub1,sub2,sub3
John Doe,john@email.com,08012345678,Mathematics,Biology,Chemistry
```

### Question Upload
```csv
subject,question,A,B,C,D,answer
Mathematics,What is 2+2?,3,4,5,6,B
English,Choose the correct word,run,ran,running,runs,B
```

---

## 🌐 Deployment (Render / Railway)

1. Push to GitHub
2. Connect repo to Render or Railway
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn app:app`
5. Done!

For persistent uploads, configure an external storage (AWS S3, Cloudinary) for production.

---

## 📱 WhatsApp Contact
Admin WhatsApp: [+2348136818190](https://wa.me/2348136818190)

---

## 🎯 Exam Scoring
- Total questions: **180** (English: 60, Each subject: 40)
- Score formula: **(Correct / 180) × 400**
- Pass mark: **200 / 400**
