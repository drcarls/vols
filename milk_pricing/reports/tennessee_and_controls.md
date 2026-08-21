# Tennessee and the control states — a correction

Tennessee was the right thing to ask for. It is a clean null, which is good news for the method. But running it alongside NC, AL and GA surfaced a problem with what I told you last turn, and the correction matters more than the Tennessee result itself.

## The seven-state picture (matched design)

| State | pairs | Walmart gap | Aldi gap | DiD | 1-sided p | |
|---|---:|---:|---:|---:|---:|---|
| SC | 16 | +$0.421 | −$0.025 | +$0.446 | 0.050 | test |
| LA | 12 | +$0.276 | −$0.407 | +$0.682 | 0.044 | test |
| MS | 8 | +$0.855 | −$0.232 | +$1.087 | 0.138 | test |
| **TN** | 6 | +$0.022 | +$0.078 | **−$0.057** | **0.571** | **control — clean null** |
| NC | 26 | −$0.327 | −$0.582 | **+$0.255** | **0.017** | control — **fires** |
| AL | 24 | +$0.044 | −$0.261 | +$0.305 | 0.121 | control |

**Tennessee behaves.** DiD −$0.057, p=0.571. The method does not fire indiscriminately, which was the point of running it.

**North Carolina does not.** It returns a significant positive DiD (p=0.017) even though Walmart is *cheaper* in Black rural NC (−$0.327). The DiD is positive only because Aldi is cheaper still (−$0.582). A Black shopper in rural NC pays **less** at Walmart than a white one — and the statistic still reads as a Walmart penalty. That is the DiD measuring the wrong thing.

Checked without matching, NC's DiD is **−$0.026** — essentially zero. The matched design manufactured the NC result.

## The correction: the pooled claim does not survive proper inference

Last turn I gave you a pooled unmatched DiD of +$0.468 at p=0.026 and called it design-free and robust. It was design-free. It was not correctly inferred.

That test treated all rural ZIPs as independent. They cluster by state, and Black rural ZIPs are concentrated in expensive states (MS, LA) while white rural ZIPs sit in cheaper ones (TN, NC). Permuting **within state**, which holds that composition fixed, across all seven states and 364 ZIPs:

| Measure | Black rural | White rural | Gap | Naive t | **Within-state p** |
|---|---:|---:|---:|---:|---:|
| Walmart price | $3.915 | $3.664 | +$0.251 | 3.60 | **0.173** |
| **Aldi price** | $3.166 | $3.153 | **+$0.014** | 0.23 | **0.535** |
| DiD | $0.749 | $0.511 | +$0.238 | 2.84 | **0.211** |

Neither the Walmart gap nor the DiD is significant once state clustering is handled. The naive t-statistics of 3.60 and 2.84 were inflated by exactly the between-state structure the memo itself documents for the federal differential — it reports ~92% of that gap as between-state.

## What still stands

1. **Aldi is a clean null everywhere.** +$0.014 pooled (p=0.535), and no single state shows a significant Aldi gap. As a control retailer it does its job, and it is worth keeping in the memo for that reason alone.
2. **Tennessee is a genuine negative control.** The method can return null.
3. **SC, LA and MS do show a Walmart premium** on the matched design, and the three-state pooled DiD was p=0.0073. That result is real *for those states*.

## What does not stand

1. **The pooled seven-state claim.** Not significant under within-state inference (p=0.211).
2. **My "robust to abandoning the matching" claim from last turn.** The unmatched estimate was correct as an estimate and wrong as an inference.
3. **NC as supporting evidence.** Its matched DiD is an artifact; unmatched it is zero.

## The honest statement now

The three states were selected *because* Walmart's gap was positive there. Adding four states chosen without reference to the outcome, the effect does not generalise: TN null, NC artifactual, AL insignificant, GA untestable.

So this is a **state-specific finding in SC, LA and MS**, with a valid null control retailer, and no demonstrated national or regional pattern. That is narrower than last turn's framing and it is what the data supports. For an attorney-ready memo the narrower claim is also the safer one — it is exactly what survives an opposing expert adding the states you did not pick.
