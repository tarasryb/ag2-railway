# ag2-railway

Minimal AG2 + FastMCP server that exposes MCP tools over HTTP:

- Tool: `ask_ag2`
- Tool: `create_sdlc_team`
- Tool: `list_sdlc_teams`
- Path: `/mcp`
- Transport: `http`

## What This Project Does

This app starts a FastMCP server and registers:

- an assistant tool (`ask_ag2`) that forwards prompts to an AG2 `ConversableAgent`
- team-management tools to create and inspect SDLC multi-agent teams

## Prerequisites

- Python 3.12 recommended
- An OpenAI API key

Why Python 3.12:

- The dependency set in this repo is most reliable on 3.12.
- Python 3.10 environments can hit FastMCP/MCP import compatibility issues.

## Quick Start (Recommended: Conda, Python 3.12)

```bash
cd /home/taras/cios/owui-projects/ag2-railway

conda create -y -n ag2railway312 python=3.12
conda run -n ag2railway312 python -m pip install -r requirements.txt
```

Create `.env` in the project root:

```env
OPENAI_API_KEY=replace-me
OPENAI_MODEL=gpt-4o-mini
HOST=127.0.0.1
PORT=8080
MCP_PATH=/mcp
```

Run:

```bash
conda run -n ag2railway312 python app.py
```

## Alternative: Local venv

```bash
cd /home/taras/cios/owui-projects/ag2-railway
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

If you use Python 3.10 in `.venv`, you may encounter FastMCP/MCP incompatibility import errors.

## Verify MCP Endpoint

In another terminal:

```bash
curl -X POST http://127.0.0.1:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

Expected result includes `ask_ag2`, `create_sdlc_team`, and `list_sdlc_teams`.

## Create And Test Agentic Teams

Use these prompts in any MCP client that supports tool calls.

### 1) Create a team

```text
Call create_sdlc_team with:
- model: gpt-4o-mini
- max_rounds: 40
- completion_token: SDLC_COMPLETE

Return team_id, agent_count, agents, and handoffs.
```

Expected result:

- `team_id` is a non-empty UUID-like string
- `agent_count` is `9`
- `agents` contains: `orchestrator`, `requirements_analyst`, `architect`, `designer`, `security`, `developer`, `qa`, `devops`, `maintainer`

### 2) Verify the team exists

```text
Call list_sdlc_teams and verify the team_id returned by create_sdlc_team is present.
Return PASS if present, FAIL otherwise.
```

### 3) Verify handoff topology matches plan

```text
Run this validation and return PASS/FAIL for each rule:

1. orchestrator -> requirements_analyst
2. requirements_analyst -> architect
3. requirements_analyst -> orchestrator
4. architect -> designer
5. architect -> security
6. designer -> developer
7. designer -> qa
8. security -> developer
9. developer -> qa
10. qa -> developer
11. qa -> devops
12. devops -> maintainer
13. maintainer -> architect

Then return an overall PASS/FAIL.
```

Note: current MCP tools validate team creation and topology. Running a business task through a created team manager would require an additional MCP tool that executes the team conversation.

## Notes About Warnings

You may see warnings like:

- `AuthlibDeprecationWarning: authlib.jose module is deprecated`

These are dependency warnings and are typically non-fatal.

## Docker

Build:

```bash
docker build -t ag2-railway .
```

Run:

```bash
docker run --rm -p 8080:8000 \
  -e PORT=8000 \
  -e OPENAI_API_KEY=replace-me \
  -e OPENAI_MODEL=gpt-4o-mini \
  ag2-railway
```

## Project Layout

- `app.py` - FastMCP server + AG2 tool wiring
- `requirements.txt` - runtime and dev dependencies
- `agents/` - agent components and prompts
- `workflow/` - SDLC workflow helpers
- `Dockerfile` - container build definition

# Sample request
```
#ask_ag2 Can you explain the Waterfall Model of SDLC?
```

## Team Creation Sample
```
#create_sdlc_team
model: gpt-4o-mini
max_rounds: 40
completion_token: SDLC_COMPLETE
```

## Team Listing Sample
```
#list_sdlc_teams
```

## Smoke test
```
#ask_ag2
Say "SDLC MCP server is alive" and list the SWEBOK knowledge areas
you cover in one line.
```

## Requirements Analyst
```
#ask_ag2
Business brief:

We need a URL shortener service for internal engineering teams.
Users paste long URLs and get short aliases they can share in
Slack. Expected load: ~500 shortenings/day, ~50k redirects/day.
Must not lose data. No public access — SSO only.

Please produce an SRS.
```