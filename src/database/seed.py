import random
import sqlite3
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

SEED = 42

CUSTOMER_FIRST_NAMES = [
    "James", "Maria", "Robert", "Linda", "Michael", "Patricia", "David", "Jennifer",
    "Richard", "Elizabeth", "Joseph", "Barbara", "Thomas", "Susan", "Charles", "Jessica",
    "Daniel", "Sarah", "Matthew", "Karen", "Anthony", "Lisa", "Mark", "Nancy",
    "Steven", "Betty", "Paul", "Margaret", "Andrew", "Sandra", "Kenneth", "Ashley",
    "Joshua", "Dorothy", "Kevin", "Kimberly", "Brian", "Emily", "George", "Donna",
    "Timothy", "Michelle", "Ronald", "Carol", "Edward", "Amanda", "Jason", "Melissa",
    "Jeffrey", "Deborah", "Ryan", "Stephanie", "Jacob", "Rebecca", "Gary", "Sharon",
    "Nicholas", "Laura", "Eric", "Cynthia",
]

CUSTOMER_LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
]

NETWORK_SITES = [
    ("NET-5G-001", "Metro 5G Tower Alpha", "5G", "Northeast", "Newark", 40.7357, -74.1724),
    ("NET-5G-002", "Downtown 5G Hub", "5G", "Northeast", "New York", 40.7128, -74.0060),
    ("NET-4G-003", "Suburban 4G Tower", "4G", "Northeast", "Hoboken", 40.7440, -74.0324),
    ("NET-FBR-004", "Fiber Central Office", "Fiber", "Southeast", "Atlanta", 33.7490, -84.3880),
    ("NET-5G-005", "Business District 5G", "5G", "Southeast", "Atlanta", 33.7851, -84.3740),
    ("NET-LTE-006", "Rural LTE Site", "LTE", "Midwest", "Columbus", 39.9612, -82.9988),
    ("NET-5G-007", "University 5G Campus", "5G", "Midwest", "Columbus", 39.9869, -83.0030),
    ("NET-4G-008", "Highway Corridor 4G", "4G", "Midwest", "Indianapolis", 39.7684, -86.1581),
    ("NET-FBR-009", "Fiber Neighborhood", "Fiber", "West", "Phoenix", 33.4484, -112.0740),
    ("NET-5G-010", "Convention Center 5G", "5G", "West", "Phoenix", 33.4487, -112.0738),
    ("NET-LTE-011", "Mountain LTE Relay", "LTE", "West", "Denver", 39.7392, -104.9903),
    ("NET-4G-012", "Suburban Expansion 4G", "4G", "West", "Denver", 39.7508, -104.9966),
    ("NET-5G-013", "Tech Park 5G", "5G", "West", "San Jose", 37.3382, -121.8863),
    ("NET-FBR-014", "Fiber Enterprise Hub", "Fiber", "West", "San Jose", 37.3420, -121.8850),
    ("NET-LTE-015", "Airport LTE Coverage", "LTE", "South", "Miami", 25.7617, -80.1918),
    ("NET-5G-016", "Beachfront 5G", "5G", "South", "Miami", 25.7907, -80.1300),
    ("NET-4G-017", "Industrial 4G Zone", "4G", "Northeast", "Philadelphia", 39.9526, -75.1652),
    ("NET-FBR-018", "Fiber Residential", "Fiber", "South", "Charlotte", 35.2271, -80.8431),
]

PLANS = [
    ("PLN-5GB", "5G Basic", "consumer", 49.99, 15, 500, 100, 100, 0),
    ("PLN-5GP", "5G Plus", "consumer", 69.99, 30, 1000, 500, 250, 1),
    ("PLN-5GU", "5G Unlimited", "consumer", 89.99, 999, 9999, 9999, 500, 1),
    ("PLN-BSP", "Business Pro", "small_business", 129.99, 50, 2000, 1000, 500, 1),
    ("PLN-ECN", "Enterprise Connect", "enterprise", 299.99, 200, 9999, 9999, 1000, 1),
    ("PLN-BBL", "Broadband Basic", "consumer", 39.99, 500, 0, 0, 100, 0),
    ("PLN-BBP", "Broadband Premium", "consumer", 59.99, 1000, 0, 0, 500, 0),
    ("PLN-BLP", "Business Link Pro", "small_business", 199.99, 1000, 0, 0, 1000, 1),
]

