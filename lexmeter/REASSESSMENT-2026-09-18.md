# Reassessment: the Tier A thesis is probably wrong

**2026-09-18.** Two platforms scouted by hand. Both clean. The Etix venue survey
found all-in pricing on every venue checked.

## What I predicted, and why it was wrong

I ranked the platform long tail as the highest-yield ground in ticketing. The
reasoning was that independent theatres, fairs and clubs have little compliance
resource, so they would be slower to adopt all-in pricing than the majors.

That reasoning contains an inversion. **The venues do not control the display —
the platform does.** And for a platform, compliance is a one-time engineering
change amortised across every venue on it. Platform economics make compliance
*cheaper* per venue than for a standalone business, not more expensive. So the
long tail *served by a platform* should be expected to be **more** compliant than
the same businesses running their own checkout, not less.

The federal rule has been in force since 2025-05-12 — sixteen months. That is
ample time for a dozen platforms to each make one change that covers hundreds of
venues each.

This generalises, which is what makes it worth writing down rather than just
correcting the Etix row:

- It predicts the **remaining twelve Tier A platforms are also compliant.** They
  are the same kind of business under the same rule with the same economics.
- It predicts the violations left in ticketing sit where **no platform made the
  change for you**: venue-direct box offices on bespoke software, which are small,
  hard to enumerate, and individually not worth suing.
- It predicts that a federal rule plus a concentrated platform layer is close to
  a solved problem, and that the remaining density is in sectors with **neither**.

## What this costs

Ticketing was chosen as the first industry because the flows are easy and the
filed cases are public — good conditions for *building the machine*. That purpose
is served: the collector has now been checked against two live sites and both
checks found real bugs in it. The reason to stay in ticketing has been spent.

## One angle that survives

Etix's banner promises all-in on *"ticket fees and taxes"*. That does not cover
delivery. A venue charging an electronic or will-call delivery fee would show it
**only at checkout** — a mandatory fee first appearing at the final step, sitting
on top of an all-in ticket price. Zanies showed that line at $0.00; a venue
showing it at $4.95 is a live claim.

Electronic delivery fees are, in general, the fee category most likely to survive
an all-in regime, because they are treated as shipping — and they are also the
least defensible as actual shipping, since nothing ships. The taxonomy already
separates them: `shipping` is statutorily excluded from the gap, `delivery` is not.

This is a cheap screen — one checkout page per venue, looking for a non-zero
delivery line — but it is a narrow claim and it does not justify the remaining
twelve platforms on its own.

## Recommendation: move to reservation platforms

The strongest case in the whole legal map is not in ticketing. *Chowning v. Tyler
Technologies* is live, is pleaded at **$398M over the contract life**, and concerns
a single mandatory reservation fee on a public-sector booking site. That sector has:

- **No federal rule.** The FTC fee rule reaches live-event tickets and short-term
  lodging only. Nothing forced a platform-wide change here.
- **No concentrated platform layer that has already fixed it.** The two conditions
  that appear to have solved ticketing are both absent.
- **The exact fee pattern the collector detects best** — one mandatory fee, named,
  appearing late, on an otherwise clean price.
- **A vendor-level replication argument that is stronger than ticketing's**, because
  public-sector contracts are enumerable from procurement records. One matched
  pattern maps directly to a list of states and agencies.

Concretely: state park and campsite reservation systems, municipal facility and
permit booking, and the vendors that operate them under contract.

Lodging (industry 2) is the weaker alternative — the federal rule covers it, so the
same compliance dynamic that appears to have cleaned ticketing applies, except for
vacation rentals and property managers, which are not platform-concentrated.

## The sample: a few Etix venues

That is enough to retire Etix. It is **not** enough to retire the other twelve,
and the reason is worth being precise about, because it is easy to mistake this
sample for stronger evidence than it is.

**Venues on one platform are not independent observations.** They all inherit a
single engineering decision made once by the platform. Checking five Etix venues
and finding all-in pricing five times is close to checking it once — the second
through fifth venues could hardly have come out differently. For the question
"are ticketing platforms compliant", this sample is effectively **n = 1**.

The relevant n is the number of **platforms**, not venues. Which means the two
claims above have to be kept apart:

- **Empirical:** a few venues on one platform. Supports retiring Etix. Nothing more.
- **Structural:** platform compliance is one change amortised across hundreds of
  venues, under a rule in force sixteen months. This does not depend on the sample
  at all — it is an argument, not evidence, and it is the stronger of the two. But
  an untested argument is what produced the original wrong ranking.

## The cheap test

Do not scout more Etix venues; they cannot tell you anything new. Check **one venue
each on two or three different platforms**. That tests the actual hypothesis, and
it is about fifteen minutes.

Suggested, in order of how informative a negative result would be:

1. **Eventbrite** — the case most likely to break the pattern, because fees are
   configured per event by the organiser rather than set once by the platform. If
   even Eventbrite displays all-in, the structural argument is strong.
2. **ShowClix** — a different platform of similar scale to Etix. Independent
   confirmation.
3. **Tixr** — white-label by design, so the display may genuinely be venue-configured.

All three all-in → retire the remaining Tier A platforms on inference and move to
reservation platforms. Any one of them not → the structural argument is wrong,
Tier A is back, and that platform is the target.
