import streamlit as st
from src.utils.supabase_client import sign_in, sign_up, sign_out, get_profile


def login(email: str, password: str) -> tuple[bool, str]:
    """
    Returns (success: bool, error_message: str)
    """
    try:
        response = sign_in(email, password)
        user = response.user
        if not user:
            return False, "Invalid email or password."

        profile = get_profile(user.id)
        if not profile:
            return False, "Profile not found. Please contact support."

        # Store in session state
        st.session_state['is_logged_in'] = True
        st.session_state['user_id'] = user.id
        st.session_state['user_email'] = user.email
        st.session_state['user_name'] = profile.get('full_name', 'User')
        st.session_state['user_role'] = profile.get('role', '')
        st.session_state['face_encoding'] = profile.get('face_encoding')
        st.session_state['voice_encoding'] = profile.get('voice_encoding')
        st.session_state['login_type'] = profile.get('role')

        return True, ""

    except Exception as e:
        err = str(e)
        if "Invalid login credentials" in err:
            return False, "Wrong email or password."
        return False, f"Login failed: {err}"


def register(email: str, password: str, full_name: str, role: str) -> tuple[bool, str]:
    """
    Returns (success: bool, error_message: str)
    """
    try:
        response = sign_up(email, password, full_name, role)
        if not response.user:
            return False, "Registration failed. Please try again."
        return True, ""
    except Exception as e:
        err = str(e)
        if "already registered" in err.lower() or "already exists" in err.lower():
            return False, "An account with this email already exists."
        return False, f"Registration failed: {err}"


def logout():
    try:
        sign_out()
    except Exception:
        pass
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def require_login():
    """Guard: redirect to home if not logged in."""
    if not st.session_state.get('is_logged_in'):
        st.session_state['login_type'] = None
        st.rerun()
