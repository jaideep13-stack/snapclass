import streamlit as st
from src.utils.auth import login, register
from src.components.face_capture import face_capture_widget
from src.utils.supabase_client import save_face_encoding, get_profile


def home_screen():
    _render_hero()

    tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register"])

    with tab_login:
        _render_login()

    with tab_register:
        _render_register()


# ─── Hero ─────────────────────────────────────────────────────────────────────

def _render_hero():
    st.markdown("""
        <div style='text-align:center; padding: 2rem 0 1rem 0;'>
            <h1 style='font-size:2.8rem; font-weight:800; margin-bottom:0;'>📸 SnapClass</h1>
            <p style='font-size:1.15rem; color:#666; margin-top:0.4rem;'>
                AI-powered attendance using Face & Voice Recognition
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
            <div style='background:#f0f4ff; border-radius:12px; padding:1rem; text-align:center;'>
                <h3>🧠</h3>
                <b>AI Recognition</b>
                <p style='font-size:0.85rem; color:#555;'>Face + Voice based attendance</p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div style='background:#f0fff4; border-radius:12px; padding:1rem; text-align:center;'>
                <h3>⚡</h3>
                <b>Instant Marking</b>
                <p style='font-size:0.85rem; color:#555;'>Mark 30+ students in seconds</p>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
            <div style='background:#fff8f0; border-radius:12px; padding:1rem; text-align:center;'>
                <h3>📊</h3>
                <b>Live Analytics</b>
                <p style='font-size:0.85rem; color:#555;'>Attendance reports & trends</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)


# ─── Login ────────────────────────────────────────────────────────────────────

def _render_login():
    st.markdown("#### Welcome back!")

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        role = st.selectbox("Login as", ["teacher", "student"])
        submitted = st.form_submit_button("Login", use_container_width=True, type="primary")

    if submitted:
        if not email or not password:
            st.error("Please enter your email and password.")
            return

        with st.spinner("Logging in..."):
            success, error = login(email, password)

        if success:
            # Role check
            if st.session_state.get("user_role") != role:
                st.error(f"This account is registered as a **{st.session_state.get('user_role')}**, not a {role}.")
                from src.utils.auth import logout
                logout()
                return
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error(error)


# ─── Register ─────────────────────────────────────────────────────────────────

def _render_register():
    st.markdown("#### Create your account")

    role = st.selectbox("I am a", ["student", "teacher"], key="reg_role")

    with st.form("register_form"):
        full_name = st.text_input("Full Name", placeholder="Aarav Sharma")
        email = st.text_input("Email", placeholder="aarav@example.com", key="reg_email")
        password = st.text_input("Password", type="password", placeholder="Min. 8 characters", key="reg_pass")
        confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="reg_confirm")
        submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")

    if submitted:
        if not full_name or not email or not password:
            st.error("All fields are required.")
            return
        if password != confirm:
            st.error("Passwords do not match.")
            return
        if len(password) < 8:
            st.error("Password must be at least 8 characters.")
            return

        with st.spinner("Creating account..."):
            success, error = register(email, password, full_name, role)

        if success:
            st.success("✅ Account created! Please check your email to verify your account, then log in.")
        else:
            st.error(error)

    # Face registration section (only for students, after account creation)
    if st.session_state.get('is_logged_in') and st.session_state.get('user_role') == 'student':
        _face_registration_section()


def _face_registration_section():
    st.markdown("---")
    st.markdown("#### 📸 Register Your Face")
    st.info("Register your face so the system can mark your attendance automatically.")

    if st.session_state.get("face_encoding"):
        st.success("✅ Face already registered.")
        if st.button("Re-register Face"):
            _do_face_registration()
    else:
        _do_face_registration()


def _do_face_registration():
    encoding = face_capture_widget(
        label="Take a clear photo of your face",
        key="register_face"
    )
    if encoding:
        with st.spinner("Saving face data..."):
            save_face_encoding(st.session_state["user_id"], encoding)
            st.session_state["face_encoding"] = encoding
        st.success("✅ Face registered successfully!")
