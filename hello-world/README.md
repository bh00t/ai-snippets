# AI Agent Hello World

A provider-agnostic AI agent sandbox. This project demonstrates a modular ReAct (Reason + Act) loop where you define your tools once and can swap out the underlying LLM provider with a single line of code.

### Get your API key

**For Claude (Anthropic):**
1. Go to https://console.anthropic.com
2. Sign up (free — no credit card needed for free tier)
3. Click "API Keys" in left sidebar
4. Click "Create Key"
5. Copy the key — it starts with  sk-ant-...
   ⚠️  You only see it ONCE. Save it somewhere safe.

**For OpenAI:**
1. Go to https://platform.openai.com/api-keys
2. Sign in → "Create new secret key"
3. Key starts with  sk-...

**For Gemini:**
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google → "Create API key"
3. Key starts with  AIza...

| Provider | Adapter Class | API Key Environment Variable |
|---|---|---|
| Google Gemini (New SDK) | `GeminiAdapter()` | `GEMINI_API_KEY` |
| Anthropic Claude | `ClaudeAdapter()` | `ANTHROPIC_API_KEY` |
| OpenAI / GitHub Copilot | `OpenAIAdapter()` | `OPENAI_API_KEY` |


## Installation
Install the required provider SDKs and environment tools:

```bash
pip install anthropic              # Claude
pip install openai                 # OpenAI / Copilot
pip install google-genai           # Gemini (New SDK)
pip install python-dotenv jupyter  # Environment & Notebook
```

## How to Run
1. Create a `.env` file in the same folder as the notebook and add your API keys:
   ```text
   GEMINI_API_KEY=your_gemini_key_here
   ANTHROPIC_API_KEY=your_claude_key_here
   ```
2. Open `hello_world.ipynb` in Jupyter Notebook or VS Code.
3. Run the cells from top to bottom.

## Switch Providers — One Line
Because the agent relies on an Abstract Base Class (`LLMAdapter`), switching the brain of your agent requires changing exactly one line. Everything else — your tools, questions, and routing logic — stays identical.

```python
adapter = GeminiAdapter()      # Gemini 2.5 Flash
# adapter = ClaudeAdapter()    # Claude 3.5 Sonnet
# adapter = OpenAIAdapter()    # GPT-4o
```

## Add Your Own Tool (3 Steps)
You can connect the agent to any Python code, database, or API.

```python
# 1. Write the Python function
def get_student_score(student_id: str) -> dict:
    return {"student_id": student_id, "score": 87}

# 2. Add it to the Tool Runner (Router)
def tool_runner(name: str, args: dict) -> str:
    fns = {
        "get_student_score": get_student_score,
        # ... other tools
    }
    return json.dumps(fns[name](**args))

# 3. Add the ToolDefinition (The menu for the AI)
ToolDefinition(
    name="get_student_score",
    description="Get exam score for a student.",
    parameters={
        "type": "object",
        "properties": {
            "student_id": {"type": "string", "description": "e.g., S001"}
        },
        "required": ["student_id"],
    },
)
```

## File Structure
```text
ai-snippets/
├── .env                  # Your private API keys (do not commit)
├── .gitignore            # Set to ignore .env
├── hello_world.ipynb     # The main agent architecture and example loop
└── README.md             # This file
```

## How It Works
The agent utilizes a continuous `While True` loop to reason about the user's prompt, fetch required data from local tools, and synthesize a final answer.

```text
User → Agent.run(question)
        └─ adapter.call() → LLM
                └─ Does the LLM need data?
                        YES → tool_runner() → fetch data → send back to LLM → loop repeats
                        NO  → final human-readable answer → return
```

## License
MIT — use freely, share openly.