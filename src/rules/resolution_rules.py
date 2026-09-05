from dataclasses import dataclass, field


@dataclass
class RuleResult:
    rule_id: str
    triggered: bool
    reason: str
    evidence: list[str] = field(default_factory=list)


def _missing_customer(context: dict) -> RuleResult:
    customer = context.get("customer")
    triggered = customer is None
    return RuleResult(
        rule_id="MISSING-CUSTOMER",
        triggered=triggered,
        reason="Customer record is missing from investigation context.",
        evidence=["customer_context=missing"] if triggered else [],
    )


def _missing_subscription(context: dict) -> RuleResult:
    subscription = context.get("subscription")
    triggered = subscription is None
    return RuleResult(
        rule_id="MISSING-SUBSCRIPTION",
        triggered=triggered,
        reason="Subscription/service record is missing.",
        evidence=["subscription=missing"] if triggered else [],
    )


def _missing_network(context: dict) -> RuleResult:
    ticket = context.get("ticket", {})
    category = ticket.get("category", "")
    network = context.get("network", {})
    site = network.get("site")
    if category not in ("network", "connectivity", "voice", "sms"):
        return RuleResult(rule_id="MISSING-NETWORK", triggered=False, reason="Network context not required for this category.")
    triggered = site is None
    return RuleResult(
        rule_id="MISSING-NETWORK",
        triggered=triggered,
        reason="Network site is missing for a network-related case.",
        evidence=["network_site=missing"] if triggered else [],
    )


def _network_site_degraded(context: dict) -> RuleResult:
    network = context.get("network", {})
    site = network.get("site")
    if not site:
        return RuleResult(rule_id="NET-DEGRADED-SITE", triggered=False, reason="No network site available.")
    status = site.get("status", "")
    triggered = status in ("degraded", "offline")
    ev = [f"site={site.get('site_code', '?')}", f"network_status={status}"]
    return RuleResult(
        rule_id="NET-DEGRADED-SITE",
        triggered=triggered,
        reason=f"Serving site {site.get('site_code', '?')} is currently {status}." if triggered else f"Serving site {site.get('site_code', '?')} is {status}.",
        evidence=ev,
    )


def _active_network_events(context: dict) -> RuleResult:
    network = context.get("network", {})
    events = network.get("events", [])
    active = [e for e in events if e.get("status") == "active"]
    high_sev = [e for e in active if e.get("severity") in ("high", "critical")]
    triggered = len(high_sev) > 0
    ev = [f"site={e.get('site_code', '?')} event={e.get('event_type', '?')} severity={e.get('severity', '?')}" for e in high_sev[:3]]
    return RuleResult(
        rule_id="NET-ACTIVE-EVENTS",
        triggered=triggered,
        reason=f"{len(high_sev)} high-severity active network event(s) at serving site." if triggered else "No high-severity active network events.",
        evidence=ev,
    )


def _active_incident_match(context: dict) -> RuleResult:
    incidents = context.get("incidents", [])
    active = [i for i in incidents if i.get("status") in ("investigating", "identified", "monitoring")]
    triggered = len(active) > 0
    ev = [f"incident={i.get('incident_number', '?')} severity={i.get('severity', '?')} region={i.get('region', '?')}" for i in active[:3]]
    return RuleResult(
        rule_id="INC-ACTIVE-MATCH",
        triggered=triggered,
        reason=f"{len(active)} active incident(s) in the same region." if triggered else "No active incidents match this case.",
        evidence=ev,
    )


def _no_incident_but_network_issue(context: dict) -> RuleResult:
    net_rule = _network_site_degraded(context)
    events_rule = _active_network_events(context)
    inc_rule = _active_incident_match(context)
    network_issue = net_rule.triggered or events_rule.triggered
    has_incident = inc_rule.triggered
    triggered = network_issue and not has_incident
    return RuleResult(
        rule_id="NET-NO-INCIDENT",
        triggered=triggered,
        reason="Network issue exists but no active incident is recorded. Do not claim outage.",
        evidence=["network_issue=true", "active_incident=false"],
    )


def _billing_case(context: dict) -> RuleResult:
    ticket = context.get("ticket", {})
    category = ticket.get("category", "")
    triggered = category == "billing"
    return RuleResult(
        rule_id="CASE-BILLING",
        triggered=triggered,
        reason="Billing case detected. Network evidence should not automatically become root cause.",
        evidence=[f"category={category}"],
    )


