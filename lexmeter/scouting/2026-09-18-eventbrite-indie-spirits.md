# Scouting note — Eventbrite / Chicago Indie Spirits Expo

**2026-09-18 · manual observation · NOT an evidence-grade capture**

## Full flow, step 0 onward

| Step | What was shown |
|---|---|
| Search results (`/d/il--chicago/all-events/`) | **From $215.26** |
| Event page | **$215.26** · Get tickets |
| Ticket modal | **$215.26** *incl. $15.26 Fee* |
| Order summary | 1 × $200.00 · Subtotal $200.00 · Fees ⓘ $15.26 · **Total $215.26** |

**All-in from the initial display.** The $215.26 a buyer sees in search results is
the amount they pay. Gap $0.00, and the fee is both quantified and broken out.

Fee is $15.26 on a $200 base — an effective **7.63%**, buyer-paid. This is the
buyer-pays configuration, so the case that *could* have shown a bare $200 headline
and revealed the fee only at checkout. It does not.

Having step 0 is what makes this conclusive. The FTC rule governs the **initial**
display, so a checkout screenshot alone could never have settled it — a natural
scouting habit is to capture where the money is, but the claim lives at the
beginning of the flow. This is the reason the collector is step-indexed.

## Three platforms, three compliant

Etix (several venues), TickPick, Eventbrite. Eventbrite was picked precisely
because its per-event organiser-configured fees made it the likeliest to break the
pattern, and it did not.

These are three independent engineering decisions at three companies, which is a
far better test than more venues on one platform. The structural argument now has
real support: a platform layer under a federal rule for sixteen months appears to
have converged on all-in display.

It still is not proof about the nine unscouted Tier A platforms. It is enough to
stop scouting them one at a time and act on the conclusion.

## What it changed in the collector

Reconciliation assumed fees are always *added* to the headline. On an all-in
display they are already inside it, so this flow reported a correct reading as
double-counting.

Fixed by testing both readings and recording **which one closes** — that is not a
hedge, it is the measurement: a headline already containing the mandatory fees is
an all-in display, and one the fees are added to is not.

    Eventbrite  $215.26 / fee $15.26 / total $215.26   ok   inclusive
    drip fixture $89.00 / fees $31.51 / total $120.51   ok   exclusive
    TickPick    $1008 x2 / fees $0    / total $2016     ok   indeterminate

`indeterminate` is honest: when fees sum to nothing, both readings close and there
is nothing to tell apart.

### An honest limit

The arithmetic **cannot** distinguish a genuine all-in display from a headline
selector that mistakenly grabbed the total — headline equals total with fee lines
shown, either way. No sum separates them.

That case is caught by cross-step consistency instead: a grabbed total reads
differently at steps where no total is displayed, while a real headline holds
steady. `Verification.headline_inconsistency` reports it and blocks a spec from
being marked verified. A headline that genuinely moves through the funnel is also
worth surfacing — that is a worse practice than a late fee, not a bug.

## Also present, not pursued

- **"89 people have their eye on this"** — an urgency claim. A third claim family
  after fees and reference prices. Out of scope; noted so it is not rediscovered.
- **"Fees ⓘ"** carries an info tooltip. Worth capturing as `purpose_text`: whether
  a fee's purpose is explained is a live test under SB 1524 for food sellers and
  useful context everywhere else.
- Search results show **"From $0.00"** and **"From $5.45"** on other events, so the
  floor-price pattern is present on Eventbrite too. Here "From $215.26" equals the
  real all-in price because the event has a single ticket type.