REGIONS = ["Northeast", "Southeast", "Midwest", "West", "South"]
REGION_SITES = {
    "Northeast": [1, 2, 3, 17],
    "Southeast": [4, 5, 18],
    "Midwest": [6, 7, 8],
    "West": [9, 10, 11, 12, 13, 14],
    "South": [15, 16, 18],
}

TICKET_TEMPLATES = [
    ("network", "high", "Slow 5G speeds during peak hours", "I've been experiencing very slow 5G speeds between 6-9 PM. Download speeds are barely reaching 10 Mbps when they should be over 200 Mbps."),
    ("network", "medium", "Intermittent 4G signal drops", "My phone keeps switching between 4G and no signal throughout the day. This has been happening for the past week."),
    ("connectivity", "high", "Cannot connect to broadband service", "My broadband connection has been down since this morning. I've tried rebooting the router multiple times."),
    ("connectivity", "medium", "Wi-Fi dropping on multiple devices", "All devices in my home are losing Wi-Fi connection every few minutes. The router shows connected but no internet."),
    ("billing", "low", "Unexpected charge on my bill", "I noticed a $25 charge labeled 'service fee' on my latest bill that I haven't seen before."),
    ("billing", "medium", "Promotional discount not applied", "My promotional rate of $49.99/month was supposed to continue for 12 months but I'm being charged $69.99."),
    ("voice", "medium", "Dropped calls on 5G", "Calls keep dropping when I'm on 5G. This doesn't happen when I switch to 4G."),
    ("voice", "low", "Poor call quality", "People on the other end keep saying my voice sounds robotic or garbled."),
    ("sms", "low", "Delayed text messages", "Text messages are arriving 5-10 minutes late, sometimes out of order."),
    ("roaming", "high", "No service while traveling abroad", "I'm in Europe and cannot get any cellular service despite having roaming enabled on my plan."),
    ("device", "medium", "SIM card not recognized", "My phone keeps saying 'No SIM detected' even after reseating the SIM card."),
    ("account", "low", "Cannot access online account", "I'm unable to log into my account through the app or website. Password reset emails aren't arriving."),
    ("network", "critical", "Complete service outage in my area", "I have zero cellular service. None of my family members have service either. This started about an hour ago."),
    ("connectivity", "high", "Business internet down affecting operations", "Our business fiber connection is completely down. We have 15 employees unable to work."),
    ("billing", "medium", "Incorrect data overage charges", "I'm on an unlimited plan but received a $150 overage charge for data usage."),
]

INTERACTION_SUMMARIES = [
    ("call", "Customer called about slow data speeds. Advised to check network settings and restart device.", "frustrated"),
    ("call", "Customer reported billing discrepancy. Escalated to billing department for review.", "neutral"),
    ("email", "Customer sent email requesting plan change. Confirmed new plan will activate next billing cycle.", "positive"),
    ("chat", "Customer initiated chat about service outage in their area. Provided estimated restoration time.", "neutral"),
    ("call", "Customer called to report dropped calls. Troubleshooting completed, issue unresolved.", "frustrated"),
    ("app", "Customer submitted feedback through app about slow speeds during commute.", "neutral"),
    ("call", "Customer called to cancel service due to repeated issues. Retention offer provided.", "angry"),
    ("email", "Customer emailed about promotional pricing not reflected on bill.", "frustrated"),
    ("chat", "Customer asked about international roaming options. Provided plan comparison.", "positive"),
    ("call", "Customer called about SIM card issues. Replacement SIM ordered.", "neutral"),
    ("sms", "Automated survey sent. Customer rated experience 3 out of 5.", "neutral"),
    ("call", "Customer called about data overage charges. Reviewed usage, explained policy.", "frustrated"),
    ("app", "Customer used app to troubleshoot Wi-Fi. Resolution successful.", "positive"),
    ("call", "Customer called about billing after recent move. Updated address and reclassified plan.", "positive"),
    ("email", "Customer emailed about intermittent connectivity. Ticket created for technical review.", "neutral"),
    ("call", "Customer called to express dissatisfaction with repeated service interruptions.", "angry"),
    ("chat", "Customer asked about 5G coverage expansion timeline. Provided available information.", "neutral"),
    ("call", "Customer called about voice quality issues during calls.", "frustrated"),
    ("email", "Customer requested upgrade from Business Pro to Enterprise Connect.", "positive"),
    ("call", "Customer called about roaming not working while traveling. APN settings updated.", "neutral"),
]

