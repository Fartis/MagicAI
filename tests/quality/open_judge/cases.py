from __future__ import annotations

from .models import (
    ForbiddenClaim,
    OpenJudgeCase,
    OpenJudgeOutcome,
    OpenJudgeTurn,
)


OPEN_JUDGE_CASES: tuple[OpenJudgeCase, ...] = (
    OpenJudgeCase(
        id="OJ-001",
        name="Young Wolf zone changes",
        tags=("conversation", "undying", "zones", "sacrifice"),
        turns=(
            OpenJudgeTurn(
                id="OJ-001-01",
                question="¿Qué hace Young Wolf?",
                required_all=("Young Wolf",),
                required_any=(
                    ("Undying", "Persistencia"),
                    ("+1/+1", "contador +1/+1"),
                    ("muere", "cementerio"),
                ),
                forbidden=(
                    ForbiddenClaim("Young Wolf tiene prisa"),
                    ForbiddenClaim("Young Wolf tiene haste"),
                ),
                expected_cards=("Young Wolf",),
            ),
            OpenJudgeTurn(
                id="OJ-001-02",
                question="¿Y si muere?",
                required_any=(
                    ("cementerio", "muere"),
                    ("no tenía", "sin contador", "sin contadores"),
                    ("vuelve", "regresa", "retorna"),
                    ("+1/+1", "contador +1/+1"),
                ),
                expected_cards=("Young Wolf",),
                missing_outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
            ),
            OpenJudgeTurn(
                id="OJ-001-03",
                question="¿Y si lo sacrifico?",
                required_any=(
                    ("sacrificar", "sacrificio"),
                    ("cementerio", "muere"),
                    ("Undying", "vuelve", "regresa", "retorna"),
                ),
                forbidden=(
                    ForbiddenClaim("sacrificar no cuenta como morir"),
                    ForbiddenClaim("sacrificar no dispara Undying"),
                ),
                expected_cards=("Young Wolf",),
                missing_outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
            ),
            OpenJudgeTurn(
                id="OJ-001-04",
                question="¿Y si lo exilio?",
                required_any=(
                    ("exilio", "exilias", "exiliar"),
                    ("no se dispara", "no activa", "no activarás", "no vuelve"),
                    ("no entra al cementerio", "no va al cementerio"),
                ),
                forbidden=(
                    ForbiddenClaim("vuelve al campo de batalla con un contador"),
                    ForbiddenClaim("Undying se dispara al exiliar"),
                ),
                expected_cards=("Young Wolf",),
                missing_outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
            ),
        ),
    ),
    OpenJudgeCase(
        id="OJ-002",
        name="Prossh cast trigger and sacrifice wording",
        tags=("conversation", "prossh", "cast-trigger", "oracle"),
        turns=(
            OpenJudgeTurn(
                id="OJ-002-01",
                question="¿Qué hace Prossh, Skyraider of Kher?",
                required_all=("Prossh", "Kobold"),
                required_any=(
                    ("cuando lo lanzas", "al lanzarlo", "cuando lanzas"),
                    ("maná gastado", "mana gastado"),
                ),
                recommended_any=(
                    ("vuelo", "flying"),
                    (
                        "sacrifica otra criatura",
                        "sacrificar otra criatura",
                        "sacrificas otra criatura",
                    ),
                ),
                expected_cards=("Prossh, Skyraider of Kher",),
            ),
            OpenJudgeTurn(
                id="OJ-002-02",
                question="¿Cuántos kobolds crea?",
                required_any=(
                    ("X", "tantos"),
                    ("maná gastado", "mana gastado"),
                    ("lanzar", "lanzas", "lanzarlo"),
                ),
                forbidden=(
                    ForbiddenClaim("siempre crea seis"),
                    ForbiddenClaim("igual a su valor de maná"),
                    ForbiddenClaim("igual a su valor de mana"),
                ),
                expected_cards=("Prossh, Skyraider of Kher",),
                missing_outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
            ),
            OpenJudgeTurn(
                id="OJ-002-03",
                question="¿Y si lo sacrifico?",
                required_any=(
                    ("otra criatura", "another creature"),
                ),
                recommended_any=(
                    (
                        "no puede sacrificarse a sí mismo",
                        "no puedes sacrificar a Prossh",
                        "no se puede sacrificar a sí mismo",
                    ),
                ),
                forbidden=(
                    ForbiddenClaim("Prossh puede sacrificarse a sí mismo"),
                    ForbiddenClaim("puedes sacrificar Prossh con su propia habilidad"),
                ),
                expected_cards=("Prossh, Skyraider of Kher",),
                missing_outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
            ),
            OpenJudgeTurn(
                id="OJ-002-04",
                question="¿Qué ocurre si vuelve a entrar al campo de batalla?",
                required_any=(
                    ("no crea", "no se dispara", "no se activa"),
                    ("al lanzarlo", "cuando lo lanzas", "lanzar"),
                    ("entrar", "entra al campo"),
                ),
                forbidden=(
                    ForbiddenClaim("crea Kobolds cuando entra"),
                    ForbiddenClaim("es una habilidad de entrar al campo"),
                ),
                expected_cards=("Prossh, Skyraider of Kher",),
                missing_outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
            ),
        ),
    ),
    OpenJudgeCase(
        id="OJ-003",
        name="Undying and Persist keyword disambiguation",
        tags=("conversation", "keyword", "disambiguation", "persist"),
        turns=(
            OpenJudgeTurn(
                id="OJ-003-01",
                question="¿Cómo funciona Undying?",
                required_any=(
                    ("muere", "cementerio desde el campo"),
                    ("sin contador +1/+1", "no tenía contadores +1/+1"),
                    ("vuelve", "regresa", "retorna"),
                    ("contador +1/+1", "+1/+1"),
                ),
                forbidden=(
                    ForbiddenClaim("Undying devuelve con un contador -1/-1"),
                ),
            ),
            OpenJudgeTurn(
                id="OJ-003-02",
                question="¿Y Persist?",
                required_any=(
                    ("muere", "cementerio desde el campo"),
                    ("sin contador -1/-1", "no tenía contadores -1/-1"),
                    ("vuelve", "regresa", "retorna"),
                    ("contador -1/-1", "-1/-1"),
                ),
                forbidden=(
                    ForbiddenClaim("cuesta {1}{B}", OpenJudgeOutcome.HALLUCINATION),
                    ForbiddenClaim("es un conjuro", OpenJudgeOutcome.HALLUCINATION),
                    ForbiddenClaim("criatura no legendaria", OpenJudgeOutcome.HALLUCINATION),
                ),
                missing_outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
                notes="La conversación trata sobre la keyword, no sobre la carta Persist.",
            ),
            OpenJudgeTurn(
                id="OJ-003-03",
                question="¿Qué diferencias tienen?",
                required_all=("Undying", "Persist"),
                required_any=(
                    ("+1/+1", "contador +1/+1"),
                    ("-1/-1", "contador -1/-1"),
                    ("sin", "no tenía"),
                ),
                forbidden=(
                    ForbiddenClaim(
                        "no hay otra carta para comparar",
                        OpenJudgeOutcome.CONTEXT_FAILURE,
                    ),
                    ForbiddenClaim(
                        "solo se incluye una carta",
                        OpenJudgeOutcome.CONTEXT_FAILURE,
                    ),
                    ForbiddenClaim(
                        "la carta Persist",
                        OpenJudgeOutcome.CONTEXT_FAILURE,
                    ),
                ),
                missing_outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
            ),
        ),
    ),
    OpenJudgeCase(
        id="OJ-004",
        name="Two-card comparison attribution",
        tags=("conversation", "comparison", "multi-entity", "attribution"),
        turns=(
            OpenJudgeTurn(
                id="OJ-004-01",
                question="¿Qué es mejor, Young Wolf o Strangleroot Geist?",
                required_all=("Young Wolf", "Strangleroot Geist"),
                required_any=(
                    ("Undying", "persistencia"),
                    ("Strangleroot Geist tiene prisa", "Geist tiene prisa", "prisa"),
                    ("depende", "según", "en función"),
                ),
                recommended_any=(
                    ("{G}", "un maná", "un mana"),
                    ("{G}{G}", "dos manás", "dos manas"),
                ),
                forbidden=(
                    ForbiddenClaim("Young Wolf tiene prisa"),
                    ForbiddenClaim("Young Wolf tiene Haste"),
                    ForbiddenClaim("Strangleroot Geist no tiene prisa"),
                    ForbiddenClaim("Strangleroot Geist no tiene Haste"),
                ),
                expected_cards=("Young Wolf", "Strangleroot Geist"),
            ),
            OpenJudgeTurn(
                id="OJ-004-02",
                question="¿En qué mazos jugarías cada uno?",
                required_all=("Young Wolf", "Strangleroot Geist"),
                required_any=(
                    ("sacrificio", "recursión", "cementerio"),
                    ("agresivo", "aggro", "prisa"),
                ),
                expected_cards=("Young Wolf", "Strangleroot Geist"),
                missing_outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
            ),
        ),
    ),
    OpenJudgeCase(
        id="OJ-005",
        name="Explicit topic switch",
        tags=("conversation", "topic-switch", "sol-ring"),
        turns=(
            OpenJudgeTurn(
                id="OJ-005-01",
                question="¿Qué hace Young Wolf?",
                required_any=(("Undying", "muere"),),
                expected_cards=("Young Wolf",),
            ),
            OpenJudgeTurn(
                id="OJ-005-02",
                question="¿Qué hace Sol Ring?",
                required_all=("Sol Ring",),
                required_any=(
                    ("{T}", "girar", "giras"),
                    ("{C}{C}", "dos manás incoloros", "dos manas incoloros"),
                ),
                expected_cards=("Sol Ring",),
                forbidden_cards=("Young Wolf",),
            ),
            OpenJudgeTurn(
                id="OJ-005-03",
                question="¿Y merece la pena jugarlo?",
                required_all=("Sol Ring",),
                required_any=(
                    ("aceleración", "acelera", "maná rápidamente", "mana rapidamente"),
                ),
                recommended_any=(
                    ("Commander", "formato"),
                ),
                forbidden=(
                    ForbiddenClaim("es legal en todos los formatos"),
                ),
                expected_cards=("Sol Ring",),
                forbidden_cards=("Young Wolf",),
                missing_outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
            ),
        ),
    ),
    OpenJudgeCase(
        id="OJ-006",
        name="Explicit rule follow-up",
        tags=("conversation", "rule-reference", "follow-up", "undying"),
        turns=(
            OpenJudgeTurn(
                id="OJ-006-01",
                question="¿Qué dice la regla 702.93?",
                required_any=(
                    ("Undying", "persistencia"),
                    ("cementerio desde el campo", "muere"),
                    ("sin contador +1/+1", "no tenía contadores +1/+1"),
                    ("contador +1/+1", "+1/+1"),
                ),
            ),
            OpenJudgeTurn(
                id="OJ-006-02",
                question="¿Puedes explicarla con un ejemplo?",
                required_any=(
                    ("ejemplo", "por ejemplo"),
                    ("muere", "cementerio"),
                    ("sin contador +1/+1", "no tenía"),
                    ("vuelve", "regresa", "retorna"),
                    ("contador +1/+1", "+1/+1"),
                ),
                forbidden=(
                    ForbiddenClaim("603.7h", OpenJudgeOutcome.CONTEXT_FAILURE),
                    ForbiddenClaim("habilidad disparada retardada", OpenJudgeOutcome.CONTEXT_FAILURE),
                ),
                missing_outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
            ),
        ),
    ),
    OpenJudgeCase(
        id="OJ-007",
        name="Commander comparison retains both cards",
        tags=("conversation", "commander", "comparison", "multi-entity"),
        turns=(
            OpenJudgeTurn(
                id="OJ-007-01",
                question="¿Qué hace Korvold, Fae-Cursed King?",
                required_all=("Korvold",),
                required_any=(
                    ("entra", "ataca"),
                    ("sacrifica otro permanente", "sacrificar otro permanente"),
                    ("roba", "robar una carta"),
                    ("+1/+1", "contador +1/+1"),
                ),
                expected_cards=("Korvold, Fae-Cursed King",),
            ),
            OpenJudgeTurn(
                id="OJ-007-02",
                question="¿Es mejor que Prossh?",
                required_all=("Korvold", "Prossh"),
                required_any=(
                    ("depende", "según", "en función"),
                    ("roba", "ventaja de cartas"),
                    ("Kobold", "fichas", "tokens"),
                ),
                expected_cards=("Korvold, Fae-Cursed King", "Prossh, Skyraider of Kher"),
                missing_outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
            ),
            OpenJudgeTurn(
                id="OJ-007-03",
                question="¿En qué se diferencian?",
                required_all=("Korvold", "Prossh"),
                required_any=(
                    ("roba", "ventaja de cartas"),
                    ("Kobold", "fichas", "tokens"),
                    ("sacrificio", "sacrificar"),
                ),
                expected_cards=("Korvold, Fae-Cursed King", "Prossh, Skyraider of Kher"),
                missing_outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
            ),
        ),
    ),
    OpenJudgeCase(
        id="OJ-008",
        name="London Mulligan follow-up",
        tags=("conversation", "mulligan", "procedure", "follow-up"),
        turns=(
            OpenJudgeTurn(
                id="OJ-008-01",
                question="Explícame el London Mulligan.",
                required_any=(
                    ("siete", "7"),
                    ("roba", "robar"),
                    ("fondo", "parte inferior"),
                    ("por cada mulligan", "tantas cartas como mulligans"),
                ),
                recommended_any=(
                    ("multijugador", "primer mulligan gratuito", "primer mulligan es gratis"),
                ),
            ),
            OpenJudgeTurn(
                id="OJ-008-02",
                question="¿Cuántas cartas robo después?",
                required_any=(
                    ("siete", "7", "tamaño inicial de mano"),
                    ("fondo", "parte inferior"),
                    ("por cada mulligan", "número de mulligans"),
                ),
                missing_outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
            ),
        ),
    ),
    OpenJudgeCase(
        id="OJ-009",
        name="Undying with an existing counter",
        tags=("conversation", "undying", "counter", "intervening-if"),
        turns=(
            OpenJudgeTurn(
                id="OJ-009-01",
                question="Si sacrifico Young Wolf teniendo Undying, ¿qué ocurre?",
                required_any=(
                    ("cementerio", "muere"),
                    ("sin contador +1/+1", "si no tenía"),
                    ("vuelve", "regresa", "retorna"),
                    ("contador +1/+1", "+1/+1"),
                ),
                expected_cards=("Young Wolf",),
            ),
            OpenJudgeTurn(
                id="OJ-009-02",
                question="¿Y si además tiene un contador +1/+1?",
                required_any=(
                    ("no se dispara", "no activa", "no vuelve"),
                    ("ya tenía", "tiene un contador +1/+1"),
                ),
                recommended_any=(
                    ("cementerio", "permanece en el cementerio"),
                ),
                forbidden=(
                    ForbiddenClaim("vuelve al campo de batalla con otro contador"),
                    ForbiddenClaim("Undying se dispara aunque tenga un contador +1/+1"),
                ),
                expected_cards=("Young Wolf",),
                missing_outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
            ),
        ),
    ),
)
