from typing import Dict, List

# Key RP phonemes that get extra weight in scoring
RP_KEY_PHONEMES = {"θ", "ð", "ɑː", "ɔː", "əʊ", "ɪ", "æ", "ʌ", "ə"}

# Phonemes that Spanish speakers struggle with most
PROBLEM_PHONEMES = {"θ", "ð"}  # Extra penalty for these

def calculate_strict_score(word_scores: List[dict]) -> float:
    """
    Calculate a strict 0-10 score from Azure word scores.
    Applies extra penalties for RP-critical phonemes.
    """
    if not word_scores:
        return 0.0

    total_weight = 0
    weighted_score = 0

    for word in word_scores:
        word_acc = word.get("accuracy", 0)
        phonemes = word.get("phonemes", [])

        # Base weight for word
        weight = 1.0

        # Check for problem phonemes
        for p in phonemes:
            phoneme = p.get("phoneme", "")
            p_acc = p.get("accuracy", 0)

            if phoneme in PROBLEM_PHONEMES:
                # Double weight for /θ/ and /ð/
                weight += 1.0
                # Extra penalty if they're bad
                if p_acc < 60:
                    word_acc = min(word_acc, p_acc * 0.8)
            elif phoneme in RP_KEY_PHONEMES:
                weight += 0.5

        weighted_score += word_acc * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    # Convert 0-100 to 0-10 scale
    raw_score = weighted_score / total_weight

    # Apply strictness curve (makes it harder to get high scores)
    # 100 -> 10, 90 -> 8.5, 80 -> 7, 70 -> 5.5, 60 -> 4
    strict_score = (raw_score / 100) * 10
    if raw_score < 90:
        strict_score -= (90 - raw_score) * 0.05

    return max(0, min(10, round(strict_score, 1)))


def get_phoneme_scores(word_scores: List[dict]) -> Dict[str, float]:
    """
    Extract individual phoneme scores from word scores.
    Returns dict mapping phoneme -> score
    """
    phoneme_scores = {}
    phoneme_counts = {}

    for word in word_scores:
        for p in word.get("phonemes", []):
            phoneme = p.get("phoneme", "")
            accuracy = p.get("accuracy", 0)

            if phoneme not in phoneme_scores:
                phoneme_scores[phoneme] = 0
                phoneme_counts[phoneme] = 0

            phoneme_scores[phoneme] += accuracy
            phoneme_counts[phoneme] += 1

    # Average scores
    for phoneme in phoneme_scores:
        if phoneme_counts[phoneme] > 0:
            phoneme_scores[phoneme] = round(
                phoneme_scores[phoneme] / phoneme_counts[phoneme], 1
            )

    return phoneme_scores


def get_problem_areas(phoneme_scores: Dict[str, float], threshold: float = 75) -> List[str]:
    """
    Return list of phonemes below threshold, sorted by severity.
    """
    problems = [
        (phoneme, score)
        for phoneme, score in phoneme_scores.items()
        if score < threshold
    ]
    problems.sort(key=lambda x: x[1])  # Worst first
    return [p[0] for p in problems]
