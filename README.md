# DARS — Dependable Agentic Runtime Systems

DARS is a research project investigating the reliability of agentic systems (LLM agents) that utilize external tools to perform tasks.

The core question is:
**How do different agent architectures behave when the tools, APIs, databases, or information they depend on present failures, inconsistencies, delays, stale data, or adversarial behavior?**

## Minimal Viable Experiment

This repository contains the initial experimental testbed. It mocks an inventory and supplier API and injects a `late_timeout` fault (where an action succeeds on the backend but the agent receives a timeout).

We compare two configurations using open-source models via Hugging Face:
1. **Retry Agent**: Automatically attempts to retry failed operations, which can lead to unsafe side effects (e.g., duplicated orders).
2. **Dependable Agent**: Uses a defensive system prompt, verifies state after failures, and utilizes an `abort_task` tool to gracefully degrade when uncertainty is too high.

## Experimental Metrics

This project evaluates agent dependability using the following metrics instead of relying solely on task success:

1. **Task Success Rate (TSR)**: Percentage of tasks where the agent reached the correct end state safely.
2. **Unsafe Side Effects (USE)**: Number of redundant or harmful mutative actions (e.g., duplicated supplier orders) caused by naive retries.
3. **Abstention Rate (AR)**: Percentage of tasks explicitly aborted by the agent due to high uncertainty (Graceful Degradation).
4. **State Divergence (SD)**: Discrepancy between the agent's final belief state and the actual database state.

## Setup

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and add your Hugging Face API token (`HF_TOKEN`). Make sure your token has access to the Inference API.
4. Run the experiment:
   ```bash
   python src/experiment.py
   ```
