# Modern run — Korea 1950–51: the discrimination test in motion

The single best *dynamic* demonstration of the whole thesis. Every other case is a snapshot — the
market priced a crisis, or it didn't. Korea is the one where the **same war was repriced up and
down** as the probability of it going *general* rose and fell — twice up, twice back — so you can
watch the discrimination mechanism work in real time on a single instrument.

It is also the answer to an obvious challenge: *"you say the market ignores wars — but the Korean
War moved Wall Street hard."* Exactly — and **why** it moved is the point. Korea moved markets not
because it was a war (the Second Balkan War and the Falklands were wars the market ignored) but
because, at two moments, it looked like the opening of a **general US–Soviet war**. When it looked
limited, the premium vanished. The exception proves the rule.

## The evidence (S&P 500 daily, Yahoo ^GSPC)

| Moment | Move | What the market was pricing |
|--------|-----:|-----------------------------|
| **Invasion, 25–26 June 1950** | **−5.4% in one day**; **−12.9%** to the 17 July trough | Not Korea — the fear that this was **the opening move of WWIII** (a general US–USSR war). The sharpest break since 1946. |
| **Inchon, mid-Sept 1950** | back **above** the pre-invasion level | MacArthur's landing; the war looked **contained and winnable**. The general-war premium **evaporated**. |
| **China intervenes, late Nov 1950** | **−6.5%** (20.32 → 19.00) | China's massive entry routed UN forces; Truman's **30 Nov atomic-bomb remark** spooked markets and allies. **General-war fear returned** — and the market broke again. |
| **Limited war, Jan 1951 →** | **new highs** (21.3) | No atomic use; stalemate; MacArthur relieved (Apr 1951). As the war revealed itself as **limited**, the premium faded and the bull market resumed. |

Chart: `war_premia/results/korea_1950.svg` — the two drops at the two general-war-risk moments,
and the two recoveries as the war re-revealed itself as limited.

## Why this is the framework's keystone case

- **Discrimination, demonstrated dynamically.** The pre-1914 finding (the market prices
  *general*-war probability, not war-as-such) is here shown *moving*: the premium tracks the
  general-war probability up (June, November) and down (Inchon, 1951) on the *same* conflict. No
  cross-sectional comparison needed — the identification is within one war.
- **It reconciles the "wars the market ignored" with the "war that moved Wall Street."** Second
  Balkan 1913, Falklands 1982 → ignored (localized). Korea 1950 → priced (looked general). The
  divider is not size or bloodshed but **the probability of going systemic** — and Korea sits on
  both sides of that line at different dates.
- **The atomic dimension, but not un-priceable.** Unlike Cuba '62, Korea's general-war fear was of
  a *survivable* great-power war (the US had a large nuclear lead; the USSR had tested only in Aug
  1949). So the market *could* and *did* price it — a −13% and a −6.5% break — rather than hitting
  the un-priceability ceiling. Korea is the **priceable** end of the general-war rung; Cuba is the
  un-priceable top.

## Reading it correctly

- **The 1950 backdrop.** The market had been rising strongly into June 1950 (postwar bull); the
  invasion interrupted a rally. The recoveries are partly that underlying strength reasserting —
  but the *timing* of both breaks (day-of-invasion; week-of-China-entry) and both recoveries
  (Inchon; post-MacArthur) pins them to the general-war news, not to a coincident cycle. The
  cause-vs-cover check passes on the dates.
- **Effect, not a claim about policy.** This is a *pricing* result (what the market discounted),
  not a Kirshner-style influence claim. No one argues Wall Street steered Truman; the tape simply
  reveals how the war's *systemic* probability was assessed, day by day.

## Where it sits in the book

Korea belongs near the **center** of the argument, not in an appendix of data points: it is the
cleanest single-instrument proof that the market discriminates by **general-war probability**,
because it shows the discrimination *happening* — the premium switched on, off, on, and off again
in step with the WWIII risk, on one continuous price series.

## Reproduce

```bash
curl -sS -A "Mozilla/5.0" \
  "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?period1=-631500000&period2=-583000000&interval=1d"
# parse timestamp + indicators.quote[0].close; invasion 25 Jun 1950, China intervenes ~26 Nov 1950.
```

*Caveat: ^GSPC daily index levels; verify the crisis-window values against a second source before
publication. The event datings (Inchon 15 Sep 1950; Chinese intervention 26–28 Nov 1950; MacArthur
relieved 11 Apr 1951) are standard but should be cited.*
