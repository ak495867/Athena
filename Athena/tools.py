import json
import os
import urllib.request
import subprocess
from bs4 import BeautifulSoup
import arxiv
import wikipedia
import networkx as nx
import fitz # pymupdf
import requests
import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder
from duckduckgo_search import DDGS
import tempfile
import sys
import traceback
from datetime import datetime

# --- Global Workspace Config ---
WORKSPACE_ROOT = os.path.abspath("workspace")
LAB_DIR = os.path.join(WORKSPACE_ROOT, "lab")
SKILLS_DIR = os.path.join(WORKSPACE_ROOT, "skills")
os.makedirs(LAB_DIR, exist_ok=True)
os.makedirs(SKILLS_DIR, exist_ok=True)

# Shared session pointer for tools
CURRENT_SESSION_ID = "default"

def set_tool_session(session_id: str):
    global CURRENT_SESSION_ID
    CURRENT_SESSION_ID = session_id
    os.makedirs(os.path.join(LAB_DIR, session_id), exist_ok=True)

# --- Initialize RAG Memory Lazily ---
class ResearchMemory:
    def __init__(self):
        self.client = chromadb.Client()
        self.model = None
        self.reranker = None
        self.collection = None

    def _ensure_initialized(self):
        if self.model is None:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            self.collection = self.client.get_or_create_collection("research_docs")

    def add_document(self, doc_id: str, text: str):
        self._ensure_initialized()
        chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
        if not chunks: return
        embeddings = self.model.encode(chunks).tolist()
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        self.collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=[{"source": doc_id}]*len(chunks))

    def query(self, query_text: str, n_results: int = 3) -> str:
        self._ensure_initialized()
        initial_results = self.collection.query(
            query_embeddings=self.model.encode([query_text]).tolist(), 
            n_results=15
        )
        candidates = initial_results['documents'][0]
        if not candidates: return "No relevant information found in memory."
        scores = self.reranker.predict([(query_text, c) for c in candidates])
        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        return "\n\n---\n\n".join([r[0] for r in ranked[:n_results]])

RAG_MEMORY = ResearchMemory()

def initialize_rag() -> str:
    """Explicitly trigger RAG initialization."""
    RAG_MEMORY._ensure_initialized()
    return "RAG Neural Engine & Cross-Encoder Initialized."

# --- ATHENA 4.0: Frontier Research Tools ---

def write_journal_entry(category: str, insight: str) -> str:
    """Log a strategic 'Aha!' moment, dead end, or paradigm shift into the Research Journal."""
    try:
        journal_path = os.path.join(LAB_DIR, CURRENT_SESSION_ID, "journal.md")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(journal_path, "a", encoding="utf-8") as f:
            f.write(f"\n### [{timestamp}] {category.upper()}\n{insight}\n")
        return f"Strategic insight recorded in Research Journal ({category})."
    except Exception as e:
        return f"Error writing journal: {str(e)}"

def create_research_skill(name: str, description: str, python_code: str) -> str:
    """Distill a successful research trajectory into a reusable Python Skill."""
    try:
        filename = f"{name.replace(' ', '_').lower()}.py"
        filepath = os.path.join(SKILLS_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f'"""\nNAME: {name}\nDESCRIPTION: {description}\n"""\n\n{python_code}\n')
        return f"Research skill '{name}' distilled and saved to {filepath}."
    except Exception as e:
        return f"Error creating skill: {str(e)}"

def update_research_plan(new_plan: str, reason: str) -> str:
    """Formally update the research plan due to new discoveries."""
    return f"PLAN EVOLUTION: {reason}. New Plan established: {new_plan}"

def record_finding(finding: str) -> str:
    """Record a research finding into the permanent scientific memory."""
    return f"Finding recorded: {finding}"

def critique_source(source_title: str, critique: str) -> str:
    """Evaluate a source for relevance and quality."""
    return f"Source '{source_title}' evaluated. Decision recorded."

# --- Existing Capability Layer ---

def search_wikipedia(query: str) -> str:
    """Search wikipedia for a given query."""
    try:
        wikipedia.set_user_agent("ATHENA-Research-Agent/4.0 (mailto:athena@example.com)")
        results = wikipedia.search(query, results=3)
        if not results: return "No wikipedia results found."
        summaries = []
        for r in results:
            try:
                page = wikipedia.page(r, auto_suggest=False)
                summaries.append(f"Title: {page.title}\nSummary: {page.summary[:1000]}\nURL: {page.url}")
            except Exception: continue
        return "\n\n".join(summaries) if summaries else "No relevant wikipedia pages found."
    except Exception as e: return f"Error searching wikipedia: {str(e)}"

