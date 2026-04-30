import numpy as np
from PIL import Image
import io

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False


def image_to_rgb_array(image_bytes: bytes) -> np.ndarray:
    """Convert image bytes to RGB numpy array."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.array(img)


def get_face_encoding(image_bytes: bytes) -> list | None:
    """
    Detect face in image and return its encoding as a list.
    Returns None if no face is found or face_recognition not available.
    """
    if not FACE_RECOGNITION_AVAILABLE:
        return None

    img_array = image_to_rgb_array(image_bytes)
    encodings = face_recognition.face_encodings(img_array)

    if not encodings:
        return None

    return encodings[0].tolist()


def compare_faces(known_encoding: list, unknown_encoding: list, tolerance: float = 0.5) -> bool:
    """
    Compare two face encodings.
    Returns True if they match within the given tolerance.
    """
    if not FACE_RECOGNITION_AVAILABLE:
        return False

    known = np.array(known_encoding)
    unknown = np.array(unknown_encoding)

    results = face_recognition.compare_faces([known], unknown, tolerance=tolerance)
    return bool(results[0])


def face_distance(known_encoding: list, unknown_encoding: list) -> float:
    """
    Returns the Euclidean distance between two face encodings.
    Lower = more similar. Typical threshold is 0.5.
    """
    if not FACE_RECOGNITION_AVAILABLE:
        return 1.0

    known = np.array(known_encoding)
    unknown = np.array(unknown_encoding)
    distances = face_recognition.face_distance([known], unknown)
    return float(distances[0])


def find_matching_student(
    students: list,
    unknown_encoding: list,
    tolerance: float = 0.5
) -> dict | None:
    """
    Given a list of student dicts (each with 'face_encoding'),
    find and return the closest matching student.
    Returns None if no match found.
    """
    best_match = None
    best_distance = tolerance + 1  # Start above threshold

    for student in students:
        stored = student.get("face_encoding")
        if not stored:
            continue

        dist = face_distance(stored, unknown_encoding)
        if dist < best_distance:
            best_distance = dist
            best_match = student

    if best_distance <= tolerance:
        return best_match
    return None


def count_faces(image_bytes: bytes) -> int:
    """Return how many faces are detected in an image."""
    if not FACE_RECOGNITION_AVAILABLE:
        return 0

    img_array = image_to_rgb_array(image_bytes)
    locations = face_recognition.face_locations(img_array)
    return len(locations)
