# Phase 1 — live-event ticketing: status

**Date:** 2026-09-14 · **Live captures run: 0**

## What is done

- **Target list built** — `config/targets/ticketing.yaml`, 20 targets.
- **Sweep orchestration** — tier-ordered weekly sweep from the control vantage,
  plus the sampled multi-vantage differential probe.
- **Reporting** — per-company report, league table, pattern-match screen.
- **robots.txt audit tool** — runnable, and correct on unreachable hosts.
- **Preflight guard** — the sweep refuses to run while captures would not be
  certifiable.
- 122 tests, all passing, entirely offline.

## Why no captures yet: two independent blockers

**1. This container cannot reach the targets.** The environment's network policy
denies the CONNECT for all 20 domains (`403 Forbidden` at the gateway). The audit
recorded 0/20 reachable. This is a property of the build environment, not of the
targets, and it is not something to work around: **Phase 1 runs in the collection
environment, not here.**

**2. Captures made now would not be certifiable.** `preflight` reports three open
items, unchanged from the Phase 0 hand-off:

    egress.attestation_on_file   false     vendor named, documents not filed
    evidence.timestamp_authority not set   hash chain unanchored outside our custody
    evidence.custodian           not set   nobody to certify under FRE 902(13)/(14)

**Bright Data is now the egress vendor** and the hard part of that decision is
settled: the ISP tier is the default, the residential tier is a fallback requiring
a recorded reason, and the unblocking products are refused in code. What remains
is filing the supporting documents and verifying that ISP coverage actually
reaches MN, MA, CO and NJ at state level.

These three degrade evidentiary weight rather than correctness, but a weekly
series is worth most when its *first* point is sound, and the first sweep is the
baseline everything later is measured against.

`sweep` therefore refuses by default. `--uncertified` overrides it, deliberately
requiring someone to say so out loud.

## The target list, and the reasoning behind it

**The target unit is the platform, not the venue.** The long tail of American
ticketing does not run on bespoke software: independent theatres, fairs, clubs,
minor-league clubs and university box offices sit on a dozen or so platforms, and
the fee display belongs to the platform. One pattern replicates across every venue
on it — the same shape as *Chowning v. Tyler Technologies*: one vendor, one
mandatory fee, many deployments, one defendant worth suing.

Each platform target therefore carries several representative deployments.
Agreement across them is the finding. Divergence means the venue configures its
own fees and the claim is venue-level instead. Both are useful; neither is
knowable without capturing more than one.

**Tier A — 14 platforms, swept first.** Etix, ShowClix, Tixr, Eventbrite,
TicketWeb, Front Gate, Paciolan, Tickets.com, See Tickets US, Prekindle,
Purplepass, TicketSpice, SimpleTix, Universe.

Three of these are owned by existing defendants — TicketWeb and Front Gate by
Live Nation, Universe by Ticketmaster. A drip pattern on a subsidiary of a company
already facing the FTC and seven-state action is a materially stronger fact than
the same pattern on an unrelated operator.

Paciolan and Tickets.com serve through venue domains rather than their own, so
deployments must be enumerated venue by venue. Higher setup cost, widest
replication if a pattern holds, and the closest structural analogue to Tyler.

**Tier B — 6 majors, swept second, low expected yield.** Ticketmaster, StubHub,
SeatGeek, Vivid Seats, AXS, TickPick.

Reporting indicates all the majors moved to all-in display after the FTC rule took
effect on 2025-05-12, and that the display changed while the economics did not —
fees folded into the listed price rather than removed. **A zero gap at a Tier B
target is the expected reading, not a collector failure.** They are captured for
three reasons: a compliant baseline to measure Tier A against, the display-switching
probe, and because their fact patterns anchor the screen.

Two Tier B rows carry specific roles:

- **AXS** is the largest operator here with no filed US drip-pricing action against
  it. If a pattern appears there it is the highest-value single finding in Phase 1.
- **TickPick** is the **negative control**. It is built on an all-in, no-added-fee
  proposition predating the rule. If the collector flags TickPick, the collector is
  wrong — and `run_sweep` checks this itself, marking the whole sweep untrustworthy
  rather than publishing findings from a run whose own control failed.

**Ticketmaster is expected to fail.** Enterprise bot management, queue systems,
commercial interdiction. Per the method statement a block is recorded, not evaded —
and that rule is what protects the two-week date, because the alternative is
spending the fortnight losing to one target.

## Nothing here is a finding

`fee_display` is `unknown` on all 20 rows and `assert_uncaptured()` fails the build
if any row claims otherwise. Expected yield is a hypothesis about where to spend the
first fortnight, designed to be falsified: **if Tier A comes back clean, that is a
real result about the market**, and a more interesting one than the alternative.

## To start collecting

1. Name the egress vendor and get the provenance attestation on file.
2. Run `robots-audit` from the collection environment. It feeds the D4 posture
   decision with evidence instead of assumption, and the current audit read nothing.
3. Write `SelectorSpec`s per target. **This is the open work and the real Phase 1
   labour.** See below.
4. Pick a TSA and name a custodian, then `preflight` goes clean.
5. First sweep: Tier A only, control vantage, one deployment each.


---

## Selector specs: machinery built, 0/14 authored

Selectors cannot be written without seeing the page, and no Tier A site is
reachable from the build environment. Guessing them produces plausible CSS that
matches nothing, and the failure mode is silent — no match, no fee, apparent
compliance — so a guessed spec makes the blindest target look like the cleanest.
All 14 are therefore left null rather than filled with something that reads as
work. `selector-status` prints the gap and `sweep` refuses to run over it.

What is built instead is the machinery that makes authoring fast and checkable:

- **Per-step-kind selectors.** A listing page and a checkout page are different
  documents; one spec per site is the most common way these go wrong.
- **Required selectors raise.** A non-match is a capture error, never a zero.
- **Arithmetic reconciliation** — the useful part. `headline × quantity + every
  displayed fee` must equal the total the page itself shows. That needs no
  knowledge of the site, so it verifies a spec written by someone who has never
  seen its DOM, and it diagnoses directionally: a positive discrepancy means a fee
  line is being missed, a negative one means a double-count or a headline selector
  that is matching a total. Quantity is part of it because a per-ticket headline
  against a multi-ticket total makes a correct spec look broken.
- **Verification gating.** A spec may only be marked `verified` once at least one
  step produced a check that actually closed. A spec whose every step returns
  "not checkable" has proven nothing, and marking it verified is how an unverified
  spec reaches a live sweep.
- **Authoring against saved pages**, not the live site: `save-page` stores one
  rendered page, `verify-selectors` checks the spec against it in the same browser
  with no network. Repeatedly re-running a live flow to tune a selector is the
  traffic pattern the declared posture disclaims.

### Authoring procedure, roughly 30–60 minutes per target

1. Walk the flow by hand from the collection environment. Stop at review. No purchase.
2. `save-page` each step.
3. Fill the `steps:` block in `config/selectors/ticketing.yaml`.
4. `verify-selectors --target <id> --pages <dir>` until the arithmetic closes.
5. Set `status: verified`.

`config/selectors/ticketing.yaml` carries one filled-in worked example against the
local fixture — machinery proof and template, not a ticketing company.

Two targets need care: **Eventbrite** sets buyer-pays vs organiser-pays per event,
so author against one of each or the spec looks broken on whichever case it was not
written for. **Paciolan** and **Tickets.com** serve through venue domains, so author
against a named venue and record which — whether one spec covers several venues is
itself the finding about how uniform the platform is.
