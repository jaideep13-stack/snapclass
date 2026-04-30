import streamlit as st
from src.utils.supabase_client import get_class_by_join_code, enroll_student


@st.dialog("Join Class")
def auto_enroll_dialog(join_code: str):
    """
    Dialog shown when a student opens the app with a ?join-code= URL param.
    Automatically looks up the class and prompts the student to confirm enrollment.
    """
    st.markdown("### 🎓 You've been invited to join a class!")

    if not join_code:
        st.error("Invalid or missing join code.")
        return

    with st.spinner("Looking up class..."):
        class_info = get_class_by_join_code(join_code)

    if not class_info:
        st.error(f"❌ No class found with join code **{join_code}**. It may have expired or been removed.")
        return

    st.success(f"Found: **{class_info['class_name']}** — {class_info.get('subject', '')}")
    st.markdown(f"**Join Code:** `{join_code}`")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Yes, Enroll Me", use_container_width=True, type="primary"):
            student_id = st.session_state.get("user_id")
            if not student_id:
                st.error("Session error. Please log in again.")
                return

            enrolled = enroll_student(class_info["id"], student_id)
            if enrolled:
                st.success(f"🎉 Enrolled in **{class_info['class_name']}** successfully!")
                st.rerun()
            else:
                st.info("You are already enrolled in this class.")
                st.rerun()

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.rerun()
