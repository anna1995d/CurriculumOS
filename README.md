# CurriculumOS

An AI-powered course development pipeline with a visible, interactive agent graph. Specialized sub-agents handle research, drafting, and review — with explicit autonomy levels and human-in-the-loop checkpoints at every critical decision.

## How it works

You submit a course brief. The system builds a task graph and runs a multi-agent pipeline:

1. **Research** — maps key concepts, subtopics, and prerequisite chains for the topic
2. **Audience Analysis** — profiles the target audience and recommends engagement strategies *(human confirms)*
3. **Catalog Search** — checks for overlap with existing courses; blocks the outline if overlap > 70%
4. **Outline Generator** — produces a structured module-by-module outline *(human approves)*
5. **Script Drafting** — writes verbatim instructor scripts for each module in parallel
6. **Review Layer** — technical, pedagogy, and business reviewers run in parallel per module
7. **Conflict Resolution** — merges reviewer agreement; surfaces disagreements for human decision *(human decides)*

Every agent action is logged to an audit trail visible in the UI.

## Autonomy levels

| Level | Meaning | Examples |
|-------|---------|---------|
| FULL | Acts and logs, no checkpoint | Research, Catalog |
| DRAFT | Produces output, human must approve | Outline, Scripts |
| RECOMMEND | Recommends, human confirms | Audience Analysis |
| ADVISORY | Advises, non-blocking | Reviewers |
| ESCALATE | Surfaces conflict, human decides | Conflict Resolution |

## Tech stack

- **Backend:** Python, FastAPI, SQLite (aiosqlite), OpenAI GPT-4o-mini
- **Frontend:** React 19, React Flow (@xyflow/react), Tailwind CSS, Vite

## Getting started

### Prerequisites

- Python 3.11+
- Node.js 18+
- An OpenAI API key

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:

```
OPENAI_API_KEY=sk-...
```

Start the server:

```bash
.venv/bin/uvicorn main:app --reload
# Runs on http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

Open `http://localhost:5173` in your browser.

## Project structure

```
backend/
├── main.py                  FastAPI app and API routes
├── orchestrator.py          Graph generation and async execution engine
├── models.py                Pydantic models and enums
├── database.py              SQLite schema and async CRUD
├── events.py                Per-node asyncio events for human-in-the-loop waits
├── ws_manager.py            WebSocket broadcast manager
├── dummy_catalog.py         Sample course catalog (6 courses)
├── config.py                Configuration (DB path, model, API key)
└── agents/
    ├── base.py              BaseAgent with LLM calling and logging
    ├── research.py
    ├── audience.py
    ├── catalog.py
    ├── outline.py
    ├── script.py
    ├── review_technical.py
    ├── review_pedagogy.py
    ├── review_business.py
    └── conflict.py

frontend/src/
├── App.jsx                  Root layout (3-panel: log | graph | detail)
├── hooks/usePipeline.js     WebSocket + REST state management
├── utils/graphLayout.js     React Flow node positioning
└── components/
    ├── BriefWizard.jsx      Multi-step course brief form
    ├── PipelineGraph.jsx    Live agent graph visualization
    ├── NodeDetail.jsx       Node inspector with approve/edit/decide actions
    ├── DecisionLog.jsx      Collapsible audit log
    ├── ResultsView.jsx      Final course output viewer
    ├── ChatPanel.jsx        Per-node chat overlay
    ├── ConflictCard.jsx     Conflict resolution UI
    └── ReviewPanel.jsx      Review summary
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/brief` | Submit a course brief, returns `pipeline_id` |
| GET | `/api/pipeline/{id}` | Full pipeline state |
| POST | `/api/pipeline/{id}/start` | Start pipeline execution |
| POST | `/api/node/{id}/approve` | Approve a node's output |
| POST | `/api/node/{id}/edit` | Edit and approve a node's output |
| POST | `/api/node/{id}/decide` | Make a decision on a conflict node |
| GET | `/api/log/{pipeline_id}` | Full decision audit log |
| GET | `/api/catalog` | Existing course catalog |
| WS | `/ws/pipeline/{id}` | Live pipeline updates |
