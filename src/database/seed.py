import random
import sqlite3
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

SEED = 42

# ── Telecom Providers ────────────────────────────────────

PROVIDERS = [
    ("JIO", "Reliance Jio", "Reliance Jio"),
    ("AIRTEL", "Bharti Airtel", "Bharti Airtel"),
    ("VI", "Vodafone Idea", "Vodafone Idea (Vi)"),
    ("BSNL", "Bharat Sanchar Nigam Limited", "BSNL"),
]

# ── Indian Customer Names ────────────────────────────────

INDIAN_FIRST_NAMES = [
    "Sai Kiran", "Ananya", "Rahul", "Priya", "Arjun", "Sneha", "Rohit", "Kavya",
    "Aditya", "Neha", "Vamsi", "Pooja", "Harshith", "Divya", "Karthik", "Meera",
    "Venkat", "Lakshmi", "Suresh", "Deepa", "Rajesh", "Swathi", "Manoj", "Padma",
    "Krishna", "Jyothi", "Mahesh", "Sunitha", "Ravi", "Kavitha", "Naveen", "Rekha",
    "Srinivas", "Geeta", "Prasad", "Usha", "Ganesh", "Sarita", "Ashok", "Latha",
    "Madhavi", "Ramesh", "Sita", "Vinod", "Anjali", "Bharat", "Shobha", "Dinesh",
    "Kamala", "Prakash",
]

INDIAN_LAST_NAMES = [
    "Reddy", "Sharma", "Verma", "Nair", "Kumar", "Rao", "Menon", "Iyer",
    "Patel", "Srinivas", "Krishna", "Murthy", "Gupta", "Joshi", "Pillai", "Das",
    "Chowdary", "Naidu", "Babu", "Prasad", "Dev", "Mishra", "Tiwari", "Singh",
    "Yadav", "Pandey", "Hegde", "Bhat", "Naik", "Shetty",
]

INDIAN_EMAIL_DOMAINS = ["example.com", "example.in"]

# ── Indian Cities & States ───────────────────────────────

CITIES = [
    ("Hyderabad", "Telangana", 17.3850, 78.4867),
    ("Bengaluru", "Karnataka", 12.9716, 77.5946),
    ("Chennai", "Tamil Nadu", 13.0827, 80.2707),
    ("Mumbai", "Maharashtra", 19.0760, 72.8777),
    ("Pune", "Maharashtra", 18.5204, 73.8567),
    ("Delhi", "Delhi", 28.7041, 77.1025),
    ("New Delhi", "Delhi", 28.6139, 77.2090),
    ("Kolkata", "West Bengal", 22.5726, 88.3639),
    ("Vijayawada", "Andhra Pradesh", 16.5062, 80.6480),
    ("Visakhapatnam", "Andhra Pradesh", 17.6868, 83.2185),
    ("Kurnool", "Andhra Pradesh", 15.8281, 78.0373),
    ("Tirupati", "Andhra Pradesh", 13.6288, 79.4192),
    ("Guntur", "Andhra Pradesh", 16.3067, 80.4365),
    ("Warangal", "Telangana", 17.9784, 79.5941),
    ("Mysuru", "Karnataka", 12.2958, 76.6394),
    ("Kochi", "Kerala", 9.9312, 76.2673),
    ("Ahmedabad", "Gujarat", 23.0225, 72.5714),
    ("Jaipur", "Rajasthan", 26.9124, 75.7873),
    ("Lucknow", "Uttar Pradesh", 26.8467, 80.9462),
    ("Bhopal", "Madhya Pradesh", 23.2599, 77.4126),
]

INDIAN_STATES = [
    "Andhra Pradesh", "Telangana", "Karnataka", "Tamil Nadu", "Maharashtra",
    "Delhi", "West Bengal", "Kerala", "Gujarat", "Rajasthan",
    "Uttar Pradesh", "Madhya Pradesh",
]

# ── Network Sites (India) ────────────────────────────────

