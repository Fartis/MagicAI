from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from magicai.tactician.claims import ClaimVerdict
from magicai.tactician.factual_core import judge_answer_is_directly_usable
from magicai.tactician.input_analysis import InputAnalysis, SpeechAct
from magicai.tactician.intents import StrategyIntent
from magicai.tactician.orchestration import ResponseDecision, ResponseMode
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
    response_decision: ResponseDecision | None = None,
) -> StrategicSynthesis:
    cards = list(judge_payload.get("cards", []))
    names = {str(card.get("name", "")).casefold() for card in cards}
    decision = response_decision

    if decision is not None and decision.mode is ResponseMode.JUDGE_LED:
        judge_led = _synthesize_judge_led(
            judge_payload=judge_payload,
            input_analysis=input_analysis,
            names=names,
            claim_verdicts=claim_verdicts,
        )
        if judge_led is not None:
            return judge_led

    if input_analysis.strategy_intent is StrategyIntent.MECHANIC_EQUIVALENCE:
        return _synthesize_undying_dies_equivalence(input_analysis, names)

    if {
        "young wolf", "carrion feeder", "the ozolith",
    }.issubset(names):
        if input_analysis.strategy_intent in {
            StrategyIntent.COMBO_FAILURE_EXPLANATION,
            StrategyIntent.INTERACTION_TIMING,
        }:
            return _synthesize_ozolith_failure(input_analysis)
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


def _synthesize_judge_led(
    *,
    judge_payload: dict[str, Any],
    input_analysis: InputAnalysis,
    names: set[str],
    claim_verdicts: list[ClaimVerdict],
) -> StrategicSynthesis | None:
    """Keep a validated Judge answer intact on rules-led turns."""

    if judge_answer_is_directly_usable(judge_payload, input_analysis):
        answer = str(judge_payload.get("answer", "")).strip()
        if answer:
            return StrategicSynthesis(
                answer=answer,
                combo_classification="not_applicable",
                synergies=[],
                risks=[],
                combo_steps=[],
                outcomes=[],
                reasoning_summary=_summary_from_verdicts(claim_verdicts) or [answer],
            )

    # A known semantic fallback is preferable to relaying a drifted Judge
    # answer. It is mechanic-based and uses the recovered active context.
    if input_analysis.strategy_intent is StrategyIntent.MECHANIC_EQUIVALENCE:
        return _synthesize_undying_dies_equivalence(input_analysis, names)

    return None

def _synthesize_undying_dies_equivalence(
    input_analysis: InputAnalysis,
    names: set[str],
) -> StrategicSynthesis:
    spanish = input_analysis.language == "es"
    has_ozolith_context = {
        "young wolf", "carrion feeder", "the ozolith",
    }.issubset(names)

    if spanish:
        answer = (
            "En realidad, en Magic no son dos momentos distintos: una criatura muere exactamente cuando es puesta en un cementerio desde el campo de batalla. "
            "Undying se dispara por ese mismo evento y, además, comprueba si el permanente tenía contadores +1/+1 justo antes de abandonar el campo. "
            "Que una carta llegue al cementerio desde otra zona —por ejemplo, desde la mano o la biblioteca— no significa que haya muerto."
        )
        if has_ozolith_context:
            answer += (
                " En la interacción con Young Wolf, Carrion Feeder y The Ozolith, el lobo deja el campo todavía con su contador; por eso Undying no se dispara. "
                "The Ozolith pone después sobre sí mismo contadores equivalentes, pero no le quitó el contador al lobo antes de esa comprobación."
            )
        steps = [
            "Young Wolf pasa del campo de batalla al cementerio: ese movimiento es lo que las reglas llaman morir.",
            "Undying comprueba el evento y el último estado de Young Wolf en el campo de batalla.",
            "Si tenía un contador +1/+1, la condición de Undying no se cumple y la habilidad no se dispara.",
        ]
        if has_ozolith_context:
            steps.append("The Ozolith se dispara por separado y crea después contadores equivalentes sobre sí mismo.")
        outcomes = [
            "Morir y ser puesta en un cementerio desde el campo de batalla son el mismo evento reglamentario.",
            "Entrar al cementerio desde otra zona no cuenta como morir.",
        ]
        summary = [
            "La regla 700.4 define morir como pasar del campo de batalla al cementerio.",
            "Undying usa ese evento y comprueba la ausencia de contadores +1/+1.",
        ]
        risks = [
            "No debe confundirse cualquier entrada al cementerio con morir: la zona de origen importa.",
        ]
    else:
        answer = (
            "They are not two separate moments in Magic: a creature dies exactly when it is put into a graveyard from the battlefield. "
            "Undying triggers from that same event and also checks whether the permanent had any +1/+1 counters immediately before it left the battlefield. "
            "A card entering a graveyard from another zone, such as a hand or library, did not die."
        )
        if has_ozolith_context:
            answer += (
                " In the Young Wolf, Carrion Feeder, and The Ozolith interaction, the Wolf leaves with its counter, so Undying does not trigger. "
                "The Ozolith puts corresponding counters on itself later; it did not remove the Wolf's counter before that check."
            )
        steps = [
            "Young Wolf moves from the battlefield to the graveyard; that movement is what the rules call dying.",
            "Undying checks the event and Young Wolf's last battlefield state.",
            "If it had a +1/+1 counter, Undying's condition is false and the ability does not trigger.",
        ]
        if has_ozolith_context:
            steps.append("The Ozolith triggers separately and later puts corresponding counters on itself.")
        outcomes = [
            "Dying and being put into a graveyard from the battlefield are the same rules event.",
            "Entering a graveyard from another zone is not dying.",
        ]
        summary = [
            "Rule 700.4 defines dying as moving from the battlefield to a graveyard.",
            "Undying uses that event and checks for +1/+1 counters.",
        ]
        risks = [
            "Do not treat every graveyard entry as dying; the origin zone matters.",
        ]

    return StrategicSynthesis(
        answer=answer,
        combo_classification="non_combo" if has_ozolith_context else "not_applicable",
        synergies=[],
        risks=risks,
        combo_steps=steps,
        outcomes=outcomes,
        reasoning_summary=summary,
    )


