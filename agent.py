import json
import os
import uuid
import re
import time
from typing import List, Dict, Any, Optional, Generator
from groq import Groq
from tools import TOOLS, TOOL_MAP, set_tool_session
from session_manager import SESSION_MANAGER

class ResearchState:
    """Tracks the global state of the research task."""
    def __init__(self):
        self.main_objective: str = ""
        self.visited_queries: List[str] = []
        self.read_papers: List[str] = [] 
        self.findings: List[str] = []
        self.hypotheses: List[str] = []
        self.sections_written: List[str] = []
        self.journal: List[str] = [] 
        self.current_phase: str = "PLANNING" 

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        state = cls()
        for k, v in data.items(): state.__setattr__(k, v)
        return state

class AthenaAgent:
    """ATHENA 4.0: Autonomous Multi-Agent Research Framework."""
    def __init__(self, api_key: str = None, model: str = "openai/gpt-oss-120b", session_id: str = None, topic: str = "New Research"):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key: raise ValueError("GROQ_API_KEY required.")
        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.topic = topic
        self.state = ResearchState()
        self.message_history = []
        set_tool_session(self.session_id)

        self.last_error, self.error_count = None, 0
        self.last_call, self.call_count = None, 0
        self.force_tool_choice = True 

        # Technical Persona descriptions
        self.personas = {
            "EXPLORER": "EXPLORER: Follow citation paths. INGEST 5+ sources. Log insights in Research Journal.",
            "LAB": "LAB: Execute 'experiment.py'. Iteratively resolve tracebacks until success.",
            "SYNTHESIZER": "SYNTHESIZER: Write sections. Use 'validate_claim' for empirical grounding. Finalize with 'complete_research'.",
            "ARCHIVIST": "ARCHIVIST: Prune context trajectories and persist procedural skills."
        }

        # Grounded system prompt
        self.system_prompt = (
            "You are ATHENA 4.0, an Autonomous Research Framework.\n"
            "1. SPECIFICATION: Start with 'save_research_spec.md'.\n"
            "2. RETRIEVAL: Ingest documentation then perform reranked queries.\n"
            "3. VALIDATION: Cross-reference claims against evidentiary support.\n"
            "4. PERSISTENCE: Maintain the Research Journal and distill successful logic into Skills.\n"
            "5. NO HALLUCINATION: Ground all synthesis in RAG memory."
        )

    def _sanitize_message(self, m: Any) -> Dict[str, Any]:
        if hasattr(m, 'model_dump'): d = m.model_dump()
        else: d = m.copy() if isinstance(m, dict) else {}
        allowed = {'role', 'content', 'name', 'tool_calls', 'tool_call_id'}
        s = {k: v for k, v in d.items() if k in allowed and v is not None}
        if 'tool_calls' in s and isinstance(s['tool_calls'], list):
            s['tool_calls'] = [{k: v for k, v in tc.items() if k in {'id', 'type', 'function'}} for tc in s['tool_calls'] if isinstance(tc, dict)]
        return s

    def _get_optimized_messages(self, messages: List[Any]) -> List[Dict[str, Any]]:
        s = [self._sanitize_message(m) for m in messages]
        if len(s) <= 10: return s
        return [s[0], s[1]] + s[-6:]

    def _determine_persona(self, turns: int) -> str:
        lab_path = os.path.abspath(os.path.join("workspace", "lab", self.session_id, "research_spec.md"))
        if not os.path.exists(lab_path): return "EXPLORER"
        if self.state.current_phase == "PRODUCTION": return "SYNTHESIZER"
        if "experiment.py" in str(self.state.visited_queries): return "LAB"
        if len(self.state.read_papers) >= 5 or turns >= 15:
            self.state.current_phase = "PRODUCTION"; return "SYNTHESIZER"
        return "EXPLORER"

    def _extract_failed_text(self, error_msg: str) -> str:
        try:
            search_str = "'failed_generation': '"
            if search_str in error_msg:
                remainder = error_msg.split(search_str, 1)[1]
                content = remainder.rsplit("'}", 1)[0]
                try: return content.encode('utf-8').decode('unicode_escape')
                except: return content
            return ""
        except: return ""

    def _surgical_json_repair(self, raw: str) -> Dict[str, Any]:
        repaired = {}
        keys = ["plan", "content", "filepath", "query", "finding", "spec_content", "claim", "insight", "python_code", "section_title", "new_model"]
        for k in keys:
            match = re.search(f'"{k}"\\s*:\\s*"(.*?)(?<!\\\\)"', raw, re.DOTALL)
            if match:
                val = match.group(1).replace('\\n', '\n').replace('\\"', '"')
                repaired[k] = val
        if not repaired and re.match(r'^[\s"{}]*$', raw): return {}
        return repaired

    def run_conversation(self, user_message: str, max_turns: int = 100) -> Generator[Dict[str, Any], None, None]:
        if not self.message_history:
            self.state.main_objective = user_message
            self.message_history = [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": user_message}]
        else: self.message_history.append({"role": "user", "content": user_message})
        
        turns = 0
        while turns < max_turns:
            turns += 1; persona = self._determine_persona(turns)
            yield {"type": "status", "turn": turns, "message": f"Mode: {persona}"}
            
            journal_text = "\n".join([f"- {j}" for j in self.state.journal[-5:]])
            state_ctx = (f"\n[JOURNAL]\n{journal_text}\n"
                         f"\n[STATE] Papers: {len(self.state.read_papers)}/5 | Goal: {self.state.main_objective[:100]}\n"
                         f"Persona: {self.personas[persona]}\n")
            self.message_history[0] = {"role": "system", "content": self.system_prompt + state_ctx}

            retry_count = 0
            while retry_count < 3:
                try:
                    t_choice = "auto"
                    lab_path = os.path.abspath(os.path.join("workspace", "lab", self.session_id, "research_spec.md"))
                    if not os.path.exists(lab_path) and self.force_tool_choice:
                        t_choice = {"type": "function", "function": {"name": "save_research_spec"}}

                    response = self.client.chat.completions.create(
                        model=self.model, messages=self._get_optimized_messages(self.message_history),
                        tools=TOOLS, tool_choice=t_choice
                    )
                    break
                except Exception as e:
                    err = str(e); retry_count += 1
                    if "rate_limit_exceeded" in err:
                        wait_match = re.search(r"try again in ([\d.]+)m?s", err)
                        wait_time = float(wait_match.group(1)) / 1000 if wait_match else 1.0
                        yield {"type": "status", "turn": turns, "message": f"Rate Limit. Waiting {wait_time}s..."}
                        time.sleep(wait_time + 0.1); continue

                    yield {"type": "status", "turn": turns, "message": "Neural Repairing..."}
                    if err == self.last_error: self.error_count += 1
                    else: self.error_count = 0; self.last_error = err
                    if self.error_count >= 3: yield {"type": "error", "message": f"Fatal Error: {err[:50]}"}; return

                    raw = self._extract_failed_text(err)
                    if not raw: yield {"type": "error", "message": f"Engine Crash: {err[:100]}"}; return
                    
                    rep = self._surgical_json_repair(raw)
                    if rep:
                        name = None
                        for t in TOOLS:
                            if t["function"]["name"] in raw:
                                name = t["function"]["name"]; break
                        if name:
                            yield {"type": "status", "turn": turns, "message": f"Recovered Tool: {name}"}
                            res = TOOL_MAP[name](**rep)
                            did = f"rep_{str(uuid.uuid4())[:8]}"
                            self.message_history.append({"role": "assistant", "content": None, "tool_calls": [{"id": did, "type": "function", "function": {"name": name, "arguments": json.dumps(rep)}}]})
                            self.message_history.append({"role": "tool", "tool_call_id": did, "name": name, "content": str(res)})
                            if name == "save_research_paper": self.state.sections_written.append(rep.get("section_title", "Section"))
                            elif name == "save_research_spec": self.state.current_phase = "ACCUMULATION"
                            break
                    self.message_history.append({"role": "system", "content": "CRITICAL: Last response failed validation. Send ONLY flat JSON for the tool call."})
                    continue

            if retry_count >= 3 and "response" not in locals(): continue
            msg = response.choices[0].message; self.message_history.append(msg)
            if msg.content: yield {"type": "thought", "content": msg.content}
            if msg.tool_calls:
                curr = f"{msg.tool_calls[0].function.name}:{msg.tool_calls[0].function.arguments}"
                if curr == self.last_call: self.call_count += 1
                else: self.call_count = 0; self.last_call = curr
                if self.call_count >= 3:
                    yield {"type": "status", "turn": turns, "message": "Loop Guard: Shifting Strategy..."}
                    self.message_history.append({"role": "system", "content": "CRITICAL: Stop repeating. Move to next task."})
                    continue
                for tc in msg.tool_calls:
                    n, raw_args = tc.function.name, tc.function.arguments
                    try: args = json.loads(raw_args)
                    except: args = self._surgical_json_repair(raw_args)
                    yield {"type": "tool_start", "tool_name": n, "args": json.dumps(args)}
                    if n == "save_research_paper":
                        t = args.get("section_title"); res = TOOL_MAP[n](**args)
                        if t and t not in self.state.sections_written: self.state.sections_written.append(t)
                    elif n == "complete_research":
                        yield {"type": "final_answer", "content": args.get("final_summary", "Complete.")}
                        self._save_state(); return
                    elif n == "write_journal_entry":
                        insight = args.get("insight")
                        if insight: self.state.journal.append(f"{args.get('category')}: {insight}")
                        res = TOOL_MAP[n](**args)
                    else:
                        if n == "search_arxiv": self.state.visited_queries.append(args.get("query", ""))
                        elif n == "read_pdf": self.state.read_papers.append(args.get("filepath_or_url", ""))
                        elif n == "record_finding": self.state.findings.append(args.get("finding", ""))
                        try: res = TOOL_MAP[n](**args) if n in TOOL_MAP else f"Unknown: {n}"
                        except Exception as ex: res = f"FAULT: {str(ex)}"
                    yield {"type": "tool_result", "tool_name": n, "result": str(res)}
                    self.message_history.append({"role": "tool", "tool_call_id": tc.id, "name": n, "content": str(res)})
            elif self.state.current_phase == "PRODUCTION" and len(self.state.sections_written) >= 3:
                yield {"type": "final_answer", "content": "Mission Complete."}; self._save_state(); return
            self._save_state()
        yield {"type": "error", "message": f"Max cycles ({max_turns})."}

    def _save_state(self):
        ser = []
        for m in self.message_history:
            if hasattr(m, 'model_dump'): ser.append(m.model_dump())
            elif isinstance(m, dict): ser.append(m)
        SESSION_MANAGER.save_session(self.session_id, self.topic, self.state.to_dict(), ser)
