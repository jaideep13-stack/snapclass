import numpy as np
import io

try:
    from resemblyzer import VoiceEncoder, preprocess_wav
    from pathlib import Path
    import librosa
    VOICE_RECOGNITION_AVAILABLE = True
    _encoder = None
except ImportError:
    VOICE_RECOGNITION_AVAILABLE = False
    _encoder = None


def _get_encoder():
    global _encoder
    if _encoder is None and VOICE_RECOGNITION_AVAILABLE:
        _encoder = VoiceEncoder()
    return _encoder


def get_voice_embedding(audio_bytes: bytes, sample_rate: int = 16000) -> list | None:
    """
    Convert audio bytes to a voice embedding vector.
    Returns None if voice recognition is not available or processing fails.
    """
    if not VOICE_RECOGNITION_AVAILABLE:
        return None

    try:
        encoder = _get_encoder()
        # Load audio with librosa
        audio_data, sr = librosa.load(
            io.BytesIO(audio_bytes),
            sr=sample_rate,
            mono=True
        )
        wav = preprocess_wav(audio_data, source_sr=sr)
        embedding = encoder.embed_utterance(wav)
        return embedding.tolist()
    except Exception:
        return None


def compare_voices(known_embedding: list, unknown_embedding: list, threshold: float = 0.75) -> bool:
    """
    Compare two voice embeddings using cosine similarity.
    Returns True if similarity is above threshold.
    """
    known = np.array(known_embedding)
    unknown = np.array(unknown_embedding)

    similarity = cosine_similarity(known, unknown)
    return similarity >= threshold


def voice_similarity_score(known_embedding: list, unknown_embedding: list) -> float:
    """Returns cosine similarity between two voice embeddings (0 to 1)."""
    known = np.array(known_embedding)
    unknown = np.array(unknown_embedding)
    return cosine_similarity(known, unknown)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def find_matching_student_voice(
    students: list,
    unknown_embedding: list,
    threshold: float = 0.75
) -> dict | None:
    """
    Find best voice match among students.
    Returns student dict or None.
    """
    best_match = None
    best_score = threshold - 0.01  # Just below threshold

    for student in students:
        stored = student.get("voice_embedding")
        if not stored:
            continue

        score = voice_similarity_score(stored, unknown_embedding)
        if score > best_score:
            best_score = score
            best_match = student

    return best_match
