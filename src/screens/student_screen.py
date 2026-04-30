import streamlit as st
import plotly.express as px

from src.utils.auth import logout, require_login
from src.utils.supabase_client import (
    get_enrolled_classes, get_class_by_join_code,
    enroll_student, get_active_session,
    mark_attendance, get_student_attendance,
    get_class_sessions, save_face_encoding,
    save_voice_encoding
)
from src.utils.face_utils import get_face_encoding, compare_faces
from src.utils.voice_utils import get_voice_embedding, compare_voices
from src.utils.helpers import format_date_only, compute_attendance_percentage
from src.components.face_capture import face_capture_widget
from src.components.attendance_table import attendance_table


def student_screen():
    require_login()
    _render_sidebar()

    student_name = st.session_state.get("user_name", "Student")
    st.markdown(f"## 👋 Hey, {student_name}")
    st.markdown("---")

    tab_classes, tab_mark, tab_history, tab_profile = st.tabs([
        "📚 My Classes",
        "✅ Mark Attendance",
        "📅 My History",
        "👤 Profile"
    ])

    with tab_classes:
        _my_classes_tab()

    with tab_mark:
        _mark_attendance_tab()

    with tab_history:
        _history_tab()

    with tab_profile:
        _profile_tab()


# ─── Sidebar ──────────────────────────────────────────────────────────────────

def _render_sidebar():
    with st.sidebar:
        st.markdown("### 🎓 SnapClass")
        st.markdown(f"**{st.session_state.get('user_name', '')}**")
        st.caption(st.session_state.get("user_email", ""))
        st.markdown("---")

        face_status = "✅ Registered" if st.session_state.get("face_encoding") else "❌ Not set"
        voice_status = "✅ Registered" if st.session_state.get("voice_encoding") else "❌ Not set"
        st.markdown(f"**Face:** {face_status}")
        st.markdown(f"**Voice:** {voice_status}")
        st.markdown("---")

        if st.button("🚪 Logout", use_container_width=True):
            logout()


# ─── My Classes Tab ───────────────────────────────────────────────────────────

def _my_classes_tab():
    student_id = st.session_state["user_id"]

    col_join, col_list = st.columns([1, 2])

    with col_join:
        st.markdown("#### ➕ Join a Class")
        with st.form("join_class_form"):
            join_code = st.text_input("Enter Join Code", placeholder="ABCD12").upper()
            submitted = st.form_submit_button("Join Class", type="primary", use_container_width=True)

        if submitted:
            if not join_code:
                st.error("Please enter a join code.")
            else:
                cls = get_class_by_join_code(join_code)
                if not cls:
                    st.error("❌ Invalid join code. Please check and try again.")
                else:
                    enrolled = enroll_student(cls["id"], student_id)
                    if enrolled:
                        st.success(f"🎉 Enrolled in **{cls['class_name']}**!")
                        st.rerun()
                    else:
                        st.info("You're already enrolled in this class.")

    with col_list:
        st.markdown("#### 📚 Enrolled Classes")
        classes = get_enrolled_classes(student_id)

        if not classes:
            st.info("You're not enrolled in any class yet. Enter a join code to get started.")
            return

        for cls in classes:
            sessions = get_class_sessions(cls["id"])
            records = get_student_attendance(student_id, cls["id"])
            pct = compute_attendance_percentage(len(records), len(sessions))

            badge = "🟢" if pct >= 75 else ("🟡" if pct >= 50 else "🔴")

            with st.expander(f"{badge} {cls['class_name']} — {cls.get('subject', '')}"):
                st.markdown(f"**Attendance:** {pct}% ({len(records)}/{len(sessions)} classes)")
                st.progress(min(pct / 100, 1.0))
                st.markdown(f"**Join Code:** `{cls['join_code']}`")


# ─── Mark Attendance Tab ──────────────────────────────────────────────────────

def _mark_attendance_tab():
    st.markdown("#### ✅ Mark Your Attendance")

    student_id = st.session_state["user_id"]
    classes = get_enrolled_classes(student_id)

    if not classes:
        st.info("You need to join a class first.")
        return

    class_options = {f"{c['class_name']} — {c.get('subject', '')}": c for c in classes}
    selected_label = st.selectbox("Select Class", list(class_options.keys()))
    selected_class = class_options[selected_label]
    class_id = selected_class["id"]

    active_session = get_active_session(class_id)

    if not active_session:
        st.warning("⚠️ No active session right now. Wait for your teacher to start one.")
        return

    session_id = active_session["id"]

    # Check if already marked
    records = get_student_attendance(student_id, class_id)
    already_marked_ids = [r.get("session_id") for r in records]
    if session_id in already_marked_ids:
        st.success("✅ You've already been marked present in this session!")
        return

    st.info(f"📍 Session active for **{selected_class['class_name']}**")
    st.markdown("---")

    method = st.radio("Choose method", ["Face Recognition", "Voice Recognition"], horizontal=True)

    if method == "Face Recognition":
        _mark_with_face(session_id, class_id, student_id)
    else:
        _mark_with_voice(session_id, class_id, student_id)


def _mark_with_face(session_id: str, class_id: str, student_id: str):
    st.markdown("**📸 Face Recognition**")

    stored_encoding = st.session_state.get("face_encoding")
    if not stored_encoding:
        st.error("❌ You haven't registered your face yet. Go to the **Profile** tab.")
        return

    photo = st.camera_input("Take a selfie", key="mark_face", label_visibility="visible")

    if photo:
        image_bytes = photo.getvalue()
        with st.spinner("Verifying your identity..."):
            encoding = get_face_encoding(image_bytes)

        if encoding is None:
            st.error("❌ No face detected. Try again in better lighting.")
            return

        match = compare_faces(stored_encoding, encoding, tolerance=0.5)

        if match:
            with st.spinner("Marking attendance..."):
                marked = mark_attendance(session_id, student_id, class_id, method="face")
            if marked:
                st.success("🎉 Attendance marked successfully via Face Recognition!")
                st.balloons()
            else:
                st.info("Already marked present.")
        else:
            st.error("❌ Face does not match your registered profile. Please try again.")


