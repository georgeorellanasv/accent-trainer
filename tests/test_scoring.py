import pytest
from services.scoring import calculate_strict_score, get_phoneme_scores

def test_calculate_strict_score_perfect():
    word_scores = [
        {"word": "think", "accuracy": 95, "phonemes": [{"phoneme": "θ", "accuracy": 95}]},
        {"word": "the", "accuracy": 92, "phonemes": [{"phoneme": "ð", "accuracy": 92}]},
    ]
    score = calculate_strict_score(word_scores)
    assert score >= 9.0

def test_calculate_strict_score_poor_th():
    word_scores = [
        {"word": "think", "accuracy": 50, "phonemes": [{"phoneme": "θ", "accuracy": 40}]},
        {"word": "the", "accuracy": 88, "phonemes": [{"phoneme": "ð", "accuracy": 88}]},
    ]
    score = calculate_strict_score(word_scores)
    assert score < 7.0  # Penalized for poor /θ/

def test_get_phoneme_scores_extracts_all():
    word_scores = [
        {"word": "think", "phonemes": [{"phoneme": "θ", "accuracy": 80}, {"phoneme": "ɪ", "accuracy": 90}]},
        {"word": "the", "phonemes": [{"phoneme": "ð", "accuracy": 70}]},
    ]
    result = get_phoneme_scores(word_scores)
    assert result["θ"] == 80
    assert result["ð"] == 70
    assert result["ɪ"] == 90