def _repeated_tickets(context: dict) -> RuleResult:
    prev = context.get("previous_tickets", [])
    same_cat = context.get("investigation", {}).get("same_category_previous_tickets", 0)
    triggered = same_cat >= 2
    return RuleResult(
        rule_id="CASE-REPEATED",
        triggered=triggered,
        reason=f"Customer has {same_cat} previous related ticket(s)." if triggered else "No repeated ticket pattern detected.",
        evidence=[f"same_category_previous_tickets={same_cat}"],
    )


def _enterprise_customer(context: dict) -> RuleResult:
    customer = context.get("customer", {})
    segment = customer.get("segment", "")
    triggered = segment == "enterprise"
    return RuleResult(
        rule_id="CASE-ENTERPRISE",
        triggered=triggered,
        reason="Enterprise customer detected. Requires careful handling.",
        evidence=[f"segment={segment}"] if triggered else [],
    )


def _critical_priority(context: dict) -> RuleResult:
    ticket = context.get("ticket", {})
    priority = ticket.get("priority", "")
    triggered = priority == "critical"
    return RuleResult(
        rule_id="CASE-CRITICAL",
        triggered=triggered,
        reason="Critical priority case.",
        evidence=[f"priority={priority}"] if triggered else [],
    )


def _high_priority(context: dict) -> RuleResult:
    ticket = context.get("ticket", {})
    priority = ticket.get("priority", "")
    triggered = priority == "high"
    return RuleResult(
        rule_id="CASE-HIGH-PRIORITY",
        triggered=triggered,
        reason="High priority case.",
        evidence=[f"priority={priority}"] if triggered else [],
    )


def _ai_conflict_with_rules(context: dict) -> RuleResult:
    ai_result = context.get("ai_result")
    if ai_result is None:
        return RuleResult(rule_id="AI-CONFLICT", triggered=False, reason="No AI result available for conflict check.")
    reasoning = ai_result.get("reasoning", {})
    inc_rule = _active_incident_match(context)
    net_degraded = _network_site_degraded(context)
    ai_summary = reasoning.get("summary", "").lower()
    ai_mentions_outage = any(w in ai_summary for w in ["outage", "outage", "service loss", "complete loss"])
    has_incident = inc_rule.triggered
    has_degraded = net_degraded.triggered
    triggered = ai_mentions_outage and not has_incident and not has_degraded
    return RuleResult(
        rule_id="AI-CONFLICT",
        triggered=triggered,
        reason="AI assessment suggests a possible outage, but no active incident or degraded site is present in operational data.",
        evidence=["ai_mentions_outage=true", f"active_incident={has_incident}", f"site_degraded={has_degraded}"],
    )


RULE_PRECEDENCE = [
    "MISSING-CUSTOMER",
    "MISSING-SUBSCRIPTION",
    "MISSING-NETWORK",
    "CASE-CRITICAL",
    "CASE-ENTERPRISE",
    "INC-ACTIVE-MATCH",
    "NET-DEGRADED-SITE",
    "NET-ACTIVE-EVENTS",
    "NET-NO-INCIDENT",
    "CASE-BILLING",
    "CASE-REPEATED",
    "CASE-HIGH-PRIORITY",
    "AI-CONFLICT",
]


ALL_RULES = [
    _missing_customer,
    _missing_subscription,
    _missing_network,
    _network_site_degraded,
    _active_network_events,
    _active_incident_match,
    _no_incident_but_network_issue,
    _billing_case,
    _repeated_tickets,
    _enterprise_customer,
    _critical_priority,
    _high_priority,
    _ai_conflict_with_rules,
]


def evaluate_rules(context: dict) -> list[RuleResult]:
    results = []
    for rule_fn in ALL_RULES:
        result = rule_fn(context)
        results.append(result)
    return results


def get_triggered_rules(results: list[RuleResult]) -> list[RuleResult]:
    return [r for r in results if r.triggered]


def requires_human_review(results: list[RuleResult, ], ai_confidence: str | None = None) -> tuple[bool, list[str]]:
    triggered = get_triggered_rules(results)
    reasons = []
    must_review_ids = {
        "MISSING-CUSTOMER", "MISSING-SUBSCRIPTION", "MISSING-NETWORK",
        "CASE-CRITICAL", "CASE-ENTERPRISE", "INC-ACTIVE-MATCH",
        "AI-CONFLICT", "NET-NO-INCIDENT",
    }
    for r in triggered:
        if r.rule_id in must_review_ids:
            reasons.append(f"Rule {r.rule_id}: {r.reason}")
    if ai_confidence == "low":
        reasons.append("AI confidence is low.")
    if not reasons and triggered:
        reasons.append("One or more operational rules were triggered.")
    requires = len(reasons) > 0
    return requires, reasons
