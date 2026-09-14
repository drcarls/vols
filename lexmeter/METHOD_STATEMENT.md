# Method Statement — Lexmeter US drip & junk fee collection

This is the document a custodian certifies. Under FRE 902(13)/(14), machine-generated
records are self-authenticating only on a certification by a qualified person, so
everything here is written to be testified to rather than merely to be true.

**Status: not yet certifiable.** Three prerequisites are outstanding and are listed
in §7. Captures made before they are met are sound as to integrity within Lexmeter's
own custody, but are not self-authenticating.

---

## 1. What is collected

Scripted browser sessions through publicly reachable purchase flows, recording at
each step what a buyer would see: the price displayed most prominently, any total
the page displays, and every fee line item with its label, amount, and whether it
could be removed.

Per step: UTC timestamp, URL, vantage state, device type, viewport screenshot with
its scroll position, DOM snapshot, and the SHA-256 digest of each. Per flow: an HTTP
archive (HAR) including response bodies, and a video recording of the session.

## 2. What is never done

Enforced in code (`politeness.py`, `config/collection_policy.yaml`), not by operator
discipline:

- No purchase is ever completed. Flows terminate at the final review step, and a flow
  that does not declare a review step as its last step is refused at construction.
- No account is created and no login is performed.
- No CAPTCHA is solved and no access control, paywall, or login wall is bypassed.
- No user agent is spoofed to disguise automation.
- No retry after an explicit block.
- Never more than one concurrent session per host.

## 3. robots.txt

**Declared position:** robots.txt is a convention addressed to crawlers and does not
govern a single, user-paced scripted session that visits a small number of pages.

This is a position, not settled law, and it is recorded as such. It is stated here so
that it can be examined rather than discovered.

The position is only defensible while the observable behaviour matches it, so the
behaviour is constrained in code: one session per host, jittered delays of 2.5–7.0
seconds between actions, a cap of twelve steps per flow, honest identification
appended to the real user agent, and a hard abort on any block signal. A defendant
examining their own access logs should see a session indistinguishable in shape from
a slow human, because that is what it is.

Discovery and inventory crawling — as distinct from the scripted flow — follows
robots.txt without exception.

## 4. Blocks

A block is a fact about the site, not a missing reading. On any of HTTP 401, 403, 407,
429 or 503, or a body marker indicating bot interdiction, the flow aborts immediately.
The partial observation is stored with its block reason and the steps observed before
it. The flow is not retried within the same sweep.

## 5. Integrity

Each artifact is stored content-addressed by the SHA-256 digest of its bytes; identical
bytes are one artifact. Each observation is serialised canonically — sorted keys, fixed
separators — so that an identical record always produces an identical digest.

Observations are append-only, enforced by database triggers that abort UPDATE and
DELETE rather than by convention. On the production store the equivalent is revoking
those grants from the collector role. Artifact storage uses versioning with object lock
in compliance mode.

Each day's new observation digests are combined into a Merkle root, with domain
separation between leaf and interior nodes. The root depends on the set of captures,
not the order they were read out of storage, so adding, removing or altering any
capture changes it.

**A digest we compute and store proves integrity only relative to our own custody.**
The external anchor is what converts it into proof of time, and it is not yet in place
(§7).

## 6. Vantage points

Flows are captured from CA, MN, MA, CO, VA, NJ and NY, with NY as the control. CT and
OR are candidate additions, as both have cross-sector price transparency statutes.

Egress is through a named commercial ISP or datacenter provider that supplies a written
consent-provenance attestation. Residential consumer proxy pools are excluded: consent
provenance that cannot be put in front of a court makes the collection method the story.

For food delivery and restaurant flows the control variable is the delivery address
entered, not the egress IP, because those platforms geolocate on address.

## 7. Outstanding prerequisites

Tracked in `config/collection_policy.yaml`, all three currently null:

1. **Egress vendor not named.** `egress.provider`. The provider class is constrained and
   residential pools are refused in code, but no vendor is selected and no attestation
   is on file.
2. **No RFC 3161 timestamp authority.** `evidence.timestamp_authority`. Until one is
   configured the hash chain is unanchored, and the code raises rather than silently
   producing an anchor that would fail at the point of use.
3. **No named custodian.** `evidence.custodian`. Without a qualified person to certify
   the process, FRE 902(13)/(14) self-authentication is unavailable and a live witness
   would be required instead.

Each capture carries a `ProvenanceRecord` written at capture time, so these gaps are
visible on every record rather than discovered when a declaration is due.

## 8. Scope of inference

The collector records what a site displayed. It does not conclude that a law was broken.
Flags describe observations; `rules.py` resolves which rule an observation engages, in
which state, on which date, and refuses to assert a rule that was not yet effective on
the observation date or whose own verification is incomplete.
