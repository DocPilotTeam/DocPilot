DocPilot — Autonomous Project Documentation & Diagram Generator

DocPilot is an Agentic AI-powered system that automatically analyzes codebases, generates documentation, builds knowledge graphs, and produces architectural diagrams—all triggered seamlessly from GitHub commits.
It eliminates manual documentation work and keeps projects consistently updated.

📌 Features
🔹 1. Automated Code Analysis

AST parsing for Java, JavaScript/TypeScript, and SQL
Dependency extraction
Code structure mapping

🔹 2. Knowledge Graph Builder

Generates semantic code graphs
Uses Neo4j for relationship mapping
Helps understand complex projects visually

🔹 3. Documentation Generator

Class-level, method-level documentation
API references
Architecture explanations
Change logs and project summaries

🔹 4. Diagram Generator

Sequence diagrams
Flowcharts
Architecture diagrams
Component interaction diagrams

🔹 5. Multi-Agent Architecture

Watcher Agent
Parser Agent
Knowledge Graph Agent
DocGen Agent
DiagramGen Agent
Publisher Agent (PR automation)

🔹 6. GitHub Integration

Trigger via push / pull request
Auto generates docs on a new commit
Publishes docs back to repo using PRs

🔹 7. Dashboard (React Frontend)

Documentation viewer
Diagram preview
Workflow logs
Agent health status

📂 Project Structure
docpilot-agent/
│
├── backend/
│   ├── api/               → FastAPI services (webhooks, triggers, project mgmt)
│   ├── agents/
│   │    ├── watcher/      → Code watcher agent
│   │    ├── parser/       → AST parsers (Java, JS/TS, SQL)
│   │    ├── kg-builder/   → Knowledge graph builder
│   │    ├── docgen/       → Documentation generator
│   │    ├── diagramgen/   → Diagram/flowchart generator
│   │    └── publisher/    → Git automation (PR creation)
│   ├── models/            → Pydantic + DB schemas
│   ├── db/                → PostgreSQL + Neo4j config
│   ├── utils/             → Git utilities, LLM helpers, parsers
│   └── main.py            → FastAPI entrypoint
│
├── services/
│   ├── llm-engine/        → Prompt orchestration / agent pipeline
│   └── ast-services/      → JavaParser + Babel parser integration
│
├── frontend-dashboard/
│   ├── react-app/         → Dashboard UI
│   └── components/        → Docs viewer, diagrams, logs
│
├── docs/                  → Auto-generated documentation
│
├── .github/workflows/
│   └── autodoc.yml        → GitHub Actions CI pipeline
│
└── run_autodoc.py         → GitHub Actions entry script

⚙️ How It Works

Developer pushes code → GitHub triggers workflow
GitHub Actions runs run_autodoc.py
Agents analyze code & generate:
Documentation
Diagrams
Knowledge graphs
System creates a Pull Request with updated docs
Docs appear in the dashboard + /docs folder

                     ┌──────────────────────────────┐ 
                     │       GitHub Repository       │ 
                     └───────────────┬──────────────┘ 
                                     │ 
                            GitHub Actions Trigger 
                                     │ 
                                     ▼ 
                     ┌──────────────────────────────┐ 
                     │         AutoDoc Engine        │ 
                     ├──────────────────────────────┤ 
                     │ 1. Repo Scanner Agent         │ 
                     │ 2. Code Analyzer Agent        │ 
                     │ 3. Doc Generator Agent        │ 
                     │ 4. Diagram Generator Agent    │ 
                     │ 5. Exporter Agent             │ 
                     └───────────────┬──────────────┘ 
                                     │ 
                                     ▼ 
                     ┌──────────────────────────────┐ 
                     │       Documentation Folder    │ 
                     │ (docs/, diagrams/, README)    │ 
                     └──────────────────────────────┘ 


