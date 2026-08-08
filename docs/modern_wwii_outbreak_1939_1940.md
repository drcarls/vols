# Modern run — the US market and the outbreak of WWII, 1939–40: boom, then crash

*Answering the direct question: how did the US market react to the 1939–40 news from Europe, and
did it price the catastrophe in advance? Short answer: it rose on the outbreak of the war and was
blindsided by the fall of France — the anticipation failure in its purest form, and a textbook
discrimination result.*

## What happened (S&P 500 daily, Yahoo ^GSPC)

| Moment | Move | Reading |
|--------|-----:|---------|
| **Germany invades Poland, 1 Sept 1939** | **+21%** to the mid-Sept peak (10.89 → 13.17) | The **"war boom."** The US market *rose* on the outbreak of the largest war in history — war orders for neutral American industry. It priced the war it could **profit from**, not war-as-catastrophe. |
| **The Phoney War, Oct 1939 – Apr 1940** | drifted (~12.5) | Eight quiet months. The market did **not** price the possibility that France might fall. |
| **Blitzkrieg west, 10–21 May 1940** | **−22% in eleven days** (11.76 → 9.14) | The fall of France repriced the market violently — Germany dominant, the US position endangered, entry looming. The **speed shocked it**: a surprise, not a priced-in event. |
| **France falls / armistice, June 1940** | **−29%** from April | One of the sharpest US crashes ever — the war had changed character from distant boom to systemic danger. |

Chart: `war_premia/results/wwii_outbreak_1939_1940.svg`.

## Did it price it in before? No — twice over.

1. **It priced the wrong sign in 1939.** With eight months' warning that a European war was coming,
   the market's frame at the actual outbreak was *boom*, not catastrophe. It **rallied** on the
   invasion of Poland. A market pricing the coming disaster does not rise 21% into it.
2. **The 1940 crash was unanticipated.** The Phoney War lulled it; the market had every chance,
   from September 1939 to May 1940, to discount the risk that France might collapse, and it **did
   not**. It took the actual blitzkrieg to force the repricing — and a −22% move in eleven trading
   days is the signature of a surprise being absorbed, not a risk that was already in the price.

## Why this is a keystone for the anticipation-vs-resolution split

This is the clearest single case that **markets are poor at anticipating a political-military
decision and fast at pricing its consequences once taken.**

- **Discrimination, again.** The market did not price "war = bad." It distinguished the **distant,
  profitable** war (1939, neutral America as arms supplier) from the **systemic** war (1940, the
  European balance collapsing and the US endangered). *Same war, repriced as its character changed*
  — the WWII twin of Korea repricing on general-war probability.
- **Anticipation failed both times** — wrong sign in '39, blindsided in '40 — because the outcome
  hung on contingent decisions (would France hold? would Hitler strike west, and how fast?) that
  the market could not handicap.
- **Resolution worked.** Once the blitzkrieg's reality was undeniable, the market repriced the new
  strategic world **quickly and correctly** — the −29% was the market getting the answer *right*,
  fast, at the moment the decision resolved.

It also sets up Pearl Harbor: by December 1941 the market had **learned** from 1940 that this war
could reach America — which is why 1941 shows a −10% autumn drift (war being priced in aggregate)
before the attack, where 1939 showed a boom. The frame shifted from "distant profit" to "our war"
between the fall of France and Pearl Harbor.

## Reproduce

```bash
python3 -c "import datetime as d;print(int(d.datetime(1939,6,1).timestamp()),int(d.datetime(1940,8,1).timestamp()))"
curl -sS -A "Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?period1=<P1>&period2=<P2>&interval=1d"
# Poland invaded 1 Sept 1939; blitzkrieg west 10 May 1940; France falls mid-June 1940.
```

*Caveat: ^GSPC daily index levels; verify against a second source, and cite the contemporaneous
market commentary (NYT/WSJ, Sept 1939 & May 1940) for the "war boom" and the fall-of-France crash.*
