from magicai.validation.answer import validate_answer


KNOWLEDGE = """
QUESTION

Sire tiene Ward. ¿Ward usa la pila y puede responderse?

============================================================
CARDS

Sire
Creature — Eldrazi

Ward—Pay 7 life.

============================================================
RULES

702.21a Ward is a triggered ability.
603.1 Triggered abilities have a trigger condition and an effect.
405.1 The stack is a zone.
117.5 Each time a player would get priority, state-based actions are checked.
"""


def test_guard_rejects_incorrect_ward_procedure():
    bad = (
        "Ward se activa y se puede responder durante su resolución. El jugador "
        "paga para evitar que el hechizo se resuelva."
    )
    violations = validate_answer(bad, KNOWLEDGE)
    assert any("activated" in item.lower() for item in violations)
    assert any("ward resolution" in item.lower() for item in violations)
    assert any("paying" in item.lower() for item in violations)


def test_guard_accepts_correct_ward_procedure():
    good = (
        "Ward es una habilidad disparada que se pone en la pila. Los jugadores "
        "pueden responder antes de que se resuelva. Si el controlador del "
        "hechizo no paga el coste, Ward contrarresta ese hechizo."
    )
    assert validate_answer(good, KNOWLEDGE) == []


def main():
    tests = [value for name,value in sorted(globals().items()) if name.startswith('test_')]
    errors=[]
    for test in tests:
        try: test(); print(f"OK: {test.__name__}")
        except Exception as exc: errors.append((test.__name__,exc)); print(f"ERROR: {test.__name__}: {exc}")
    print(f"Tests: {len(tests)} · Errors: {len(errors)}")
    if errors: raise SystemExit(1)

if __name__ == '__main__': main()