NETWORK_SITES = [
    # Hyderabad - Telangana
    ("SITE-HYD-01", "Hyderabad Metro 5G Alpha", "5G", "JIO", "South", "Hyderabad", "Telangana", 17.3950, 78.4700),
    ("SITE-HYD-02", "Hyderabad 4G Tower Secunderabad", "4G", "AIRTEL", "South", "Hyderabad", "Telangana", 17.4399, 78.4983),
    ("SITE-HYD-03", "HITEC City Fiber Hub", "Fiber", "JIO", "South", "Hyderabad", "Telangana", 17.4435, 78.3772),
    ("SITE-HYD-04", "Gachibowli 5G Business Park", "5G", "AIRTEL", "South", "Hyderabad", "Telangana", 17.4400, 78.3489),
    # Bengaluru - Karnataka
    ("SITE-BLR-01", "Whitefield 5G Tech Park", "5G", "JIO", "South", "Bengaluru", "Karnataka", 12.9698, 77.7500),
    ("SITE-BLR-02", "Koramangala 4G Hub", "4G", "VI", "South", "Bengaluru", "Karnataka", 12.9352, 77.6245),
    ("SITE-BLR-03", "HSR Layout Fiber Node", "Fiber", "AIRTEL", "South", "Bengaluru", "Karnataka", 12.9116, 77.6389),
    # Chennai - Tamil Nadu
    ("SITE-CHN-01", "T Nagar 5G Tower", "5G", "JIO", "South", "Chennai", "Tamil Nadu", 13.0418, 80.2341),
    ("SITE-CHN-02", "OMR Corridor 4G", "4G", "AIRTEL", "South", "Chennai", "Tamil Nadu", 12.9165, 80.2274),
    # Mumbai - Maharashtra
    ("SITE-MUM-01", "Andheri 5G Business District", "5G", "JIO", "West", "Mumbai", "Maharashtra", 19.1136, 72.8697),
    ("SITE-MUM-02", "BKC Fiber Enterprise", "Fiber", "AIRTEL", "West", "Mumbai", "Maharashtra", 19.0596, 72.8656),
    ("SITE-MUM-03", "Navi Mumbai 4G Tower", "4G", "VI", "West", "Mumbai", "Maharashtra", 19.0330, 73.0297),
    # Pune - Maharashtra
    ("SITE-PUN-01", "Hinjewadi IT Park 5G", "5G", "JIO", "West", "Pune", "Maharashtra", 18.5913, 73.7389),
    ("SITE-PUN-02", "Kothrud 4G Tower", "4G", "BSNL", "West", "Pune", "Maharashtra", 18.5074, 73.8077),
    # Delhi / New Delhi
    ("SITE-DEL-01", "Connaught Place 5G Hub", "5G", "JIO", "North", "New Delhi", "Delhi", 28.6315, 77.2167),
    ("SITE-DEL-02", "Dwarka Fiber Node", "Fiber", "AIRTEL", "North", "Delhi", "Delhi", 28.5921, 77.0460),
    ("SITE-DEL-03", "South Delhi 4G Tower", "4G", "VI", "North", "New Delhi", "Delhi", 28.5244, 77.2066),
    # Vijayawada - Andhra Pradesh
    ("SITE-VJD-01", "Vijayawada 5G Tower", "5G", "JIO", "South", "Vijayawada", "Andhra Pradesh", 16.5062, 80.6480),
    ("SITE-VJD-02", "Guntur Road 4G", "4G", "BSNL", "South", "Vijayawada", "Andhra Pradesh", 16.5100, 80.6300),
    # Visakhapatnam - Andhra Pradesh
    ("SITE-VSK-01", "Visakhapatnam Beach Road 5G", "5G", "AIRTEL", "East", "Visakhapatnam", "Andhra Pradesh", 17.7153, 83.2985),
    # Kolkata - West Bengal
    ("SITE-KOL-01", "Salt Lake 5G Tower", "5G", "JIO", "East", "Kolkata", "West Bengal", 22.5804, 88.4169),
    ("SITE-KOL-02", "Park Street 4G Hub", "4G", "AIRTEL", "East", "Kolkata", "West Bengal", 22.5530, 88.3510),
    # Kochi - Kerala
    ("SITE-KCH-01", "Kakkanad IT Hub 5G", "5G", "JIO", "South", "Kochi", "Kerala", 10.0159, 76.3067),
    # Ahmedabad - Gujarat
    ("SITE-AMD-01", "SG Highway 5G Tower", "5G", "JIO", "West", "Ahmedabad", "Gujarat", 23.0369, 72.5290),
    ("SITE-AMD-02", "CG Road 4G Hub", "4G", "VI", "West", "Ahmedabad", "Gujarat", 23.0469, 72.5720),
    # Jaipur - Rajasthan
    ("SITE-JAI-01", "Malviya Nagar 5G", "5G", "AIRTEL", "North", "Jaipur", "Rajasthan", 26.8550, 75.8120),
    # Lucknow - Uttar Pradesh
    ("SITE-LKO-01", "Gomti Nagar 4G Tower", "4G", "BSNL", "North", "Lucknow", "Uttar Pradesh", 26.8560, 80.9920),
    # Mysuru - Karnataka
    ("SITE-MYS-01", "Mysuru 5G Tower", "5G", "VI", "South", "Mysuru", "Karnataka", 12.2958, 76.6394),
    # Warangal - Telangana
    ("SITE-WRG-01", "Warangal 4G Hub", "4G", "BSNL", "South", "Warangal", "Telangana", 17.9784, 79.5941),
    # Kurnool - Andhra Pradesh
    ("SITE-KNL-01", "Kurnool 4G Tower", "4G", "BSNL", "South", "Kurnool", "Andhra Pradesh", 15.8281, 78.0373),
]

