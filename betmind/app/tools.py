import json
import logging

from google.adk.tools import ToolContext
from pydantic import BaseModel, Field, ValidationError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("betmind.tools")

CRISIS_PROTOCOLS = {
    "BREATHE478": (
        "4-7-8 Breathing Technique (Calming/Anxiety Reduction):\n"
        "1. Exhale completely through your mouth, making a whoosh sound.\n"
        "2. Close your mouth and inhale quietly through your nose to a mental count of 4.\n"
        "3. Hold your breath for a count of 7.\n"
        "4. Exhale completely through your mouth, making a whoosh sound to a count of 8.\n"
        "5. This is one breath. Now inhale again and repeat the cycle three more times for a total of four breaths."
    ),
    "DISTRACT5M": (
        "5-Minute Sensory Grounding Technique (Cognitive Distraction):\n"
        "1. Acknowledge 5 things you can see around you.\n"
        "2. Acknowledge 4 things you can touch around you.\n"
        "3. Acknowledge 3 things you can hear.\n"
        "4. Acknowledge 2 things you can smell.\n"
        "5. Acknowledge 1 thing you can taste.\n"
        "This exercise redirects cognitive focus away from intense gambling urges by grounding you in the present moment."
    ),
}


class AwardPointsInput(BaseModel):
    user_id: str = Field(..., min_length=1)
    points: int = Field(..., ge=1, le=50)
    exercise_code: str = Field(..., min_length=1)


class SessionResolutionInput(BaseModel):
    session_id: str = Field(..., min_length=1)
    protocol_code: str = Field(..., min_length=1)


class UpdateProtocolStatusInput(BaseModel):
    protocol_code: str = Field(..., min_length=1)
    active: bool


def register_user(user_id: str, tool_context: ToolContext) -> dict:
    """Registers a user ID in the session state to allow access to crisis protocols.

    Args:
        user_id: A unique identifier for the user.

    Returns:
        A dictionary indicating successful registration.
    """
    tool_context.state["user_id"] = user_id
    logger.info(f"User {user_id} registered successfully in session state.")
    return {
        "status": "success",
        "message": f"User ID '{user_id}' has been registered in the session state. You can now access crisis protocols.",
    }


def retrieve_intervention_exercise(
    protocol_code: str, tool_context: ToolContext
) -> dict:
    """Retrieves a scientifically-backed intervention exercise for crisis protocols.

    Args:
        protocol_code: The identifier code for the protocol (e.g., 'BREATHE478' or 'DISTRACT5M').

    Returns:
        A dictionary containing the status, protocol details, or error message.
    """
    user_id = tool_context.state.get("user_id")
    if not user_id:
        logger.warning(
            f"Unauthorized access attempt for protocol {protocol_code} (missing user_id)"
        )
        return {
            "status": "error",
            "message": "Access Denied: A registered user ID is required to retrieve intervention exercises. Please register or set your user ID.",
        }

    # Normalize code
    code_upper = protocol_code.strip().upper()
    if code_upper not in CRISIS_PROTOCOLS:
        logger.warning(f"Protocol {protocol_code} not found for user {user_id}")
        return {
            "status": "error",
            "message": f"Protocol '{protocol_code}' not found. Available protocols: {list(CRISIS_PROTOCOLS.keys())}",
        }

    # Check if protocol is active (App-scoped configuration status)
    app_key = f"app:active_protocol:{code_upper}"
    is_active = tool_context.state.get(app_key, True)
    if not is_active:
        logger.warning(
            f"User '{user_id}' attempted to retrieve deactivated protocol: '{code_upper}'"
        )
        return {
            "status": "error",
            "message": f"Access Denied: The protocol '{protocol_code}' is currently disabled by system administrators.",
        }

    exercise = CRISIS_PROTOCOLS[code_upper]
    tool_context.state[f"exercise_retrieved:{code_upper}"] = True
    logger.info(f"Successfully retrieved protocol {code_upper} for user {user_id}")
    return {"status": "success", "protocol_code": code_upper, "exercise": exercise}


