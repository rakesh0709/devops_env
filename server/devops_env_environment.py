"""
DevOps Environment Logic.
Simulates an SRE on-call environment where the agent must clear active alerts.
"""
from uuid import uuid4
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import DevopsAction, DevopsObservation
except ImportError:
    from models import DevopsAction, DevopsObservation

class DevopsEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS = True

    TASKS = [
        {
            "id": "task_1_easy", 
            "difficulty": "easy",
            "alert": "502 Bad Gateway - Nginx Service Down", 
            "solution": "systemctl restart nginx"
        },
        {
            "id": "task_2_medium", 
            "difficulty": "medium",
            "alert": "CPU at 100% due to rogue crypto_miner process", 
            "solution": "killall crypto_miner"
        },
        {
            "id": "task_3_hard", 
            "difficulty": "hard",
            "alert": "Application crashing on boot. DB connection refused on port 5432.", 
            "solution": "systemctl restart postgresql && systemctl restart backend"
        }
    ]

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.task_idx = -1
        self.is_resolved = False
        self.partial_progress = 0.0

    def reset(self) -> DevopsObservation:
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.task_idx = (self.task_idx + 1) % len(self.TASKS)
        self.is_resolved = False
        self.partial_progress = 0.0
        
        task = self.TASKS[self.task_idx]
        return DevopsObservation(
            terminal_output=f"New PagerDuty alert received! Start investigation.",
            current_alert=task["alert"],
            server_status={"cpu": "99%" if "CPU" in task["alert"] else "10%", "memory": "40%", "disk": "50%"},
            done=False,
            reward=0.0
        )

    def step(self, action: DevopsAction) -> DevopsObservation:
        self._state.step_count += 1
        task = self.TASKS[self.task_idx]
        cmd = action.command.strip().lower()
        
        reward = 0.0
        output = f"Executing '{cmd}'..."
        
        if self.is_resolved:
            return DevopsObservation(
                terminal_output="Incident already resolved.",
                current_alert="None",
                server_status={"cpu": "10%", "memory": "40%", "disk": "50%"},
                done=True,
                reward=0.0
            )

        # Detect correct solution
        if task["solution"] in cmd or all(sub in cmd.split("&&") for sub in task["solution"].split("&&")):
            self.is_resolved = True
            reward = 1.0 - self.partial_progress  # Ensure total exactly caps at 1.0
            self.partial_progress = 1.0
            output = "SUCCESS: Command ran successfully. Service restored and alert cleared."
            
        # Add partial progress for proper investigation tools (hackathon partial signal requirement)
        elif "tail" in cmd or "htop" in cmd or "log" in cmd or "ps aux" in cmd:
            if self.partial_progress < 0.4:
                reward = 0.2
                self.partial_progress += 0.2
            output = "Showing internal logs/processes... found relevant hints related to the alert."
            
        else:
            # Penalize destructive or useless actions
            reward = -0.05
            output = f"bash: {cmd}: command not found or does not resolve the issue."

        # Clamp reward just in case
        reward = max(min(reward, 1.0), -1.0)

        return DevopsObservation(
            terminal_output=output,
            current_alert=task["alert"] if not self.is_resolved else "None",
            server_status={"cpu": "10%" if self.is_resolved else ("99%" if "CPU" in task["alert"] else "15%"), "memory": "40%", "disk": "50%"},
            done=self.is_resolved,
            reward=reward,
            metadata={"step": self._state.step_count, "task_id": task["id"], "score": self.partial_progress}
        )

    @property
    def state(self) -> State:
        return self._state