TICKET_HISTORY_TEMPLATES = [
    ("created", "customer", "Customer submitted ticket through {channel}."),
    ("assigned", "system", "Ticket auto-assigned to {team} team."),
    ("troubleshooting", "support_agent", "Agent initiated standard network troubleshooting steps."),
    ("status_changed", "system", "Ticket status changed from {old_status} to {new_status}."),
    ("customer_reply", "customer", "Customer responded: '{response}'."),
    ("agent_note", "support_agent", "Agent note: {note}."),
    ("escalation", "system", "Ticket escalated to {team} team due to {reason}."),
    ("resolved", "support_agent", "Issue resolved: {resolution}."),
]

TEAMS = ["Network Operations", "Billing Support", "Technical Support", "Customer Retention", "Enterprise Support", "Field Operations"]


def _random_date(start: datetime, end: datetime, rng: random.Random) -> datetime:
    delta = end - start
    random_seconds = rng.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


def _format(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def seed_database(conn: sqlite3.Connection, force: bool = False) -> None:
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] > 0 and not force:
        logger.info("Database already seeded, skipping")
        return

    if force:
        tables = [
            "customer_interactions", "ticket_events", "tickets",
            "network_events", "incidents", "subscriptions",
            "customers", "plans", "network_sites"
        ]
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")

    rng = random.Random(SEED)
    now = datetime(2026, 9, 4, 12, 0, 0)
    six_months_ago = now - timedelta(days=180)
    one_year_ago = now - timedelta(days=365)
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    _insert_plans(cursor)
    _insert_network_sites(cursor)
    customer_ids = _insert_customers(cursor, rng, now, one_year_ago)
    plan_ids = _get_plan_ids(cursor)
    site_ids = _get_site_ids(cursor)
    subscription_ids = _insert_subscriptions(cursor, customer_ids, plan_ids, site_ids, rng, one_year_ago)
    _insert_network_events(cursor, site_ids, rng, now, thirty_days_ago, seven_days_ago)
    incident_ids = _insert_incidents(cursor, rng, now, thirty_days_ago)
    ticket_data = _insert_tickets(cursor, customer_ids, subscription_ids, rng, now, thirty_days_ago, seven_days_ago)
    _insert_ticket_events(cursor, ticket_data, rng, now, thirty_days_ago)
    _insert_customer_interactions(cursor, customer_ids, ticket_data, rng, now, thirty_days_ago)

    conn.commit()
    logger.info("Database seeded successfully")


def _insert_plans(cursor: sqlite3.Cursor) -> None:
    for code, name, ptype, price, data, voice, sms, speed, roaming in PLANS:
        cursor.execute(
            "INSERT INTO plans (plan_code, plan_name, plan_type, monthly_price, data_limit_gb, voice_minutes, sms_limit, speed_mbps, roaming_enabled, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')",
            (code, name, ptype, price, data, voice, sms, speed, roaming),
        )


def _insert_network_sites(cursor: sqlite3.Cursor) -> None:
    base_maintenance = datetime(2026, 8, 15, 2, 0, 0)
    statuses = ["operational"] * 12 + ["degraded"] * 3 + ["maintenance"] * 2 + ["offline"] * 1
    rng_site = random.Random(SEED + 100)
    for i, (code, name, tech, region, city, lat, lon) in enumerate(NETWORK_SITES):
        capacity = rng_site.randint(45, 98)
        status = statuses[i]
        maintenance = _format(base_maintenance + timedelta(days=rng_site.randint(0, 20), hours=rng_site.randint(0, 6)))
        cursor.execute(
            "INSERT INTO network_sites (site_code, site_name, technology, region, city, latitude, longitude, capacity_percent, status, last_maintenance_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (code, name, tech, region, city, lat, lon, capacity, status, maintenance),
        )


def _insert_customers(cursor: sqlite3.Cursor, rng: random.Random, now: datetime, one_year_ago: datetime) -> list[int]:
    segments = (["consumer"] * 35 + ["small_business"] * 12 + ["enterprise"] * 8)[:55]
    statuses = (["active"] * 47 + ["suspended"] * 5 + ["closed"] * 3)[:55]
    ids = []
    for i in range(55):
        first = rng.choice(CUSTOMER_FIRST_NAMES)
        last = rng.choice(CUSTOMER_LAST_NAMES)
        name = f"{first} {last}"
        number = f"CUST-{100001 + i}"
        email = f"{first.lower()}.{last.lower()}{i}@example.com"
        phone = f"+1-201-{rng.randint(200, 999)}-{rng.randint(1000, 9999)}"
        segment = segments[i]
        status = statuses[i]
        created = _format(_random_date(one_year_ago, now, rng))
        cursor.execute(
            "INSERT INTO customers (customer_number, name, email, phone, segment, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (number, name, email, phone, segment, status, created),
        )
        ids.append(cursor.lastrowid)
    return ids