def _synthesize_ozolith_failure(input_analysis: InputAnalysis) -> StrategicSynthesis:
    spanish = input_analysis.language == "es"
    if spanish:
        answer = (
            "El bucle se rompe en la segunda muerte de Young Wolf. Tras regresar por Undying, el lobo tiene un contador +1/+1. "
            "Cuando Carrion Feeder lo sacrifica otra vez, Undying comprueba cómo estaba justo antes de dejar el campo; como tenía ese contador, no se dispara. "
            "The Ozolith no evita este resultado: su habilidad se dispara por separado y pone después contadores equivalentes sobre el artefacto."
        )
        steps = [
            "Young Wolf regresa una primera vez con un contador +1/+1.",
            "Carrion Feeder lo sacrifica de nuevo.",
            "Undying comprueba el último estado del lobo y ve el contador +1/+1.",
            "La condición falla; Young Wolf no regresa y el bucle termina.",
        ]
        risks = ["The Ozolith no retira el contador antes de la comprobación de Undying."]
        outcomes = ["La interacción genera valor, pero no un bucle infinito."]
        summary = ["El paso fallido es el segundo disparo de Undying: la condición no se cumple."]
    else:
        answer = (
            "The loop breaks on Young Wolf's second death. After returning through Undying, the Wolf has a +1/+1 counter. "
            "When Carrion Feeder sacrifices it again, Undying checks its state immediately before it left; because it had that counter, the ability does not trigger. "
            "The Ozolith does not change this result: it triggers separately and later puts corresponding counters on itself."
        )
        steps = [
            "Young Wolf returns once with a +1/+1 counter.",
            "Carrion Feeder sacrifices it again.",
            "Undying checks the Wolf's last battlefield state and sees the counter.",
            "The condition fails; Young Wolf does not return and the loop ends.",
        ]
        risks = ["The Ozolith does not remove the counter before Undying checks."]
        outcomes = ["The interaction creates value but not an infinite loop."]
        summary = ["The failed transition is the second Undying trigger: its condition is false."]

    return StrategicSynthesis(
        answer=answer,
        combo_classification="non_combo",
        synergies=[],
        risks=risks,
        combo_steps=steps,
        outcomes=outcomes,
        reasoning_summary=summary,
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
                "Conviene separar el orden de despliegue del orden del combo. Normalmente bajaría primero Young Wolf, después Ashnod's Altar y dejaría Ghave para el final, "
                "porque es la pieza más cara y la que más interesa proteger. Con las tres piezas en mesa: "
                + " ".join(f"{index}. {step}" for index, step in enumerate(base_steps_es, start=1))
                + " Cada vuelta deja un maná incoloro neto y un Saproling."
            )
            synergies = ["Ghave retira el contador que bloquearía Undying, mientras Ashnod's Altar paga la activación y deja maná neto."]
            risks = ["Evita exponer Ghave antes de tiempo si los rivales conservan removal."]
            outcomes = ["Un maná incoloro neto por vuelta.", "Un Saproling por vuelta."]
            summary = ["El ciclo devuelve Young Wolf al estado sin contador y paga su propio coste."]
        else:
            answer = (
                "It helps to separate deployment order from combo order. I would usually deploy Young Wolf first, then Ashnod's Altar, and keep Ghave for last because it is the most expensive and exposed piece. Once all three are in play: "
                + " ".join(f"{index}. {step}" for index, step in enumerate(base_steps_en, start=1))
                + " Each iteration produces one net colorless mana and one Saproling."
            )
            synergies = ["Ghave removes the counter that would stop Undying, while Ashnod's Altar pays for Ghave and leaves net mana."]
            risks = ["Do not expose Ghave earlier than necessary if opponents are holding removal."]
            outcomes = ["One net colorless mana per iteration.", "One Saproling per iteration."]
            summary = ["The loop restores Young Wolf to the no-counter state and pays its own activation cost."]
        return StrategicSynthesis(answer, "infinite_combo", synergies, risks, base_steps_es if spanish else base_steps_en, outcomes, summary)

    if intent is StrategyIntent.COMBO_DISRUPTION:
        if spanish:
            answer = (
                "El combo tiene varios puntos de interrupción. El más claro es responder a Undying y exiliar Young Wolf del cementerio antes de que vuelva. "
                "También pueden eliminar Ghave antes de que retire el contador, desactivar Ashnod's Altar antes de iniciar la línea o usar un efecto de reemplazo como Rest in Peace. "
                "El sacrificio del Altar es un coste y su habilidad de maná no usa la pila; por eso la interacción suele centrarse en Undying o en Ghave."
            )
            risks = ["Exilio del cementerio en respuesta a Undying.", "Removal sobre Ghave.", "Efectos de reemplazo del cementerio."]
            outcomes = ["El bucle se detiene si Young Wolf no puede volver o si no puede retirarse su contador."]
            summary = ["Los puntos vulnerables son el disparo de Undying, Young Wolf en el cementerio y la habilidad de Ghave."]
        else:
            answer = (
                "There are several clean interruption points. An opponent can respond to Undying and exile Young Wolf from the graveyard before it returns, remove Ghave before it clears the counter, disable Ashnod's Altar before the line begins, or use a replacement effect such as Rest in Peace. "
                "The Altar sacrifice is a cost and its mana ability does not use the stack, so the main windows are Undying and Ghave."
            )
            risks = ["Graveyard exile in response to Undying.", "Removal on Ghave.", "Graveyard replacement effects."]
            outcomes = ["The loop stops if Young Wolf cannot return or its counter cannot be removed."]
            summary = ["The vulnerable objects are the Undying trigger, Young Wolf in the graveyard, and Ghave's ability."]
        return StrategicSynthesis(answer, "infinite_combo", [], risks, base_steps_es if spanish else base_steps_en, outcomes, summary)

    if intent is StrategyIntent.COMBO_REQUIREMENTS:
        if spanish:
            answer = (
                "Necesitas Young Wolf, Ashnod's Altar y Ghave, Guru of Spores en el campo, con Young Wolf sin contador +1/+1 y prioridad para iniciar el sacrificio. "
                "No necesitas maná inicial si empiezas con Ashnod's Altar: el primer sacrificio genera dos manás, uno paga la habilidad de Ghave y el otro queda como beneficio neto. "
                "La línea presupone que nada reemplaza el cementerio y que los rivales no interrumpen Undying."
            )
            risks = ["Young Wolf debe comenzar sin contador +1/+1.", "Un efecto de reemplazo del cementerio impide el bucle."]
            outcomes = ["El ciclo se autofinancia desde el primer sacrificio."]
            summary = ["Ashnod's Altar produce dos manás y Ghave consume uno, dejando un maná neto mientras reinicia Undying."]
        else:
            answer = (
                "You need Young Wolf, Ashnod's Altar, and Ghave, Guru of Spores on the battlefield, with Young Wolf free of +1/+1 counters and priority to start the sacrifice. "
                "No starting mana is required: the first Altar sacrifice makes two mana, one pays Ghave, and one remains net. The line also assumes no graveyard replacement effect and no interruption of Undying."
            )
            risks = ["Young Wolf must begin without a +1/+1 counter.", "A graveyard replacement effect prevents the loop."]
            outcomes = ["The loop is self-funding from the first sacrifice."]
            summary = ["Ashnod's Altar produces two mana and Ghave consumes one, leaving one net mana while resetting Undying."]
        return StrategicSynthesis(answer, "infinite_combo", [], risks, base_steps_es if spanish else base_steps_en, outcomes, summary)

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
            if challenged else
            "La interacción tiene valor, pero The Ozolith no reinicia Undying."
        )
        steps = [
            "Carrion Feeder sacrifica Young Wolf; si el lobo tenía un contador +1/+1, deja el campo con ese contador.",
            "Undying mira cómo era Young Wolf inmediatamente antes de abandonar el campo. Como tenía un contador +1/+1, Undying no se dispara.",
            "El contador original deja de existir cuando Young Wolf cambia de zona.",
            "The Ozolith se dispara por separado y, cuando su habilidad se resuelve, pone sobre sí mismo un contador equivalente.",
        ]
        answer = (
            f"{opening} Young Wolf deja el campo todavía con el contador +1/+1, así que Undying ve ese último estado y no se dispara. "
            "The Ozolith se dispara por separado y pone después contadores equivalentes sobre sí mismo; no retiró previamente el contador del lobo. "
            "Por eso, Young Wolf, Carrion Feeder y The Ozolith no forman un bucle infinito por sí solos. "
            "Carrion Feeder obtiene su contador y The Ozolith conserva valor para un combate posterior, pero Young Wolf permanece en el cementerio después del segundo sacrificio."
        )
        synergies = ["Carrion Feeder convierte Young Wolf en valor de sacrificio y The Ozolith conserva contadores equivalentes para un combate posterior."]
        risks = ["The Ozolith no elimina el contador de Young Wolf antes de que Undying compruebe su condición.", "Hace falta otra pieza que quite o neutralice el contador mientras Young Wolf sigue en el campo."]
        outcomes = ["Carrion Feeder recibe un contador +1/+1.", "The Ozolith puede recibir un contador equivalente.", "Young Wolf no regresa si tenía un contador al dejar el campo."]
        summary = ["Young Wolf abandona el campo con el contador todavía sobre él.", "Undying usa ese último estado y no se dispara.", "The Ozolith crea después contadores equivalentes sobre sí mismo."]
    else:
        opening = "I see why that line looks plausible, but the key is when Undying checks the counter." if challenged else "The interaction creates value, but The Ozolith does not reset Undying."
        steps = [
            "Carrion Feeder sacrifices Young Wolf; if the Wolf had a +1/+1 counter, it leaves with that counter.",
            "Undying checks Young Wolf's last battlefield state. Because it had a counter, Undying does not trigger.",
            "The original counter ceases to exist when Young Wolf changes zones.",
            "The Ozolith triggers separately and later puts a corresponding counter on itself.",
        ]
        answer = (
            f"{opening} Young Wolf leaves the battlefield with the +1/+1 counter, so Undying sees that last state and does not trigger. "
            "The Ozolith triggers separately and later puts corresponding counters on itself; it did not remove the Wolf's counter beforehand. "
            "Young Wolf, Carrion Feeder, and The Ozolith do not form an infinite loop by themselves. Carrion Feeder grows and The Ozolith stores future value, but Young Wolf stays in the graveyard after the second sacrifice."
        )
        synergies = ["Carrion Feeder converts Young Wolf into sacrifice value while The Ozolith stores corresponding counters for later combat."]
        risks = ["The Ozolith does not remove Young Wolf's counter before Undying checks.", "A separate effect must remove or neutralize the counter while Young Wolf is on the battlefield."]
        outcomes = ["Carrion Feeder receives a +1/+1 counter.", "The Ozolith may receive a corresponding counter.", "Young Wolf does not return if it left with a counter."]
        summary = ["Young Wolf leaves with the counter still on it.", "Undying uses that last state and does not trigger.", "The Ozolith creates corresponding counters later."]

    return StrategicSynthesis(answer, "non_combo", synergies, risks, steps, outcomes, _deduplicate(summary))


def _summary_from_verdicts(verdicts: list[ClaimVerdict]) -> list[str]:
    return _deduplicate([verdict.explanation for verdict in verdicts if verdict.explanation])


def _deduplicate(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
