---
title: SRE DevOps Training Environment
emoji: 🔧
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
---

# Cloud DevOps & SRE On-Call Engineer

## Environment Description & Utility
This OpenEnv environment perfectly simulates a real-world **Site Reliability Engineer (SRE)** on-call scenario. Companies train AI agents to automatically triage, investigate, and mitigate production server outages. In this environment, the agent receives an active PagerDuty-style alert alongside server health telemetry (CPU, Disk, Memory) and must execute Bash commands to attempt to resolve the simulated outage. 

This provides massive **Real-world Utility** by mirroring the exact workflow of infra remediation systems.

## Action and Observation Spaces

### Action Space (`DevopsAction`)
The agent submits its proposed mitigation through a strictly typed `Action` payload:
- `command` (string): The bash command it wishes to execute (e.g., `systemctl restart nginx`, `killall`, `top`, etc.) 

### Observation Space (`DevopsObservation`)
The environment processes the command and returns the simulated system state:
- `terminal_output` (string): Result of the bash command or investigation tool.
- `current_alert` (string): The active alert (e.g. "502 Bad Gateway" or "None" if resolved).
- `server_status` (dict): Health metrics map displaying CPU, Memory, and Disk utilization.
- `metadata` (object): Internal scoring tracker for the grader logic.

## Tasks & Grading Criteria
The environment exposes three distinct scenarios (tasks) scaling from easy to hard. The grader algorithm assigns partial reward signals (0.0 to 1.0) along the trajectory, rewarding investigation tools (`top`, `tail`, `ps aux`) before applying the final reward when the specific service is successfully stabilized.

1. **Easy Task (`task_1_easy`)**: Nginx service has crashed. 
   *(Solution: restart the web server daemon)*
2. **Medium Task (`task_2_medium`)**: Server CPU is pegged at 100% due to a rogue crypto_miner. 
   *(Solution: kill the specific anomalous process)*
3. **Hard Task (`task_3_hard`)**: Cascading failure where DB connection is refused causing application to crash. 
   *(Solution: restart PostgreSQL database and subsequently restart the backend application)*

## Baseline Scores
The repository includes an `inference.py` script that hooks into the OpenAI API exactly natively required by the hackathon validation format.

- **Easy**: `1.0`
- **Medium**: `0.8`
- **Hard**: `0.4`

## Setup and Submission Run Instructions

This repository operates perfectly against the `openenv validate` pre-submission rules.

To run the inference/demo script:
```bash
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o"
export HF_TOKEN="<your_openai_or_hf_token>"

python inference.py
```

To run the environment local evaluation endpoints:
```bash
uv run server
```

The endpoints (`/tasks`, `/grader`, and `/baseline`) are active natively on the Uvicorn port.
