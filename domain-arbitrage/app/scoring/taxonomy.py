"""Industry taxonomy and geographic vocabulary.

Deliberately small and readable. The point is not exhaustive coverage - it is
that classification be *inspectable*: you can see exactly which token caused a
domain to be filed under `insurance`, and correct it by editing one line.

An LLM classifier (``app/scoring/classify.py``) can refine or override a
low-confidence deterministic result, but the deterministic pass always runs
first and is always recorded.
"""

from __future__ import annotations

CATEGORY_KEYWORDS: dict[str, set[str]] = {
    "legal": {"law", "legal", "attorney", "attorneys", "lawyer", "lawyers",
              "counsel", "litigation", "paralegal", "solicitor", "justice",
              "defense", "injury", "claims", "arbitration", "compliance"},
    "health": {"health", "medical", "clinic", "dental", "dentist", "doctor",
               "care", "therapy", "therapist", "wellness", "pharmacy", "med",
               "surgery", "surgical", "hospital", "nurse", "nursing", "rehab",
               "chiropractic", "orthodontic", "dermatology", "psychiatry",
               "telehealth", "patient", "diagnostic", "diagnostics"},
    "biotech": {"bio", "biotech", "genomics", "genome", "pharma", "protein",
                "molecular", "clinical", "vaccine", "peptide", "assay"},
    "finance": {"finance", "financial", "capital", "invest", "investing",
                "investment", "fund", "funds", "wealth", "bank", "banking",
                "credit", "loan", "loans", "lending", "mortgage", "payments",
                "payment", "payroll", "accounting", "tax", "taxes", "audit",
                "treasury", "equity", "trading", "trader", "broker", "fintech"},
    "insurance": {"insurance", "insure", "insured", "underwriting", "policy",
                  "premium", "actuarial", "coverage", "annuity", "reinsurance"},
    "real_estate": {"realty", "realtor", "property", "properties", "estate",
                    "homes", "housing", "apartment", "apartments", "rental",
                    "rentals", "lease", "leasing", "landlord", "tenant",
                    "mortgage", "escrow", "appraisal", "condo"},
    "construction": {"roofing", "roof", "plumbing", "plumber", "electrician",
                     "electrical", "hvac", "flooring", "masonry", "concrete",
                     "paving", "landscaping", "remodel", "remodeling",
                     "renovation", "contractor", "contractors", "builders",
                     "construction", "carpentry", "painting", "drywall",
                     "insulation", "scaffolding", "excavation", "demolition",
                     "windows", "siding", "fencing", "welding"},
    "home_services": {"cleaning", "cleaners", "maid", "janitorial", "pest",
                      "moving", "movers", "storage", "locksmith", "handyman",
                      "gardening", "lawn", "pool", "chimney", "gutter",
                      "restoration", "carpet", "upholstery", "laundry"},
    "automotive": {"auto", "automotive", "car", "cars", "truck", "trucks",
                   "vehicle", "vehicles", "motor", "motors", "tire", "tires",
                   "garage", "mechanic", "dealership", "parts", "rims",
                   "detailing", "towing", "collision", "bodyshop"},
    "logistics": {"fleet", "logistics", "freight", "shipping", "trucking",
                  "haulage", "courier", "delivery", "warehouse", "warehousing",
                  "supply", "dispatch", "cargo", "customs", "telematics",
                  "distribution", "fulfilment", "fulfillment", "lastmile"},
    "software": {"software", "app", "apps", "platform", "saas", "cloud", "api",
                 "devops", "code", "coding", "developer", "stack", "server",
                 "hosting", "database", "runtime", "framework", "microservice",
                 "kubernetes", "container", "deploy", "deployment"},
    "ai": {"ai", "ml", "intelligence", "neural", "llm", "gpt", "agent",
           "agents", "model", "models", "inference", "vision", "robotics",
           "robot", "automation", "autonomous", "cognitive", "copilot"},
    "data": {"data", "analytics", "analysis", "insights", "metrics",
             "dashboard", "reporting", "warehouse", "etl", "pipeline",
             "telemetry", "observability", "bi", "statistics", "forecasting"},
    "cybersecurity": {"security", "cyber", "secure", "threat", "firewall",
                      "encryption", "vpn", "identity", "auth", "phishing",
                      "malware", "ransomware", "soc", "pentest", "zerotrust"},
    "marketing": {"marketing", "seo", "ads", "advertising", "adtech", "brand",
                  "branding", "agency", "campaign", "leads", "lead", "growth",
                  "conversion", "affiliate", "influencer", "creative", "media",
                  "outreach", "crm", "funnel"},
    "ecommerce": {"shop", "store", "buy", "cart", "checkout", "retail",
                  "commerce", "ecommerce", "marketplace", "wholesale", "deals",
                  "discount", "coupon", "outlet", "dropship", "merch"},
    "food": {"food", "restaurant", "cafe", "coffee", "kitchen", "bakery",
             "brewing", "brewery", "catering", "grill", "pizza", "bistro",
             "eatery", "dining", "chef", "recipe", "recipes", "nutrition",
             "organic", "vegan", "snack", "beverage", "wine", "spirits"},
    "travel": {"travel", "tour", "tours", "hotel", "hotels", "resort",
               "flights", "booking", "vacation", "holiday", "cruise",
               "hostel", "airbnb", "itinerary", "destination", "safari"},
    "education": {"education", "school", "academy", "learning", "learn",
                  "course", "courses", "tutor", "tutoring", "training",
                  "university", "college", "campus", "student", "students",
                  "curriculum", "edtech", "certification", "bootcamp"},
    "energy": {"energy", "solar", "wind", "power", "electric", "battery",
               "grid", "renewable", "utility", "utilities", "oil", "gas",
               "petroleum", "nuclear", "hydrogen", "carbon", "emissions",
               "sustainability"},
    "manufacturing": {"manufacturing", "industrial", "factory", "machining",
                      "fabrication", "tooling", "cnc", "molding", "assembly",
                      "components", "bearings", "hydraulic", "pneumatic",
                      "valve", "valves", "pump", "pumps", "cooling", "hvac",
                      "chiller", "compressor", "automation"},
    "agriculture": {"farm", "farming", "agriculture", "agri", "crop", "crops",
                    "harvest", "livestock", "dairy", "poultry", "irrigation",
                    "seed", "seeds", "soil", "greenhouse", "hydroponic"},
    "hr": {"hr", "recruiting", "recruitment", "hiring", "talent", "staffing",
           "jobs", "job", "careers", "career", "payroll", "onboarding",
           "workforce", "employee", "employees", "benefits", "resume"},
    "crypto": {"crypto", "blockchain", "bitcoin", "ethereum", "token", "web3",
               "defi", "nft", "wallet", "mining", "staking", "dao", "ledger"},
    "gaming": {"game", "games", "gaming", "esports", "player", "arcade",
               "console", "studio", "quest", "guild", "casino", "poker",
               "betting", "wager"},
    "media": {"news", "magazine", "journal", "press", "podcast", "video",
              "streaming", "film", "movie", "movies", "music", "radio",
              "broadcast", "publishing", "editorial", "photography"},
    "sports": {"sport", "sports", "fitness", "gym", "athletic", "training",
               "coach", "coaching", "yoga", "pilates", "running", "cycling",
               "golf", "tennis", "soccer", "football", "basketball",
               "climbing", "surf", "ski", "snowboard"},
    "fashion": {"fashion", "style", "apparel", "clothing", "wear", "boutique",
                "jewelry", "jewellery", "watches", "shoes", "sneakers",
                "beauty", "cosmetics", "skincare", "salon", "spa", "makeup",
                "haircare", "perfume"},
    "pets": {"pet", "pets", "dog", "dogs", "cat", "cats", "puppy", "kitten",
             "vet", "veterinary", "grooming", "kennel", "aquarium"},
    "events": {"event", "events", "wedding", "weddings", "party", "venue",
               "conference", "expo", "festival", "ticket", "tickets",
               "catering", "planner", "photobooth"},
    "telecom": {"telecom", "wireless", "broadband", "fiber", "network",
                "networking", "voip", "sim", "mobile", "satellite", "5g"},
    "nonprofit": {"charity", "foundation", "nonprofit", "ngo", "volunteer",
                  "donate", "donation", "fundraising", "community"},
}

