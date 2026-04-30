import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


# ─── Auth ────────────────────────────────────────────────────────────────────

def sign_up(email: str, password: str, full_name: str, role: str) -> dict:
    client = get_supabase()
    response = client.auth.sign_up({
        "email": email,
        "password": password,
        "options": {
            "data": {
                "full_name": full_name,
                "role": role
            }
        }
    })
    return response


def sign_in(email: str, password: str) -> dict:
    client = get_supabase()
    response = client.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    return response


def sign_out():
    client = get_supabase()
    client.auth.sign_out()


def get_current_user():
    client = get_supabase()
    return client.auth.get_user()


# ─── Profiles ────────────────────────────────────────────────────────────────

def get_profile(user_id: str) -> dict | None:
    client = get_supabase()
    response = client.table("profiles") \
        .select("*") \
        .eq("id", user_id) \
        .single() \
        .execute()
    return response.data


def update_profile(user_id: str, data: dict):
    client = get_supabase()
    client.table("profiles").update(data).eq("id", user_id).execute()


def save_face_encoding(user_id: str, encoding: list):
    update_profile(user_id, {"face_encoding": encoding})


def save_voice_encoding(user_id: str, encoding: list):
    update_profile(user_id, {"voice_encoding": encoding})


# ─── Classes ─────────────────────────────────────────────────────────────────

def create_class(teacher_id: str, class_name: str, subject: str, join_code: str) -> dict:
    client = get_supabase()
    response = client.table("classes").insert({
        "teacher_id": teacher_id,
        "class_name": class_name,
        "subject": subject,
        "join_code": join_code,
        "is_active": True
    }).execute()
    return response.data[0] if response.data else {}


def get_teacher_classes(teacher_id: str) -> list:
    client = get_supabase()
    response = client.table("classes") \
        .select("*") \
        .eq("teacher_id", teacher_id) \
        .order("created_at", desc=True) \
        .execute()
    return response.data or []


def get_class_by_join_code(join_code: str) -> dict | None:
    client = get_supabase()
    response = client.table("classes") \
        .select("*") \
        .eq("join_code", join_code.upper()) \
        .single() \
        .execute()
    return response.data


def delete_class(class_id: str):
    client = get_supabase()
    client.table("classes").delete().eq("id", class_id).execute()


# ─── Enrollments ─────────────────────────────────────────────────────────────

def enroll_student(class_id: str, student_id: str) -> bool:
    client = get_supabase()
    # Check if already enrolled
    existing = client.table("enrollments") \
        .select("id") \
        .eq("class_id", class_id) \
        .eq("student_id", student_id) \
        .execute()
    if existing.data:
        return False  # Already enrolled
    client.table("enrollments").insert({
        "class_id": class_id,
        "student_id": student_id
    }).execute()
    return True


def get_enrolled_classes(student_id: str) -> list:
    client = get_supabase()
    response = client.table("enrollments") \
        .select("class_id, classes(*)") \
        .eq("student_id", student_id) \
        .execute()
    return [row["classes"] for row in (response.data or []) if row.get("classes")]


def get_class_students(class_id: str) -> list:
    client = get_supabase()
    response = client.table("enrollments") \
        .select("student_id, profiles(id, full_name, email, face_encoding, voice_encoding)") \
        .eq("class_id", class_id) \
        .execute()
    return [row["profiles"] for row in (response.data or []) if row.get("profiles")]


def unenroll_student(class_id: str, student_id: str):
    client = get_supabase()
    client.table("enrollments") \
        .delete() \
        .eq("class_id", class_id) \
        .eq("student_id", student_id) \
        .execute()


# ─── Attendance Sessions ──────────────────────────────────────────────────────

def create_session(class_id: str, teacher_id: str, session_date: str) -> dict:
    client = get_supabase()
    response = client.table("attendance_sessions").insert({
        "class_id": class_id,
        "teacher_id": teacher_id,
        "session_date": session_date,
        "is_active": True
    }).execute()
    return response.data[0] if response.data else {}


def close_session(session_id: str):
    client = get_supabase()
    client.table("attendance_sessions") \
        .update({"is_active": False}) \
        .eq("id", session_id) \
        .execute()


def get_active_session(class_id: str) -> dict | None:
    client = get_supabase()
    response = client.table("attendance_sessions") \
        .select("*") \
        .eq("class_id", class_id) \
        .eq("is_active", True) \
        .limit(1) \
        .execute()
    return response.data[0] if response.data else None


def get_class_sessions(class_id: str) -> list:
    client = get_supabase()
    response = client.table("attendance_sessions") \
        .select("*") \
        .eq("class_id", class_id) \
        .order("created_at", desc=True) \
        .execute()
    return response.data or []


# ─── Attendance Records ───────────────────────────────────────────────────────

def mark_attendance(session_id: str, student_id: str, class_id: str, method: str) -> bool:
    client = get_supabase()
    # Prevent duplicates in same session
    existing = client.table("attendance_records") \
        .select("id") \
        .eq("session_id", session_id) \
        .eq("student_id", student_id) \
        .execute()
    if existing.data:
        return False
    client.table("attendance_records").insert({
        "session_id": session_id,
        "student_id": student_id,
        "class_id": class_id,
        "method": method
    }).execute()
    return True


def get_session_attendance(session_id: str) -> list:
    client = get_supabase()
    response = client.table("attendance_records") \
        .select("*, profiles(full_name, email)") \
        .eq("session_id", session_id) \
        .execute()
    return response.data or []


def get_student_attendance(student_id: str, class_id: str) -> list:
    client = get_supabase()
    response = client.table("attendance_records") \
        .select("*, attendance_sessions(session_date)") \
        .eq("student_id", student_id) \
        .eq("class_id", class_id) \
        .order("marked_at", desc=True) \
        .execute()
    return response.data or []


def get_class_attendance_summary(class_id: str) -> list:
    """Returns per-student attendance count for a class."""
    client = get_supabase()
    response = client.table("attendance_records") \
        .select("student_id, profiles(full_name, email)") \
        .eq("class_id", class_id) \
        .execute()
    return response.data or []
