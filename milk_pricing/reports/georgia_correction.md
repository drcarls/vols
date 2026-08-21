# Georgia: not untestable — and it confirms the memo's structural point

I said GA was untestable. That was imprecise. Only the **same-region variant** fails, and it fails for a reason that is itself a finding. Cross-region and unmatched, Georgia is the largest control state in the set.

## Why the same-region test fails

Georgia's rural ZIPs sit on non-overlapping federal floors by race:

| | Class I differential ($/cwt) |
|---|---|
| Black rural (39 ZIPs) | 5.6 ×2, **5.8 ×22, 6.0 ×15** |
| White rural (18 ZIPs) | **5.4 ×3, 5.6 ×15** |
| Overlap | **only 5.6** |

**Only 2 of 39 Black rural ZIPs have any white rural ZIP within ±0.2/cwt.** The same-region design needs same-floor pairs and Georgia has almost none, so it produced 2 pairs and I dropped it.

This is precisely the memo's own claim, now with numbers behind it: *"in much of the Deep South (Georgia, Mississippi) majority-Black rural areas have no majority-white rural area at the same federal floor … the Black Belt is its own contiguous high-cost region."* In Georgia the Black rural population sits at 5.8–6.0/cwt and the white rural population at 5.4–5.6. They are on different rungs of the federal surface, with essentially no overlap. That is a result worth stating in the memo directly rather than as a caveat.

## Georgia cross-region and unmatched — a clean null

| Test | pairs | Walmart gap | Aldi gap | DiD | |
|---|---:|---:|---:|---:|---|
| Cross-region | **39** | −$0.019 (t=−0.22) | +$0.213 (t=+2.12) | −$0.233 | p=0.78 |
| Same-region | 2 | — | — | — | not testable |
| **Unmatched** | 39 v 18 | — | — | **−$0.004** | **t=−0.02** |

The unmatched figure is as clean as a null gets: the Walmart-minus-Aldi spread is **+$0.272 in Black rural ZIPs and +$0.276 in white rural ZIPs**. Four tenths of a cent apart.

Note also that in Georgia it is **Aldi** that charges more in Black rural ZIPs (+$0.213, t=2.12) while Walmart is flat (−$0.019). Whatever is happening in Georgia, it is not a Walmart penalty.

## What this does to the control picture

With Georgia restored, all four control states are null on the unmatched DiD:

| State | Unmatched DiD | |
|---|---:|---|
| TN | +$0.322 | control (only 6 Black ZIPs) |
| **GA** | **−$0.004** | control — 39 pairs, the largest |
| NC | −$0.026 | control |
| AL | −$0.033 | control |
| SC | +$0.162 | test |
| LA | +$0.020 | test |
| MS | +$0.667 | test |

Georgia is the strongest single null in the set — more pairs than any test state, and a DiD indistinguishable from zero. It does not weaken the SC/LA/MS finding, but it does firmly bound it: the effect is not a Deep South pattern, because Georgia is Deep South and shows nothing.

It also sharpens what remains. Unmatched, only **MS (+$0.667)** and **SC (+$0.162)** show a positive DiD at all; Louisiana's is +$0.020, essentially nil. The matched design is doing most of the work in LA.

## Correction to the record

"GA untestable" should read: **the same-region variant is not estimable in Georgia because Black and white rural ZIPs occupy disjoint federal floors — which is itself evidence for the memo's Black Belt argument — and Georgia is otherwise fully testable and returns a clean null.**
