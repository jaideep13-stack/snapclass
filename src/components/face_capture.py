import streamlit as st
from src.utils.face_utils import get_face_encoding, count_faces


def face_capture_widget(label: str = "Take a photo", key: str = "face_photo") -> list | None:
    """
    A reusable widget that captures a photo from the user's camera,
    validates the face, and returns its encoding.

    Returns face encoding (list) or None if no valid face found.
    """
    st.markdown(f"**{label}**")
    st.caption("Make sure your face is clearly visible, well-lit, and centred.")

    photo = st.camera_input("📷 Click to capture", key=key, label_visibility="collapsed")

    if photo is None:
        return None

    image_bytes = photo.getvalue()

    with st.spinner("Detecting face..."):
        num_faces = count_faces(image_bytes)

        if num_faces == 0:
            st.error("❌ No face detected. Please try again with better lighting.")
            return None

        if num_faces > 1:
            st.warning("⚠️ Multiple faces detected. Please make sure only your face is in the frame.")
            return None

        encoding = get_face_encoding(image_bytes)

        if encoding is None:
            st.error("❌ Could not process face. Please retake the photo.")
            return None

    st.success("✅ Face captured successfully!")
    return encoding
