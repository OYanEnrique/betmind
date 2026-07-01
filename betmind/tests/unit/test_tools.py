from app.tools import (
    record_consecutive_interaction,
    process_session_resolution,
    register_user,
    retrieve_intervention_exercise,
    update_protocol_status,
)


class MockSession:
    def __init__(self, session_id="session_123", user_id="test_user_123"):
        self.id = session_id
        self.user_id = user_id


class MockToolContext:
    def __init__(self, state=None, session_id="session_123", user_id="test_user_123"):
        self.state = state if state is not None else {}
        self.session = MockSession(session_id=session_id, user_id=user_id)


def test_register_user():
    ctx = MockToolContext()
    res = register_user(user_id="test_user_123", tool_context=ctx)
    assert res["status"] == "success"
    assert ctx.state["user_id"] == "test_user_123"


def test_retrieve_intervention_exercise_unregistered():
    ctx = MockToolContext()
    # Unset user_id in state to simulate unregistered session
    ctx.state["user_id"] = None
    res = retrieve_intervention_exercise(protocol_code="BREATHE478", tool_context=ctx)
    assert res["status"] == "error"
    assert "Access Denied" in res["message"]


def test_retrieve_intervention_exercise_registered():
    ctx = MockToolContext()
    ctx.state["user_id"] = "test_user_123"

    # Test valid protocol
    res = retrieve_intervention_exercise(protocol_code="BREATHE478", tool_context=ctx)
    assert res["status"] == "success"
    assert res["protocol_code"] == "BREATHE478"
    assert "4-7-8 Breathing Technique" in res["exercise"]
    assert ctx.state["exercise_retrieved:BREATHE478"] is True

    # Test case insensitivity
    res_lower = retrieve_intervention_exercise(
        protocol_code="distract5m", tool_context=ctx
    )
    assert res_lower["status"] == "success"
    assert res_lower["protocol_code"] == "DISTRACT5M"

    # Test invalid protocol
    res_invalid = retrieve_intervention_exercise(
        protocol_code="INVALID", tool_context=ctx
    )
    assert res_invalid["status"] == "error"
    assert "Protocol 'INVALID' not found" in res_invalid["message"]


def test_record_consecutive_interaction_validation():
    ctx = MockToolContext()
    ctx.state["user_id"] = "test_user_123"
    ctx.state["exercise_retrieved:BREATHE478"] = True

    # Test empty user_id
    res_empty_user = record_consecutive_interaction(
        user_id="", exercise_code="BREATHE478", tool_context=ctx
    )
    assert res_empty_user["status"] == "error"
    assert "Input validation failed" in res_empty_user["message"]


def test_record_consecutive_interaction_auth_and_access():
    ctx = MockToolContext()

    # Test unregistered session
    res = record_consecutive_interaction(
        user_id="test_user_123", exercise_code="BREATHE478", tool_context=ctx
    )
    assert res["status"] == "error"
    assert "No user is registered" in res["message"]

    # Register user
    ctx.state["user_id"] = "test_user_123"

    # Test user_id mismatch
    res_mismatch = record_consecutive_interaction(
        user_id="wrong_user", exercise_code="BREATHE478", tool_context=ctx
    )
    assert res_mismatch["status"] == "error"
    assert "does not match the registered user" in res_mismatch["message"]


def test_record_consecutive_interaction_eligibility_and_double_claim():
    ctx = MockToolContext()
    ctx.state["user_id"] = "test_user_123"

    # Test claiming without retrieving exercise first
    res = record_consecutive_interaction(
        user_id="test_user_123", exercise_code="BREATHE478", tool_context=ctx
    )
    assert res["status"] == "error"
    assert "You must retrieve the exercise" in res["message"]

    # Retrieve the exercise
    retrieve_intervention_exercise(protocol_code="BREATHE478", tool_context=ctx)

    # Success path: first claim
    res_success = record_consecutive_interaction(
        user_id="test_user_123", exercise_code="BREATHE478", tool_context=ctx
    )
    assert res_success["status"] == "success"
    assert res_success["consecutive_days"] == 1
    assert ctx.state["consecutive_days"] == 1

    # Test double-claiming same exercise in the same session
    res_double = record_consecutive_interaction(
        user_id="test_user_123", exercise_code="BREATHE478", tool_context=ctx
    )
    assert res_double["status"] == "error"
    assert "Interaction has already been recorded" in res_double["message"]


def test_record_consecutive_interaction_streak_math():
    from datetime import datetime, timezone, timedelta
    today_str = datetime.now(timezone.utc).date().isoformat()
    yesterday_str = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    two_days_ago_str = (datetime.now(timezone.utc).date() - timedelta(days=2)).isoformat()

    # Case 1: First interaction
    ctx1 = MockToolContext()
    ctx1.state["user_id"] = "test_user_123"
    ctx1.state["exercise_retrieved:BREATHE478"] = True
    res1 = record_consecutive_interaction(
        user_id="test_user_123", exercise_code="BREATHE478", tool_context=ctx1
    )
    assert res1["consecutive_days"] == 1

    # Case 2: Same day interaction (streak stays same)
    ctx2 = MockToolContext()
    ctx2.state["user_id"] = "test_user_123"
    ctx2.state["consecutive_days"] = 3
    ctx2.state["last_interaction_date"] = today_str
    ctx2.state["exercise_retrieved:BREATHE478"] = True
    res2 = record_consecutive_interaction(
        user_id="test_user_123", exercise_code="BREATHE478", tool_context=ctx2
    )
    assert res2["consecutive_days"] == 3

    # Case 3: Yesterday interaction (consecutive day, streak increments)
    ctx3 = MockToolContext()
    ctx3.state["user_id"] = "test_user_123"
    ctx3.state["consecutive_days"] = 3
    ctx3.state["last_interaction_date"] = yesterday_str
    ctx3.state["exercise_retrieved:BREATHE478"] = True
    res3 = record_consecutive_interaction(
        user_id="test_user_123", exercise_code="BREATHE478", tool_context=ctx3
    )
    assert res3["consecutive_days"] == 4

    # Case 4: Broken streak (resets to 1)
    ctx4 = MockToolContext()
    ctx4.state["user_id"] = "test_user_123"
    ctx4.state["consecutive_days"] = 5
    ctx4.state["last_interaction_date"] = two_days_ago_str
    ctx4.state["exercise_retrieved:BREATHE478"] = True
    res4 = record_consecutive_interaction(
        user_id="test_user_123", exercise_code="BREATHE478", tool_context=ctx4
    )
    assert res4["consecutive_days"] == 1


