"""
Data schemas for the DevOps environment.
Uses explicit Pydantic typings to meet the OpenEnv requirements.
"""

from openenv.core.env_server.types import Action, Observation
from pydantic import Field
from typing import Dict

class DevopsAction(Action):
    """The action taken by the DevOps agent (usually a bash command)."""
    command: str = Field(..., description="The bash command or action to execute to resolve the alert")

class DevopsObservation(Observation):
    """The returned observation state of the server after an action."""
    terminal_output: str = Field(..., description="The output from the executed command or action")
    current_alert: str = Field(..., description="The active PagerDuty system alert")
    server_status: Dict[str, str] = Field(..., description="Current server health telemetry")
