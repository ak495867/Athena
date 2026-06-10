# CONTRIBUTING TO ATHENA

ATHENA is an open-source autonomous research project. We welcome contributions that enhance its scientific rigor, toolset, and autonomy.

## Development Principles

*   **Rigor First:** Tools and agents must prioritize scientific accuracy and claim validation over conversational speed.
*   **Minimalist Aesthetic:** The TUI should remain emoji-free and industrial. Use technical ASCII/Unicode for visualizations.
*   **Fault Tolerance:** Every new tool must be wrapped in robust error handling to support the "Armored Agent" architecture.

## How to Contribute

### 1. Adding New Tools
New research tools should be implemented in `tools.py`.
*   Ensure the tool returns a string representation of the result or error.
*   Add the tool to the `TOOLS` schema with a concise, technical description.
*   Map the tool in `TOOL_MAP`.

### 2. Refining Personas
Agent personas are defined in `agent.py`. Current personas include:
*   **EXPLORER:** Discovery and "Paper Trail" citation traversal.
*   **LAB:** Empirical code generation, execution, and iterative debugging.
*   **SYNTHESIZER:** RAG-based drafting and section production.
*   **RED_TEAM:** Adversarial peer-review and claim validation.
*   **ARCHIVIST:** Procedural skill distillation and trajectory compression.

### 3. Workspace Extensions
If adding features that save files or maintain state, utilize the `workspace/` directory. All persistent lab experiments must be session-specific.

## Code Standards
*   **Type Hinting:** Use Python type hints for all function signatures.
*   **UTF-8:** All file I/O operations must explicitly use UTF-8 encoding.
*   **Dependencies:** Any new dependency must be added to `requirements.txt` and vetted for stability.

## Research Compliance
When contributing code that fetches data from academic APIs (e.g., ArXiv, Semantic Scholar), ensure compliance with their respective Terms of Service and Rate Limiting policies.

---

**Advance the frontier of autonomous discovery.**
