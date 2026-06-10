import os
import sys
import subprocess

def setup_athena():
    print("--- ATHENA 4.0: ENVIRONMENT SETUP ---")
    
    # 1. Check API Key
    if "GROQ_API_KEY" not in os.environ:
        print("[!] WARNING: GROQ_API_KEY not found in environment.")
        print("Please set it using: export GROQ_API_KEY='your-key-here'")
    else:
        print("[+] Groq API Key detected.")

    # 2. Create Workspace
    folders = [
        "workspace",
        "workspace/lab",
        "workspace/skills",
        "sessions",
        "examples"
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    print("[+] Research workspaces initialized.")

    # 3. Check Dependencies
    print("[+] Verifying dependencies...")
    try:
        import rich
        import chromadb
        import sentence_transformers
        print("[+] Core neural engines verified.")
    except ImportError:
        print("[!] Missing dependencies. Run: pip install -r requirements.txt")

    print("\n[SUCCESS] ATHENA 4.0 is ready for discovery.")
    print("Execute 'python tui.py' to begin.")

if __name__ == "__main__":
    setup_athena()
