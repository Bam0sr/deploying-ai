# Chef Amico

Chef Amico is a cooking chatbot with an Italian-chef style. It helps with recipe lookup, recipe Q&A, and kitchen math.

# IMPORTANT:
To come up with this idea, I brainstormed with my ChatGPT, and I'm hoping that's OK.

## How to Run
If `data/chroma_db/` does not exist, run this one-time setup:

```bash
python -m assignment_chat.embed_recipes
```

then run

```bash
python -m assignment_chat.app
```

This starts the Gradio app at `http://127.0.0.1:7860`.

## Services

### Service 1: TheMealDB API (tools_api.py)

- `search_meal`: looks up a meal by name from TheMealDB.
- `random_meal`: gets one random meal.
- The raw API output is not shown directly; the assistant rewrites it in normal chat style.
- API used: [TheMealDB](https://www.themealdb.com/api.php).

### Service 2: Semantic Recipe Search / RAG (tools_rag.py)

- `search_recipes`: semantic search over embedded recipes using ChromaDB.
- This handles open-ended requests like recommendations and "what can I cook with X?" questions.
- Retrieved recipes are used as context for the final answer.

### Service 3: Kitchen Utilities / Function Calling (tools_utils.py)

- `convert_cooking_units`: converts common units (cups, ml, oz, g, kg, tbsp, tsp, F/C, etc.).
- `adjust_servings`: scales ingredient quantities to a new serving size.
- Both are called by the model as tools.

## Embedding Process

`embed_recipes.py` was used to build the recipe knowledge base:

1. Fetch recipes from TheMealDB A-Z endpoints (595 unique recipes).
2. Format each recipe into a text document.
3. Embed with `all-MiniLM-L6-v2` (`sentence-transformers`).
4. Save vectors with `chromadb.PersistentClient` in `data/chroma_db/`.

Raw recipe data is in `data/recipes.json`.  
Graders should not need to run `embed_recipes.py` again if the persisted Chroma data is included.


## Architecture

The app uses a LangGraph `StateGraph`:

- `call_model` node runs GPT-4o-mini (through the course gateway) with tools bound.
- `ToolNode` runs the selected tool.
- `tools_condition` routes between model/tool steps.
- Chat history is kept through Gradio and passed in each turn.

## Implementation Decisions

- TheMealDB is simple, free, and easy to integrate.
- `all-MiniLM-L6-v2` was used to avoid paid API calls during embedding. I remember people complaining on Slack about this.
- ChromaDB persistence was used to match project requirements.
- Function calling was used for practical utilities (unit conversion + serving scaling).
- Prompt guardrails were added for protected prompt and restricted topics.

## Guardrails

- The system prompt cannot be accessed or revealed by users.
- Restricted topics (cats/dogs, horoscopes/zodiac signs, Taylor Swift) are declined with a polite redirect to cooking.
