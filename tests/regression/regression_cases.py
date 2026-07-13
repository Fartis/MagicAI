from tests.quality.open_judge.cases import OPEN_JUDGE_CASES


# Legacy regression runners reuse the same conversational corpus as the
# Open Judge Gauntlet. Semantic expectations live only in open_judge/cases.py.
TESTS = [
    {
        "name": case.name,
        "questions": [turn.question for turn in case.turns],
    }
    for case in OPEN_JUDGE_CASES
]