def search_web(query: str, max_results: int = 3) -> str:
    """Search the web for general information and URLs."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"Title: {r.get('title')}\nURL: {r.get('href')}\nSnippet: {r.get('body')}")
        return "\n\n".join(results) if results else "No web results found."
    except Exception as e: return f"Error searching the web: {str(e)}"

def search_arxiv(query: str, max_results: int = 2) -> str:
    """Search arXiv for papers matching a query."""
    try:
        client = arxiv.Client()
        search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
        results = []
        for paper in client.results(search):
            summary = paper.summary[:800] + "..." if len(paper.summary) > 800 else paper.summary
            results.append(f"Title: {paper.title}\nAuthors: {[a.name for a in paper.authors]}\nSummary: {summary}\nURL: {paper.pdf_url}")
        return "\n\n".join(results) if results else "No papers found."
    except Exception as e: return f"Error reading arxiv: {str(e)}"

def search_semantic_scholar(query: str) -> str:
    """Search Semantic Scholar API for papers and citations."""
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=3&fields=title,authors,year,abstract,citationCount,venue,externalIds"
        response = requests.get(url, timeout=10)
        data = response.json()
        papers = data.get("data", [])
        results = []
        for p in papers:
            results.append(f"Title: {p.get('title')}\nID: {p.get('paperId')}\nYear: {p.get('year')}\nCitations: {p.get('citationCount')}\nAbstract: {p.get('abstract', '')[:500]}...")
        return "\n\n".join(results) if results else "No papers found."
    except Exception as e: return f"Semantic Scholar Error: {str(e)}"

def traverse_citations(paper_id: str, direction: str = "references") -> str:
    """Traverse the citation graph. direction='references' (backward) or 'citations' (forward)."""
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/{direction}?limit=5&fields=title,authors,year,abstract"
        response = requests.get(url, timeout=10)
        data = response.json()
        papers = data.get("data", [])
        results = []
        for p in papers:
            paper_data = p.get("citedPaper") or p.get("citingPaper")
            if paper_data:
                results.append(f"Title: {paper_data.get('title')}\nYear: {paper_data.get('year')}\nAbstract: {paper_data.get('abstract', '')[:400]}...")
        return f"Top 5 {direction}:\n\n" + "\n\n".join(results) if results else f"No {direction} found."
    except Exception as e: return f"Citation Traversal Error: {str(e)}"

def query_document_memory(query: str) -> str:
    """Query the RAG memory for specific details from ingested PDFs/URLs."""
    return RAG_MEMORY.query(query)

def read_pdf(filepath_or_url: str) -> str:
    """Download, parse, and INGEST PDF into RAG memory."""
    try:
        if filepath_or_url.startswith("http"):
            filepath, _ = urllib.request.urlretrieve(filepath_or_url)
        else: filepath = filepath_or_url
        doc = fitz.open(filepath)
        text = "".join([page.get_text() for page in doc])
        RAG_MEMORY.add_document(filepath_or_url, text)
        return f"PDF '{filepath_or_url}' ingested successfully."
    except Exception as e: return f"Error reading PDF: {str(e)}"

def read_url(url: str) -> str:
    """Fetch and INGEST text from a URL into RAG memory."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read()
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup(["script", "style"]): script.extract()
        text = soup.get_text(separator=' ', strip=True)
        RAG_MEMORY.add_document(url, text)
        return f"URL '{url}' ingested successfully."
    except Exception as e: return f"Error reading url: {str(e)}"

