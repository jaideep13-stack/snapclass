import streamlit as st
import plotly.express as px
from datetime import date

from src.utils.auth import logout, require_login
from src.utils.supabase_client import (
    get_teacher_classes, create_class, delete_class,
    get_class_students, create_session, close_session,
    get_active_session, get_class_sessions,
    get_session_attendance, get_class_attendance_summary,
    mark_attendance
)
from src.utils.qr_utils import generate_join_qr, qr_to_html, generate_join_code
from src.utils.face_utils import get_face_encoding, find_matching_student
from src.utils.helpers import (
    build_attendance_dataframe, attendance_summary_df, format_date_only
)
from src.components.attendance_table import attendance_table, attendance_summary_table


def teacher_screen():
    require_login()
    _render_sidebar()

    teacher_name = st.session_state.get("user_name", "Teacher")
    st.markdown(f"## 👋 Welcome, {teacher_name}")
    st.markdown("---")

    tab_classes, tab_attendance, tab_reports = st.tabs([
        "📚 My Classes",
        "✅ Take Attendance",
        "📊 Reports"
    ])

    with tab_classes:
        _classes_tab()

    with tab_attendance:
        _attendance_tab()

    with tab_reports:
        _reports_tab()


# ─── Sidebar ──────────────────────────────────────────────────────────────────

def _render_sidebar():
    with st.sidebar:
        st.markdown("### 🎓 SnapClass")
        st.markdown(f"**{st.session_state.get('user_name', '')}**")
        st.caption(st.session_state.get("user_email", ""))
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout()


# ─── Classes Tab ──────────────────────────────────────────────────────────────

def _classes_tab():
    col_left, col_right = st.columns([1.2, 2])

    with col_left:
        _create_class_form()

    with col_right:
        _list_classes()


def _create_class_form():
    st.markdown("#### ➕ Create New Class")
    with st.form("create_class_form"):
        class_name = st.text_input("Class Name", placeholder="CSE Batch A")
        subject = st.text_input("Subject", placeholder="Machine Learning")
        auto_code = generate_join_code()
        join_code = st.text_input("Join Code", value=auto_code,
                                   help="Students use this to join. You can customize it.")
        submitted = st.form_submit_button("Create Class", type="primary", use_container_width=True)

    if submitted:
        if not class_name or not subject:
            st.error("Class name and subject are required.")
            return
        teacher_id = st.session_state["user_id"]
        with st.spinner("Creating class..."):
            create_class(teacher_id, class_name, subject, join_code.upper())
        st.success(f"✅ Class **{class_name}** created!")
        st.rerun()


def _list_classes():
    st.markdown("#### 📚 Your Classes")
    teacher_id = st.session_state["user_id"]

    with st.spinner("Loading classes..."):
        classes = get_teacher_classes(teacher_id)

    if not classes:
        st.info("No classes yet. Create one to get started.")
        return

    for cls in classes:
        with st.expander(f"📘 {cls['class_name']} — {cls.get('subject', '')}", expanded=False):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Join Code:** `{cls['join_code']}`")
                students = get_class_students(cls["id"])
                st.markdown(f"**Students enrolled:** {len(students)}")
                if students:
                    for s in students[:5]:
                        st.markdown(f"- {s['full_name']} ({s['email']})")
                    if len(students) > 5:
                        st.caption(f"...and {len(students) - 5} more")

            with col2:
                # QR Code
                qr_b64 = generate_join_qr(cls["join_code"])
                st.markdown(qr_to_html(qr_b64, size=160), unsafe_allow_html=True)
                st.caption("Scan to join")

            # Share link
            join_url = f"https://your-app.streamlit.app/?join-code={cls['join_code']}"
            st.code(join_url, language=None)

            if st.button("🗑️ Delete Class", key=f"del_{cls['id']}"):
                delete_class(cls["id"])
                st.warning(f"Class **{cls['class_name']}** deleted.")
                st.rerun()


# ─── Attendance Tab ───────────────────────────────────────────────────────────

def _attendance_tab():
    st.markdown("#### ✅ Take Attendance with AI")

    teacher_id = st.session_state["user_id"]
    classes = get_teacher_classes(teacher_id)

    if not classes:
        st.info("Create a class first before taking attendance.")
        return

    class_options = {f"{c['class_name']} — {c.get('subject', '')}": c for c in classes}
    selected_label = st.selectbox("Select Class", list(class_options.keys()))
    selected_class = class_options[selected_label]
    class_id = selected_class["id"]

    active_session = get_active_session(class_id)

    st.markdown("---")

    if active_session:
        _active_session_panel(active_session, class_id)
    else:
        _start_session_panel(class_id, teacher_id)


def _start_session_panel(class_id: str, teacher_id: str):
    st.info("No active session. Start one to begin marking attendance.")
    session_date = st.date_input("Session Date", value=date.today())
    if st.button("▶️ Start Attendance Session", type="primary"):
        with st.spinner("Starting session..."):
            create_session(class_id, teacher_id, str(session_date))
        st.success("Session started!")
        st.rerun()


