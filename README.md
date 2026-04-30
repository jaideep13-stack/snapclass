# 📸 SnapClass — AI Attendance System

An AI-powered attendance system built with Streamlit, Face Recognition, Voice Recognition, and Supabase.

## Features

- **Face Recognition** — Mark attendance by scanning students' faces
- **Voice Recognition** — Alternate attendance method via voice verification
- **QR Code Join** — Students join classes by scanning a QR code or entering a join code
- **Teacher Dashboard** — Create classes, run sessions, view live attendance
- **Student Dashboard** — Mark attendance, track history, register biometrics
- **Analytics** — Per-student attendance %, charts, and CSV export
- **Supabase Backend** — Auth, database, and row-level security

---

## Project Structure

```
app.py                     # Main entry point
requirements.txt           # Python dependencies
supabase_schema.sql        # Database schema (run in Supabase SQL editor)

.streamlit/
  secrets.toml             # API keys (do not commit)

src/
  __init__.py
  screens/
    __init__.py
    home_screen.py         # Login / Register
    teacher_screen.py      # Teacher dashboard
    student_screen.py      # Student dashboard
  components/
    __init__.py
    dialog_auto_enroll.py  # QR join dialog
    face_capture.py        # Reusable camera capture widget
    attendance_table.py    # Reusable attendance table
  utils/
    __init__.py
    supabase_client.py     # All DB operations
    auth.py                # Login / register / logout helpers
    face_utils.py          # Face encoding & comparison
    voice_utils.py         # Voice embedding & comparison
    qr_utils.py            # QR code generation
    helpers.py             # Formatting & dataframe utilities
```

---

## Setup

### 1. Clone & Install

```bash
git clone <your-repo>
cd snapclass
pip install -r requirements.txt
```

> Note: `dlib` installation can be tricky. On Ubuntu: `sudo apt-get install cmake` first.
> On Windows, use `dlib-bin` (already in requirements.txt).

### 2. Supabase Setup

1. Create a project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** and run `supabase_schema.sql`
3. Copy your **Project URL** and **anon public key** from Project Settings → API

### 3. Configure Secrets

Edit `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-public-key"
```

### 4. Run

```bash
streamlit run app.py
```

---

## Deployment (Streamlit Cloud)

1. Push to GitHub (do **not** push `secrets.toml`)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy the repo, set secrets in the cloud dashboard under **Settings → Secrets**

---

## Notes

- Face encodings are stored as float arrays in Supabase
- Voice embeddings use `resemblyzer` (d-vector approach)
- Attendance is deduplicated per session — one record per student per session
- RLS (Row Level Security) is enabled on all tables
