"""
Hackathon Baseline Inference Script
Complies with mandatory Additional Instructions
"""
import os
import asyncio
from typing import List
from openai import AsyncOpenAI
import json

# Import local Environment
from client import DevopsEnv
from models import DevopsAction

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
HF_TOKEN = os.getenv("HF_TOKEN")
IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME", "devops_env_env:latest")

def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: str = None):
    err_str = f" error={error}" if error else ""
    print(f"[STEP] step={step} action='{action}' reward={reward} done={done}{err_str}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    print(f"[END] success={success} steps={steps} score={score} rewards={rewards}", flush=True)

SYSTEM_PROMPT = "You are a DevOps engineer solving issues on a Linux server. Return ONLY the bash command you want to run. Be concise."

def build_user_prompt(step, current_alert, status) -> str:
    return f"Step {step}: Active Alert is '{current_alert}'. Server Status: {status}. Execute a bash command to fix the issue or investigate."

async def main():
    client = AsyncOpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN or "dummy_key")
    
    # Boot environment dynamically
    try:
        env = await DevopsEnv.from_docker_image(IMAGE_NAME)
    except Exception as e:
        print(f"Falling back to local URL logic: {e}")
        env = DevopsEnv(base_url="http://localhost:8000")
        
    history = []
    rewards = []
    steps_taken = 0
    score = 0.0
    success = False
    
    log_start(task="devops_env", env="devops", model=MODEL_NAME)
    
    try:
        result = await env.reset()
        current_alert = result.observation.current_alert
        status = result.observation.server_status
        
        for step in range(1, 11):
            if result.done:
                break
                
            user_prompt = build_user_prompt(step, current_alert, status)
            
            try:
                completion = await client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.0,
                    max_tokens=60
                )
                action_text = (completion.choices[0].message.content or "").strip()
            except Exception as exc:
                print(f"[DEBUG] Model failed: {exc}", flush=True)
                action_text = "ls"
                
            result = await env.step(DevopsAction(command=action_text))
            
            obs = result.observation
            reward = result.reward or 0.0
            done = result.done
            
            rewards.append(reward)
            steps_taken = step
            current_alert = obs.current_alert
            status = obs.server_status
            
            log_step(step=step, action=action_text, reward=reward, done=done)
            
            if done:
                break
                
        # Total logic ensures partial sum
        score = min(max(sum(rewards), 0.0), 1.0)
        success = score >= 0.5
        
    finally:
        try:
            await env.close()
        except Exception:
            pass
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    asyncio.run(main())
