from magicai.validation.rule_renderer import render_rule_answer


QUESTION = """Estoy jugando Commander. Mi oponente controla Blood Moon. Yo controlo
Urborg, Tomb of Yawgmoth y después lanzo Dryad of the Ilysian Grove.

¿Qué tipos de tierra, habilidades de maná y colores pueden producir mis tierras
básicas, mis tierras no básicas y las tierras no básicas del oponente?

¿Cambiaría el resultado si Dryad of the Ilysian Grove hubiera entrado antes que
Blood Moon? Explica las capas, dependencias y timestamp aplicables."""


KNOWLEDGE = f"""QUESTION

{QUESTION}

============================================================
CARDS

Dryad of the Ilysian Grove
Enchantment Creature — Nymph Dryad

You may play an additional land on each of your turns.
Lands you control are every basic land type in addition to their other types.

Urborg, Tomb of Yawgmoth
Legendary Land

Each land is a Swamp in addition to its other land types.

Blood Moon
Enchantment

Nonbasic lands are Mountains.

============================================================
RULES

305.6
Basic land types grant intrinsic mana abilities.

305.7
Setting a basic land type removes old land types and printed abilities.

305.8
Basic is a supertype; nonbasic lands remain nonbasic.

611.3
Static abilities generate continuous effects.

613.1d
Layer 4 type-changing effects.

613.7
Timestamp order.

613.8a
Dependency definition.

613.8b
Dependent effects wait.
"""


def test_land_type_renderer_resolves_dependency_and_timestamp() -> None:
    answer = render_rule_answer(KNOWLEDGE)

    assert answer is not None
    assert "capa 4" in answer
    assert "dependencia prevalece sobre la marca de tiempo" in answer
    assert "Urborg, Tomb of Yawgmoth no llega a convertir las tierras en Pantano" in answer
    assert "Tus tierras básicas" in answer
    assert "pueden producir los cinco colores" in answer
    assert "Tus tierras no básicas" in answer
    assert "Llanura, Isla, Pantano, Montaña y Bosque" in answer
    assert "Las tierras no básicas del oponente" in answer
    assert "solo pueden producir maná rojo (R)" in answer
    assert "hubiera entrado antes que Blood Moon" in answer
    assert "terminarían siendo solo Montaña" in answer
    assert "todo se resuelva únicamente por timestamp" in answer


def main() -> int:
    test_land_type_renderer_resolves_dependency_and_timestamp()
    print("OK: land type layer renderer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


GENERIC_QUESTION = """Estoy jugando Commander. Mi oponente controla Ashen Eclipse.
Yo controlo Tidal Nexus y después lanzo Prismatic Sage.

¿Qué tipos de tierra y colores pueden producir mis tierras básicas, mis tierras
no básicas y las tierras no básicas del oponente?

¿Cambiaría si Prismatic Sage hubiera entrado antes que Ashen Eclipse?
Explica capa, dependencia y timestamp."""


GENERIC_KNOWLEDGE = f"""QUESTION

{GENERIC_QUESTION}

============================================================
CARDS

Prismatic Sage
Enchantment Creature — Sage

Lands you control are every basic land type in addition to their other types.

Tidal Nexus
Legendary Land

Each land is an Island in addition to its other land types.

Ashen Eclipse
Enchantment

Nonbasic lands are Swamps.

============================================================
RULES

305.6
Basic land types grant intrinsic mana abilities.

305.7
Setting a basic land type removes old land types and printed abilities.

305.8
Basic is a supertype; nonbasic lands remain nonbasic.

611.3
Static abilities generate continuous effects.

613.1d
Layer 4 type-changing effects.

613.7
Timestamp order.

613.8a
Dependency definition.

613.8b
Dependent effects wait.
"""


def test_land_type_renderer_is_oracle_pattern_driven_not_card_name_driven() -> None:
    answer = render_rule_answer(GENERIC_KNOWLEDGE)

    assert answer is not None
    assert "Tidal Nexus" in answer
    assert "Ashen Eclipse" in answer
    assert "Prismatic Sage" in answer
    assert "convertir las tierras en Isla" in answer
    assert "solo Pantano" in answer
    assert "maná negro (B)" in answer
