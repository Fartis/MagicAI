from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from magicai.tactician.claims import ClaimVerdict, ClaimVerdictStatus
from magicai.tactician.input_analysis import InputAnalysis, SpeechAct
from magicai.tactician.intents import StrategyIntent
from magicai.tactician.strategy import StrategyAnalysis, analyze_strategy


@dataclass(slots=True)
class StrategicSynthesis:
    answer: str
    combo_classification: str
    synergies: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    combo_steps: list[str] = field(default_factory=list)
    outcomes: list[str] = field(default_factory=list)
    reasoning_summary: list[str] = field(default_factory=list)


def synthesize_strategy(
    *,
    question: str,
    judge_payload: dict[str, Any],
    input_analysis: InputAnalysis,
    claim_verdicts: list[ClaimVerdict],
) -> StrategicSynthesis:
    cards = list(judge_payload.get("cards", []))
    names = {str(card.get("name", "")).casefold() for card in cards}

    if {"young wolf", "carrion feeder", "the ozolith"}.issubset(names):
        return _synthesize_ozolith_interaction(input_analysis, claim_verdicts)

    if {"young wolf", "ashnod's altar", "ghave, guru of spores"}.issubset(names):
        follow_up = _synthesize_ghave_loop(input_analysis)
        if follow_up is not None:
            return follow_up

    fallback: StrategyAnalysis = analyze_strategy(
        question,
        judge_payload,
        intent=input_analysis.strategy_intent,
    )
    answer = fallback.answer
    if input_analysis.language == "es" and input_analysis.speech_act in {SpeechAct.CHALLENGE, SpeechAct.HYPOTHESIS}:
        answer = "Entiendo la línea que propones. " + answer
    elif input_analysis.language == "en" and input_analysis.speech_act in {SpeechAct.CHALLENGE, SpeechAct.HYPOTHESIS}:
        answer = "I see the line you are proposing. " + answer

    return StrategicSynthesis(
        answer=answer,
        combo_classification=fallback.combo_classification,
        synergies=fallback.synergies,
        risks=fallback.risks,
        combo_steps=fallback.combo_steps,
        outcomes=fallback.outcomes,
        reasoning_summary=_summary_from_verdicts(claim_verdicts),
    )