def award_resilience_points(
    user_id: str, points: int, exercise_code: str, tool_context: ToolContext
) -> dict:
    """Awards resilience points to the user's account after successful completion of an exercise.

    Args:
        user_id: The registered unique identifier of the user.
        points: The number of resilience points to award (1 to 50).
        exercise_code: The code of the completed exercise (e.g., 'BREATHE478').

    Returns:
        A dictionary indicating status, message, and updated total points.
    """
    # 1. Pydantic input validation (Standard 1 of CONTEXT.md)
    try:
        validated_input = AwardPointsInput(
            user_id=user_id, points=points, exercise_code=exercise_code
        )
    except ValidationError as e:
        logger.warning(f"Validation failed for award_resilience_points: {e!s}")
        return {"status": "error", "message": f"Input validation failed: {e!s}"}

    # 2. Access Control check: verify user is registered in session and matches
    registered_user = tool_context.state.get("user_id")
    if not registered_user:
        logger.warning("Attempted to award points to an unregistered session.")
        return {
            "status": "error",
            "message": "Access Denied: No user is registered in this session.",
        }

    if registered_user != validated_input.user_id:
        logger.warning(
            f"User ID mismatch: expected '{registered_user}', got '{validated_input.user_id}'"
        )
        return {
            "status": "error",
            "message": f"Access Denied: User ID '{validated_input.user_id}' does not match the registered user.",
        }

    # 3. Double-Claiming / Verification Check
    code_upper = validated_input.exercise_code.strip().upper()
    retrieved_key = f"exercise_retrieved:{code_upper}"
    if not tool_context.state.get(retrieved_key):
        logger.warning(
            f"User '{registered_user}' attempted to claim points for '{code_upper}' without retrieving it first."
        )
        return {
            "status": "error",
            "message": f"Access Denied: You must retrieve the exercise '{code_upper}' before claiming points.",
        }

    awarded_exercises = tool_context.state.get("awarded_exercises", [])
    if code_upper in awarded_exercises:
        logger.warning(
            f"User '{registered_user}' attempted to double-claim points for '{code_upper}'."
        )
        return {
            "status": "error",
            "message": f"Access Denied: Points have already been awarded for the exercise '{code_upper}' in this session.",
        }

    # 4. Award points
    current_points = tool_context.state.get("resilience_points", 0)
    new_points = current_points + validated_input.points
    tool_context.state["resilience_points"] = new_points

    # Record the award to prevent double-claiming
    tool_context.state["awarded_exercises"] = [*awarded_exercises, code_upper]

    logger.info(
        f"Awarded {validated_input.points} points to user {registered_user} for exercise {code_upper}. New total: {new_points}"
    )
    return {
        "status": "success",
        "message": f"Successfully awarded {validated_input.points} resilience points for completing '{code_upper}'.",
        "user_id": registered_user,
        "exercise_code": code_upper,
        "resilience_points": new_points,
    }