def _get_plan_ids(cursor: sqlite3.Cursor) -> list[int]:
    cursor.execute("SELECT id FROM plans ORDER BY id")
    return [row[0] for row in cursor.fetchall()]


def _get_site_ids(cursor: sqlite3.Cursor) -> list[int]:
    cursor.execute("SELECT id FROM network_sites ORDER BY id")
    return [row[0] for row in cursor.fetchall()]


def _insert_subscriptions(cursor: sqlite3.Cursor, customer_ids: list[int], plan_ids: list[int], site_ids: list[int], rng: random.Random, one_year_ago: datetime) -> list[int]:
    service_types = (["mobile"] * 40 + ["broadband"] * 15 + ["business_link"] * 8)[:63]
    statuses = (["active"] * 55 + ["suspended"] * 5 + ["cancelled"] * 3)[:63]
    ids = []
    service_counter = 10001
    for i in range(63):
        customer_id = rng.choice(customer_ids)
        plan_id = rng.choice(plan_ids)
        site_id = rng.choice(site_ids)
        stype = service_types[i] if i < len(service_types) else "mobile"
        snumber = f"SVS-{service_counter}"
        service_counter += 1
        activation = _format(_random_date(one_year_ago, datetime(2026, 6, 1, 0, 0, 0), rng))
        status = statuses[i] if i < len(statuses) else "active"
        usage = round(rng.uniform(0.5, 80.0), 2)
        billing_day = rng.randint(1, 28)
        cursor.execute(
            "INSERT INTO subscriptions (customer_id, plan_id, service_number, service_type, activation_date, status, network_site_id, data_usage_gb, billing_cycle_day) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (customer_id, plan_id, snumber, stype, activation, status, site_id, usage, billing_day),
        )
        ids.append(cursor.lastrowid)
    return ids


def _insert_network_events(cursor: sqlite3.Cursor, site_ids: list[int], rng: random.Random, now: datetime, thirty_days_ago: datetime, seven_days_ago: datetime) -> None:
    event_templates = [
        ("latency", "high", "Elevated latency detected", "Network monitoring detected sustained latency above 200ms on this site."),
        ("packet_loss", "medium", "Packet loss observed", "Intermittent packet loss of 5-8% detected during peak hours."),
        ("congestion", "critical", "Site congestion critical", "Cell congestion exceeding 95% capacity. Multiple users affected."),
        ("hardware_failure", "high", "RRU hardware failure", "Remote radio unit reported hardware fault. Field team dispatched."),
        ("service_degradation", "medium", "Service quality degradation", "Throughput below expected thresholds for this technology class."),
        ("maintenance", "low", "Scheduled maintenance window", "Planned maintenance for firmware upgrade and optimization."),
        ("latency", "low", "Minor latency increase", "Slight increase in round-trip time observed during off-peak."),
        ("congestion", "high", "Peak hour congestion", "Congestion levels reaching 85% during evening hours."),
        ("packet_loss", "critical", "Severe packet loss", "Packet loss exceeding 15% reported. Users unable to maintain connections."),
        ("service_degradation", "high", "5G mmWave coverage gap", "Identified coverage gap in 5G mmWave deployment area."),
    ]
    for i in range(42):
        site_id = rng.choice(site_ids)
        template = rng.choice(event_templates)
        started = _format(_random_date(seven_days_ago, now, rng))
        is_resolved = rng.random() > 0.35
        resolved = _format(_random_date(datetime.strptime(started, "%Y-%m-%dT%H:%M:%S"), now, rng)) if is_resolved else None
        status = "resolved" if is_resolved else "active"
        cursor.execute(
            "INSERT INTO network_events (site_id, event_type, severity, title, description, started_at, resolved_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (site_id, template[0], template[1], template[2], template[3], started, resolved, status),
        )


