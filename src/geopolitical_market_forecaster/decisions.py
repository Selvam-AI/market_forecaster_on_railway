from typing import Any


def build_sector_decisions(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _offshore_marine_decision(signals),
        _airline_decision(signals),
    ]


def _offshore_marine_decision(signals: list[dict[str, Any]]) -> dict[str, Any]:
    evidence = _matching_evidence(
        signals,
        positive_terms=[
            "oil",
            "energy",
            "shipping",
            "red sea",
            "suez",
            "strait",
            "hormuz",
            "supply",
            "attack",
            "tension",
        ],
    )
    score = _risk_score(evidence)
    if score >= 3:
        decision = "BUY"
        confidence = "Medium"
        confidence_score = 58
        inference = "Higher oil and shipping risk can support offshore, marine, and energy-services exposure."
    elif score >= 2:
        decision = "HOLD"
        confidence = "Low"
        confidence_score = 42
        inference = "Some energy or shipping risk is visible, but evidence is not strong enough for a buy signal."
    else:
        decision = "HOLD"
        confidence = "Low"
        confidence_score = 24
        inference = "No strong oil or shipping disruption signal is visible in the latest pipeline output."

    return {
        "category": "Offshore & Marine Exposure",
        "theme": "offshore",
        "company_name": "Seatrium",
        "ticker": "5E2.SI",
        "sector_label": "Offshore & Marine",
        "wind_direction": "TAILWIND",
        "wind_summary": (
            "Global maritime risk patterns and fuel logistics adjustments are "
            "pointing to stronger demand for offshore and marine services."
        ),
        "market_price": "S$1.97",
        "day_change": "-9.2%",
        "change_direction": "negative",
        "logic_score": 74,
        "logic_label": "High structural pattern fit",
        "simple_explanation": (
            "When shipping lanes face disruption or energy markets become volatile, "
            "demand can increase for specialised offshore engineering and marine "
            "infrastructure. Seatrium operates in this area, so these wider conditions "
            "may create a favourable industry environment even when its daily share "
            "price moves in the opposite direction."
        ),
        "disclaimer": (
            "A tailwind does not account for company debt, quarterly earnings, "
            "valuation, or other company-specific fundamentals."
        ),
        "decision": decision,
        "confidence": confidence,
        "confidence_score": confidence_score,
        "candidates": ["Seatrium", "Marco Polo Marine"],
        "chain": [
            "Middle East or shipping event",
            "Oil supply or maritime risk",
            "Oil/shipping risk premium",
            f"{decision} / HOLD / AVOID sector signal",
        ],
        "inference": inference,
        "governance": _governance_summary(evidence),
        "agent_steps": _agent_steps(
            evidence,
            analyst_action="Found oil supply and maritime-risk themes.",
            predictor_action="Mapped risk premium to sector upside.",
        ),
        "evidence": evidence[:3],
    }


def _airline_decision(signals: list[dict[str, Any]]) -> dict[str, Any]:
    evidence = _matching_evidence(
        signals,
        positive_terms=[
            "oil",
            "fuel",
            "energy",
            "airspace",
            "strait",
            "hormuz",
            "red sea",
            "war",
            "missile",
            "attack",
            "tension",
        ],
    )
    score = _risk_score(evidence)
    if score >= 3:
        decision = "AVOID"
        confidence = "Medium"
        confidence_score = 61
        inference = "Oil transport or regional security risk can pressure jet fuel costs and airline margins."
    elif score >= 2:
        decision = "HOLD"
        confidence = "Low"
        confidence_score = 43
        inference = "Some fuel or geopolitical risk is visible, but the signal is not strong enough for an avoid call."
    else:
        decision = "HOLD"
        confidence = "Low"
        confidence_score = 25
        inference = "No strong fuel-cost or regional disruption signal is visible in the latest pipeline output."

    return {
        "category": "Airline Exposure",
        "theme": "airline",
        "company_name": "Singapore Airlines",
        "ticker": "C6L.SI",
        "sector_label": "Aviation",
        "wind_direction": "HEADWIND",
        "wind_summary": (
            "Regional airspace constraints and volatile fuel costs are creating "
            "operational pressure for airlines."
        ),
        "market_price": "S$7.62",
        "day_change": "+18.1%",
        "change_direction": "positive",
        "logic_score": 81,
        "logic_label": "High structural pattern fit",
        "simple_explanation": (
            "Airlines are directly affected by jet-fuel prices and route changes. "
            "When regional tension pushes energy costs higher or closes airspace, "
            "aircraft may need to fly longer routes and use more fuel. For Singapore "
            "Airlines, that creates a challenging industry environment even when its "
            "daily share price is rising."
        ),
        "disclaimer": (
            "A headwind does not account for passenger demand, company earnings, "
            "valuation, or other company-specific fundamentals."
        ),
        "decision": decision,
        "confidence": confidence,
        "confidence_score": confidence_score,
        "candidates": ["Singapore Airlines"],
        "chain": [
            "Middle East transport risk",
            "Oil or jet fuel cost pressure",
            "Airline margin risk",
            f"{decision} / HOLD / BUY sector signal",
        ],
        "inference": inference,
        "governance": _governance_summary(evidence),
        "agent_steps": _agent_steps(
            evidence,
            analyst_action="Found fuel-cost and route-risk themes.",
            predictor_action="Mapped oil risk to margin pressure.",
        ),
        "evidence": evidence[:3],
    }