# ── Plans (INR) ──────────────────────────────────────────

PLANS = [
    # Jio plans
    ("PLN-JIO-5GB", "Jio 5G Basic", "consumer", "JIO", 299, 15, 500, 100, 100, 0),
    ("PLN-JIO-5GP", "Jio 5G Plus", "consumer", "JIO", 599, 30, 1000, 500, 250, 1),
    ("PLN-JIO-5GU", "Jio 5G Unlimited", "consumer", "JIO", 999, 999, 9999, 9999, 500, 1),
    # Airtel plans
    ("PLN-AIR-5GB", "Airtel 5G Basic", "consumer", "AIRTEL", 349, 20, 500, 100, 150, 0),
    ("PLN-AIR-5GP", "Airtel 5G Premium", "consumer", "AIRTEL", 699, 40, 1500, 500, 300, 1),
    ("PLN-AIR-ECN", "Airtel Enterprise Connect", "enterprise", "AIRTEL", 4999, 200, 9999, 9999, 1000, 1),
    # Vi plans
    ("PLN-VI-5GB", "Vi 5G Basic", "consumer", "VI", 279, 15, 400, 100, 100, 0),
    ("PLN-VI-BSP", "Vi Business Pro", "small_business", "VI", 1499, 100, 3000, 1000, 500, 1),
    # BSNL plans
    ("PLN-BSN-BBL", "BSNL Broadband Basic", "consumer", "BSNL", 399, 500, 0, 0, 100, 0),
    ("PLN-BSN-BBP", "BSNL Broadband Premium", "consumer", "BSNL", 799, 1000, 0, 0, 500, 0),
    ("PLN-BSN-BLP", "BSNL Business Link Pro", "small_business", "BSNL", 1999, 1000, 0, 0, 1000, 1),
]

# ── Region-Site Mapping ──────────────────────────────────

REGIONS = ["South", "West", "North", "East"]
REGION_SITES = {
    "South": [1, 2, 3, 4, 5, 6, 7, 8, 9, 17, 18, 19, 20, 21, 22, 23, 24, 27, 28],
    "West": [10, 11, 12, 13, 14, 25, 26],
    "North": [15, 16, 29, 30],
    "East": [21, 22],
}

# ── Ticket Templates ─────────────────────────────────────