def _insert_incidents(cursor: sqlite3.Cursor, rng: random.Random, now: datetime, thirty_days_ago: datetime) -> list[int]:
    incidents = [
        ("Northeast", "critical", "Major 5G outage in Newark metro area", "Complete loss of 5G connectivity across Newark metropolitan region. 4G fallback available but congested.", "5G", 15000),
        ("Southeast", "high", "Fiber backbone degradation Atlanta", "Fiber link between Atlanta CO and regional hub experiencing elevated BER. Affects enterprise customers.", "Fiber", 2500),
        ("Midwest", "medium", "Columbus area packet loss", "Widespread packet loss reported across Columbus suburban sites. Root cause under investigation.", "4G", 8000),
        ("West", "high", "Phoenix heat-related tower issues", "Multiple sites in Phoenix reporting thermal throttling due to extreme heat. Cooling systems activated.", "5G", 5000),
        ("South", "critical", "Miami coastal flooding impacts", "Severe weather caused flooding near coastal network sites. Multiple sites offline.", "4G", 12000),
        ("Northeast", "medium", "New York fiber maintenance", "Planned maintenance on fiber routes affecting some business customers.", "Fiber", 1200),
        ("West", "low", "Denver LTE spectrum optimization", "Ongoing spectrum refarming in Denver metro. Minor service interruptions possible.", "LTE", 3000),
        ("Midwest", "high", "Indianapolis tower hardware failure", "Main transmission equipment failure at Indianapolis central site.", "4G", 6000),
        ("Southeast", "medium", "Charlotte 5G rollout interference", "New 5G installations causing interference with existing 4G equipment.", "5G", 1800),
        ("West", "critical", "San Jose data center connectivity", "Primary data center link down. Customers experiencing complete service loss.", "5G", 20000),
        ("South", "medium", "Miami 5G mmWave handover issues", "Users on 5G mmWave experiencing frequent handover failures near Beachfront area.", "5G", 4000),
        ("Northeast", "low", "Philadelphia scheduled upgrade", "Network upgrade at Industrial zone site. Brief service interruptions expected.", "4G", 1500),
    ]
    ids = []
    statuses_pool = [
        ("investigating", 3), ("identified", 3), ("monitoring", 3), ("resolved", 3)
    ]
    for i, (region, severity, title, desc, service, affected) in enumerate(incidents):
        number = f"INC-{2026001 + i}"
        started = _format(_random_date(thirty_days_ago, now - timedelta(days=2), rng))
        status_weights = rng.choice(["investigating", "identified", "monitoring", "resolved"])
        is_resolved = status_weights == "resolved"
        resolved = _format(_random_date(datetime.strptime(started, "%Y-%m-%dT%H:%M:%S"), now, rng)) if is_resolved else None
        cursor.execute(
            "INSERT INTO incidents (incident_number, title, description, affected_service, severity, region, started_at, resolved_at, status, affected_customers_estimate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (number, title, desc, service, severity, region, started, resolved, status_weights, affected),
        )
        ids.append(cursor.lastrowid)
    return ids


def _insert_tickets(cursor: sqlite3.Cursor, customer_ids: list[int], subscription_ids: list[int], rng: random.Random, now: datetime, thirty_days_ago: datetime, seven_days_ago: datetime) -> list[tuple[int, int, int, str, str]]:
    ticket_data = []
    ticket_counter = 300001
    for i in range(110):
        customer_id = rng.choice(customer_ids)
        subscription_id = rng.choice(subscription_ids)
        template = rng.choice(TICKET_TEMPLATES)
        category, priority, subject, description = template
        number = f"TKT-{ticket_counter}"
        ticket_counter += 1
        channel = rng.choice(["web", "mobile_app", "call_center", "email", "store"])
        team = rng.choice(TEAMS)
        created = _format(_random_date(thirty_days_ago, now - timedelta(days=1), rng))
        updated = _format(_random_date(datetime.strptime(created, "%Y-%m-%dT%H:%M:%S"), now, rng))
        status = rng.choice(["open"] * 15 + ["in_progress"] * 20 + ["pending_customer"] * 10 + ["resolved"] * 50 + ["escalated"] * 15)
        resolved = None
        if status == "resolved":
            resolved = _format(_random_date(datetime.strptime(updated, "%Y-%m-%dT%H:%M:%S"), now, rng))
        cursor.execute(
            "INSERT INTO tickets (ticket_number, customer_id, subscription_id, category, priority, subject, description, status, channel, assigned_team, created_at, updated_at, resolved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (number, customer_id, subscription_id, category, priority, subject, description, status, channel, team, created, updated, resolved),
        )
        ticket_id = cursor.lastrowid
        ticket_data.append((ticket_id, customer_id, subscription_id, status, created))
    return ticket_data


