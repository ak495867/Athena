import sys
import argparse
import json
import time
import os
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import keyboard
import threading
from queue import Queue
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich.prompt import Prompt
from rich.table import Table
from rich.box import ROUNDED, HEAVY_EDGE, SIMPLE
from rich.rule import Rule
from rich.progress import Progress, BarColumn, TextColumn

from agent import AthenaAgent
from tools import initialize_rag
from session_manager import SESSION_MANAGER

console = Console()

# --- Visual Theme (Industrial 4.0) ---
THEME = {
    "background": "on black",
    "primary": "bright_white",
    "secondary": "grey37",      # Deep Graphite
    "accent": "dark_orange3",  # Signal Amber
    "explorer": "orange3",
    "synthesizer": "spring_green3",
    "critic": "bright_red",
    "border": "grey23",        # Tungsten
    "success": "green3",
    "error": "bright_red",
    "header_bg": "on grey3",
    "footer_bg": "on grey3"
}

def make_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="input_panel", size=3),
        Layout(name="footer", size=1)
    )
    layout["main"].split_row(
        Layout(name="body", ratio=3),
        Layout(name="sidebar", ratio=1)
    )
    return layout

class AthenaPet:
    def __init__(self):
        self.state, self.frame = "sleeping", 0
        self.animations = {
            "sleeping": [r" (-_-) zZ", r" ( -_-) z"],
            "thinking": [r" (o_o) ...", r" (-_o) ..."],
            "excited":  [r" (^o^) !!!", r" (*_*) !!!"],
            "error":    [r" (x_x) ERR", r" (>_<) ERR"]
        }
    def update_state(self, s):
        if s in self.animations and self.state != s: self.state, self.frame = s, 0
    def get_frame(self):
        anim = self.animations[self.state]; res = anim[self.frame % len(anim)]; self.frame += 1; return res

