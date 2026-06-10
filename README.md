# ATHENA 4.0: Autonomous Multi-Agent Research Framework

ATHENA is an autonomous, research-oriented agent orchestration framework designed for systematic scientific discovery, empirical validation, and automated report generation. The system employs a multi-agent loop to facilitate deep literature traversal, claim verification, and iterative experimentation within stateful local environments.

---

## Core Architecture: Feedback-Driven Orchestration

ATHENA utilizes a specialized multi-persona loop to ensure scientific assertions are cross-referenced and challenged.

### 1. Persistent Experimental Environments
ATHENA operates a stateful workspace for empirical validation.
*   Traceback Analysis: If an execution fails, the agent parses the stack trace to identify logical or syntactic errors, iteratively refining the implementation.
*   Stateful Workspaces: All research artifacts are maintained in session-specific directories, ensuring data persistence and auditability.

### 2. Two-Stage Reranked Retrieval (RAG)
To maximize signal-to-noise ratios in retrieved context, ATHENA employs a two-stage pipeline:
*   Candidate Selection: High-speed vector search using a fast bi-encoder.
*   Precision Reranking: A Cross-Encoder scoring pass that filters for the most relevant evidentiary support.

### 3. Adversarial Peer-Review
The framework incorporates a mandatory review phase to mitigate hallucination and logical inconsistencies.
*   Adversarial Persona: Drafted sections undergo a critique pass where an adversarial agent identifies weak evidence and mandates revisions.

### 4. Citation Graph Traversal
ATHENA explores the academic landscape by programmatically following citation paths.
*   Recursive Discovery: Utilizing the Semantic Scholar API, the system traverses reference lists and citation networks to identify foundational and contemporary research.

---

## Technical Toolset

*   save_research_spec: Formalizes objectives and methodology into a structured specification.
*   validate_claim: Verifies assertions against vector memory using neural reranking.
*   write_journal_entry: Records strategic insights and experimental trajectories.
*   create_research_skill: Distills successful task trajectories into reusable procedural logic.
*   search_web: Real-time information retrieval via DuckDuckGo.

---

## Dashboard & Observability (TUI)

The ATHENA interface is an industrial-grade terminal dashboard built for real-time monitoring of agent state.
*   Dynamic ASCII Glyph: A geometric identifier visualizing the agent's current operational mode.
*   Observability Sidebar: Live tracking of ingestion progress, turn counts, and research metrics.
*   Error Recovery: Automated repair of malformed model outputs and rate-limit backoff.

---

## Quick Start

### Prerequisites
*   Python 3.10+
*   Groq API Key (Exported as GROQ_API_KEY)

### Create Virtual Environment
```bash
python -m venv venv
```

### Activate Virtual Environment

**Windows**
```bash
.\venv\Scripts\activate
```

**Linux/macOS**
```bash
source venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Initialize ATHENA Environment
```bash
python setup_env.py
```

This will:
- Verify your configuration
- Create the ATHENA workspace structure
- Check required dependencies
- Prepare the research environment

### Run ATHENA
```bash
python tui.py
```
---

## Scientific Auditability
ATHENA is designed as a transparent research instrument. All logs, source code, and specifications are archived in the workspace/ directory for post-session review.

Framework Integrity. Systematic Discovery. Rigorous Validation.
