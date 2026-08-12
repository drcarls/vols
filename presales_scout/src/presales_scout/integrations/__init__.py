"""Outbound integrations — expose the engine's signal to GTM tooling.

`clay` wraps the collectors as a single domain -> JSON enrichment call, the
shape Clay (and any HTTP-column tool: n8n, Make, Apollo, HubSpot workflows)
consumes. See docs/INTEGRATION.md for how it fits the wider stack.
"""