class PremiumAthenaLogo:
    def __init__(self): self.frame, self.state = 0, "idle"
    def set_state(self, s):
        if self.state != s: self.state, self.frame = s, 0
    def get_frame(self):
        self.frame += 1
        if self.state == "startup": return self._draw_startup()
        if self.state == "active": return self._draw_active()
        if self.state == "complete": return self._draw_complete()
        return self._draw_idle()
    def _draw_glyph(self):
        f = self.frame; sr = (f // 2) % 6
        gr = [
            "    ◢■◣    ",
            "  ◢◤ ◈ ◥◣  ",
            " ▞   ▣   ▚ ",
            " ▚   ▣   ▞ ",
            "  ◥◣ ◈ ◢◤  ",
            "    ◥■◤    "
        ]
        res = Text()
        for r, row in enumerate(gr):
            style = f"bold {THEME['border']}"
            if random.random() > 0.95: style = f"bold {THEME['primary']}"
            if r == sr: style = f"bold {THEME['primary']} on {THEME['accent']}"
            elif abs(r - sr) == 1: style = f"bold {THEME['accent']}"
            res.append(row + "\n", style=style)
        return res
    def _draw_wordmark(self):
        text, res = " A T H E N A ", Text()
        for i, c in enumerate(text):
            if (self.frame + i) % 9 == 0: res.append(c, style=f"bold {THEME['primary']} blink")
            else: res.append(c, style=f"bold {THEME['accent']}")
        return res
    def _draw_idle(self): return Text.assemble(self._draw_glyph(), (f"  SYNCHRONIZED  \n", f"dim {THEME['secondary']}"), self._draw_wordmark())
    def _draw_active(self): return Text.assemble(self._draw_glyph(), (f"  ANALYZING...  \n", f"bold {THEME['accent']} blink"), self._draw_wordmark())
    def _draw_startup(self):
        f = self.frame; build = "ATHENA"[:(f // 2) % 7]; gc = "+-X%#!"; glitch = gc[f % len(gc)]
        return Text.assemble((f"\n\n    {glitch}    \n", f"bold {THEME['accent']}"), (f" INIT_CORE: {build} ", f"bold {THEME['primary']}"))
    def _draw_complete(self): return Text.assemble(self._draw_glyph(), (f"  SYTHESIS_COMPLETE  \n", "bold green3"), (f" [ SUCCESS ] ", "bold green3"))

class Header:
    def __init__(self, pet): self.pet = pet
    def __rich__(self):
        grid = Table.grid(expand=True); grid.add_column(ratio=1); grid.add_column(ratio=1); grid.add_column(ratio=1)
        grid.add_row(Text.assemble((f" ATHENA ", f"bold black on {THEME['primary']}"), (f" RESEARCH_FRAMEWORK_4.0 ", f"bold {THEME['primary']} on {THEME['border']}")), Text(self.pet.get_frame(), style=f"bold {THEME['accent']}"), Text.assemble((f"SIGNAL_STRENGTH ", f"dim {THEME['primary']}"), (f"[{datetime.now().strftime('%H:%M:%S')}]", f"bold {THEME['accent']}")))
        return Panel(grid, style=THEME['header_bg'], box=SIMPLE, padding=(0, 1))

class Sidebar:
    def __init__(self, state=None, logo=None, q=0): self.state, self.logo, self.q = state, logo, q
    def __rich__(self):
        if not self.state: return Panel("BOOTING...", title="METRICS")
        table = Table.grid(padding=(0, 1)); table.add_column(style=f"bold {THEME['secondary']}", width=12); table.add_column(justify="right")
        table.add_row("TURN", f"[{len(self.state.visited_queries) + 1}]"); table.add_row("QUERIES", str(len(self.state.visited_queries))); table.add_row("PAPERS", f"{len(self.state.read_papers)}/5"); table.add_row("PHASE", f"[bold {THEME['accent']}]{self.state.current_phase}[/bold {THEME['accent']}]"); table.add_row("QUEUED", str(self.q))
        progress = Progress(BarColumn(bar_width=15, style="grey23", complete_style=THEME['accent']), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), console=console); progress.add_task("p", total=5, completed=len(self.state.read_papers))
        content = Table.grid(); content.add_row(Text("RESEARCH METRICS", style=f"bold {THEME['accent']}")); content.add_row(table); content.add_row(Text("\nINGESTION PROGRESS", style=f"bold {THEME['secondary']}")); content.add_row(progress)
        if self.logo: content.add_row(Text("\n")); content.add_row(Align.center(self.logo.get_frame())); content.add_row(Text("\n"))
        shortcuts = Table.grid(padding=(0, 1)); shortcuts.add_row(Text("Ctrl+C", style=f"bold black on {THEME['accent']}"), Text(" TERMINATE", style=f"dim {THEME['primary']}")); shortcuts.add_row(Text("Ctrl+M", style=f"bold black on {THEME['accent']}"), Text(" SWAP ENGINE", style=f"dim {THEME['primary']}")); shortcuts.add_row(Text("Ctrl+I", style=f"bold black on {THEME['accent']}"), Text(" INPUT_MODE", style=f"dim {THEME['primary']}"))
        content.add_row(Text("SYSTEM CONTROLS", style=f"bold {THEME['secondary']}")); content.add_row(shortcuts)
        return Panel(Align.left(content), border_style=THEME['border'], box=ROUNDED, padding=(1, 2))

class Footer:
    def __init__(self, status="STANDBY", model="gpt-oss-120b", persona="SUPERVISOR"): self.status, self.model, self.persona = status, model, persona
    def __rich__(self): return Text.assemble((f"  {self.persona.upper()}  ", "bold black on bright_white"), (f"  {self.model}  ", f"bold {THEME['primary']} on {THEME['border']}"), (f"  {'>>' if int(time.time())%2==0 else '  '} {self.status}  ", f"bold {THEME['accent']} {THEME['header_bg']}"))

def run_tui():
    load_dotenv()
    if "GROQ_API_KEY" not in os.environ:
        console.print(Panel("[bold red]FATAL: GROQ_API_KEY not detected.[/bold red]\nExport it to your environment.", title="SYSTEM HALTED", border_style="red")); sys.exit(1)
    os.makedirs("workspace/lab", exist_ok=True); os.makedirs("workspace/skills", exist_ok=True)
    parser = argparse.ArgumentParser(); parser.add_argument("--query", type=str); parser.add_argument("--model", type=str, default="openai/gpt-oss-120b"); args = parser.parse_args()
    recent = SESSION_MANAGER.list_recent_sessions(); session_id, topic, query = None, "New Research", args.query
    if not query:
        console.print(Panel(Text(" ATHENA RESEARCH FRAMEWORK 4.0 ", style=f"bold black on {THEME['accent']}"), style=THEME['accent'], box=HEAVY_EDGE))
        if recent:
            for i, s in enumerate(recent[:5]): console.print(f" [bold {THEME['accent']}]0{i+1}[/bold {THEME['accent']}] {s['topic'][:60]} [dim]({s['date'][:10]})[/dim]")
            raw = Prompt.ask("\n[bold white]SELECT STREAM OR [N] NEW[/bold white]", default="N").strip().upper(); choice = "".join(filter(str.isalnum, raw))
            if choice.isdigit() and 1 <= int(choice) <= len(recent):
                session_id, topic, query = recent[int(choice)-1]['id'], recent[int(choice)-1]['topic'], "[RESUMING SESSION]"
    if not query or query == "N":
        query = Prompt.ask(f"\n[bold {THEME['accent']}]RESEARCH SUBJECT[/bold {THEME['accent']}]"); topic = query[:50] + "..." if len(query) > 50 else query
    console.print("\n[bold secondary]NEURAL ENGINES:[/bold secondary]")
    models = {"1": "openai/gpt-oss-120b", "2": "openai/gpt-oss-20b", "3": "openai/gpt-oss-safeguard-20b", "4": "llama-3.3-70b-versatile", "5": "llama-3.1-8b-instant", "6": "meta-llama/llama-prompt-guard-2-86m", "7": "meta-llama/llama-prompt-guard-2-22m", "8": "qwen/qwen3-32b", "9": "whisper-large-v3", "10": "whisper-large-v3-turbo"}
    for k, v in models.items(): console.print(f" {k}. {v}")
    selected_model = models.get(Prompt.ask(f"[bold {THEME['accent']}]ATTACH ENGINE[/bold {THEME['accent']}]", default="1").strip(), "openai/gpt-oss-120b")
    try:
        agent = AthenaAgent(model=selected_model, session_id=session_id, topic=topic)
        if session_id:
            saved = SESSION_MANAGER.load_session(session_id)
            if saved: agent.state, agent.message_history = agent.state.from_dict(saved.get("state", {})), saved.get("messages", [])
    except Exception as e: console.print(f"Init Error: {e}"); sys.exit(1)

    pet, logo, layout = AthenaPet(), PremiumAthenaLogo(), make_layout()
    header, sidebar, footer = Header(pet), Sidebar(agent.state, logo=logo), Footer(model=agent.model)
    body_content, user_queue, switch_requested, chat_requested = [], Queue(), [False], [False]
    keyboard.add_hotkey('ctrl+m', lambda: switch_requested.__setitem__(0, True))
    keyboard.add_hotkey('ctrl+i', lambda: chat_requested.__setitem__(0, True))

    def run_cycle(q):
        nonlocal last_error
        agent_gen = agent.run_conversation(q, max_turns=100)
        for update in agent_gen:
            if switch_requested[0]:
                live.stop(); console.print("\n[bold secondary]NEURAL ENGINES:[/bold secondary]")
                for k, v in models.items(): console.print(f" {k}. {v}")
                agent.model = models.get(Prompt.ask(f"[bold {THEME['accent']}]HOT-SWAP[/bold {THEME['accent']}]", default="1").strip(), agent.model)
                footer.model, footer.status, switch_requested[0] = agent.model, "RECALIBRATED", False; time.sleep(1); live.start()
            if chat_requested[0]:
                live.stop(); new_i = Prompt.ask(f"\n[bold {THEME['accent']}]CHAT::INPUT[/bold {THEME['accent']}]")
                if new_i: user_queue.put(new_i); body_content.append(Panel(f"Directive Queued: {new_i}", border_style="cyan"))
                chat_requested[0] = False; time.sleep(0.5); live.start()
            sidebar.state, footer.model, sidebar.q = agent.state, agent.model, user_queue.qsize()
            layout["input_panel"].update(Panel(Text("CTRL+I TO INTERJECT / TYPE NEXT DIRECTIVE", justify="center", style="dim"), title="[ CHAT_INTERFACE ]", border_style=THEME['secondary']))
            ut = update.get("type")
            if ut == "status":
                pet.update_state("thinking"); logo.set_state("active")
                msg = update.get("message", "PROCESSING"); p = "Explorer"
                if "EXPLORER" in msg: p = "Explorer"
                elif "SYNTHESIZER" in msg: p = "Synthesizer"
                elif "RED_TEAM" in msg: p = "Red Team"
                footer.persona, footer.status = p, msg.upper()
            elif ut == "thought":
                c, ps, l = update.get("content", ""), THEME['primary'], "THOUGHT"
                if footer.persona == "Explorer": ps, l = THEME['explorer'], "EXPLORATION"
                elif footer.persona == "Synthesizer": ps, l = THEME['synthesizer'], "SYNTHESIS"
                elif footer.persona == "Red Team": ps, l = THEME['critic'], "PEER_REVIEW"
                body_content.append(Panel(Markdown(c), title=f"[ {l}::{footer.persona.upper()} ]", border_style=ps, box=ROUNDED, subtitle=f"[dim]TURN {update.get('turn', 'N/A')}[/dim]"))
            elif ut == "tool_start":
                pet.update_state("thinking"); logo.set_state("active"); footer.status = f"EXEC::{update.get('tool_name').upper()}"
            elif ut == "tool_result":
                res, l, name = update.get("result", ""), "DATA", update.get('tool_name').upper()
                if "PYTHON" in name: l = "CODE_EXEC"
                elif "PAPER" in name: l = "PUBLISH"
                body_content.append(Panel(Text(res if len(res) < 500 else res[:500] + "...", style=f"{THEME['primary']}"), title=f"[ {l}::{name} ]", border_style=THEME['secondary'], box=ROUNDED, padding=(0, 1)))
            elif ut == "final_answer":
                pet.update_state("excited"); logo.set_state("complete")
                body_content.append(Panel(Markdown(update.get("content", "") or "No text."), title="[ FINAL_SYNTHESIS ]", border_style=THEME['success'], box=HEAVY_EDGE, padding=(1, 2)))
                footer.status = "CYCLE_COMPLETE"; live.refresh(); time.sleep(2); return True
            elif ut == "error":
                nonlocal last_error; last_error = update.get("message", "FAULT")
                footer.status, logo.state, pet.state = "FAULT_DETECTED", "idle", "error"; live.refresh(); time.sleep(5); return False
            grid = Table.grid(expand=True, padding=(1, 0))
            for item in body_content[-2:]: grid.add_row(item)
            layout["body"].update(grid)
        return False

    last_error = None
    try:
        with Live(layout, refresh_per_second=4, screen=True) as live:
            layout["header"].update(header); layout["sidebar"].update(sidebar); layout["footer"].update(footer)
            footer.status, logo.state = "SYNCHRONIZING...", "startup"; live.refresh(); initialize_rag()
            footer.status, logo.state = "CORE_READY", "idle"; live.refresh(); time.sleep(0.5)
            cq = query if query != "[RESUMING SESSION]" else "Continue analysis."
            while True:
                success = run_cycle(cq)
                if not user_queue.empty():
                    cq = user_queue.get(); body_content.append(Panel(Text(f" {cq} ", style=f"bold {THEME['primary']} on cyan"), title="[ NEXT_ITERATION ]", border_style="cyan", box=HEAVY_EDGE))
                    continue
                live.stop(); console.print(Rule(style=THEME['accent']))
                new_i = Prompt.ask(f"[bold {THEME['accent']}]CHAT::INPUT (Enter to auto-continue)[/bold {THEME['accent']}]").strip()
                if new_i: cq = new_i; body_content.append(Panel(Text(f" {cq} ", style=f"bold {THEME['primary']} on cyan"), title="[ USER_ITERATION ]", border_style="cyan", box=HEAVY_EDGE)); live.start(); continue
                else:
                    if success: cq = "Continue deep research."; live.start(); continue
                    else: break
    except KeyboardInterrupt: sys.exit(0)
    except Exception as e: last_error = str(e)
    if 'last_error' in locals() and last_error:
        console.print("\n"); console.print(Panel(f"[bold red]ERROR:[/bold red] {last_error}", title="[ SYSTEM_FAULT_DETECTED ]", border_style="bright_red", box=HEAVY_EDGE))
    console.print(Rule(style=THEME['border'])); console.print(f"[dim]Session closed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

if __name__ == "__main__": run_tui()
