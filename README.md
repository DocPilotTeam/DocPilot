
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

📂 Project Structure.

autodoc-agent/<br>
│<br>
├── backend/<br>
│   ├── api/               → FastAPI services (webhook, triggers, project mgmt)<br>
│   ├── agents/<br>
│   │    ├── watcher/      → Code watcher agent<br>
│   │    ├── parser/       → AST parsers (Java, JS/TS, SQL)<br>
│   │    ├── kg-builder/   → Knowledge graph builder<br>
│   │    ├── docgen/       → Documentation generator<br>
│   │    ├── diagramgen/   → Diagram generator<br>
│   │    └── publisher/    → Commit/PR automation<br>
│   ├── models/            → Pydantic models + DB models<br>
│   ├── db/                → PostgreSQL(Supabase) + Neo4j integration<br>
│   ├── utils/             → Git operations, LLM utilities, file readers<br>
│   └── [main.py](http://main.py/)            → FastAPI entry<br>
│<br>
├── services/<br>
│    ├── llm-engine/       → Agent orchestration, prompts, workflows<br>
│    └── ast-services/     → JavaParser + Babel parser invocations<br>
│<br>
├── frontend-dashboard/<br>
│    ├── react-app/        → Project dashboard<br>
│    └── components/       → Docs viewer, diagrams preview<br>
│<br>
├── docs/                  → Auto generated docs<br>
│<br>
├── .github/workflows/<br>
│    └── autodoc.yml       → GitHub Actions pipeline<br>
│<br>
└── run_autodoc.py         → Entry file for GitHub Actions runner<br>

Webhook Integration<br>

├── Ngrok  → for Focusing local APIs to the internet<br>
<br>
├── Header and Request from FASTAPI for reciving the headers and Requests to serve on<br>


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


