from magicai.retrieval.concept_evidence import (
    detected_evidence_concepts,
    mandatory_rule_numbers,
)


def test_ward_pins_trigger_stack_and_priority_rules():
    rules = mandatory_rule_numbers("Sire tiene Ward. ¿Usa la pila y puedo responder?")
    assert rules == ("702.21a", "603.1", "405.1", "117.5")


def test_source_independence_pins_resolution_rules():
    rules = mandatory_rule_numbers(
        "Activo una habilidad, destruyen su fuente y ya está en la pila. ¿Se resuelve?"
    )
    assert rules == ("113.7a", "405.1", "608.2h", "609.3")


def test_unrelated_question_has_no_pinned_evidence():
    assert detected_evidence_concepts("¿Cuántas cartas robo?") == ()
    assert mandatory_rule_numbers("¿Cuántas cartas robo?") == ()


def main():
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    errors=[]
    for test in tests:
        try:
            test(); print(f"OK: {test.__name__}")
        except Exception as exc:
            errors.append((test.__name__,exc)); print(f"ERROR: {test.__name__}: {exc}")
    print(f"Tests: {len(tests)} · Errors: {len(errors)}")
    if errors: raise SystemExit(1)

if __name__ == '__main__': main()
