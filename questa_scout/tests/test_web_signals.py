from questa_scout.collectors.web_signals import evaluate_html


def test_detects_ai_and_chatbot():
    html = """
    <html><body>
      <h1>Powered by AI</h1>
      <p>Our AI assistant helps you.</p>
      <script src="https://widget.intercom.io/widget.js"></script>
    </body></html>
    """
    sig = evaluate_html(html)
    assert sig.public_ai is True
    assert sig.chatbot is True
    assert sig.reachable is True


def test_clean_site_has_no_signal():
    sig = evaluate_html("<html><body><h1>We sell rugs</h1></body></html>")
    assert sig.public_ai is False
    assert sig.chatbot is False


def test_ai_without_chatbot():
    sig = evaluate_html("<p>We use large language models internally.</p>")
    assert sig.public_ai is True
    assert sig.chatbot is False
