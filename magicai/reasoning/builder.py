from magicai.reasoning.actions import ACTIONS


def build_reasoning(question: str, language: str = "es") -> list[str]:

    language = _normalize_language(language)

    detected_actions = detect_actions(question)

    hints = []

    for action in detected_actions:

        action_name = action[f"name_{language}"]

        if language == "es":
            hints.append(
                f"Acción detectada: {action_name}."
            )
        else:
            hints.append(
                f"Action detected: {action_name}."
            )

    return hints


def extract_action_search_terms(question: str) -> list[str]:

    detected_actions = detect_actions(question)

    terms = []

    for action in detected_actions:

        for term in action.get("search_terms", []):

            if term not in terms:

                terms.append(term)

    return terms


def detect_actions(question: str) -> list[dict]:

    q = question.lower()

    detected = []

    for action in ACTIONS:

        if _matches_action(q, action["patterns"]):

            detected.append(action)

    return detected


def _matches_action(question: str, patterns: list[str]) -> bool:

    for pattern in patterns:

        if pattern in question:

            return True

    return False


def _normalize_language(language: str) -> str:

    if language in ("es", "en"):

        return language

    return "es"
