# Scouting note — Etix / Zanies Chicago

**2026-09-18 · manual observation · NOT an evidence-grade capture**

Source: operator screenshots of a hand-walked flow. No DOM, no hashes, no
controlled vantage, no provenance record. This note exists to steer the build;
it must never be cited as a finding, and it is deliberately filed outside the
capture store so it cannot be mistaken for one.

## What was observed

Event: Kevin Bozeman, Zanies Chicago, Sep 19 2026, General Admission.

| Step | URL | Headline | Total |
|---|---|---|---|
| Listing | `etix.com/ticket/e/1054347/...` | $37.95 | — |
| Detail | `etix.com/ticket/p/36110276/...` | $37.95 | — |
| Cart | `.../legacyOnlineSale/performance/sale/viewShoppingCart` | $37.95 | $37.95 subtotal |
| Checkout | `.../legacyOnlineSale/performance/sale/displayPrice` | $37.95 | **$37.95** |

Gap: **$0.00**. One fee line appears, `Will Call Delivery Fee: $0.00`.

Two disclosures, both explicit:
- Detail step: *"This venue uses All-In Pricing. The total price listed includes
  ticket fees and taxes."*
- Checkout: *"This 'all-in price' includes all fees and taxes."*

No flag would fire. This flow is compliant, and visibly so.

## The finding that matters: "**This venue** uses All-In Pricing"

That wording is the important observation, not the null result.

It reads as a **per-venue setting**, which would mean all-in display on Etix is
configured by the venue rather than imposed by the platform. If so, the Phase 1
thesis needs adjusting:

- The platform-level claim (one pattern replicating across every venue on the
  platform, per *Chowning v. Tyler Technologies*) **weakens for Etix**. The
  display is the venue's choice, so the defendant is the venue, not Etix.
- But a better-shaped question replaces it: **what proportion of Etix venues have
  the toggle off?** That is a survey, it is cheap to run because a single page per
  venue answers it, and the output — a compliance league table across hundreds of
  venues on one platform — is a genuinely sellable product that the original
  design did not anticipate.
- Etix's own exposure would then turn on whether it defaults the setting off, or
  markets the ability to hide fees. That is a documents question, not a
  collection question.

**Unverified.** Inferred from six words of UI copy on one venue. Confirm by
checking whether any Etix venue shows a different pattern (see protocol below).

## Reusable structure

The cart and checkout steps sit on shared Etix paths
(`/ticket/mvc/legacyOnlineSale/performance/sale/...`), not venue-specific ones,
which supports one selector spec covering many Etix venues even where the fee
*display* differs.

Note `legacyOnlineSale`. That names a legacy checkout, which implies a newer one
exists and that some venues are on it. **Expect to need two spec variants**, and
record which variant each capture ran through.

## Revised next step: scout before authoring

Writing selectors against a venue with nothing to find is wasted effort. Cheaper
sequence:

1. Open 8–10 Etix venues, **detail page only**, one page each.
2. Record whether the all-in banner is present.
3. If every one shows it, Etix is compliant and Phase 1 should move on — that is
   a real result about the market, reached for an hour's work rather than a week's.
4. If some do not, author the spec against one of those, and the survey becomes
   the product.

Suggested spread, to avoid sampling one venue type: comedy clubs, independent
music venues, performing arts centres, county fairs, festivals, museums and
attractions. Fee practice plausibly varies more by venue type than by geography.
