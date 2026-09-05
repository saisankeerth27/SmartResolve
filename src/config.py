"""SmartResolve configuration with configurable thresholds."""
import os

# ── Retrieval thresholds ──────────────────────────────
SAFE_RETRIEVAL_THRESHOLD = float(os.getenv("SAFE_RETRIEVAL_THRESHOLD", "0.35"))
STRONG_RETRIEVAL_THRESHOLD = float(os.getenv("STRONG_RETRIEVAL_THRESHOLD", "0.55"))
WEAK_RETRIEVAL_THRESHOLD = float(os.getenv("WEAK_RETRIEVAL_THRESHOLD", "0.25"))
MIN_RETRIEVAL_RESULTS = int(os.getenv("MIN_RETRIEVAL_RESULTS", "1"))

# ── AI confidence thresholds ──────────────────────────
AI_CONFIDENCE_HIGH = "high"
AI_CONFIDENCE_MEDIUM = "medium"
AI_CONFIDENCE_LOW = "low"

# ── Repeat complaint thresholds ───────────────────────
REPEAT_COMPLAINT_THRESHOLD = int(os.getenv("REPEAT_COMPLAINT_THRESHOLD", "2"))
REPEAT_COMPLAINT_WINDOW_DAYS = int(os.getenv("REPEAT_COMPLAINT_WINDOW_DAYS", "90"))

# ── Escalation thresholds ────────────────────────────
SENSITIVE_BILLING_LIMIT_INR = float(os.getenv("SENSITIVE_BILLING_LIMIT_INR", "5000"))
CLARIFICATION_MAX_TURNS = int(os.getenv("CLARIFICATION_MAX_TURNS", "3"))

# ── Enterprise / high-impact ─────────────────────────
ENTERPRISE_SEGMENTS = ("enterprise",)
HIGH_IMPACT_PRIORITIES = ("critical", "high")

# ── Incident severity levels ─────────────────────────
MAJOR_INCIDENT_SEVERITIES = ("critical", "high")
ACTIVE_INCIDENT_STATUSES = ("investigating", "identified", "monitoring")

# ── Network status levels ────────────────────────────
CRITICAL_SITE_STATUSES = ("offline",)
DEGRADED_SITE_STATUSES = ("degraded",)

# ── Category to knowledge category mapping ───────────
CATEGORY_KNOWLEDGE_MAP = {
    "network": ["network", "connectivity"],
    "connectivity": ["connectivity", "network"],
    "billing": ["billing"],
    "voice": ["support", "connectivity"],
    "sms": ["support", "connectivity"],
    "roaming": ["roaming"],
    "device": ["device"],
    "account": ["support", "billing"],
}

# ── Clarification fallback questions ─────────────────
FALLBACK_QUESTIONS = {
    "location": "Could you please tell me your location or area so I can check network status in your region?",
    "timing": "When did you first notice this issue? Is it constant or intermittent?",
    "device": "What device are you using, and have you tried restarting it?",
    "scope": "Does this issue affect all your devices or just one specific device?",
    "symptoms": "Could you describe the specific symptoms you are experiencing?",
    "account": "Could you confirm your account or service number so I can look up your details?",
    "default": "Could you provide a bit more detail about the issue you are experiencing?",
}

# ── Escalation queues ────────────────────────────────
ESCALATION_QUEUES = {
    "critical": "Network Operations - Critical",
    "enterprise": "Enterprise Support - Priority",
    "repeat": "Customer Retention - L2",
    "conflict": "Billing Operations - Investigation",
    "billing_sensitive": "Billing Operations - Supervisor",
    "legal_safety": "Legal & Compliance - Immediate",
    "general": "Technical Support - L1",
    "insufficient": "Technical Support - L1",
}
