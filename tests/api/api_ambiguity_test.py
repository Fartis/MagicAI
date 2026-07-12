import json
import sys
import urllib.error
import urllib.request


BASE_URL = "http://127.0.0.1:8000"


def ask(question: str, session_id: str | None = None) -> dict:

    payload = {
        "question": question,
    }

    if session_id:

        payload["session_id"] = session_id

    request = urllib.request.Request(
        f"{BASE_URL}/ask",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=120) as response:

        return json.loads(
            response.read().decode("utf-8")
        )


def assert_contains(text: str, expected: str):

    if expected.lower() not in text.lower():

        raise AssertionError(
            f"Expected to find {expected!r} in:\n{text}"
        )


def assert_not_contains(text: str, forbidden: str):

    if forbidden.lower() in text.lower():

        raise AssertionError(
            f"Did not expect to find {forbidden!r} in:\n{text}"
        )


def main():

    errors = []

    print("=" * 80)
    print("MagicAI API Ambiguity Test")
    print("=" * 80)

    try:

        first = ask(
            "¿Qué ocurre si sacrifico un permanente con Korvold en mesa?"
        )

        answer = first["answer"]
        session_id = first["session_id"]

        if first.get("status") != "needs_clarification":
            raise AssertionError(
                f"Expected needs_clarification, got {first.get('status')!r}"
            )

        if first.get("origin") != "disambiguation":
            raise AssertionError(
                f"Expected disambiguation origin, got {first.get('origin')!r}"
            )

        print()
        print("Initial ambiguous answer:")
        print(answer)

        assert_contains(
            answer,
            "He encontrado varias cartas",
        )

        assert_contains(
            answer,
            "Korvold, Fae-Cursed King",
        )

        assert_contains(
            answer,
            "Korvold, Gleeful Glutton",
        )

        assert_contains(
            answer,
            "Respóndeme con el número",
        )

        if not session_id:

            raise AssertionError(
                "Expected a session_id in ambiguity response."
            )

    except Exception as exc:

        errors.append(
            f"Ambiguous Korvold prompt failed: {exc}"
        )

        session_id = None

    if session_id:

        try:

            second = ask(
                "Korvold, Fae-Cursed King",
                session_id=session_id,
            )

            answer = second["answer"]

            print()
            print("Resolved ambiguous answer:")
            print(answer)

            assert_not_contains(
                answer,
                "He encontrado varias cartas",
            )

            assert_contains(
                answer,
                "+1/+1",
            )

            if (
                "robas una carta" not in answer.lower()
                and "roba una carta" not in answer.lower()
            ):

                raise AssertionError(
                    f"Expected the answer to mention drawing a card:\n{answer}"
                )

            forbidden_patterns = [
                "food",
                "no se activa",
                "no desencadena",
                "no obtiene beneficio",
                "no hay otros efectos",
                "requiere sacrificar",
                "korvold mismo",
                "si el permanente sacrificado es korvold",
                "si sacrificas a korvold",
                "sacrificar a korvold",
                "aún así activa",
                "aun así activa",
            ]

            for pattern in forbidden_patterns:

                assert_not_contains(
                    answer,
                    pattern,
                )

        except Exception as exc:

            errors.append(
                f"Resolved Korvold answer failed: {exc}"
            )

    try:

        olivia = ask(
            "¿Qué hace Olivia?"
        )

        answer = olivia["answer"]

        print()
        print("Olivia ambiguous answer:")
        print(answer)

        assert_contains(
            answer,
            "He encontrado varias cartas",
        )

        assert_contains(
            answer,
            "Olivia",
        )

        assert_contains(
            answer,
            "Respóndeme con el número",
        )

    except Exception as exc:

        errors.append(
            f"Ambiguous Olivia prompt failed: {exc}"
        )

    print()
    print("=" * 80)
    print("RESULT")
    print("=" * 80)
    print(f"Errors: {len(errors)}")

    if errors:

        for error in errors:

            print(f"- {error}")

        sys.exit(1)

    print("OK")


if __name__ == "__main__":

    main()