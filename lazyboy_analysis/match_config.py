"""Match a dealer's stocked configuration to the same configuration on La-Z-Boy.com.

Matching on model name alone compares whatever the dealer stocks against
La-Z-Boy.com's cheapest cover of the base frame, which is not the same product.
Steinhafels names its items by configuration -- "Fully Loaded", "Power Headrest",
"Wall Saver" -- and La-Z-Boy.com sells each of those as a separate product with
its own price. Read loosely, a fully loaded chair priced against a base one
looked like an 85% dealer premium; it is a spec difference.

So a match here requires the same collection, form, drive, and the same
headrest / lumbar / wall / high-leg / lift attributes on both sides.

Leather is a known gap. La-Z-Boy.com renders only six or seven covers per
product server-side, and a leather cover (an LB-prefixed id) appears for just 21
of 226 products, so a dealer's leather item usually has no leather counterpart
to price against. Those are excluded rather than compared to a fabric cover.
"""

import re

FULLY_LOADED = re.compile(r"fully loaded", re.I)

ATTRS = {
    "power":     r"\bpower\b|\btri-?power\b|\bdual power\b",
    "headrest":  r"head\s?rest",
    "lumbar":    r"lumbar",
    "wall":      r"wall\s?saver|\bwall\b",
    "highleg":   r"high\s?leg",
    "lift":      r"\blift\b",
}

FORMS = [("Loveseat", r"loveseat"), ("Sofa", r"\bsofa\b"),
         ("Sectional", r"sectional"), ("Recliner", r"recliner|reclining chair")]

# "w/" has no trailing word boundary, so it must be stripped before the
# word-based pass -- left in, it deposits a stray "w" and "jay w" never matches
# "jay".
SLASHED = re.compile(r"\bw/", re.I)

# Words that describe cover, trim or retail packaging rather than configuration.
NOISE = re.compile(
    r"\b(leather|fabric|with wireless remote|wireless remote|w/ wireless remote|"
    r"zero gravity|platinum|gold|bronze|luxe|massage|heat|oversized|petite|"
    r"big & tall|swivel|glider|gliding|rocking|rocker|reclining|recliner|chair|"
    r"sofa|loveseat|sectional|console|storage|modular|chaise|duo|power|manual|"
    r"headrest|head rest|lumbar|wall\s?saver|wall|high\s?leg|lift|fully loaded|"
    r"w/|with|and|&|\d+-?pc\.?)\b", re.I)


def collection(title):
    """The model name, with configuration and trim words removed."""
    t = re.sub(r"[®™]", " ", title or "")
    t = SLASHED.sub(" ", t)
    t = NOISE.sub(" ", t)
    t = re.sub(r"[^A-Za-z\- ]", " ", t)
    # Drop orphaned single letters left by stripped tokens.
    t = " ".join(w for w in t.split() if len(w) > 1)
    return re.sub(r"\s+", " ", t).strip().lower()


def form_of(title):
    for name, pattern in FORMS:
        if re.search(pattern, title or "", re.I):
            return name
    return "Other"


def spec(title):
    """Configuration signature. 'Fully loaded' expands to power+headrest+lumbar."""
    t = title or ""
    loaded = bool(FULLY_LOADED.search(t))
    out = {k: bool(re.search(p, t, re.I)) for k, p in ATTRS.items()}
    if loaded:
        out["power"] = out["headrest"] = out["lumbar"] = True
    # A "wall saver" is a wall recliner; a rocking recliner is not.
    if re.search(r"rock", t, re.I) and not re.search(r"wall", t, re.I):
        out["wall"] = False
    return out


def key(title):
    s = spec(title)
    return (collection(title), form_of(title),
            tuple(sorted(k for k, v in s.items() if v)))


def is_leather(title):
    return bool(re.search(r"\bleather\b", title or "", re.I))
