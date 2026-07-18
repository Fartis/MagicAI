from __future__ import annotations

from magicai.language.detection import LanguageDecision, detect_language


def resolve_language_policy(
    text: str,
    *,
    session_language: str | None = None,
    default_language: str = "es",
) -> LanguageDecision:
    session = session_language if session_language in {"es", "en"} else default_language
    input_language, confidence, spanish_score, english_score = detect_language(
        text,
        default=session,
    )

    # A conversation only changes language when the current turn gives a clear
    # signal. Ambiguous turns containing English card names or rules keywords
    # inherit the established session language.
    if confidence == "high":
        response_language = input_language
        locked = True
    else:
        response_language = session
        locked = bool(session_language in {"es", "en"})

    return LanguageDecision(
        input_language=input_language,
        session_language=session,
        response_language=response_language,
        confidence=confidence,
        locked=locked,
        spanish_score=spanish_score,
        english_score=english_score,
    )