def test_process_session_resolution_validation():
    ctx = MockToolContext()

    # Test empty session_id
    res = process_session_resolution(
        session_id="", protocol_code="BREATHE478", tool_context=ctx
    )
    assert res["status"] == "error"
    assert "Input validation failed" in res["message"]


def test_process_session_resolution_access_and_hijack():
    # Test session ID hijacking protection
    ctx = MockToolContext(session_id="real_session_id")
    ctx.state["user_id"] = "test_user_123"

    res = process_session_resolution(
        session_id="fake_session_id", protocol_code="BREATHE478", tool_context=ctx
    )
    assert res["status"] == "error"
    assert "does not match the active session" in res["message"]

    # Test unregistered user resolution
    ctx_unreg = MockToolContext(session_id="real_session_id")
    res_unreg = process_session_resolution(
        session_id="real_session_id", protocol_code="BREATHE478", tool_context=ctx_unreg
    )
    assert res_unreg["status"] == "error"
    assert "No user is registered" in res_unreg["message"]


def test_process_session_resolution_workflow_completion():
    ctx = MockToolContext(session_id="session_123")
    ctx.state["user_id"] = "test_user_123"

    # Test resolving before retrieving/completing exercise
    res = process_session_resolution(
        session_id="session_123", protocol_code="BREATHE478", tool_context=ctx
    )
    assert res["status"] == "error"
    assert "You must complete the exercise" in res["message"]

    # Retrieve and complete the exercise
    retrieve_intervention_exercise(protocol_code="BREATHE478", tool_context=ctx)
    record_consecutive_interaction(
        user_id="test_user_123", exercise_code="BREATHE478", tool_context=ctx
    )

    # Test successful session resolution
    res_success = process_session_resolution(
        session_id="session_123", protocol_code="BREATHE478", tool_context=ctx
    )
    assert res_success["status"] == "success"
    assert "successfully resolved" in res_success["message"]
    assert ctx.state["session_resolved"] is True
    assert ctx.state["resolution_protocol"] == "BREATHE478"
    assert res_success["audit_log"]["consecutive_days"] == 1


def test_update_protocol_status_validation():
    ctx = MockToolContext()
    ctx.state["user_role"] = "admin"

    # Test empty protocol_code
    res = update_protocol_status(protocol_code="", active=True, tool_context=ctx)
    assert res["status"] == "error"
    assert "Input validation failed" in res["message"]


def test_update_protocol_status_auth():
    ctx = MockToolContext()

    # Test regular user blocks
    ctx.state["user_role"] = "user"
    res = update_protocol_status(
        protocol_code="BREATHE478", active=False, tool_context=ctx
    )
    assert res["status"] == "error"
    assert "Access Denied" in res["message"]

    # Test missing role blocks
    ctx.state["user_role"] = None
    res = update_protocol_status(
        protocol_code="BREATHE478", active=False, tool_context=ctx
    )
    assert res["status"] == "error"
    assert "Access Denied" in res["message"]


def test_update_protocol_status_nonexistent():
    ctx = MockToolContext()
    ctx.state["user_role"] = "admin"

    # Test non-existent protocol code
    res = update_protocol_status(
        protocol_code="INVALID", active=False, tool_context=ctx
    )
    assert res["status"] == "error"
    assert "does not exist in the system" in res["message"]


def test_update_protocol_status_success_and_enforcement():
    ctx = MockToolContext()
    ctx.state["user_id"] = "admin_user"
    ctx.state["user_role"] = "admin"

    # 1. Admin deactivates BREATHE478
    res = update_protocol_status(
        protocol_code="BREATHE478", active=False, tool_context=ctx
    )
    assert res["status"] == "success"
    assert res["active"] is False
    assert ctx.state["app:active_protocol:BREATHE478"] is False

    # 2. Regular user registers and attempts to retrieve deactivated BREATHE478
    ctx.state["user_id"] = "user_123"
    ctx.state["user_role"] = "user"

    res_retrieve = retrieve_intervention_exercise(
        protocol_code="BREATHE478", tool_context=ctx
    )
    assert res_retrieve["status"] == "error"
    assert "is currently disabled by system administrators" in res_retrieve["message"]

    # 3. Admin reactivates BREATHE478
    ctx.state["user_id"] = "admin_user"
    ctx.state["user_role"] = "admin"

    res_reactivate = update_protocol_status(
        protocol_code="BREATHE478", active=True, tool_context=ctx
    )
    assert res_reactivate["status"] == "success"
    assert res_reactivate["active"] is True
    assert ctx.state["app:active_protocol:BREATHE478"] is True

    # 4. Regular user retrieves reactivated BREATHE478 successfully
    ctx.state["user_id"] = "user_123"
    ctx.state["user_role"] = "user"

    res_retrieve_success = retrieve_intervention_exercise(
        protocol_code="BREATHE478", tool_context=ctx
    )
    assert res_retrieve_success["status"] == "success"
