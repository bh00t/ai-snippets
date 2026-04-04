# AI Agent: Hello World (DuckDB Edition)

A provider-agnostic AI agent sandbox. This project demonstrates a modular ReAct (Reason + Act) loop where you define your tools once and can swap out the underlying LLM provider with a single line of code.

This specific variant (`hello-world-duckdb`) upgrades the data layer to use an embedded **DuckDB** SQL database instead of static Python dictionaries, demonstrating how agents can autonomously query real database tables.

### Get your API key

**For Claude (Anthropic):**
1. Go to https://console.anthropic.com
2. Sign up (free — no credit card needed for free tier)
3. Click "API Keys" in left sidebar
4. Click "Create Key"
5. Copy the key — it starts with `sk-ant-...`
   ⚠️ You only see it ONCE. Save it somewhere safe.

**For OpenAI:**
1. Go to https://platform.openai.com/api-keys
2. Sign in → "Create new secret key"
3. Key starts with `sk-...`

**For Gemini:**
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google → "Create API key"
3. Key starts with `AIza...`

| Provider | Adapter Class | API Key Environment Variable |
|---|---|---|
| Google Gemini (New SDK) | `GeminiAdapter()` | `GEMINI_API_KEY` |
| Anthropic Claude | `ClaudeAdapter()` | `ANTHROPIC_API_KEY` |
| OpenAI / GitHub Copilot | `OpenAIAdapter()` | `OPENAI_API_KEY` |

## Installation
Install the required provider SDKs, environment tools, and DuckDB:

```bash
pip install anthropic              # Claude
pip install openai                 # OpenAI / Copilot
pip install google-genai           # Gemini (New SDK)
pip install duckdb                 # SQL Database
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
Because the agent relies on an Abstract Base Class (`LLMAdapter`), switching the brain of your agent requires changing exactly one line. Everything else — your tools, SQL queries, and routing logic — stays identical.

```python
adapter = GeminiAdapter()      # Gemini 2.5 Flash
# adapter = ClaudeAdapter()    # Claude 3.5 Sonnet
# adapter = OpenAIAdapter()    # GPT-4o
```

## Add Your Own Tool (3 Steps)
You can connect the agent to any Python code or database query.

```python
# 1. Write the Python function (Executing DuckDB SQL!)
def get_student_score(student_id: str) -> dict:
    result = conn.execute(
        "SELECT score FROM students WHERE student_id = ?", 
        [student_id]
    ).fetchone()
    
    if not result: return {"error": f"Student {student_id} not found"}
    return {"student_id": student_id, "score": result[0]}

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
hello-world-duckdb/
├── .env                  # Your private API keys (do not commit)
├── .gitignore            # Set to ignore .env
├── hello_world.ipynb     # The main agent architecture with DuckDB integration
└── README.md             # This file
```

## How It Works
The agent utilizes a continuous `While True` loop to reason about the user's prompt, fetch required data from local tools, and synthesize a final answer.

```text
User → Agent.run(question)
        └─ adapter.call() → LLM
                └─ Does the LLM need data?
                        YES → tool_runner() → fetch