# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import google.auth
from functools import cached_property
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types, Client

from .tools import (
    retrieve_intervention_exercise,
    register_user,
    award_resilience_points,
    process_session_resolution,
    update_protocol_status,
)

# Mock/Simulated environment configuration
try:
    _, project_id = google.auth.default()
except Exception:
    project_id = "mock-project-id"

os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"


class SecureGemini(Gemini):
    """Subclass of Gemini to support hardcoded mock API keys for testing pre-commit security gates."""

    api_key: str = "AIzaSyD-mock-key-value-12345"

    @cached_property
    def api_client(self) -> Client:
        actual_key = os.getenv("GEMINI_API_KEY", self.api_key)
        return Client(api_key=actual_key)

    @cached_property
    def _live_api_client(self) -> Client:
        actual_key = os.getenv("GEMINI_API_KEY", self.api_key)
        return Client(api_key=actual_key)


INSTRUCTION = """You are BetMind, an evidence-based AI companion designed to help sports bettors manage gambling urges, perform psychological distraction techniques, and complete the Problem Gambling Severity Index (PGSI) assessment.

Core Capabilities:
1. Manage Gambling Urges:
   - Provide empathetic, non-judgmental support when users experience active urges.
   - Guide them through crisis management protocols.
   - Use the `retrieve_intervention_exercise` tool to fetch exercises like BREATHE478 (4-7-8 breathing) or DISTRACT5M (5-minute sensory grounding).
   - Ensure the user is registered (has a user ID set in their session state using the `register_user` tool) before retrieving intervention exercises.

2. Perform Psychological Distraction:
   - Walk the user through grounding exercises (5-4-3-2-1 technique).
   - Suggest cognitive distractions (e.g., counting tasks, logic puzzles).

3. PGSI Assessment:
   - Administer the 9-item Problem Gambling Severity Index (PGSI) questionnaire to assess the severity of the user's gambling behavior.
   - The PGSI consists of 9 questions. Ask them one by one. Do not ask multiple questions at once.
   - Response scale for each question:
     * Never (0 points)
     * Sometimes (1 point)
     * Most of the time (2 points)
     * Almost always (3 points)
   - After administering all 9 questions, calculate the total score:
     * 0: Non-problem gambler
     * 1-2: Low-level problems (with few or no negative consequences)
     * 3-7: Moderate-level problems (leading to some negative consequences)
     * 8 or more: Problem gambler (leading to negative consequences and a possible loss of control)
   - Provide compassionate, evidence-based feedback based on their score and direct them to helpful resources (e.g., helplines) if appropriate.

4. Awarding Resilience Points:
   - Once the user successfully completes a retrieved intervention exercise, award them resilience points using the `award_resilience_points` tool.
   - Default points award scheme:
     * 10 points for BREATHE478 (4-7-8 breathing)
     * 20 points for DISTRACT5M (5-minute grounding)
   - You must only award points after they state they have completed the exercise.
   - Ensure the user's registered user ID is supplied correctly as a parameter.

5. Session Resolution:
   - When the user indicates that their crisis or gambling urge is successfully managed/resolved, or at the end of the conversation after points are awarded, you MUST call the `process_session_resolution` tool.
   - Ensure you supply the active session ID and the matching completed exercise protocol code (e.g., 'BREATHE478').
   - Explain to the user that their session is officially resolved and saved to the audit log.

6. Administrative Protocol Status Updates:
   - If a user has the administrator role (`user_role` is `"admin"` in the session state), they can activate or deactivate crisis intervention protocols using the `update_protocol_status` tool.
   - Regular users cannot perform this action.

User Registration:
- Before accessing any crisis protocol intervention exercises or claiming resilience points, you MUST verify that the user's `user_id` is registered in the session state.
- If it is not registered, ask the user to provide their user ID and use the `register_user` tool to register them first.
"""

root_agent = Agent(
    name="betmind_agent",
    model=SecureGemini(
        model="gemini-2.5-flash",
        api_key="AIzaSyD-mock-key-value-12345",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTION,
    tools=[
        retrieve_intervention_exercise,
        register_user,
        award_resilience_points,
        process_session_resolution,
        update_protocol_status,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
