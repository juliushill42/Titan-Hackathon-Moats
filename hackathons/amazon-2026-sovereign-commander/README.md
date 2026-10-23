# TitanU Sovereign Agent Commander — Autonomous Mission Fabric

**Amazon Developer Hackathon 2026 — Alexa+ track.** Local autonomous multi-agent execution plus a stateless MCP 2025-11-25 Streamable HTTP endpoint. Built and MIT licensed as a **clean-room, public reference adapter**. Private EAISWARM orchestration, proprietary algorithms, training data, production systems and secrets are **not present, invoked, or required**.

This standalone entry is an Alexa+-style simulation **and** exposes a standards-shaped MCP-over-HTTP tool interface. It does not claim a live Alexa+ device or certified Amazon integration. No cloud services or paid API keys are needed. Work is initiated by explicit instructions; the locally authorized coordination, planning, file generation and verification proceed autonomously.

## Differentiator

**The output is not a chatbot answer.** The user delegates a goal to distinct workers that read persistent local state; concurrent agents independently analyze risks, task dependencies and communications. A coordinator joins the findings, reacts to blockers, creates up to three local remediation tasks **only with explicit authorization**, replans after changes, and materializes a markdown brief, CSV schedule and unsent customer draft. An independent auditing stage verifies every artifact against SHA-256 digests and an ordered SHA-256-linked event trail. Readers can reverify completed missions later. This is **local tamper evidence, not third-party notarization**; a trusted external anchor and digital signatures would be future production additions.

## One-command local launch

```bash
# Repository contains this independent public project. Only this folder needs execution.
git clone https://github.com/juliushill42/Titan-Hackathon-Moats.git
cd Titan-Hackathon-Moats/hackathons/amazon-2026-sovereign-commander
./titanu-amazon-commander-bootstrap.sh
# Web console http://127.0.0.1:8787
```

Requirements: Python 3.10+ (standard library only), browser. No install into system directories. Task, receipt, event and artifact data under `./data`, ignored by Git. For an isolated data directory: `TITANU_DATA_DIR=/tmp/titanu-data ./titanu-amazon-commander-bootstrap.sh`.

### Proof

```bash
./titanu-amazon-commander-bootstrap.sh proof
# 25 unit and HTTP tests: agent fan-out/fan-in, authorization boundaries,
# replanning, artifact hashing, deliberate hash-chain tamper detection,
# stateless MCP handshake and tools/list, actual mission execution.
```

## Demo scenario

1. Open the cinematic mission console; existing user-entered tasks persist in SQLite.
2. Set the goal: "Prepare TitanU launch: assess blockers, coordinate a work plan, prepare customer outreach and verify outputs."
3. Keep **local remediation writes disabled** to show the default no-write policy; launch the autonomous mission.
4. Observe Scope Scout → concurrent Risk Analyst / Timeline Planner / Customer Comms → Remediation Agent → Artifact Builder → Independent Auditor.
5. Download the *actual* generated mission brief, CSV schedule, and unsent customer draft; open the integrity proof with event-chain head and SHA-256 results.
6. Enable local remediation writes and repeat: up to three derived tasks are written to SQLite and the plan is automatically recalculated from the new state. No external calls or messages are made.
7. Demonstrate MCP handshake and `tools/call` against the same engine.

## MCP 2025-11-25 Streamable HTTP

Stateless JSON-RPC at **`POST http://127.0.0.1:8787/mcp`** supports `initialize`, `notifications/initialized`, `tools/list`, and `tools/call`. Requests can include `Accept: application/json, text/event-stream`. MCP transports may return JSON bodies instead of SSE; this implementation uses JSON responses. `GET /mcp` streaming is not implemented (optional for server-to-client messages in this stateless example). Tools:

- `titanu_mission_launch` — validated goal and optional `allow_local_writes` (false by default)
- `titanu_mission_status` — mission telemetry, steps, artifacts, event chain
- `titanu_mission_verify` — hash-chain/artifact integrity proof
- `titanu_task_list` — limited read-only context

```bash
curl -fsS http://127.0.0.1:8787/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"hackathon-auditor","version":"1.0"}}}'
curl -fsS http://127.0.0.1:8787/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  --data '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
```

## Security and scope

- The HTTP service binds to `127.0.0.1` by default; **no remote authentication** is provided, so do not expose it to the Internet. A separate authenticated ingress is required before remote use.
- MCP rejects cross-origin requests from non-loopback browser origins; local HTTP calls are expected from the same machine.
- All database mutations use parameterized statements. UI content is escaped. JSON request body is capped at 32 KiB. Mission goal is capped at 500 chars. Artifact output is allowlisted with non-traversing basenames, capped at 512 KiB each and limited to 3 per run.
- No shell execution, no remote code execution, no internet requests, no payment operations, no real email sending, and no autonomous work outside the user-authorized local workspace.
- Evidence is **local** SHA-256 chaining, not cryptographic authorship signatures or globally independent timestamp proof. If an attacker controls both disk and database, they may rewrite all history; the source does not make stronger guarantees.
- Voice dictation uses optional browser speech capability which may rely on a browser vendor. Typed input and command execution do not require a voice service.
- Autonomy is deterministic goal decomposition, bounded specialists, concurrent work and evidence-informed replanning — **not a claim of generalized LLM reasoning or self-evolving agents**.

## Source/IP boundary

This directory is MIT-licensed independent contest code. It communicates through explicit data and MCP tool contracts, rather than revealing private EAISWARM swarm orchestration implementation. Do not add production credentials, internal service discovery, private network addresses, or proprietary model weights to this public repo. Private assets stay in their separate private repository.

Copyright (c) 2026 Julius Cameron Hill / Titan Universal AI LLC.