def _synthesize_ghave_loop(input_analysis: InputAnalysis) -> StrategicSynthesis | None:
    spanish = input_analysis.language == "es"
    intent = input_analysis.strategy_intent
    base_steps_es = [
        "Sacrifica Young Wolf con Ashnod's Altar para añadir dos manás incoloros.",
        "Undying devuelve Young Wolf con un contador +1/+1.",
        "Paga un maná con Ghave, retira ese contador de Young Wolf y crea un Saproling.",
        "Young Wolf vuelve a estar sin contador: el ciclo queda listo para repetirse.",
    ]
    base_steps_en = [
        "Sacrifice Young Wolf to Ashnod's Altar to add two colorless mana.",
        "Undying returns Young Wolf with a +1/+1 counter.",
        "Pay one mana with Ghave, remove that counter from Young Wolf, and create a Saproling.",
        "Young Wolf is free of +1/+1 counters again, so the loop can repeat.",
    ]

    if intent is StrategyIntent.PLAY_SEQUENCE:
        if spanish:
            answer = (
                "Sí, aquí conviene separar el orden de despliegue del orden del combo. "
                "Normalmente bajaría primero Young Wolf, después Ashnod's Altar y dejaría Ghave para el final, "
                "porque es la pieza más cara y la que más interesa proteger. Con las tres piezas en mesa, sigue esta secuencia: "
                + " ".join(f"{index}. {step}" for index, step in enumerate(base_steps_es, start=1))
                + " Cada vuelta deja un maná incoloro neto y un Saproling."
            )
        else:
            answer = (
                "It helps to separate deployment order from combo order. I would usually deploy Young Wolf first, "
                "then Ashnod's Altar, and keep Ghave for last because it is the most expensive and exposed piece. "
                "Once all three are in play: "
                + " ".join(f"{index}. {step}" for index, step in enumerate(base_steps_en, start=1))
                + " Each iteration produces one net colorless mana and one Saproling."
            )
        return StrategicSynthesis(
            answer=answer,
            combo_classification="infinite_combo",
            synergies=["Ghave removes the counter that would stop Undying, while Ashnod's Altar pays for Ghave and leaves net mana."],
            risks=["Do not expose Ghave earlier than necessary if opponents are holding removal."],
            combo_steps=base_steps_es if spanish else base_steps_en,
            outcomes=["One net colorless mana per iteration", "One Saproling per iteration"],
            reasoning_summary=["The loop restores Young Wolf to the no-counter state and pays its own activation cost."],
        )

    if intent is StrategyIntent.COMBO_DISRUPTION:
        if spanish:
            answer = (
                "El combo tiene varios puntos donde pueden cortártelo. El más claro es responder a Undying y exiliar Young Wolf del cementerio antes de que vuelva. "
                "También pueden eliminar Ghave antes de que retire el contador, destruir o anular Ashnod's Altar antes de iniciar la línea, "
                "o usar un efecto de reemplazo como Rest in Peace para impedir que Young Wolf llegue al cementerio. "
                "Una vez activas el Altar, el sacrificio ya está pagado y esa activación de maná no usa la pila, así que la interacción suele centrarse en Undying o en Ghave."
            )
        else:
            answer = (
                "There are several clean interruption points. An opponent can respond to Undying and exile Young Wolf from the graveyard before it returns, "
                "remove Ghave before it clears the counter, disable Ashnod's Altar before the line begins, or use a replacement effect such as Rest in Peace. "
                "Once the Altar ability is activated, the sacrifice is already paid and the mana ability does not use the stack, so the main windows are Undying and Ghave."
            )
        return StrategicSynthesis(
            answer=answer,
            combo_classification="infinite_combo",
            risks=["Graveyard exile in response to Undying", "Removal on Ghave", "Graveyard replacement effects"],
            combo_steps=base_steps_es if spanish else base_steps_en,
            outcomes=["The loop stops if Young Wolf cannot return or its counter cannot be removed."],
            reasoning_summary=["The vulnerable objects are the Undying trigger, Young Wolf in the graveyard, and Ghave's counter-removal ability."],
        )

    if intent is StrategyIntent.COMBO_REQUIREMENTS:
        if spanish:
            answer = (
                "Necesitas las tres piezas en el campo, Young Wolf sin contador +1/+1 y al menos la prioridad para iniciar el sacrificio. "
                "No necesitas maná inicial si empiezas con Ashnod's Altar: el primer sacrificio genera dos manás, uno paga la habilidad de Ghave y el otro queda como beneficio neto. "
                "La línea también presupone que nada reemplaza el cementerio y que los rivales no interrumpen Undying."
            )
        else:
            answer = (
                "You need all three permanents in play, Young Wolf without a +1/+1 counter, and priority to start the sacrifice. "
                "No starting mana is required if Ashnod's Altar begins the loop: the first sacrifice makes two mana, one pays Ghave, and one remains net. "
                "The line also assumes no graveyard replacement effect and no interruption of Undying."
            )
        return StrategicSynthesis(
            answer=answer,
            combo_classification="infinite_combo",
            risks=["Young Wolf must begin without a +1/+1 counter.", "A graveyard replacement effect prevents the loop."],
            combo_steps=base_steps_es if spanish else base_steps_en,
            outcomes=["The loop is self-funding after the first sacrifice."],
            reasoning_summary=["Ashnod's Altar produces two mana and Ghave consumes one, leaving one net mana while resetting Undying."],
        )

    return None

