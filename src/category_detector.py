"""Category detector for incoming customer messages.

Maps customer intent to valid ticket categories:
network, billing, connectivity, voice, sms, roaming, device, account
"""
from __future__ import annotations

import re

CATEGORY_KEYWORDS = {
    "billing": [
        "bill", "billing", "charge", "charged", "charging", "refund", "payment",
        "invoice", "overcharge", "overcharged", "deduction", "debited", "balance",
        "tariff", "recharge", "plan price", "cost", "receipt", "rupees", "rs",
        "inr", "duplicate charge", "unauthorized charge", "fee",
    ],
    "connectivity": [
        "wifi", "wi-fi", "broadband", "internet", "connection", "disconnect",
        "disconnected", "slow", "speed", "buffering", "latency", "ping",
        "packet loss", "fiber", "drop", "dropping", "drops", "signal",
        "browsing", "connectivity", "no internet", "poor speed", "download",
    ],
    "network": [
        "tower", "coverage", "reception", "no service", "outage", "blackout",
        "site", "network down", "5g", "4g", "lte", "network issue", "signal bar",
        "degradation", "frequency", "cell",
    ],
    "voice": [
        "call", "calling", "voice", "incoming call", "outgoing call", "call drop",
        "call dropping", "audio", "hear", "voice quality", "can't hear", "ringing",
        "dial", "busy tone", "voicemail",
    ],
    "sms": [
        "sms", "text message", "otp", "verification code", "message delivery",
        "can't receive text", "can't send text",
    ],
    "roaming": [
        "roaming", "international roaming", "national roaming", "abroad", "travel",
        "overseas", "out of country", "roaming pack",
    ],
    "device": [
        "router", "modem", "sim", "sim card", "esim", "handset", "phone",
        "hardware", "device", "dongle", "adapter", "equipment",
    ],
    "account": [
        "account", "profile", "password", "login", "update details", "address",
        "transfer", "ownership", "kyc", "verification", "name change", "support",
    ],
}


def detect_category(text: str) -> str:
    """Detect ticket category from customer message text."""
    if not text:
        return "account"

    text_lower = text.lower()

    # Score each category based on keyword matches
    scores: dict[str, int] = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                # Phrase matches have higher weight
                score += 2 if " " in kw else 1
        if score > 0:
            scores[cat] = score

    if not scores:
        return "account"

    # Return category with highest score
    return max(scores.items(), key=lambda x: x[1])[0]
