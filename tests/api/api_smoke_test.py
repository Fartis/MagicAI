import json
import os
import sys
import time
import urllib.error
import urllib.request


API_URL = os.environ.get(
    "MAGICAI_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


def post_json(path: str, payload: dict) -> dict:

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        API_URL + path,
        data=data,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=120) as response:

        return json.loads(
            response.read().decode("utf-8")
        )



def get_json(path: str) -> dict:
    with urllib.request.urlopen(API_URL + path, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json_error(path: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        API_URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        urllib.request.urlopen(request, timeout=10)
    except urllib.error.HTTPError as error:
        return (
            error.code,
            json.loads(error.read().decode("utf-8")),
        )

    raise AssertionError("Expected an HTTP error response.")

def assert_contains(text: str, expected: list[str], label: str):

    lower = text.lower()

    missing = [
        item
        for item in expected
        if item.lower() not in lower
    ]

    if missing:

        raise AssertionError(
            f"{label}: missing {missing!r} in answer:\n{text}"
        )
    
def assert_not_contains(text: str, forbidden: list[str], label: str):

    lower = text.lower()

    present = [
        item
        for item in forbidden
        if item.lower() in lower
    ]

    if present:

        raise AssertionError(
            f"{label}: unexpected {present!r} in answer:\n{text}"
        )




def assert_judge_result(payload: dict, label: str) -> None:
    required = [
        "schema_version",
        "answer",
        "session_id",
        "question",
        "status",
        "origin",
        "confidence",
        "authority",
        "cards",
        "rules",
        "rulings",
        "retrieval_queries",
        "assumptions",
        "warnings",
        "source_versions",
        "source_health",
        "validation_attempts",
    ]
    missing = [key for key in required if key not in payload]
    if missing:
        raise AssertionError(f"{label}: missing JudgeResult fields {missing!r}")

    if payload.get("authority") != "judge":
        raise AssertionError(f"{label}: unexpected authority {payload.get('authority')!r}")


def main():

    started = time.perf_counter()

    print("=" * 80)
    print("MagicAI API Smoke Test")
    print("=" * 80)
    print(f"API URL: {API_URL}")
    print()

    metadata = get_json("/meta")
    if metadata.get("judge_result_schema_version") != "1.0":
        raise AssertionError(f"Unexpected schema version: {metadata!r}")

    health = get_json("/health")
    if "ready" not in health or "sources" not in health:
        raise AssertionError(f"Invalid health payload: {health!r}")

    error_status, error_payload = post_json_error(
        "/ask",
        {"question": "   "},
    )
    if error_status != 422:
        raise AssertionError(f"Expected 422, got {error_status}")
    if error_payload.get("error", {}).get("code") != "invalid_request":
        raise AssertionError(f"Invalid structured error: {error_payload!r}")

    #
    # Session A: Young Wolf
    #

    print("[1/4] Young Wolf initial question")

    response_1 = post_json(
        "/ask",
        {
            "question": "¿Qué hace Young Wolf?",
        },
    )

    assert_judge_result(response_1, "Young Wolf initial response")

    session_young_wolf = response_1.get("session_id")
    answer_1 = response_1.get("answer", "")

    if not session_young_wolf:

        raise AssertionError("Young Wolf response has no session_id")

    assert_contains(
        answer_1,
        [
            "Young Wolf",
            "Undying",
        ],
        "Young Wolf initial answer",
    )

    print(f"  session_id: {session_young_wolf}")
    print("  OK")
    print()

    print("[2/4] Young Wolf follow-up with same session")

    response_2 = post_json(
        "/ask",
        {
            "session_id": session_young_wolf,
            "question": "¿Y si muere?",
        },
    )

    answer_2 = response_2.get("answer", "")
    session_2 = response_2.get("session_id")

    if session_2 != session_young_wolf:

        raise AssertionError(
            "Follow-up did not preserve Young Wolf session_id"
        )

    assert_contains(
        answer_2,
        [
            "Undying",
            "campo",
        ],
        "Young Wolf follow-up answer",
    )

    print("  OK")
    print()

    #
    # Session B: Sol Ring
    #

    print("[3/4] Sol Ring initial question, separate session")

    response_3 = post_json(
        "/ask",
        {
            "question": "¿Qué hace Sol Ring?",
        },
    )

    session_sol_ring = response_3.get("session_id")
    answer_3 = response_3.get("answer", "")

    if not session_sol_ring:

        raise AssertionError("Sol Ring response has no session_id")

    if session_sol_ring == session_young_wolf:

        raise AssertionError(
            "Sol Ring reused Young Wolf session unexpectedly"
        )

    assert_contains(
        answer_3,
        [
            "Sol Ring",
            "incoloro",
        ],
        "Sol Ring initial answer",
    )

    print(f"  session_id: {session_sol_ring}")
    print("  OK")
    print()

    print("[4/4] Sol Ring follow-up with same session")

    response_4 = post_json(
        "/ask",
        {
            "session_id": session_sol_ring,
            "question": "¿Merece la pena jugarlo en Commander?",
            "auto_handoff": False,
        },
    )

    assert_judge_result(response_4, "Sol Ring strategy response")

    answer_4 = response_4.get("answer", "")
    session_4 = response_4.get("session_id")

    if session_4 != session_sol_ring:

        raise AssertionError(
            "Follow-up did not preserve Sol Ring session_id"
        )

    assert_contains(
        answer_4,
        [
            "Sol Ring",
            "Commander",
        ],
        "Sol Ring follow-up answer",
    )
    
    if response_4.get("status") != "strategy_required":
        raise AssertionError(
            f"Sol Ring follow-up: expected strategy_required, got {response_4.get('status')!r}"
        )

    assert_not_contains(
        answer_4,
        [
            "He encontrado varias cartas",
            "¿A cuál te refieres?",
            "Commander Eesha",
            "Commander's Plate",
        ],
        "Sol Ring follow-up answer",
    )

    print("  OK")
    print()

    elapsed = time.perf_counter() - started

    print("=" * 80)
    print("API Smoke Test finished")
    print("=" * 80)
    print("Questions : 4")
    print("Errors    : 0")
    print(f"Time      : {elapsed:.2f}s")
    print("=" * 80)


if __name__ == "__main__":

    try:

        main()

    except urllib.error.URLError as error:

        print("ERROR: Could not connect to MagicAI API.")
        print(f"API URL: {API_URL}")
        print(error)
        sys.exit(1)

    except Exception as error:

        print("ERROR:", error)
        sys.exit(1)