def _mark_with_voice(session_id: str, class_id: str, student_id: str):
    st.markdown("**🎙️ Voice Recognition**")
    st.info("Upload a short audio clip (3-10 seconds) of your voice.")

    stored_embedding = st.session_state.get("voice_encoding")
    if not stored_embedding:
        st.error("❌ You haven't registered your voice yet. Go to the **Profile** tab.")
        return

    audio_file = st.file_uploader("Upload audio clip", type=["wav", "mp3", "ogg"], key="mark_voice")

    if audio_file:
        with st.spinner("Verifying your voice..."):
            embedding = get_voice_embedding(audio_file.read())

        if embedding is None:
            st.error("❌ Could not process audio. Please upload a clear clip.")
            return

        match = compare_voices(stored_embedding, embedding, threshold=0.75)

        if match:
            with st.spinner("Marking attendance..."):
                marked = mark_attendance(session_id, student_id, class_id, method="voice")
            if marked:
                st.success("🎉 Attendance marked successfully via Voice Recognition!")
                st.balloons()
            else:
                st.info("Already marked present.")
        else:
            st.error("❌ Voice does not match your profile. Please try again or use Face Recognition.")


# ─── History Tab ─────────────────────────────────────────────────────────────

def _history_tab():
    st.markdown("#### 📅 Your Attendance History")

    student_id = st.session_state["user_id"]
    classes = get_enrolled_classes(student_id)

    if not classes:
        st.info("Join a class first to see your attendance history.")
        return

    class_options = {f"{c['class_name']} — {c.get('subject', '')}": c for c in classes}
    selected_label = st.selectbox("Select Class", list(class_options.keys()), key="history_class")
    selected_class = class_options[selected_label]
    class_id = selected_class["id"]

    sessions = get_class_sessions(class_id)
    records = get_student_attendance(student_id, class_id)
    pct = compute_attendance_percentage(len(records), len(sessions))

    col1, col2, col3 = st.columns(3)
    col1.metric("Classes Attended", len(records))
    col2.metric("Total Sessions", len(sessions))
    col3.metric("Attendance %", f"{pct}%")

    st.progress(min(pct / 100, 1.0))

    if records:
        # Timeline chart
        dates = []
        for r in records:
            session_info = r.get("attendance_sessions", {})
            d = session_info.get("session_date") or r.get("marked_at", "")
            dates.append(format_date_only(d))

        import pandas as pd
        df_chart = pd.DataFrame({"Date": dates, "Present": [1] * len(dates)})
        st.markdown("---")
        st.markdown("**Attendance Timeline**")
        fig = px.scatter(df_chart, x="Date", y="Present",
                         title="Days you were present",
                         color_discrete_sequence=["#22c55e"])
        fig.update_traces(marker=dict(size=12, symbol="circle"))
        fig.update_layout(yaxis=dict(showticklabels=False), height=250)
        st.plotly_chart(fig, use_container_width=True)

        # Table
        import pandas as pd
        rows = []
        for r in records:
            session_info = r.get("attendance_sessions", {})
            d = session_info.get("session_date") or r.get("marked_at", "")
            rows.append({
                "Date": format_date_only(d),
                "Method": r.get("method", "").capitalize()
            })
        df_table = pd.DataFrame(rows)
        attendance_table(df_table, title="Attendance Log", show_export=True)
    else:
        st.info("No attendance records found for this class.")


# ─── Profile Tab ─────────────────────────────────────────────────────────────

def _profile_tab():
    st.markdown("#### 👤 Your Profile")

    st.markdown(f"**Name:** {st.session_state.get('user_name', '')}")
    st.markdown(f"**Email:** {st.session_state.get('user_email', '')}")
    st.markdown(f"**Role:** Student")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📸 Face Registration**")
        if st.session_state.get("face_encoding"):
            st.success("✅ Face registered")
            update_face = st.checkbox("Update my face")
        else:
            st.warning("⚠️ Face not registered")
            update_face = True

        if update_face:
            encoding = face_capture_widget(
                label="Take a clear selfie",
                key="profile_face"
            )
            if encoding:
                with st.spinner("Saving..."):
                    save_face_encoding(st.session_state["user_id"], encoding)
                    st.session_state["face_encoding"] = encoding
                st.success("✅ Face updated!")

    with col2:
        st.markdown("**🎙️ Voice Registration**")
        if st.session_state.get("voice_encoding"):
            st.success("✅ Voice registered")
            update_voice = st.checkbox("Update my voice")
        else:
            st.warning("⚠️ Voice not registered")
            update_voice = True

        if update_voice:
            st.caption("Upload a 5-10 second audio clip of yourself speaking.")
            audio_file = st.file_uploader("Upload audio", type=["wav", "mp3", "ogg"], key="profile_voice")
            if audio_file:
                with st.spinner("Processing voice..."):
                    embedding = get_voice_embedding(audio_file.read())
                if embedding:
                    save_voice_encoding(st.session_state["user_id"], embedding)
                    st.session_state["voice_encoding"] = embedding
                    st.success("✅ Voice registered!")
                else:
                    st.error("❌ Could not process audio. Try a clearer, louder clip.")
