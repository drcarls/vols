# Scouting note — TickPick (negative control)

**2026-09-18 · manual observation · NOT an evidence-grade capture**

Source: operator screenshots of two hand-walked flows. No DOM, no hashes, no
controlled vantage. Filed outside the capture store so it cannot be mistaken for
evidence.

## What was observed

Event: Bears vs. Vikings, Soldier Field, Sun Sep 20 2026. Two listings walked to
checkout, quantity 2 in both.

| Listing | Unit price | Quantity | Total | Service fees |
|---|---|---|---|---|
| Section 110 Row 7 | $1,008 each | 2 | $2,016.00 | $0 |
| Section 108 Row 12 | $1,190 each | 2 | $2,380.00 | $0 |

Both reconcile exactly. Checkout states *"the only major ticket site that doesn't
charge buyers any service fees"*; the listing page carries *"The price you see is
the price you pay"*.

**The negative control passes.** No flags, zero gap, arithmetic closes on both.

## It also failed the collector, which is the point of a control

Run through the collector as it stood, the first flow produced a **556% gap** and
would have placed TickPick at the top of the league table as the worst offender in
the market. Two compounding errors, neither of which announces itself:

**1. A floor price used as the headline.** The listing page shows *"From $307+"* —
a floor across every listing, not the price of anything a buyer can select.
Compared against a $2,016 checkout total it invents a gap out of the comparison
itself. Resale marketplaces all lead this way, so this would have mis-scored the
entire resale half of Tier B.

Fixed: prices now carry a basis (exact / floor / range / unknown), detected from
wording and from a trailing `+`. The gap is computed only against an exact price,
and **withheld entirely** rather than fabricated when a flow offers nothing better.

**2. No quantity multiplier in the gap.** The headline is per ticket, the total
covers two. $1,008 each against $2,016 is a zero gap, not a 100% one. The
reconciliation check already handled quantity; the published metric did not —
so the number in the report was wrong while the internal check read clean.

Fixed: quantity is recorded per step and the gap is total minus headline × quantity.

Both are locked in `tests/test_real_world_regressions.py` against these observed
numbers, alongside a test that a genuine two-ticket drip is still caught — so the
fix cannot quietly suppress real findings.

## Free vantage verification

TickPick renders its own geolocation guess in the UI (*"Events Near ..."*). That
is a way to verify the proxy is actually exiting where the vendor's label claims,
rather than trusting the label — which is an open diligence item on the Bright Data
ISP tier for MN, MA, CO and NJ.

Worth noting the observed session showed **"Events Near Dublin"**, so this scouting
ran from an uncontrolled and probably non-US vantage. It does not affect the
arithmetic, but it is a reminder that a real capture must pin the vantage, and that
this signal is worth extracting on every TickPick capture.

## Still unbuilt: floor-price honesty

The collector measures whether *the item you selected* changes price through the
flow. It does not measure whether an advertised *"From $307"* is achievable — that
needs a flow that selects the cheapest listing and compares the advertised floor to
the cheapest all-in total.

That is a distinct and legally live measurement: a headline floor that no buyer can
actually obtain is the same deception in a different shape. Here, "From $307+"
against a cheapest listing of $311 looks close enough to be honest. On a site that
does charge fees it would not be.