# Reverse index built once at import. Deterministic and O(1) per token.
KEYWORD_TO_CATEGORY: dict[str, str] = {}
for _cat, _words in CATEGORY_KEYWORDS.items():
    for _w in _words:
        # First category wins on collision; the dict order above is the
        # precedence order. Collisions are intentional and few.
        KEYWORD_TO_CATEGORY.setdefault(_w, _cat)

# Tokens that carry commercial intent regardless of industry.
TRANSACTIONAL_TOKENS = {"buy", "shop", "store", "price", "prices", "pricing",
                        "quote", "quotes", "cost", "cheap", "deal", "deals",
                        "hire", "rent", "rental", "book", "booking", "order",
                        "sale", "sales", "service", "services", "repair",
                        "installation", "contractor", "supplier", "supply"}

INFORMATIONAL_TOKENS = {"how", "what", "why", "guide", "guides", "tips",
                        "blog", "wiki", "news", "review", "reviews", "about",
                        "learn", "info", "facts", "history"}

# Geography. Enough to detect that a name is locally scoped, which changes both
# buyer depth (fewer buyers) and valuation (smaller market).
CITIES = {
    "london", "berlin", "paris", "madrid", "rome", "milan", "munich", "hamburg",
    "vienna", "zurich", "geneva", "amsterdam", "rotterdam", "brussels",
    "copenhagen", "stockholm", "oslo", "helsinki", "dublin", "lisbon",
    "warsaw", "prague", "budapest", "athens", "istanbul", "moscow",
    "newyork", "brooklyn", "manhattan", "boston", "chicago", "houston",
    "dallas", "austin", "denver", "phoenix", "seattle", "portland", "atlanta",
    "miami", "orlando", "tampa", "detroit", "philadelphia", "baltimore",
    "nashville", "charlotte", "minneapolis", "cleveland", "pittsburgh",
    "sandiego", "sanfrancisco", "losangeles", "lasvegas", "sacramento",
    "toronto", "vancouver", "montreal", "calgary", "ottawa",
    "sydney", "melbourne", "brisbane", "perth", "adelaide", "auckland",
    "tokyo", "osaka", "seoul", "beijing", "shanghai", "shenzhen", "hongkong",
    "singapore", "bangkok", "jakarta", "manila", "mumbai", "delhi",
    "bangalore", "chennai", "hyderabad", "dubai", "abudhabi", "doha", "riyadh",
    "capetown", "johannesburg", "nairobi", "lagos", "cairo",
    "saopaulo", "riodejaneiro", "buenosaires", "santiago", "bogota",
    "mexicocity", "lima", "manchester", "birmingham", "leeds", "glasgow",
    "edinburgh", "bristol", "liverpool", "cardiff", "belfast",
}