def _insert_ticket_events(cursor: sqlite3.Cursor, ticket_data: list[tuple], rng: random.Random, now: datetime, thirty_days_ago: datetime) -> None:
    responses = [
        "I've tried restarting my device but the issue persists.",
        "Can someone please look into this urgently?",
        "The problem started again after your last fix.",
        "Thank you, the issue seems to be improving.",
        "I need an update on this ticket.",
        "This is affecting my business operations significantly.",
        "I was told this would be resolved by now.",
        "Still experiencing the same problem.",
    ]
    notes = [
        "Standard troubleshooting completed. Monitoring for 24 hours.",
        "Escalated to network operations for deeper investigation.",
        "Customer confirmed partial improvement after APN reset.",
        "Checked account status. All services appear active.",
        "Tested line from our end. Signal levels nominal.",
        "Customer's subscription is active with no billing issues.",
        "Regional team notified. Site visit scheduled.",
        "Applied configuration update. Awaiting customer feedback.",
    ]
    resolutions = [
        "Issue resolved by resetting network settings on customer device.",
        "Network configuration updated. Customer confirmed service restored.",
        "Ticket resolved after regional outage was fixed.",
        "Customer's plan upgraded to resolve speed limitations.",
        "Field technician replaced damaged equipment at customer premises.",
        "Billing correction applied. Customer satisfied.",
    ]
    for ticket_id, customer_id, subscription_id, status, created in ticket_data:
        created_dt = datetime.strptime(created, "%Y-%m-%dT%H:%M:%S")
        channel = rng.choice(["web", "mobile_app", "call_center", "email", "store"])
        team = rng.choice(TEAMS)
        cursor.execute(
            "INSERT INTO ticket_events (ticket_id, event_type, actor_type, description, created_at) VALUES (?, 'created', 'customer', ?, ?)",
            (ticket_id, f"Customer submitted ticket through {channel}.", created),
        )
        assigned_time = _format(created_dt + timedelta(minutes=rng.randint(5, 60)))
        cursor.execute(
            "INSERT INTO ticket_events (ticket_id, event_type, actor_type, description, created_at) VALUES (?, 'assigned', 'system', ?, ?)",
            (ticket_id, f"Ticket auto-assigned to {team} team.", assigned_time),
        )
        num_events = rng.randint(1, 5)
        for j in range(num_events):
            event_type = rng.choice(["customer_reply", "agent_note", "troubleshooting", "status_changed"])
            actor = "customer" if event_type == "customer_reply" else "support_agent"
            if event_type == "customer_reply":
                desc = rng.choice(responses)
            elif event_type == "agent_note":
                desc = rng.choice(notes)
            elif event_type == "troubleshooting":
                desc = "Agent performed standard network diagnostics and signal verification."
            else:
                desc = f"Ticket status updated. Current status: {status}."
            event_time = _format(created_dt + timedelta(hours=rng.randint(1, 72), minutes=rng.randint(0, 59)))
            cursor.execute(
                "INSERT INTO ticket_events (ticket_id, event_type, actor_type, description, created_at) VALUES (?, ?, ?, ?, ?)",
                (ticket_id, event_type, actor, desc, event_time),
            )
        if status == "resolved":
            res_time = _format(created_dt + timedelta(hours=rng.randint(24, 168)))
            cursor.execute(
                "INSERT INTO ticket_events (ticket_id, event_type, actor_type, description, created_at) VALUES (?, 'resolved', 'support_agent', ?, ?)",
                (ticket_id, rng.choice(resolutions), res_time),
            )
        if status == "escalated":
            esc_time = _format(created_dt + timedelta(hours=rng.randint(2, 48)))
            cursor.execute(
                "INSERT INTO ticket_events (ticket_id, event_type, actor_type, description, created_at) VALUES (?, 'escalation', 'system', ?, ?)",
                (ticket_id, f"Ticket escalated to {team} team due to unresolved customer issue.", esc_time),
            )


def _insert_customer_interactions(cursor: sqlite3.Cursor, customer_ids: list[int], ticket_data: list[tuple], rng: random.Random, now: datetime, thirty_days_ago: datetime) -> None:
    for i in range(110):
        customer_id = rng.choice(customer_ids)
        template = rng.choice(INTERACTION_SUMMARIES)
        itype, summary, sentiment = template
        created = _format(_random_date(thirty_days_ago, now, rng))
        ticket_id = None
        if rng.random() > 0.3 and ticket_data:
            chosen = rng.choice(ticket_data)
            ticket_id = chosen[0]
        cursor.execute(
            "INSERT INTO customer_interactions (customer_id, ticket_id, interaction_type, summary, sentiment, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (customer_id, ticket_id, itype, summary, sentiment, created),
        )