TICKET_TEMPLATES = [
    ("network", "high", "Slow 5G speeds during peak hours in Hyderabad",
     "I've been experiencing very slow 5G speeds between 6-9 PM in Gachibowli area. Download speeds are barely reaching 10 Mbps when they should be over 200 Mbps."),
    ("network", "medium", "Intermittent 4G signal drops in Bengaluru",
     "My phone keeps switching between 4G and no signal throughout the day in Koramangala. This has been happening for the past week."),
    ("connectivity", "high", "Cannot connect to broadband service in Mumbai",
     "My broadband connection has been down since this morning in Andheri. I've tried rebooting the router multiple times."),
    ("connectivity", "medium", "Wi-Fi dropping on multiple devices in Pune",
     "All devices in my home in Hinjewadi are losing Wi-Fi connection every few minutes. The router shows connected but no internet."),
    ("billing", "low", "Unexpected charge on my bill",
     "I noticed a ₹450 charge labeled 'service fee' on my latest bill that I haven't seen before."),
    ("billing", "medium", "Promotional discount not applied",
     "My promotional rate of ₹299/month was supposed to continue for 12 months but I'm being charged ₹599."),
    ("voice", "medium", "Dropped calls on 5G network",
     "Calls keep dropping when I'm on 5G in Delhi. This doesn't happen when I switch to 4G."),
    ("voice", "low", "Poor call quality",
     "People on the other end keep saying my voice sounds robotic or garbled."),
    ("sms", "low", "Delayed text messages",
     "Text messages are arriving 5-10 minutes late, sometimes out of order."),
    ("roaming", "high", "No service while traveling",
     "I'm in Kolkata and cannot get any cellular service despite having roaming enabled on my plan."),
    ("device", "medium", "SIM card not recognized",
     "My phone keeps saying 'No SIM detected' even after reseating the SIM card."),
    ("account", "low", "Cannot access online account",
     "I'm unable to log into my account through the app or website. Password reset emails aren't arriving."),
    ("network", "critical", "Complete service outage in my area",
     "I have zero cellular service in Vijayawada. None of my family members have service either. This started about an hour ago."),
    ("connectivity", "high", "Business internet down affecting operations",
     "Our business fiber connection is completely down in Whitefield, Bengaluru. We have 15 employees unable to work."),
    ("billing", "medium", "Incorrect data overage charges",
     "I'm on an unlimited plan but received a ₹2500 overage charge for data usage."),
    ("network", "high", "5G connectivity degradation in Hyderabad",
     "The 5G network in HITEC City has been extremely slow for 3 days. Multiple colleagues report the same issue."),
    ("network", "medium", "Network congestion near Jaipur",
     "Mobile data is extremely slow in Malviya Nagar area during evening hours."),
    ("connectivity", "high", "Fiber cut in Lucknow",
     "Our office broadband in Gomti Nagar has been down since morning. A neighbor mentioned a fiber cut nearby."),
    ("billing", "medium", "Roaming charges dispute",
     "I was charged ₹1200 for roaming even though I have a roaming-inclusive plan."),
    ("voice", "high", "VoLTE calls not connecting",
     "VoLTE calls fail to connect in Kurnool. I have to switch to 3G to make calls."),
]

# ── Interaction Summaries ─────────────────────────────────

INTERACTION_SUMMARIES = [
    ("call", "Customer called about slow data speeds in Hyderabad. Advised to check network settings and restart device.", "frustrated"),
    ("call", "Customer reported billing discrepancy. Escalated to billing department for review.", "neutral"),
    ("email", "Customer sent email requesting plan change. Confirmed new plan will activate next billing cycle.", "positive"),
    ("chat", "Customer initiated chat about service outage in their area. Provided estimated restoration time.", "neutral"),
    ("call", "Customer called to report dropped calls on 5G. Troubleshooting completed, issue unresolved.", "frustrated"),
    ("app", "Customer submitted feedback through app about slow speeds during commute in Bengaluru.", "neutral"),
    ("call", "Customer called to cancel service due to repeated issues. Retention offer provided.", "angry"),
    ("email", "Customer emailed about promotional pricing not reflected on bill.", "frustrated"),
    ("chat", "Customer asked about international roaming options. Provided plan comparison.", "positive"),
    ("call", "Customer called about SIM card issues in Chennai. Replacement SIM ordered.", "neutral"),
    ("sms", "Automated survey sent. Customer rated experience 3 out of 5.", "neutral"),
    ("call", "Customer called about data overage charges. Reviewed usage, explained policy.", "frustrated"),
    ("app", "Customer used app to troubleshoot Wi-Fi at home in Pune. Resolution successful.", "positive"),
    ("call", "Customer called about billing after recent move from Delhi to Mumbai. Updated address.", "positive"),
    ("email", "Customer emailed about intermittent connectivity in Kolkata. Ticket created for technical review.", "neutral"),
    ("call", "Customer called to express dissatisfaction with repeated service interruptions in Vijayawada.", "angry"),
    ("chat", "Customer asked about 5G coverage expansion timeline in Mysuru. Provided available information.", "neutral"),
    ("call", "Customer called about voice quality issues during calls in Kochi.", "frustrated"),
    ("email", "Customer requested upgrade from Vi Business Pro to Airtel Enterprise Connect.", "positive"),
    ("call", "Customer called about roaming not working while traveling. APN settings updated.", "neutral"),
]

