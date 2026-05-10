import os
import json
from openai import OpenAI
from fastapi import HTTPException

COACHING_SYSTEM = """You are a strict RP (Received Pronunciation) accent coach for Latin American Spanish speakers.
You receive Azure Pronunciation Assessment data with exact scores per word and phoneme.
Give specific, actionable tips for words that scored below 75. Be honest and direct.

Common Spanish→RP errors to reference:
- /θ/ (thin) → said as /s/ or /t/
- /ð/ (the, this) → said as /d/
- Non-rhotic R: RP drops R after vowels (water=/ˈwɔːtə/) — Spanish speakers keep it
- /ɪ/ vs /iː/ — Spanish only has one /i/
- /ɑː/ bath broadening (bath, dance, can't) — Spanish speakers use /a/
- /ʌ/ (cup, but) → said as /a/
- RP diphthongs: /əʊ/ not /oʊ/, /eɪ/ in day

Return ONLY valid JSON:
{
  "tips": [{"word": str, "tip": str, "phoneme_focus": str}],
  "focus": str,
  "encouragement": str
}
Keep tips under 25 words each. Be warm but precise and honest."""


def get_client() -> OpenAI:
    key = os.environ.get("CEREBRAS_API_KEY", "")
    if not key:
        raise HTTPException(503, "CEREBRAS_API_KEY not configured")
    return OpenAI(base_url="https://api.cerebras.ai/v1", api_key=key)


def get_coaching(phrase: dict, word_scores: list, attempt: int) -> dict:
    """
    Get AI coaching feedback based on pronunciation assessment.
    """
    try:
        client = get_client()
        problem_words = [w for w in word_scores if w["accuracy"] < 75]

        user_msg = (
            f'Phrase: "{phrase["en"]}"\n'
            f'IPA RP: {phrase["ipa_rp"]}\n'
            f'Target phonemes: {", ".join(phrase.get("target_phonemes", []))}\n'
            f'Attempt #{attempt}\n\n'
            f'Word scores (Azure):\n' +
            "\n".join(
                f'  {w["word"]}: {w["accuracy"]:.0f}/100'
                + (f' — worst phoneme: /{w["worst_phoneme"]}/ ({w["worst_phoneme_score"]:.0f}/100)'
                   if w.get("worst_phoneme") else "")
                for w in word_scores
            ) +
            f'\n\nProblem words: {[w["word"] for w in problem_words]}'
        )

        resp = client.chat.completions.create(
            model="llama3.1-8b",
            max_tokens=512,
            messages=[
                {"role": "system", "content": COACHING_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
        )

        raw = resp.choices[0].message.content.strip()

        # Handle markdown code blocks
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        return json.loads(raw.strip())

    except json.JSONDecodeError:
        return {
            "tips": [],
            "focus": phrase.get("notes", "Focus on the target phonemes."),
            "encouragement": "Keep practising — every attempt counts!",
        }
    except Exception:
        return {
            "tips": [],
            "focus": phrase.get("notes", "Focus on the target phonemes."),
            "encouragement": "Keep practising — every attempt counts!",
        }
