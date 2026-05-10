from typing import Dict, List

# Azure Speech SDK phoneme to IPA mapping for en-GB
# Azure uses SAPI-like phonemes, we convert to IPA for display
AZURE_TO_IPA = {
    # Consonants - TH sounds (critical for Spanish speakers)
    "θ": "θ",  # voiceless th (think)
    "ð": "ð",  # voiced th (the)
    "th": "θ",  # alternate representation
    "dh": "ð",  # alternate representation

    # Vowels
    "ɪ": "ɪ",  # KIT
    "iː": "iː", # FLEECE
    "i": "iː",  # sometimes Azure omits length mark
    "iy": "iː", # SAPI style
    "ih": "ɪ",  # SAPI style
    "æ": "æ",  # TRAP
    "ae": "æ",  # alternate
    "ʌ": "ʌ",  # STRUT
    "ah": "ʌ",  # SAPI style
    "ɑː": "ɑː", # BATH/PALM
    "ɑ": "ɑː",  # without length
    "aa": "ɑː", # SAPI style
    "ə": "ə",  # schwa
    "ax": "ə",  # SAPI style
    "əʊ": "əʊ", # GOAT
    "oʊ": "əʊ", # American-style
    "ow": "əʊ", # SAPI style
    "eɪ": "eɪ", # FACE
    "ey": "eɪ", # SAPI style
    "aɪ": "aɪ", # PRICE
    "ay": "aɪ", # SAPI style
    "ɔː": "ɔː", # THOUGHT
    "ɔ": "ɔː",  # without length
    "ao": "ɔː", # SAPI style
    "ʊ": "ʊ",  # FOOT
    "uh": "ʊ",  # SAPI style
    "uː": "uː", # GOOSE
    "uw": "uː", # SAPI style
    "ɜː": "ɜː", # NURSE
    "er": "ɜː", # SAPI style
    "e": "e",   # DRESS
    "eh": "e",  # SAPI style
}

# Key RP phonemes that get extra weight in scoring
RP_KEY_PHONEMES = {"θ", "ð", "ɑː", "ɔː", "əʊ", "ɪ", "æ", "ʌ", "ə"}

# Phonemes that Spanish speakers struggle with most - CRITICAL for RP
PROBLEM_PHONEMES = {"θ", "ð"}

def normalize_phoneme(phoneme: str) -> str:
    """Convert Azure phoneme to standard IPA."""
    return AZURE_TO_IPA.get(phoneme, phoneme)

