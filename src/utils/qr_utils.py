import segno
import io
import base64


def generate_join_qr(join_code: str, base_url: str = "https://your-app.streamlit.app") -> str:
    """
    Generate a QR code for class join link.
    Returns base64 encoded PNG string for display in Streamlit.
    """
    join_url = f"{base_url}/?join-code={join_code}"
    qr = segno.make_qr(join_url, error='h')

    buffer = io.BytesIO()
    qr.save(buffer, kind='png', scale=8, dark='#1a1a2e', light='#ffffff')
    buffer.seek(0)

    encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return encoded


def qr_to_html(base64_str: str, size: int = 250) -> str:
    """Return an HTML img tag for the QR code."""
    return f'<img src="data:image/png;base64,{base64_str}" width="{size}" style="border-radius:8px;" />'


def generate_join_code(length: int = 6) -> str:
    """Generate a random uppercase alphanumeric join code."""
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))
