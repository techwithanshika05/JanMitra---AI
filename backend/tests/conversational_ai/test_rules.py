from app.conversational_ai.rules import route_rule


def test_sensitive_data_rule_blocks_collection():
    result = route_rule("My OTP is 123456", "en-IN")
    assert result.matched
    assert result.intent == "sensitive_data"


def test_language_switch():
    assert route_rule("Please speak English", "hi-IN").intent == "change_language_en"


def test_unmatched_question_reaches_knowledge_pipeline():
    assert not route_rule("How can I update my ration card?", "en-IN").matched
