# USAGE GUIDE: ATHENA 4.0

This guide outlines the standard operational procedures for conducting research with the ATHENA Framework.

## 1. Initializing a Session

Launch the dashboard from your terminal:
```bash
python tui.py
```

### Session Recovery
Upon launch, ATHENA will display "Persisted Research Streams." 
*   To resume a previous session: Enter the corresponding index number (e.g., `01`).
*   To start a new session: Press `Enter` or type `N`.

## 2. Setting the Research Objective

When starting a new session, provide a technical research subject. 
ATHENA will enter a planning phase and generate a `research_spec.md` file in your workspace. This file acts as the primary reference for the session.

## 3. Model Selection

ATHENA supports switching between different LLM engines:
*   **Startup:** Select your engine from the provided menu.
*   **Mid-Session (Hot-Swap):** Press `Ctrl+M` at any time to pause the dashboard and switch engines.

## 4. Interactive Research Queue

ATHENA 4.0 supports iterative research through an asynchronous instruction queue:
1.  **Queue Instruction:** Press `Ctrl+I` while the agent is working to pause the dashboard.
2.  **Input follow-up:** Provide a new instruction.
3.  **Iteration:** ATHENA will finalize its current task and transition to your queued instruction.
4.  **Capacity:** Each session supports up to **100 computational turns**.

## 5. The Research Workflow

ATHENA follows a two-phase pipeline:

### Phase 1: Accumulation (Discovery)
The agent operates in EXPLORER mode to build a local context library. Ingestion progress is tracked in the sidebar.

### Phase 2: Production (Synthesis)
Once the threshold is met, the system transitions to SYNTHESIZER mode:
1.  **Experimental Code:** The agent generates and executes `experiment.py` in the workspace.
2.  **Section Drafting:** Sections are written sequentially.
3.  **Validation:** Key assertions are cross-referenced against retrieved evidence.

## 6. Workspace Management

All research artifacts are stored in the `workspace/` directory:
*   `workspace/lab/{session_id}/`: Specifications, experimental code, and reports.
*   `workspace/skills/`: Distilled procedural logic.

## 6. Project-Specific Rules (RESEARCH.md)

You can customize ATHENA's behavior for a specific directory by creating a `RESEARCH.md` file. The agent will read this at startup and follow its instructions (e.g., "Always use APA 7th edition formatting").
