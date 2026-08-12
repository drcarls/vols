from __future__ import annotations

"""Passive homepage check for AI adoption signals.

Fetches the company's public homepage over HTTPS and looks for two concrete,
screenshot-ready signals:

  * public AI usage -- the site itself advertises AI features ("AI assistant",
    "powered by AI", "GPT", "our AI", ...).
  * a customer-facing chatbot -- an embedded widget (Intercom, Drift,
    Zendesk, a generic "chat with us", or an inline LLM call).

Everything read here is public. The pure grader ``evaluate_html`` is
unit-testable without the network; ``fetch_homepage`` degrades to an
"unknown" (empty) reading if the site can't be reached, so the rest of the
pipeline still runs. Tests use fixed HTML, not the network.
"""

from dataclasses import dataclass
from urllib.request import Request, urlopen

AI_KEYWORDS = (
    "ai assistant", "ai-powered", "powered by ai", "our ai", "genai",
    "generative ai", "gpt", "copilot", "large language model", "llm",
    "machine learning", "chatgpt", "claude", "ai agent", "ai chatbot",
)

CHATBOT_MARKERS = (
    "intercom", "drift.com", "zendesk", "livechat", "tawk.to", "crisp.chat",
    "hubspot conversations", "widget.js", "chat with us", "ai chatbot",
    "chatbot", "messenger chat", "chat-widget",
)


@dataclass
class WebSignal:
    reachable: bool
    public_ai: bool = False
    chatbot: bool = False
    findings: list[str] | None = None

    def __post_init__(self):
        if self.findings is None:
            self.findings = []


def evaluate_html(html: str) -> WebSignal:
    """Grade homepage HTML for AI + chatbot signals. Pure function."""
    low = (html or "").lower()
    public_ai = any(k in low for k in AI_KEYWORDS)
    chatbot = any(m in low for m in CHATBOT_MARKERS)
    findings: list[str] = []
    if public_ai:
        findings.append("Site advertises AI features")
    if chatbot:
        findings.append("Customer-facing chat/chatbot widget detected")
    return WebSignal(reachable=True, public_ai=public_ai, chatbot=chatbot, findings=findings)


def fetch_homepage(domain: str | None, timeout: int = 15) -> WebSignal:
    """Fetch and grade a homepage, degrading to unreachable on any error."""
    if not domain:
        return WebSignal(reachable=False, findings=["No domain to check"])
    host = domain.strip().lower().replace("https://", "").replace("http://", "").strip("/")
    url = f"https://{host}/"
    try:
        req = Request(url, headers={"User-Agent": "questa-scout/0.1 (+prospecting)"})
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read(400_000)  # cap at ~400KB; homepages are small
        html = raw.decode("utf-8", errors="ignore")
    except Exception as exc:  # noqa: BLE001 -- degrade gracefully
        return WebSignal(reachable=False, findings=[f"Homepage unreachable: {exc}"])
    return evaluate_html(html)
