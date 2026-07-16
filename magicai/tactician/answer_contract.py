from __future__ import annotations

from dataclasses import dataclass, field
import re
import unicodedata

from magicai.tactician.input_analysis import InputAnalysis
from magicai.tactician.intents import StrategyIntent


@dataclass(frozen=True, slots=True)
class AnswerObligation:
    code: str
    description: str
    required: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "description": self.description,
            "required": self.required,
        }


@dataclass(slots=True)
class AnswerContractResult:
    obligations: list[AnswerObligation] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)
    forbidden_checks: dict[str, bool] = field(default_factory=dict)

    @property
    def complete(self) -> bool:
        required_codes = {item.code for item in self.obligations if item.required}
        return all(self.checks.get(code, False) for code in required_codes) and not any(self.forbidden_checks.values())

    def to_dict(self) -> dict[str, object]:
        return {
            "obligations": [item.to_dict() for item in self.obligations],
            "checks": dict(self.checks),
            "forbidden_checks": dict(self.forbidden_checks),
            "answer_complete": self.complete,
        }


def build_answer_obligations(analysis: InputAnalysis, *, has_current_interaction: bool) -> list[AnswerObligation]:
    spanish = analysis.language == "es"
    intent = analysis.strategy_intent
    obligations: list[AnswerObligation] = []

    if intent is StrategyIntent.MECHANIC_RESOLUTION:
        if "sacrifice" in analysis.concepts and "undying" in analysis.concepts:
            obligations.extend([
                AnswerObligation("sacrifice_transition", "Explicar que sacrificar mueve la criatura del campo al cementerio." if spanish else "Explain that sacrificing moves the creature from the battlefield to the graveyard."),
                AnswerObligation("dies_event", "Explicar que ese cambio de zona hace que la criatura muera." if spanish else "Explain that this zone change makes the creature die."),
                AnswerObligation("undying_condition", "Explicar cuándo se dispara Undying." if spanish else "Explain when Undying triggers."),
                AnswerObligation("undying_return", "Explicar cómo regresa la criatura por Undying." if spanish else "Explain how the creature returns through Undying."),
            ])
        else:
            obligations.append(AnswerObligation(
                "direct_user_question",
                "Resolver directamente el evento preguntado." if spanish else "Resolve the event asked about directly.",
            ))
    elif intent is StrategyIntent.MECHANIC_EQUIVALENCE:
        obligations.extend([
            AnswerObligation("define_dies", "Definir qué significa morir." if spanish else "Define what dying means."),
            AnswerObligation("compare_events", "Aclarar si morir y pasar del campo al cementerio son el mismo evento." if spanish else "Clarify whether dying and moving from battlefield to graveyard are the same event."),
            AnswerObligation("exclude_other_zone_changes", "Aclarar que entrar al cementerio desde otra zona no es morir." if spanish else "Clarify that entering a graveyard from another zone is not dying."),
            AnswerObligation("apply_undying", "Aplicar la definición a Undying." if spanish else "Apply the definition to Undying."),
        ])
        if has_current_interaction:
            obligations.append(AnswerObligation(
                "apply_current_interaction",
                "Aplicar la regla a la interacción activa." if spanish else "Apply the rule to the active interaction.",
            ))
    elif intent is StrategyIntent.COMBO_FAILURE_EXPLANATION:
        obligations.extend([
            AnswerObligation("identify_failed_transition", "Identificar el paso exacto que impide el bucle." if spanish else "Identify the exact transition that stops the loop."),
            AnswerObligation("explain_rule", "Explicar la regla que produce ese resultado." if spanish else "Explain the rule producing that result."),
            AnswerObligation("apply_current_interaction", "Aplicar la regla a las piezas activas." if spanish else "Apply the rule to the active pieces."),
        ])
    elif intent is StrategyIntent.COMBO_REQUIREMENTS:
        obligations.extend([
            AnswerObligation("list_required_permanents", "Enumerar las piezas necesarias." if spanish else "List the required pieces."),
            AnswerObligation("list_initial_state", "Indicar el estado inicial requerido." if spanish else "State the required initial state."),
        ])
    else:
        obligations.append(AnswerObligation(
            "direct_user_question",
            "Responder directamente a la pregunta actual." if spanish else "Answer the current question directly.",
        ))
    return obligations


