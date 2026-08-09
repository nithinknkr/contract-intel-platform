"""
Fixed, closed risk checklist for the agentic clause-risk reviewer (B4).

Hardcoded, not DB-configurable -- a per-org configurable checklist is real
scope creep for a solo portfolio project (see B4 decisions log, Step 2).
Six categories chosen to prove the checklist-loop pattern generalizes
across categories without turning this into a data-entry exercise.

Category names are drawn from RiskCategory (app.models.risk_flag) rather
than redefined here as raw strings -- one source of truth, so this list
and the DB enum cannot silently drift apart from each other.
"""

from dataclasses import dataclass

from app.models.risk_flag import RiskCategory


@dataclass(frozen=True)
class RiskChecklistItem:
    category: RiskCategory
    description: str
    guiding_question: str


RISK_CHECKLIST: list[RiskChecklistItem] = [
    RiskChecklistItem(
        category=RiskCategory.AUTO_RENEWAL,
        description=(
            "Whether the contract automatically renews, and if so, the "
            "notice period and process required to opt out of renewal."
        ),
        guiding_question=(
            "Does this contract auto-renew, and if so, under what notice terms?"
        ),
    ),
    RiskChecklistItem(
        category=RiskCategory.LIABILITY_CAP,
        description=(
            "Whether liability is capped or limited, what the cap is based "
            "on, and what categories of damages are excluded."
        ),
        guiding_question=(
            "Is there a cap or limitation on liability, and what does it "
            "cover or exclude?"
        ),
    ),
    RiskChecklistItem(
        category=RiskCategory.TERMINATION_TERMS,
        description=(
            "The conditions, notice periods, and cure periods under which "
            "either party may terminate the contract."
        ),
        guiding_question=(
            "Under what conditions can either party terminate this contract?"
        ),
    ),
    RiskChecklistItem(
        category=RiskCategory.INDEMNIFICATION,
        description=(
            "What indemnification obligations each party has, and the "
            "scope of claims covered."
        ),
        guiding_question=(
            "What indemnification obligations does either party have?"
        ),
    ),
    RiskChecklistItem(
        category=RiskCategory.GOVERNING_LAW,
        description=(
            "The governing law and the dispute resolution mechanism "
            "(litigation, arbitration, escalation process) specified."
        ),
        guiding_question=(
            "What governing law and dispute resolution mechanism applies?"
        ),
    ),
    RiskChecklistItem(
        category=RiskCategory.CONFIDENTIALITY_SCOPE,
        description=(
            "The scope of what counts as confidential information and the "
            "duration confidentiality obligations survive termination."
        ),
        guiding_question=(
            "What is the scope and duration of confidentiality obligations?"
        ),
    ),
]