def _synthesize_ozolith_interaction(
    input_analysis: InputAnalysis,
    verdicts: list[ClaimVerdict],
) -> StrategicSynthesis:
    spanish = input_analysis.language == "es"
    challenged = input_analysis.speech_act in {SpeechAct.CHALLENGE, SpeechAct.HYPOTHESIS}

    if spanish:
        opening = (
            "Entiendo por qué lo interpretas así, pero la clave está en el momento exacto en que Undying comprueba el contador."
            if challenged
            else "La interacción tiene valor, pero The Ozolith no reinicia Undying."
        )
        steps = [
            "Carrion Feeder sacrifica Young Wolf; si el lobo tenía un contador +1/+1, deja el campo con ese contador.",
            "Undying mira cómo era Young Wolf inmediatamente antes de abandonar el campo. Como tenía un contador +1/+1, Undying no se dispara.",
            "El contador original deja de existir cuando Young Wolf cambia de zona.",
            "The Ozolith se dispara por separado y, cuando su habilidad se resuelve, pone sobre sí mismo un contador equivalente; no retiró el contador del lobo antes de la comprobación de Undying.",
        ]
        answer = (
            f"{opening} "
            "Por eso, Young Wolf, Carrion Feeder y The Ozolith no forman un bucle infinito por sí solos. "
            "Carrion Feeder sí obtiene su contador y The Ozolith conserva valor para un combate posterior, "
            "pero Young Wolf permanece en el cementerio después del segundo sacrificio."
        )
        synergies = [
            "Carrion Feeder convierte Young Wolf en valor de sacrificio y The Ozolith conserva una copia de los contadores de la criatura que salió.",
        ]
        risks = [
            "The Ozolith no elimina el contador de Young Wolf antes de que Undying compruebe su condición.",
            "Para repetir el ciclo hace falta una pieza que quite o neutralice el contador +1/+1 mientras Young Wolf sigue en el campo de batalla.",
        ]
        outcomes = [
            "Carrion Feeder recibe un contador +1/+1 por el sacrificio.",
            "The Ozolith puede recibir un contador equivalente cuando se resuelva su habilidad.",
            "Young Wolf no regresa mediante Undying si tenía un contador +1/+1 al dejar el campo.",
        ]
        summary = [
            "Young Wolf abandona el campo con el contador +1/+1 todavía sobre él.",
            "Undying usa esa última información del campo de batalla y no se dispara.",
            "The Ozolith crea contadores sobre sí mismo después; no mueve el contador a tiempo para cambiar la comprobación de Undying.",
        ]
    else:
        opening = (
            "I see why that line looks plausible, but the key is when Undying checks the counter."
            if challenged
            else "The interaction creates value, but The Ozolith does not reset Undying."
        )
        steps = [
            "Carrion Feeder sacrifices Young Wolf; if the Wolf had a +1/+1 counter, it leaves the battlefield with that counter.",
            "Undying checks Young Wolf's last battlefield state. Because it had a +1/+1 counter, Undying does not trigger.",
            "The original counter ceases to exist when Young Wolf changes zones.",
            "The Ozolith triggers separately and later puts a corresponding counter on itself; it did not remove the Wolf's counter before Undying checked.",
        ]
        answer = (
            f"{opening} Young Wolf, Carrion Feeder, and The Ozolith therefore do not form an infinite loop by themselves. "
            "Carrion Feeder grows and The Ozolith stores future value, but Young Wolf stays in the graveyard after the second sacrifice."
        )
        synergies = [
            "Carrion Feeder converts Young Wolf into sacrifice value, while The Ozolith preserves a corresponding counter for later combat.",
        ]
        risks = [
            "The Ozolith does not remove Young Wolf's counter before Undying checks its condition.",
            "A separate effect must remove or neutralize the +1/+1 counter while Young Wolf is still on the battlefield to repeat the loop.",
        ]
        outcomes = [
            "Carrion Feeder receives a +1/+1 counter.",
            "The Ozolith may receive a corresponding counter when its trigger resolves.",
            "Young Wolf does not return through Undying if it left with a +1/+1 counter.",
        ]
        summary = [
            "Young Wolf leaves the battlefield while it still has the +1/+1 counter.",
            "Undying uses that last battlefield state and does not trigger.",
            "The Ozolith puts counters on itself later and cannot retroactively change Undying's check.",
        ]

    return StrategicSynthesis(
        answer=answer,
        combo_classification="non_combo",
        synergies=synergies,
        risks=risks,
        combo_steps=steps,
        outcomes=outcomes,
        reasoning_summary=_deduplicate(summary),
    )


def _summary_from_verdicts(verdicts: list[ClaimVerdict]) -> list[str]:
    return _deduplicate(
        [verdict.explanation for verdict in verdicts if verdict.explanation]
    )


def _deduplicate(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