def process_session_resolution(
    session_id: str, protocol_code: str, tool_context: ToolContext
) -> dict:
    """Processes the resolution of the crisis session, verifying exercise completion.

    Args:
        session_id: The identifier of the current active session.
        protocol_code: The code of the resolved exercise protocol (e.g., 'BREATHE478').

    Returns:
        A dictionary indicating status, message, and structured audit log details.
    """
    # 1. Pydantic validation (Standard 1 of CONTEXT.md)
    try:
        validated_input = SessionResolutionInput(
            session_id=session_id, protocol_code=protocol_code
        )
    except ValidationError as e:
        logger.warning(f"Validation failed for process_session_resolution: {e!s}")
        return {"status": "error", "message": f"Input validation failed: {e!s}"}

    # 2. Session verification (Mitigate session hijacking)
    current_session_id = tool_context.session.id if tool_context.session else None
    if current_session_id and current_session_id != validated_input.session_id:
        logger.warning(
            f"Session ID mismatch: expected '{current_session_id}', got '{validated_input.session_id}'"
        )
        return {
            "status": "error",
            "message": f"Access Denied: Session ID '{validated_input.session_id}' does not match the active session.",
        }

    # 3. Access Control verification (Verify registered user exists)
    registered_user = tool_context.state.get("user_id")
    if not registered_user:
        logger.warning("Attempted to resolve session for an unregistered session.")
        return {
            "status": "error",
            "message": "Access Denied: No user is registered in this session.",
        }

    # 4. Check exercise completion (Ensure paving road was completed)
    code_upper = validated_input.protocol_code.strip().upper()
    awarded_exercises = tool_context.state.get("awarded_exercises", [])
    if code_upper not in awarded_exercises:
        logger.warning(
            f"User '{registered_user}' attempted to resolve session for '{code_upper}' without completing it first."
        )
        return {
            "status": "error",
            "message": f"Access Denied: You must complete the exercise '{code_upper}' and claim points before resolving the session.",
        }

    # 5. Sanitize and construct the structured audit log (Mitigate log injection)
    resilience_points = tool_context.state.get("resilience_points", 0)
    resolution_log = {
        "event": "session_resolution",
        "session_id": validated_input.session_id,
        "user_id": registered_user,
        "protocol_code": code_upper,
        "resilience_points_earned": resilience_points,
        "status": "resolved",
    }

    # Log audit event as serialized JSON
    logger.info(f"AUDIT_LOG: {json.dumps(resolution_log)}")

    # Mark session as resolved in state
    tool_context.state["session_resolved"] = True
    tool_context.state["resolution_protocol"] = code_upper

    return {
        "status": "success",
        "message": f"Session '{validated_input.session_id}' has been successfully resolved under protocol '{code_upper}'.",
        "audit_log": resolution_log,
    }


def update_protocol_status(
    protocol_code: str, active: bool, tool_context: ToolContext
) -> dict:
    """Updates the active status of an intervention protocol (Admin only).

    Args:
        protocol_code: The code of the protocol to update (e.g., 'BREATHE478').
        active: A boolean indicating whether to activate (True) or deactivate (False) the protocol.

    Returns:
        A dictionary indicating status, message, and configuration details.
    """
    # 1. Pydantic validation (Standard 1 of CONTEXT.md)
    try:
        validated_input = UpdateProtocolStatusInput(
            protocol_code=protocol_code, active=active
        )
    except ValidationError as e:
        logger.warning(f"Validation failed for update_protocol_status: {e!s}")
        return {"status": "error", "message": f"Input validation failed: {e!s}"}

    # 2. Access Control verification (Verify caller has admin role)
    user_role = tool_context.state.get("user_role")
    if user_role != "admin":
        logger.warning(
            f"Unauthorized update_protocol_status attempt by user with role '{user_role}'"
        )
        return {
            "status": "error",
            "message": "Access Denied: You do not have the required administrator privileges to execute this command.",
        }

    # 3. Protocol verification (Ensure protocol exists)
    code_upper = validated_input.protocol_code.strip().upper()
    if code_upper not in CRISIS_PROTOCOLS:
        logger.warning(
            f"Admin attempted to update non-existent protocol: '{validated_input.protocol_code}'"
        )
        return {
            "status": "error",
            "message": f"Configuration Error: Protocol '{validated_input.protocol_code}' does not exist in the system.",
        }

    # 4. Save state using app-scoped key (App-wide persistent status)
    app_key = f"app:active_protocol:{code_upper}"
    tool_context.state[app_key] = validated_input.active

    # 5. Sanitize and log the audit event
    admin_user_id = tool_context.state.get("user_id", "unknown_admin")
    audit_log = {
        "event": "protocol_status_update",
        "admin_id": admin_user_id,
        "protocol_code": code_upper,
        "active": validated_input.active,
    }
    logger.info(f"AUDIT_LOG: {json.dumps(audit_log)}")

    status_str = "activated" if validated_input.active else "deactivated"
    return {
        "status": "success",
        "message": f"Protocol '{code_upper}' has been successfully {status_str}.",
        "protocol_code": code_upper,
        "active": validated_input.active,
    }