def validate_answer_contract(
    answer: str,
    *,
    analysis: InputAnalysis,
    obligations: list[AnswerObligation],
    has_current_interaction: bool,
) -> AnswerContractResult:
    normalized = _normalize(answer)
    checks: dict[str, bool] = {}
    for obligation in obligations:
        checks[obligation.code] = _check_obligation(
            obligation.code,
            normalized,
            analysis=analysis,
            has_current_interaction=has_current_interaction,
        )

    forbidden_checks = {
        "language_switch": _wrong_language(answer, expected=analysis.language),
        "player_loses_game_drift": any(
            marker in normalized
            for marker in (
                "jugador pierde el juego",
                "abdica por empate",
                "player loses the game",
                "concedes the game",
            )
        ) and analysis.strategy_intent is StrategyIntent.MECHANIC_EQUIVALENCE,
    }
    return AnswerContractResult(obligations=obligations, checks=checks, forbidden_checks=forbidden_checks)


def _check_obligation(
    code: str,
    answer: str,
    *,
    analysis: InputAnalysis,
    has_current_interaction: bool,
) -> bool:
    if code == "sacrifice_transition":
        return _has_all(answer, ("campo de batalla", "cementerio")) or _has_all(answer, ("battlefield", "graveyard"))
    if code == "dies_event":
        return any(marker in answer for marker in ("muere", "morir", "dies"))
    if code == "undying_condition":
        return "undying" in answer and any(marker in answer for marker in ("sin contador", "no tenia", "no tenía", "no +1/+1", "had no +1/+1"))
    if code == "undying_return":
        return any(marker in answer for marker in ("vuelve", "regresa", "returns")) and "+1/+1" in answer
    if code == "define_dies":
        return _has_all(answer, ("muere", "cementerio", "campo de batalla")) or _has_all(answer, ("dies", "graveyard", "battlefield"))
    if code == "compare_events":
        return any(marker in answer for marker in ("mismo evento", "significa exactamente", "equivale a", "same event", "means exactly"))
    if code == "exclude_other_zone_changes":
        return (
            any(marker in answer for marker in ("otra zona", "biblioteca", "mano", "exilio", "another zone", "library", "hand", "exile"))
            and any(marker in answer for marker in (
                "no muere",
                "no cuenta como morir",
                "no significa que haya muerto",
                "does not die",
                "doesn't die",
            ))
        )
    if code == "apply_undying":
        return "undying" in answer and any(marker in answer for marker in ("se dispara", "no se dispara", "triggers", "does not trigger"))
    if code == "apply_current_interaction":
        if not has_current_interaction:
            return True
        return "undying" in answer and any(
            marker in answer
            for marker in ("ozolith", "young wolf", "carrion feeder", "ghave", "ashnod")
        )
    if code == "identify_failed_transition":
        return any(marker in answer for marker in ("no se dispara", "no vuelve", "se rompe", "does not trigger", "does not return", "breaks"))
    if code == "explain_rule":
        return any(marker in answer for marker in ("regla", "condicion", "condición", "ultimo estado", "último estado", "justo antes", "inmediatamente antes", "rule", "condition", "last battlefield state", "immediately before"))
    if code == "list_required_permanents":
        return all(name in answer for name in ("young wolf", "ashnod's altar", "ghave"))
    if code == "list_initial_state":
        return any(marker in answer for marker in ("sin contador", "without a +1/+1 counter", "free of +1/+1 counters"))
    if code == "direct_user_question":
        focus = set(analysis.answer_focus)
        if "sacrifice" in focus or "sacrifice" in analysis.concepts:
            return any(marker in answer for marker in ("sacrific", "graveyard", "cementerio", "muere", "dies"))
        return len(answer.split()) >= 5
    return False


def _wrong_language(answer: str, *, expected: str) -> bool:
    normalized = _normalize(answer)
    if expected == "es":
        english_markers = sum(marker in normalized for marker in ("the interaction", "does not", "you need", "the loop", "therefore"))
        spanish_markers = sum(marker in normalized for marker in ("la interaccion", "no se", "necesitas", "el bucle", "por tanto", "porque"))
        return english_markers >= 2 and spanish_markers == 0
    spanish_markers = sum(marker in normalized for marker in ("la interaccion", "necesitas", "el bucle", "por tanto"))
    english_markers = sum(marker in normalized for marker in ("the interaction", "you need", "the loop", "therefore"))
    return spanish_markers >= 2 and english_markers == 0


def _has_all(text: str, markers: tuple[str, ...]) -> bool:
    return all(marker in text for marker in markers)


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value.casefold()).strip()