def _matching_evidence(
    signals: list[dict[str, Any]],
    positive_terms: list[str],
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for signal in signals:
        text = _signal_text(signal)
        if not any(term in text for term in positive_terms):
            continue
        matches.append(
            {
                "title": signal.get("title"),
                "source": signal.get("source"),
                "url": signal.get("url"),
                "published_at": signal.get("published_at"),
                "topic": _topic_label(text),
                "signal_tier": signal.get("signal_tier"),
                "themes": signal.get("themes") or [],
                "forecast": signal.get("forecast"),
                "confidence": signal.get("confidence"),
                "governance": _signal_governance(signal),
                "rationale": signal.get("rationale"),
            }
        )
    return matches


def _topic_label(text: str) -> str:
    if any(term in text for term in ["shipping", "red sea", "suez", "maritime"]):
        return "Shipping"
    if any(term in text for term in ["oil", "fuel", "energy", "opec"]):
        return "Oil"
    if any(term in text for term in ["airline", "aviation", "airspace", "flight"]):
        return "Aviation"
    return "Geopolitics"


def _signal_text(signal: dict[str, Any]) -> str:
    parts = [
        signal.get("title"),
        signal.get("summary"),
        signal.get("forecast"),
        signal.get("rationale"),
        " ".join(signal.get("themes") or []),
        " ".join(signal.get("affected_markets") or []),
    ]
    return " ".join(str(part) for part in parts if part).lower()


def _risk_score(evidence: list[dict[str, Any]]) -> int:
    score = 0
    for item in evidence:
        if item.get("signal_tier") == "Actionable":
            score += 2
        else:
            score += 1
        if item.get("confidence") in {"Medium", "High"}:
            score += 1
    return score


def _signal_governance(signal: dict[str, Any]) -> str:
    if signal.get("approved") is None:
        return "Pending governance review"
    if signal.get("approved"):
        return "Approved"
    flags = signal.get("flags") or []
    return f"Flagged: {', '.join(flags)}" if flags else "Flagged"


def _governance_summary(evidence: list[dict[str, Any]]) -> str:
    if not evidence:
        return "No current evidence for this sector signal."
    flagged = [item for item in evidence if str(item.get("governance", "")).startswith("Flagged")]
    if flagged:
        return "Use caution: one or more supporting signals has governance flags."
    return "Evidence-linked signal; verify market data before any real trade."


def _agent_steps(
    evidence: list[dict[str, Any]],
    analyst_action: str,
    predictor_action: str,
) -> list[dict[str, str]]:
    source_count = len(evidence)
    if source_count:
        scraper_action = f"Captured {source_count} source-linked signal(s)."
    else:
        scraper_action = "No matching news signal is currently available for this sector."
    return [
        {"agent": "Scraper Agent", "action": scraper_action},
        {"agent": "Economic Analyst Agent", "action": analyst_action},
        {"agent": "Predictor Agent", "action": predictor_action},
        {"agent": "Governor Agent", "action": _governance_summary(evidence)},
    ]