def write_file(filepath: str, content: str) -> str:
    """Write text content to the session's lab workspace."""
    try:
        if not filepath: return "Error: Filepath cannot be empty."
        full_path = os.path.abspath(os.path.join(LAB_DIR, CURRENT_SESSION_ID, filepath))
        dir_name = os.path.dirname(full_path)
        if dir_name: os.makedirs(dir_name, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f: f.write(content)
        return f"Successfully wrote to {filepath} in lab workspace."
    except Exception as e: return f"Error writing file: {str(e)}"

def read_file(filepath: str, line_start: int = 1, line_end: int = None) -> str:
    """Read specific lines from a file in the session's lab workspace."""
    try:
        full_path = os.path.abspath(os.path.join(LAB_DIR, CURRENT_SESSION_ID, filepath))
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            start, end = max(0, line_start - 1), line_end if line_end is not None else len(lines)
            return "".join(lines[start:end])
    except Exception as e: return f"Error reading file: {str(e)}"

def run_python(code: str) -> str:
    """Execute Python code in the persistent session lab with full traceback reporting."""
    try:
        # Auto-detect dependencies
        lines = code.split('\n')
        packages = []
        for line in lines:
            if line.startswith('import ') or line.startswith('from '):
                parts = line.split()
                if len(parts) > 1:
                    pkg = parts[1].split('.')[0]
                    if pkg not in sys.modules and pkg not in ['json', 'os', 'sys', 'math', 'datetime', 're', 'traceback', 'random']:
                        packages.append(pkg)
        
        session_lab = os.path.abspath(os.path.join(LAB_DIR, CURRENT_SESSION_ID))
        os.makedirs(session_lab, exist_ok=True)
        
        if packages: 
            subprocess.run([sys.executable, "-m", "pip", "install", *list(set(packages))], capture_output=True, check=False)
        
        script_path = os.path.join(session_lab, "experiment.py")
        with open(script_path, "w", encoding='utf-8') as f: f.write(code)
        
        # Use absolute path for the script to avoid double-concatenation with cwd
        result = subprocess.run([sys.executable, os.path.abspath(script_path)], capture_output=True, text=True, timeout=30, cwd=session_lab)
        
        if result.returncode != 0:
            return f"LAB EXECUTION FAILED:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        return result.stdout if result.stdout else "Lab execution successful (no output)."
    except subprocess.TimeoutExpired: return "Error: Lab execution timed out (30s limit)."
    except Exception as e: return f"LAB CRITICAL FAULT: {str(e)}\n{traceback.format_exc()}"

def save_research_paper(section_title: str, content: str) -> str:
    """Save or append a specific section to the final research_paper.md file."""
    try:
        filename = os.path.abspath(os.path.join(LAB_DIR, CURRENT_SESSION_ID, "research_paper.md"))
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"\n# {section_title}\n\n{content}\n")
        return f"Section '{section_title}' saved to research_paper.md."
    except Exception as e: return f"Error saving paper: {str(e)}"

def clear_current_paper() -> str:
    """Clear the session's research_paper.md."""
    try:
        filename = os.path.abspath(os.path.join(LAB_DIR, CURRENT_SESSION_ID, "research_paper.md"))
        with open(filename, "w", encoding="utf-8") as f: f.write("# Research Paper\n")
        return "Cleared session paper."
    except Exception as e: return f"Error clearing paper: {str(e)}"

def save_research_spec(spec_content: str) -> str:
    """Save the formal research specification to research_spec.md."""
    try:
        filename = os.path.abspath(os.path.join(LAB_DIR, CURRENT_SESSION_ID, "research_spec.md"))
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# RESEARCH SPECIFICATION\n\n{spec_content}\n")
        return "Spec saved to session workspace."
    except Exception as e: return f"Error saving spec: {str(e)}"

def validate_claim(claim: str) -> str:
    """Surgically validate a scientific claim against RAG memory using the Cross-Encoder."""
    try:
        RAG_MEMORY._ensure_initialized()
        initial = RAG_MEMORY.collection.query(query_embeddings=RAG_MEMORY.model.encode([claim]).tolist(), n_results=5)
        candidates = initial['documents'][0]
        if not candidates: return "VALIDATION FAILED: No supporting evidence in RAG."
        scores = RAG_MEMORY.reranker.predict([(claim, c) for c in candidates])
        best_score = max(scores)
        best_match = candidates[scores.argmax()]
        status = "CONFIRMED" if best_score > 0.5 else "UNVERIFIED"
        return f"VALIDATION {status} (Score: {best_score:.2f})\nEvidence: {best_match[:300]}..."
    except Exception as e: return f"Validation Error: {str(e)}"

def complete_research(final_summary: str) -> str:
    """Finalize the research task."""
    return f"MISSION COMPLETE: {final_summary}"

def update_knowledge_graph(node: str, edges: str) -> str:
    """Update concept graph."""
    graph_path = os.path.abspath(os.path.join(LAB_DIR, CURRENT_SESSION_ID, "knowledge_graph.graphml"))
    if os.path.exists(graph_path): G = nx.read_graphml(graph_path)
    else: G = nx.DiGraph()
    G.add_node(node)
    if edges:
        for edge in [e.strip() for e in edges.split(",")]: G.add_edge(node, edge)
    nx.write_graphml(G, graph_path)
    return f"Updated graph with {node} -> {edges}"