# Word to phoneme mapping for common RP practice words
WORD_PHONEMES = {
    # θ words (voiceless th)
    "think": ["θ"], "thought": ["θ"], "through": ["θ"], "three": ["θ"],
    "thing": ["θ"], "third": ["θ"], "think": ["θ"], "thanks": ["θ"],
    "thursday": ["θ"], "therapy": ["θ"], "thick": ["θ"], "thin": ["θ"],
    "thaw": ["θ"], "throw": ["θ"], "threat": ["θ"], "throne": ["θ"],
    "bath": ["θ", "ɑː"], "path": ["θ", "ɑː"], "cloth": ["θ"],
    "wealth": ["θ"], "health": ["θ"], "teeth": ["θ", "iː"],
    "month": ["θ"], "earth": ["θ", "ɜː"], "worth": ["θ", "ɜː"],

    # ð words (voiced th)
    "the": ["ð"], "this": ["ð"], "that": ["ð"], "these": ["ð"],
    "those": ["ð"], "there": ["ð"], "their": ["ð"], "they": ["ð"],
    "them": ["ð"], "then": ["ð"], "than": ["ð"], "thus": ["ð"],
    "though": ["ð"], "although": ["ð"], "mother": ["ð"], "father": ["ð"],
    "brother": ["ð"], "other": ["ð"], "another": ["ð"], "together": ["ð"],
    "weather": ["ð"], "whether": ["ð"], "feather": ["ð"], "leather": ["ð"],
    "rather": ["ð", "ɑː"], "bother": ["ð"], "gather": ["ð"],
    "with": ["ð"], "within": ["ð"], "without": ["ð"],
    "breathe": ["ð", "iː"], "bathe": ["ð"], "soothe": ["ð"],

    # ɪ words (short i)
    "sit": ["ɪ"], "bit": ["ɪ"], "ship": ["ɪ"], "fish": ["ɪ"],
    "is": ["ɪ"], "it": ["ɪ"], "in": ["ɪ"], "if": ["ɪ"],
    "this": ["ɪ", "ð"], "with": ["ɪ", "ð"], "which": ["ɪ"],
    "will": ["ɪ"], "still": ["ɪ"], "fill": ["ɪ"], "bill": ["ɪ"],
    "big": ["ɪ"], "pig": ["ɪ"], "dig": ["ɪ"], "fig": ["ɪ"],
    "quick": ["ɪ"], "thick": ["ɪ", "θ"], "sick": ["ɪ"], "pick": ["ɪ"],
    "little": ["ɪ"], "middle": ["ɪ"], "riddle": ["ɪ"],
    "dreadful": ["ɪ"], "beautiful": ["ɪ"], "wonderful": ["ɪ"],

    # iː words (long ee)
    "see": ["iː"], "bee": ["iː"], "free": ["iː"], "tree": ["iː"],
    "beat": ["iː"], "seat": ["iː"], "meat": ["iː"], "heat": ["iː"],
    "sheep": ["iː"], "deep": ["iː"], "keep": ["iː"], "sleep": ["iː"],
    "read": ["iː"], "lead": ["iː"], "need": ["iː"], "feed": ["iː"],
    "these": ["iː", "ð"], "please": ["iː"], "cheese": ["iː"],

    # æ words (cat vowel)
    "cat": ["æ"], "bat": ["æ"], "hat": ["æ"], "fat": ["æ"],
    "bad": ["æ"], "sad": ["æ"], "mad": ["æ"], "dad": ["æ"],
    "man": ["æ"], "can": ["æ"], "pan": ["æ"], "ran": ["æ"],
    "that": ["æ", "ð"], "have": ["æ"], "has": ["æ"], "had": ["æ"],
    "apple": ["æ"], "happy": ["æ"], "matter": ["æ"],

    # ʌ words (cup vowel)
    "cup": ["ʌ"], "but": ["ʌ"], "cut": ["ʌ"], "shut": ["ʌ"],
    "love": ["ʌ"], "above": ["ʌ"], "come": ["ʌ"], "some": ["ʌ"],
    "done": ["ʌ"], "none": ["ʌ"], "one": ["ʌ"], "won": ["ʌ"],
    "money": ["ʌ"], "honey": ["ʌ"], "funny": ["ʌ"], "sunny": ["ʌ"],
    "mother": ["ʌ", "ð"], "brother": ["ʌ", "ð"], "other": ["ʌ", "ð"],
    "another": ["ʌ", "ð"], "country": ["ʌ"], "young": ["ʌ"],

    # ɑː words (bath/palm vowel)
    "bath": ["ɑː", "θ"], "path": ["ɑː", "θ"], "grass": ["ɑː"],
    "class": ["ɑː"], "glass": ["ɑː"], "pass": ["ɑː"], "last": ["ɑː"],
    "fast": ["ɑː"], "past": ["ɑː"], "cast": ["ɑː"], "ask": ["ɑː"],
    "task": ["ɑː"], "mask": ["ɑː"], "basket": ["ɑː"],
    "father": ["ɑː", "ð"], "rather": ["ɑː", "ð"], "after": ["ɑː"],
    "car": ["ɑː"], "far": ["ɑː"], "star": ["ɑː"], "bar": ["ɑː"],
    "heart": ["ɑː"], "part": ["ɑː"], "start": ["ɑː"], "art": ["ɑː"],

    # ə words (schwa)
    "about": ["ə"], "again": ["ə"], "away": ["ə"], "ago": ["ə"],
    "today": ["ə"], "tomorrow": ["ə"], "together": ["ə", "ð"],
    "doctor": ["ə"], "teacher": ["ə"], "worker": ["ə"],
    "weather": ["ə", "ð"], "father": ["ə", "ð"], "mother": ["ə", "ð"],
    "water": ["ə"], "after": ["ə"], "under": ["ə"], "over": ["ə"],
    "i": ["aɪ"],  # pronoun

    # əʊ words (goat vowel)
    "go": ["əʊ"], "no": ["əʊ"], "so": ["əʊ"], "know": ["əʊ"],
    "show": ["əʊ"], "grow": ["əʊ"], "slow": ["əʊ"], "flow": ["əʊ"],
    "home": ["əʊ"], "phone": ["əʊ"], "stone": ["əʊ"], "bone": ["əʊ"],
    "boat": ["əʊ"], "coat": ["əʊ"], "goat": ["əʊ"], "float": ["əʊ"],
    "road": ["əʊ"], "load": ["əʊ"], "code": ["əʊ"], "mode": ["əʊ"],
    "those": ["əʊ", "ð"], "although": ["əʊ", "ð"],
}

def get_phonemes_for_word(word: str) -> List[str]:
    """Get the target phonemes for a word."""
    return WORD_PHONEMES.get(word.lower(), [])

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
            raw_phoneme = p.get("phoneme", "")
            phoneme = normalize_phoneme(raw_phoneme)  # Convert to IPA
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
    Uses word-to-phoneme mapping since Azure doesn't return phoneme names.
    Returns dict mapping IPA phoneme -> score
    """
    phoneme_scores = {}
    phoneme_counts = {}

    for word_data in word_scores:
        word = word_data.get("word", "").lower()
        word_accuracy = word_data.get("accuracy", 0)

        # Get phonemes for this word from our mapping
        word_phonemes = get_phonemes_for_word(word)

        for phoneme in word_phonemes:
            if phoneme not in phoneme_scores:
                phoneme_scores[phoneme] = 0
                phoneme_counts[phoneme] = 0

            phoneme_scores[phoneme] += word_accuracy
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
