from tests.quality.open_judge.cases import OPEN_JUDGE_CASES


def main() -> int:
    assert len(OPEN_JUDGE_CASES) == 9

    case_ids = [case.id for case in OPEN_JUDGE_CASES]
    assert len(case_ids) == len(set(case_ids))

    turns = [turn for case in OPEN_JUDGE_CASES for turn in case.turns]
    assert len(turns) == 25

    turn_ids = [turn.id for turn in turns]
    assert len(turn_ids) == len(set(turn_ids))

    for case in OPEN_JUDGE_CASES:
        assert case.id.startswith("OJ-")
        assert case.name.strip()
        assert case.tags
        assert case.turns

        for turn in case.turns:
            assert turn.question.strip()
            assert (
                turn.required_all
                or turn.required_any
                or turn.forbidden
                or turn.expected_cards
            ), turn.id

    print("Open Judge contract test: 9 cases, 25 turns, all contracts valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