# ── Teams ─────────────────────────────────────────────────

TEAMS = [
    "Network Operations", "Billing Support", "Technical Support",
    "Customer Retention", "Enterprise Support", "Field Operations",
]


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
            "review_states", "customer_interactions", "ticket_events", "tickets",
            "network_events", "incidents", "subscriptions",
            "customers", "plans", "network_sites", "telecom_providers",
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

    provider_ids = _insert_providers(cursor)
    _insert_plans(cursor, provider_ids)
    site_ids = _insert_network_sites(cursor, provider_ids)
    customer_ids = _insert_customers(cursor, rng, now, one_year_ago)
    plan_ids = _get_plan_ids(cursor)
    subscription_ids = _insert_subscriptions(cursor, customer_ids, plan_ids, site_ids, rng, one_year_ago)
    _insert_network_events(cursor, site_ids, rng, now, thirty_days_ago, seven_days_ago)
    incident_ids = _insert_incidents(cursor, provider_ids, rng, now, thirty_days_ago)
    ticket_data = _insert_tickets(cursor, customer_ids, subscription_ids, rng, now, thirty_days_ago, seven_days_ago)
    _insert_ticket_events(cursor, ticket_data, rng, now, thirty_days_ago)
    _insert_customer_interactions(cursor, customer_ids, ticket_data, rng, now, thirty_days_ago)

    conn.commit()
    logger.info("Database seeded successfully with India-focused data")


def _insert_providers(cursor: sqlite3.Cursor) -> dict[str, int]:
    ids = {}
    for code, name, display_name in PROVIDERS:
        cursor.execute(
            "INSERT INTO telecom_providers (code, name, display_name, status) VALUES (?, ?, ?, 'active')",
            (code, name, display_name),
        )
        ids[code] = cursor.lastrowid
    return ids


def _insert_plans(cursor: sqlite3.Cursor, provider_ids: dict[str, int]) -> None:
    for code, name, ptype, provider_code, price, data, voice, sms, speed, roaming in PLANS:
        cursor.execute(
            "INSERT INTO plans (plan_code, plan_name, plan_type, provider_id, monthly_price, data_limit_gb, voice_minutes, sms_limit, speed_mbps, roaming_enabled, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')",
            (code, name, ptype, provider_ids[provider_code], price, data, voice, sms, speed, roaming),
        )


def _insert_network_sites(cursor: sqlite3.Cursor, provider_ids: dict[str, int]) -> list[int]:
    base_maintenance = datetime(2026, 8, 15, 2, 0, 0)
    statuses = ["operational"] * 20 + ["degraded"] * 5 + ["maintenance"] * 3 + ["offline"] * 2
    rng_site = random.Random(SEED + 100)
    ids = []
    for i, (code, name, tech, provider_code, region, city, state, lat, lon) in enumerate(NETWORK_SITES):
        capacity = rng_site.randint(45, 98)
        status = statuses[i] if i < len(statuses) else "operational"
        maintenance = _format(base_maintenance + timedelta(days=rng_site.randint(0, 20), hours=rng_site.randint(0, 6)))
        cursor.execute(
            "INSERT INTO network_sites (site_code, site_name, technology, provider_id, region, city, state, latitude, longitude, capacity_percent, status, last_maintenance_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (code, name, tech, provider_ids[provider_code], region, city, state, lat, lon, capacity, status, maintenance),
        )
        ids.append(cursor.lastrowid)
    return ids


