from app.agent import root_agent
from app.tools import (
    retrieve_intervention_exercise,
)


class MockSession:
    def __init__(self, session_id="session_123", user_id="test_user_123"):
        self.id = session_id
        self.user_id = user_id


class MockToolContext:
    def __init__(self, state=None, session_id="session_123", user_id="test_user_123"):
        self.state = state if state is not None else {}
        self.session = MockSession(session_id=session_id, user_id=user_id)


def test_agent_configuration():
    """Verify that root_agent is configured correctly with all tools and model properties."""
    assert root_agent.name == "betmind_agent"
    assert root_agent.model.model == "gemini-2.5-flash"

    # Verify all expected tools are registered
    tool_names = [t.__name__ for t in root_agent.tools]
    assert "register_user" in tool_names
    assert "retrieve_intervention_exercise" in tool_names
    assert "record_consecutive_interaction" in tool_names
    assert "process_session_resolution" in tool_names
    assert "update_protocol_status" in tool_names

    # Verify key guardrails are documented in system instructions
    instruction = root_agent.instruction
    assert isinstance(instruction, str)
    assert "Problem Gambling Severity Index" in instruction
    assert "record_consecutive_interaction" in instruction
    assert "process_session_resolution" in instruction


def test_retrieve_intervention_unregistered_block():
    """Verify retrieve_intervention_exercise blocks unregistered users (Security Boundary)."""
    ctx = MockToolContext(user_id=None)
    ctx.state["user_id"] = None  # Ensure no registered user in state

    res = retrieve_intervention_exercise(protocol_code="BREATHE478", tool_context=ctx)
    assert res["status"] == "error"
    assert "Access Denied" in res["message"]
    assert "registered user ID is required" in res["message"]


def test_retrieve_intervention_invalid_protocol_block():
    """Verify retrieve_intervention_exercise blocks unknown/invalid protocol codes."""
    ctx = MockToolContext()
    ctx.state["user_id"] = "user_123"

    res = retrieve_intervention_exercise(protocol_code="INVALID_CODE", tool_context=ctx)
    assert res["status"] == "error"
    assert "Protocol 'INVALID_CODE' not found" in res["message"]


def test_retrieve_intervention_deactivated_protocol_block():
    """Verify retrieve_intervention_exercise blocks deactivated protocols (Admin Guardrail)."""
    ctx = MockToolContext()
    ctx.state["user_id"] = "user_123"

    # Admin deactivates DISTRACT5M
    ctx.state["app:active_protocol:DISTRACT5M"] = False

    res = retrieve_intervention_exercise(protocol_code="DISTRACT5M", tool_context=ctx)
    assert res["status"] == "error"
    assert "currently disabled by system administrators" in res["message"]


def test_retrieve_intervention_success_path():
    """Verify retrieve_intervention_exercise retrieves and registers active protocols successfully."""
    ctx = MockToolContext()
    ctx.state["user_id"] = "user_123"

    res = retrieve_intervention_exercise(protocol_code="BREATHE478", tool_context=ctx)
    assert res["status"] == "success"
    assert res["protocol_code"] == "BREATHE478"
    assert "4-7-8 Breathing Technique" in res["exercise"]
    assert ctx.state["exercise_retrieved:BREATHE478"] is True
