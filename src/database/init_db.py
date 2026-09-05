import sqlite3
import logging

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS telecom_providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    segment TEXT NOT NULL CHECK (segment IN ('consumer', 'small_business', 'enterprise')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'closed')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_code TEXT NOT NULL UNIQUE,
    plan_name TEXT NOT NULL,
    plan_type TEXT NOT NULL,
    provider_id INTEGER NOT NULL REFERENCES telecom_providers(id),
    monthly_price REAL NOT NULL,
    data_limit_gb INTEGER NOT NULL,
    voice_minutes INTEGER NOT NULL,
    sms_limit INTEGER NOT NULL,
    speed_mbps INTEGER NOT NULL,
    roaming_enabled INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'deprecated', 'archived'))
);

CREATE TABLE IF NOT EXISTS network_sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_code TEXT NOT NULL UNIQUE,
    site_name TEXT NOT NULL,
    technology TEXT NOT NULL CHECK (technology IN ('4G', '5G', 'LTE', 'Fiber')),
    provider_id INTEGER NOT NULL REFERENCES telecom_providers(id),
    region TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    capacity_percent INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'operational' CHECK (status IN ('operational', 'degraded', 'maintenance', 'offline')),
    last_maintenance_at TEXT
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    plan_id INTEGER NOT NULL REFERENCES plans(id),
    service_number TEXT NOT NULL UNIQUE,
    service_type TEXT NOT NULL CHECK (service_type IN ('mobile', 'broadband', 'business_link')),
    activation_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'cancelled')),
    network_site_id INTEGER NOT NULL REFERENCES network_sites(id),
    data_usage_gb REAL NOT NULL DEFAULT 0,
    billing_cycle_day INTEGER NOT NULL CHECK (billing_cycle_day BETWEEN 1 AND 28)
);

CREATE TABLE IF NOT EXISTS network_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL REFERENCES network_sites(id),
    event_type TEXT NOT NULL CHECK (event_type IN ('latency', 'packet_loss', 'congestion', 'hardware_failure', 'service_degradation', 'maintenance')),
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    started_at TEXT NOT NULL,
    resolved_at TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'resolved'))
);

CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_number TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    affected_service TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    region TEXT NOT NULL,
    provider_id INTEGER NOT NULL REFERENCES telecom_providers(id),
    started_at TEXT NOT NULL,
    resolved_at TEXT,
    status TEXT NOT NULL DEFAULT 'investigating' CHECK (status IN ('investigating', 'identified', 'monitoring', 'resolved')),
    affected_customers_estimate INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_number TEXT NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    subscription_id INTEGER REFERENCES subscriptions(id),
    category TEXT NOT NULL CHECK (category IN ('network', 'billing', 'connectivity', 'voice', 'sms', 'roaming', 'device', 'account')),
    priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    subject TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'pending_customer', 'resolved', 'escalated', 'closed', 'analyzing', 'needs_information', 'pending_agent_approval', 'escalation_requested', 'human_review', 'approved', 'dismissed', 'new')),
    channel TEXT NOT NULL CHECK (channel IN ('web', 'mobile_app', 'call_center', 'email', 'store')),
    assigned_team TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    resolved_at TEXT
    ,archived INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ticket_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    event_type TEXT NOT NULL CHECK (event_type IN ('created', 'assigned', 'customer_reply', 'agent_note', 'status_changed', 'troubleshooting', 'escalation', 'resolved')),
    actor_type TEXT NOT NULL CHECK (actor_type IN ('customer', 'support_agent', 'system')),
    description TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS customer_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    ticket_id INTEGER REFERENCES tickets(id),
    interaction_type TEXT NOT NULL CHECK (interaction_type IN ('call', 'email', 'chat', 'sms', 'app')),
    summary TEXT NOT NULL,
    sentiment TEXT NOT NULL CHECK (sentiment IN ('positive', 'neutral', 'frustrated', 'angry')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    recommendation_category TEXT,
    recommendation_action TEXT,
    confidence TEXT,
    reviewer_decision TEXT CHECK (reviewer_decision IN ('pending_review', 'approved', 'needs_information', 'escalation_requested', 'dismissed')),
    reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS case_state_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    actor TEXT NOT NULL DEFAULT 'system',
    reason TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clarification_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    question TEXT NOT NULL,
    missing_field TEXT NOT NULL,
    reason TEXT,
    turn_number INTEGER NOT NULL DEFAULT 1,
    answer TEXT,
    asked_at TEXT NOT NULL,
    answered_at TEXT
);

CREATE TABLE IF NOT EXISTS escalation_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    escalation_queue TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    escalation_reasons TEXT,
    handover_summary TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    assigned_to TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    event_type TEXT NOT NULL,
    details TEXT,
    actor TEXT NOT NULL DEFAULT 'system',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS internal_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    note TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT 'agent',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resolution_drafts (
    ticket_id INTEGER PRIMARY KEY REFERENCES tickets(id),
    draft TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT NOT NULL DEFAULT 'agent'
);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'closed')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id),
    sender TEXT NOT NULL CHECK (sender IN ('customer', 'assistant', 'system')),
    content TEXT NOT NULL,
    mode TEXT CHECK (mode IN ('A', 'B', 'C')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS case_analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    mode TEXT NOT NULL CHECK (mode IN ('A', 'B', 'C')),
    classification_json TEXT NOT NULL,
    draft_json TEXT,
    clarification_json TEXT,
    handover_json TEXT,
    conflicts_json TEXT,
    retrieval_info_json TEXT,
    errors_json TEXT,
    state_transition_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_customers_number ON customers(customer_number);
CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status);
CREATE INDEX IF NOT EXISTS idx_customers_segment ON customers(segment);
CREATE INDEX IF NOT EXISTS idx_subscriptions_customer ON subscriptions(customer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_plan ON subscriptions(plan_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_site ON subscriptions(network_site_id);
CREATE INDEX IF NOT EXISTS idx_network_events_site ON network_events(site_id);
CREATE INDEX IF NOT EXISTS idx_network_events_status ON network_events(status);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_region ON incidents(region);
CREATE INDEX IF NOT EXISTS idx_tickets_customer ON tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(category);
CREATE INDEX IF NOT EXISTS idx_ticket_events_ticket ON ticket_events(ticket_id);
CREATE INDEX IF NOT EXISTS idx_interactions_customer ON customer_interactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_review_states_ticket ON review_states(ticket_id);
CREATE INDEX IF NOT EXISTS idx_plans_provider ON plans(provider_id);
CREATE INDEX IF NOT EXISTS idx_sites_provider ON network_sites(provider_id);
CREATE INDEX IF NOT EXISTS idx_incidents_provider ON incidents(provider_id);
CREATE INDEX IF NOT EXISTS idx_state_history_ticket ON case_state_history(ticket_id);
CREATE INDEX IF NOT EXISTS idx_clarification_ticket ON clarification_requests(ticket_id);
CREATE INDEX IF NOT EXISTS idx_escalation_ticket ON escalation_records(ticket_id);
CREATE INDEX IF NOT EXISTS idx_escalation_status ON escalation_records(status);
CREATE INDEX IF NOT EXISTS idx_audit_ticket ON audit_events(ticket_id);
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_events(event_type);
CREATE INDEX IF NOT EXISTS idx_conversations_ticket ON conversations(ticket_id);
CREATE INDEX IF NOT EXISTS idx_conversations_customer ON conversations(customer_id);
CREATE INDEX IF NOT EXISTS idx_conv_messages_conversation ON conversation_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_case_analysis_ticket ON case_analysis_results(ticket_id);
"""


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    logger.info("Database schema created successfully")