def _active_session_panel(session: dict, class_id: str):
    session_id = session["id"]
    st.success(f"🟢 Active session — {format_date_only(session.get('session_date', session.get('created_at', '')))}")

    col1, col2 = st.columns(2)

    with col1:
        _face_scan_panel(session_id, class_id)

    with col2:
        _live_attendance_panel(session_id)

    st.markdown("---")
    if st.button("⏹️ Close Session", type="secondary"):
        close_session(session_id)
        st.success("Session closed.")
        st.rerun()


def _face_scan_panel(session_id: str, class_id: str):
    st.markdown("**📸 Scan Student Face**")
    st.caption("Point camera at a student to mark their attendance.")

    photo = st.camera_input("📷 Capture", key=f"scan_{session_id}", label_visibility="collapsed")

    if photo:
        image_bytes = photo.getvalue()

        with st.spinner("Recognizing face..."):
            students = get_class_students(class_id)
            encoding = get_face_encoding(image_bytes)

            if encoding is None:
                st.error("❌ No face detected. Try again.")
                return

            match = find_matching_student(students, encoding)

        if match:
            st.success(f"✅ Recognized: **{match['full_name']}**")
            marked = mark_attendance(session_id, match["id"], class_id, method="face")
            if not marked:
                st.info(f"{match['full_name']} is already marked present.")
        else:
            st.warning("⚠️ Face not recognized. Student may not be enrolled or face not registered.")

        # Manual override
        with st.expander("Mark manually instead"):
            _manual_mark_panel(session_id, class_id)


def _manual_mark_panel(session_id: str, class_id: str):
    students = get_class_students(class_id)
    if not students:
        st.info("No enrolled students.")
        return

    options = {s["full_name"]: s for s in students}
    selected_name = st.selectbox("Select Student", list(options.keys()), key=f"manual_{session_id}")
    if st.button("✅ Mark Present", key=f"mark_{session_id}"):
        student = options[selected_name]
        marked = mark_attendance(session_id, student["id"], class_id, method="manual")
        if marked:
            st.success(f"Marked {selected_name} as present.")
        else:
            st.info(f"{selected_name} already marked.")
        st.rerun()


def _live_attendance_panel(session_id: str):
    st.markdown("**👥 Present in this session**")
    records = get_session_attendance(session_id)

    if not records:
        st.info("No one marked yet.")
        return

    for r in records:
        name = r.get("profiles", {}).get("full_name", "Unknown")
        method = r.get("method", "").capitalize()
        st.markdown(f"✅ **{name}** — _{method}_")

    st.markdown(f"**Total present: {len(records)}**")


# ─── Reports Tab ──────────────────────────────────────────────────────────────

def _reports_tab():
    st.markdown("#### 📊 Attendance Reports")

    teacher_id = st.session_state["user_id"]
    classes = get_teacher_classes(teacher_id)

    if not classes:
        st.info("No classes to report on.")
        return

    class_options = {f"{c['class_name']} — {c.get('subject', '')}": c for c in classes}
    selected_label = st.selectbox("Select Class", list(class_options.keys()), key="report_class")
    selected_class = class_options[selected_label]
    class_id = selected_class["id"]

    sessions = get_class_sessions(class_id)
    total_sessions = len(sessions)

    if total_sessions == 0:
        st.info("No sessions held for this class yet.")
        return

    st.markdown(f"**Total sessions held:** {total_sessions}")

    records = get_class_attendance_summary(class_id)
    summary_df = attendance_summary_df(records, total_sessions)

    if not summary_df.empty:
        attendance_summary_table(summary_df, title="Student Attendance Summary")

        # Chart
        fig = px.bar(
            summary_df,
            x="Name",
            y="Attendance %",
            color="Attendance %",
            color_continuous_scale=["red", "orange", "green"],
            range_color=[0, 100],
            title="Attendance % by Student",
            text="Attendance %"
        )
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    # Per-session records
    st.markdown("---")
    st.markdown("#### 📋 Session-wise Records")
    selected_session_label = st.selectbox(
        "Select Session",
        [format_date_only(s.get("session_date", s.get("created_at", ""))) + f" (ID: {s['id'][:6]}...)"
         for s in sessions],
        key="session_picker"
    )
    session_idx = [
        format_date_only(s.get("session_date", s.get("created_at", ""))) + f" (ID: {s['id'][:6]}...)"
        for s in sessions
    ].index(selected_session_label)
    chosen_session = sessions[session_idx]
    session_records = get_session_attendance(chosen_session["id"])

    if session_records:
        df = build_attendance_dataframe(session_records, [chosen_session])
        attendance_table(df, title=f"Session: {selected_session_label}")
    else:
        st.info("No attendance records for this session.")
