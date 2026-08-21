# National file: what it does and does not support

4,140 usable Walmart store-ZIPs, 51 states, with demographics, rural/urban and the Class I differential. This is the dataset that can settle the questions the 92-store SC file could not.

## 1. There is no national Walmart race premium — the sign is negative

| Model | % Black coef | t |
|---|---:|---:|
| race alone | -0.0026 | -3.89 |
| + income | -0.0043 | -6.35 |
| + urbanicity | -0.0020 | -3.00 |
| + population | -0.0015 | -2.23 |
| **+ state fixed effects** | **-0.0017** | **-3.45** |

Nationally, a higher Black share predicts a **lower** Walmart milk price, and it stays negative and significant through every control including state fixed effects. This is consistent with the memo's own disclosure that the pattern is not a blanket "minorities pay more." Any framing that generalises SC beyond the specific states is contradicted by this file.

## 2. State-by-state, the matched design splits both ways

| State | Cross-region gap | t | Unmatched group difference | Welch t |
|---|---:|---:|---:|---:|
| MS | **+$0.928** | 6.06 | +$0.371 | 0.87 |
| SC | +$0.356 | 3.63 | +$0.278 | 1.39 |
| LA | +$0.276 | 7.23 | +$0.106 | 1.07 |
| AR | +$0.180 | 1.86 | **+$0.426** | **4.66** |
| GA | -$0.049 | -0.58 | +$0.226 | 1.53 |
| TX | -$0.195 | -1.00 | -$0.019 | -0.12 |
| AL | -$0.330 | -2.12 | -$0.060 | -0.42 |
| NC | **-$0.466** | -4.73 | -$0.215 | -1.65 |

Three states significantly positive (MS, SC, LA), two significantly negative (NC, AL), median state gap **$0.000**.

**Mississippi contradicts the memo.** It reports MS at −$0.31 (t=−4.6), a reversal. In this file MS is the *largest positive* gap in the country at **+$0.928 (t=6.06)**, and it strengthens with a sharper threshold (+$1.20 at ≥50% Black). Either the vintages differ or a threshold definition does, but the discrepancy needs resolving before filing — it is the difference between MS being a disclosed null and being the strongest case in the dataset.

Note also that in every state the matched gap is far larger in |t| than the plain unmatched group difference, and in Arkansas the two **disagree in sign significance**: matched +$0.18 (n.s.) against unmatched +$0.43 (t=4.66).

## 3. The design's t-statistics are badly miscalibrated

Permutation placebo: hold the state fixed, randomly relabel which rural ZIPs are "Black" and "white" keeping group sizes, re-run the identical matching, 400 times. A sound design yields |t| > 2 about 5% of the time.

| State | Nominal real t | Placebo rate of \|t\|>2 | Permutation p |
|---|---:|---:|---:|
| SC | +3.63 | **24%** | **0.04** |
| LA | +7.23 | **40%** | <0.01 |
| MS | +6.06 | **45%** | 0.02 |
| NC | -4.73 | 11% | <0.01 |
| AR | +1.86 | 7% | 0.10 |

In the small-pool states the design produces a nominally significant result on **random labels 24–45% of the time**. The reported t-statistics overstate significance by roughly five- to nine-fold in error-rate terms.

**The findings survive, but weaker.** Against its own placebo distribution South Carolina's gap is exceeded by only 4% of shuffles — a permutation p of about **0.04**. That is real, and it is a very different claim from t = 3.6 (nominal p < 0.001). LA and MS also survive; AR does not.

## 4. Comparator pool size predicts the result

`corr(log comparator-pool size, matched gap) = **-0.735**` across 11 states:

| State | White rural pool | Matched gap |
|---|---:|---:|
| MS | 4 | +$0.928 |
| LA | 6 | +$0.276 |
| SC | 10 | +$0.356 |
| GA | 19 | -$0.049 |
| AL | 29 | -$0.330 |
| AR | 43 | +$0.180 |
| NC | 48 | -$0.466 |
| TX | 140 | -$0.195 |

The three significant positives are the three smallest pools. This is confounded — small pools occur in the Deep South, which is where the memo argues the effect lives, and the memo already makes the structural point that the Black Belt has no white rural comparator at the same federal floor. So it is not proof of artifact. But it is the first thing a competent opposing expert will plot, and the memo should address it directly.

## 5. What I would change in the memo

1. **Report permutation p-values, not nominal t.** SC becomes p≈0.04 rather than t=3.6. Still a finding; a defensible one.
2. **Resolve Mississippi.** The sign is opposite here and MS is the largest effect in the file.
3. **Show the unmatched group difference alongside every matched gap.** Where they diverge (SC 3.63 vs 1.39; AR reverses) the reader should see it first from you.
4. **Add the pool-size plot and explain it** as Black Belt structure rather than leaving it to be found.
5. **Keep the national negative coefficient in the memo.** It is the strongest evidence that this is not a general Walmart practice — which narrows the claim but makes the surviving state findings much harder to dismiss as fishing.

None of this touches Finding A (the federal differential), which I have not examined.
