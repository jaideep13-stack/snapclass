import streamlit as st
import pandas as pd
from src.utils.helpers import status_badge


def attendance_table(df: pd.DataFrame, show_export: bool = True, title: str = "Attendance Records"):
    """
    Renders a styled attendance table with optional CSV export.
    """
    if df.empty:
        st.info("No attendance records found.")
        return

    st.markdown(f"#### {title}")
    st.dataframe(df, use_container_width=True, hide_index=True)

    if show_export:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Export as CSV",
            data=csv,
            file_name="attendance.csv",
            mime="text/csv",
            use_container_width=False
        )


def attendance_summary_table(df: pd.DataFrame, title: str = "Student Summary"):
    """
    Renders the attendance summary table with color-coded attendance %.
    """
    if df.empty:
        st.info("No data available.")
        return

    st.markdown(f"#### {title}")

    # Add status badge column
    if "Attendance %" in df.columns:
        df = df.copy()
        df["Status"] = df["Attendance %"].apply(status_badge)
        cols = ["Status", "Name", "Email", "Classes Attended", "Total Classes", "Attendance %"]
        df = df[[c for c in cols if c in df.columns]]

    st.dataframe(df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Export Summary CSV",
        data=csv,
        file_name="attendance_summary.csv",
        mime="text/csv"
    )