TOOLS = [
    {"type": "function", "function": {"name": "save_research_spec", "description": "Save research plan.", "parameters": {"type": "object", "properties": {"spec_content": {"type": "string"}}, "required": ["spec_content"]}}},
    {"type": "function", "function": {"name": "validate_claim", "description": "Validate claim via RAG.", "parameters": {"type": "object", "properties": {"claim": {"type": "string"}}, "required": ["claim"]}}},
    {"type": "function", "function": {"name": "update_research_plan", "description": "Evolve plan.", "parameters": {"type": "object", "properties": {"new_plan": {"type": "string"}, "reason": {"type": "string"}}, "required": ["new_plan", "reason"]}}},
    {"type": "function", "function": {"name": "write_journal_entry", "description": "Log strategic insight.", "parameters": {"type": "object", "properties": {"category": {"type": "string"}, "insight": {"type": "string"}}, "required": ["category", "insight"]}}},
    {"type": "function", "function": {"name": "create_research_skill", "description": "Save reusable skill.", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "description": {"type": "string"}, "python_code": {"type": "string"}}, "required": ["name", "description", "python_code"]}}},
    {"type": "function", "function": {"name": "traverse_citations", "description": "Follow paper trail.", "parameters": {"type": "object", "properties": {"paper_id": {"type": "string"}, "direction": {"enum": ["citations", "references"]}}, "required": ["paper_id", "direction"]}}},
    {"type": "function", "function": {"name": "switch_model", "description": "Hot-swap engine.", "parameters": {"type": "object", "properties": {"new_model": {"type": "string"}}, "required": ["new_model"]}}},
    {"type": "function", "function": {"name": "record_finding", "description": "Log data.", "parameters": {"type": "object", "properties": {"finding": {"type": "string"}}, "required": ["finding"]}}},
    {"type": "function", "function": {"name": "critique_source", "description": "Evaluate methodology.", "parameters": {"type": "object", "properties": {"source_title": {"type": "string"}, "critique": {"type": "string"}}, "required": ["source_title", "critique"]}}},
    {"type": "function", "function": {"name": "search_wikipedia", "description": "Wiki search.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "search_web", "description": "Web search.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "search_arxiv", "description": "ArXiv search.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "search_semantic_scholar", "description": "Scholar search.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "query_document_memory", "description": "Precise RAG query.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "read_url", "description": "Ingest URL.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "read_pdf", "description": "Ingest PDF.", "parameters": {"type": "object", "properties": {"filepath_or_url": {"type": "string"}}, "required": ["filepath_or_url"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read lab file.", "parameters": {"type": "object", "properties": {"filepath": {"type": "string"}, "line_start": {"type": "integer"}, "line_end": {"type": "integer"}}, "required": ["filepath"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Write lab file.", "parameters": {"type": "object", "properties": {"filepath": {"type": "string"}, "content": {"type": "string"}}, "required": ["filepath", "content"]}}},
    {"type": "function", "function": {"name": "run_python", "description": "Execute experiment.", "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}},
    {"type": "function", "function": {"name": "save_research_paper", "description": "Publish section.", "parameters": {"type": "object", "properties": {"section_title": {"type": "string"}, "content": {"type": "string"}}, "required": ["section_title", "content"]}}},
    {"type": "function", "function": {"name": "clear_current_paper", "description": "Wipe draft.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "complete_research", "description": "Final synthesis.", "parameters": {"type": "object", "properties": {"final_summary": {"type": "string"}}, "required": ["final_summary"]}}},
    {"type": "function", "function": {"name": "update_knowledge_graph", "description": "Update graph.", "parameters": {"type": "object", "properties": {"node": {"type": "string"}, "edges": {"type": "string"}}, "required": ["node", "edges"]}}}
]

TOOL_MAP = {
    "initialize_rag": initialize_rag, "save_research_spec": save_research_spec, "validate_claim": validate_claim,
    "update_research_plan": update_research_plan, "write_journal_entry": write_journal_entry,
    "create_research_skill": create_research_skill, "traverse_citations": traverse_citations,
    "switch_model": lambda new_model: None, "record_finding": record_finding,
    "critique_source": critique_source, "search_wikipedia": search_wikipedia, "search_web": search_web,
    "search_arxiv": search_arxiv, "search_semantic_scholar": search_semantic_scholar, "query_document_memory": query_document_memory,
    "read_url": read_url, "read_pdf": read_pdf, "read_file": read_file, "write_file": write_file,
    "save_research_paper": save_research_paper, "clear_current_paper": clear_current_paper,
    "complete_research": complete_research, "run_python": run_python, "update_knowledge_graph": update_knowledge_graph
}