REGIONS = {
    "texas", "california", "florida", "georgia", "arizona", "nevada", "ohio",
    "michigan", "colorado", "oregon", "utah", "virginia", "carolina",
    "alabama", "indiana", "missouri", "tennessee", "kentucky", "kansas",
    "iowa", "minnesota", "wisconsin", "oklahoma", "arkansas", "louisiana",
    "bavaria", "catalonia", "andalusia", "tuscany", "provence", "yorkshire",
    "wales", "scotland", "ireland", "cornwall", "kent", "essex", "surrey",
    "ontario", "quebec", "alberta", "queensland", "victoria",
}

COUNTRIES = {
    "usa", "america", "american", "uk", "britain", "british", "england",
    "canada", "canadian", "australia", "australian", "germany", "german",
    "france", "french", "spain", "spanish", "italy", "italian", "japan",
    "japanese", "china", "chinese", "india", "indian", "brazil", "brazilian",
    "mexico", "mexican", "netherlands", "dutch", "sweden", "swedish",
    "norway", "denmark", "finland", "poland", "polish", "portugal", "ireland",
    "switzerland", "swiss", "austria", "belgium", "greece", "turkey",
    "singapore", "korea", "korean", "thailand", "vietnam", "indonesia",
    "nigeria", "kenya", "egypt", "israel", "uae", "emirates", "qatar",
    "saudi", "africa", "europe", "asia", "global", "international",
}


def geo_scope(words: list[str]) -> tuple[str, str | None]:
    """Return (scope, matched_token). Scope in {none, city, region, country}."""
    for w in words:
        if w in CITIES:
            return "city", w
    for w in words:
        if w in REGIONS:
            return "region", w
    for w in words:
        if w in COUNTRIES:
            return "country", w
    return "none", None
