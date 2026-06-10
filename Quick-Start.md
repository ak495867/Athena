# Quick Start — ATHENA 4.0

This guide gets you from zero to running your first research session in under five minutes.

---

## Prerequisites

- Python 3.10 or higher
- A Groq API key — get one free at [console.groq.com](https://console.groq.com)

---

## 1. Clone the repository

```bash
git clone https://github.com/ak495867/Athena.git
cd Athena
```

---

## 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**macOS / Linux**
```bash
source venv/bin/activate
```

**Windows**
```bash
.\venv\Scripts\activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Set your API key

**macOS / Linux**
```bash
export GROQ_API_KEY=your_key_here
```

**Windows (Command Prompt)**
```cmd
set GROQ_API_KEY=your_key_here
```

**Windows (PowerShell)**
```powershell
$env:GROQ_API_KEY="your_key_here"
```

> Alternatively, create a `.env` file in the project root with `GROQ_API_KEY=your_key_here`.

---

## 5. Initialize the workspace

```bash
python setup_env.py
```

This verifies your configuration, checks dependencies, and creates the `workspace/` directory structure.

---

## 6. Launch ATHENA

```bash
python tui.py
```

You'll be greeted by the terminal dashboard. Press `Enter` to start a new session, then type your research topic when prompted.

---

## Your first session

Once launched, ATHENA runs a two-phase pipeline automatically:

| Phase | Mode | What happens |
|---|---|---|
| 1 | `EXPLORER` | Retrieves and indexes literature; traverses citation graph |
| 2 | `SYNTHESIZER` | Generates experiment code, drafts report sections, validates claims |

Watch the sidebar for live ingestion progress and turn count.

---

## Useful keybindings

| Key | Action |
|---|---|
| `Ctrl+I` | Queue a follow-up instruction while the agent is working |
| `Ctrl+M` | Hot-swap the LLM engine mid-session |
| `Ctrl+C` | Exit the dashboard |

---

## Resuming a session

ATHENA saves all sessions automatically. On next launch, persisted sessions appear as a numbered list — enter the index to resume, or press `Enter` to start fresh.

---

## Customizing behavior

Drop a `RESEARCH.md` file into your working directory before launching. ATHENA reads it at startup and follows any instructions inside — citation style, output format, domain constraints, etc.

**Example `RESEARCH.md`:**
```
Always use APA 7th edition for citations.
Focus only on papers published after 2018.
Generate experiment code in PyTorch.
```

---

## Where to find your output

All research artifacts are saved to:

```
workspace/
└── lab/
    └── {session_id}/
        ├── research_spec.md    # Session objective and methodology
        ├── experiment.py       # Generated and executed experiment code
        ├── report.md           # Final research report
        └── journal.md          # Agent's strategic log
```

---

## Troubleshooting

**`GROQ_API_KEY` not found** — make sure you exported it in the same terminal session, or added it to `.env`.

**Rate limit errors** — free-tier Groq keys have per-minute limits. For sessions over 80 turns, consider a paid key or add a short delay between instructions.

**Dependency conflicts** — make sure your virtual environment is activated before running `pip install`.

---

For the full operational guide, see [`USAGE.md`](USAGE.md).