def _insert_customers(cursor: sqlite3.Cursor, rng: random.Random, now: datetime, one_year_ago: datetime) -> list[int]:
    segments = (["consumer"] * 35 + ["small_business"] * 12 + ["enterprise"] * 8)[:55]
    statuses = (["active"] * 47 + ["suspended"] * 5 + ["closed"] * 3)[:55]
    ids = []
    used_names = set()
    for i in range(55):
        while True:
            first = rng.choice(INDIAN_FIRST_NAMES)
            last = rng.choice(INDIAN_LAST_NAMES)
            full_name = f"{first} {last}"
            if full_name not in used_names:
                used_names.add(full_name)
                break
        number = f"CUST-{100001 + i}"
        email = f"{first.lower().replace(' ', '')}.{last.lower()}{i}@{'example.in' if i % 3 == 0 else 'example.com'}"
        phone = f"+91 {rng.choice([7, 8, 9])}{rng.randint(10000000, 99999999)}"
        segment = segments[i]
        status = statuses[i]
        city = rng.choice(CITIES)
        created = _format(_random_date(one_year_ago, now, rng))
        cursor.execute(
            "INSERT INTO customers (customer_number, name, email, phone, segment, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (number, full_name, email, phone, segment, status, created),
        )
        ids.append(cursor.lastrowid)
    return ids


def _get_plan_ids(cursor: sqlite3.Cursor) -> list[int]:
    cursor.execute("SELECT id FROM plans ORDER BY id")
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
        snumber = f"+91 {rng.choice([7, 8, 9])}{rng.randint(10000000, 99999999)}"
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


def _insert_incidents(cursor: sqlite3.Cursor, provider_ids: dict[str, int], rng: random.Random, now: datetime, thirty_days_ago: datetime) -> list[int]:
    incidents = [
        ("South", "critical", "Major 5G outage in Hyderabad metro area", "Complete loss of 5G connectivity across Hyderabad metropolitan region. 4G fallback available but congested.", "5G", "JIO", 15000),
        ("South", "high", "Fiber backbone degradation Bengaluru", "Fiber link between Bengaluru CO and regional hub experiencing elevated BER. Affects enterprise customers.", "Fiber", "AIRTEL", 2500),
        ("South", "medium", "Chennai area packet loss", "Widespread packet loss reported across Chennai suburban sites. Root cause under investigation.", "4G", "VI", 8000),
        ("West", "high", "Mumbai monsoon-related tower issues", "Multiple sites in Mumbai reporting thermal throttling due to monsoon humidity. Cooling systems activated.", "5G", "JIO", 5000),
        ("South", "critical", "Kochi coastal flooding impacts", "Severe monsoon flooding near coastal network sites. Multiple sites offline in Kochi.", "4G", "AIRTEL", 12000),
        ("North", "medium", "Delhi fiber maintenance", "Planned maintenance on fiber routes affecting some business customers in New Delhi.", "Fiber", "AIRTEL", 1200),
        ("South", "low", "Mysuru LTE spectrum optimization", "Ongoing spectrum refarming in Mysuru metro. Minor service interruptions possible.", "LTE", "VI", 3000),
        ("North", "high", "Lucknow tower hardware failure", "Main transmission equipment failure at Lucknow central site.", "4G", "BSNL", 6000),
        ("East", "medium", "Kolkata 5G rollout interference", "New 5G installations causing interference with existing 4G equipment in Salt Lake.", "5G", "JIO", 1800),
        ("West", "critical", "Pune data center connectivity", "Primary data center link down in Hinjewadi. Customers experiencing complete service loss.", "5G", "JIO", 20000),
        ("South", "medium", "Visakhapatnam 5G mmWave handover issues", "Users on 5G mmWave experiencing frequent handover failures near Beach Road area.", "5G", "AIRTEL", 4000),
        ("South", "low", "Vijayawada scheduled upgrade", "Network upgrade at Vijayawada central site. Brief service interruptions expected.", "4G", "BSNL", 1500),
    ]
    ids = []
    for i, (region, severity, title, desc, service, provider_code, affected) in enumerate(incidents):
        number = f"INC-{2026001 + i}"
        started = _format(_random_date(thirty_days_ago, now - timedelta(days=2), rng))
        status_weights = rng.choice(["investigating", "identified", "monitoring", "resolved"])
        is_resolved = status_weights == "resolved"
        resolved = _format(_random_date(datetime.strptime(started, "%Y-%m-%dT%H:%M:%S"), now, rng)) if is_resolved else None
        cursor.execute(
            "INSERT INTO incidents (incident_number, title, description, affected_service, severity, region, provider_id, started_at, resolved_at, status, affected_customers_estimate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (number, title, desc, service, severity, region, provider_ids[provider_code], started, resolved, status_weights, affected),
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
        "Still experiencing the same problem in my area.",
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
