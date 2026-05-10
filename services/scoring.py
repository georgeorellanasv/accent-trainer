from typing import Dict, List

# Key RP phonemes that get extra weight in scoring
RP_KEY_PHONEMES = {"θ", "ð", "ɑː", "ɔː", "əʊ", "ɪ", "æ", "ʌ", "ə"}

# Phonemes that Spanish speakers struggle with most - CRITICAL for RP
PROBLEM_PHONEMES = {"θ", "ð"}

def calculate_strict_score(word_scores: List[dict]) -> float:
    """
    VERY STRICT scoring for RP accent training.
    - Any /θ/ or /ð/ below 85 = major penalty
    - Need 95+ average to get 8+
    - Need 98+ to get 9+
    - Only perfect gets 10
    """
    if not word_scores:
        return 0.0

    total_weight = 0
    weighted_score = 0
    critical_penalty = 0

    for word in word_scores:
        word_acc = word.get("accuracy", 0)
        phonemes = word.get("phonemes", [])

        # Base weight for word
        weight = 1.0

        for p in phonemes:
            phoneme = p.get("phoneme", "")
            p_acc = p.get("accuracy", 0)

            if phoneme in PROBLEM_PHONEMES:
                # /θ/ and /ð/ are CRITICAL - triple weight
                weight += 2.0
                # Harsh penalty if below 85
                if p_acc < 85:
                    critical_penalty += (85 - p_acc) * 0.3
                if p_acc < 70:
                    # Very bad - cap the word score
                    word_acc = min(word_acc, p_acc * 0.6)
            elif phoneme in RP_KEY_PHONEMES:
                weight += 1.0
                if p_acc < 80:
                    critical_penalty += (80 - p_acc) * 0.1

        weighted_score += word_acc * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    raw_score = weighted_score / total_weight

    # Apply critical penalty
    raw_score = max(0, raw_score - critical_penalty)

    # VERY strict conversion curve:
    # 100 -> 10, 98 -> 9, 95 -> 8, 90 -> 6.5, 85 -> 5, 80 -> 4, 70 -> 2, 60 -> 1
    if raw_score >= 100:
        strict_score = 10.0
    elif raw_score >= 98:
        strict_score = 9.0 + (raw_score - 98) * 0.5
    elif raw_score >= 95:
        strict_score = 8.0 + (raw_score - 95) * 0.33
    elif raw_score >= 90:
        strict_score = 6.5 + (raw_score - 90) * 0.3
    elif raw_score >= 85:
        strict_score = 5.0 + (raw_score - 85) * 0.3
    elif raw_score >= 80:
        strict_score = 4.0 + (raw_score - 80) * 0.2
    elif raw_score >= 70:
        strict_score = 2.0 + (raw_score - 70) * 0.2
    elif raw_score >= 60:
        strict_score = 1.0 + (raw_score - 60) * 0.1
    else:
        strict_score = raw_score / 60

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
