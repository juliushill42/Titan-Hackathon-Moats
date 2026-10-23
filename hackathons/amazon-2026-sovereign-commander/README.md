# TitanU Sovereign Agent Commander

**Amazon Developer Hackathon (2026) — Alexa+ simulated-experience entry**

A working, local-first, Alexa+-style *simulation* demonstrating user intent translated into auditable specialist-agent workflows. Independent TitanU project, **not an Amazon-certified Alexa skill, not live Alexa integration, and not an LLM-connected assistant**. The four specialists execute real deterministic operations over a persistent SQLite task store. No claimed external calls or email sending.

## Run

```bash
python3 app.py
# Open http://127.0.0.1:8787
python3 -m unittest -v test_app
```

No dependencies beyond Python 3.10+; Chromium/Chrome supports optional speech recognition on compatible systems. Text command works everywhere. Data lives in `./data/commander.sqlite`; it is generated on first launch and persists across restarts. `TITANU_DATA_DIR` relocates the database. `PORT` selects the HTTP port. The server binds loopback by default and is **not authenticated for deployment on the public Internet**.

## Demo (less than 3 minutes)

1. Show the command deck and six seeded tasks.
2. Speak or type **"Alexa, plan my day"**. Verify dynamically generated time blocks and the 4-agent receipt.
3. Mark a launch blocker done, then **"Alexa, check launch readiness"**. Show status changing with persisted data.
4. **"Alexa, draft a customer follow-up"**. Show email body assembled from stored customer tasks. No email leaves the machine.
5. Add a new task. **"Alexa, give me a portfolio brief"**. Confirm the new workstream appears and open the saved JSON receipt.

## Agent execution

| Stage | Real behavior |
|---|---|
| Intent Router | Deterministic intent classification; unsupported requests rejected |
| Task Reader | Loads real open tasks from SQLite (WAL mode) |
| Specialist Agent | Prioritized schedule, release blocker audit, customer draft, or portfolio brief |
| Evidence Verifier | Persists tool outcome plus agent event chain; downloadable receipt |

Commands and task state are written under `data/`, which should not be committed. The system intentionally does not send email or connect to any Alexa account, Ring device, or paid cloud service. Use the ***simulated Alexa+ experience*** category rather than the independent MCP-server implementation category; this repo does not claim MCP 2025-11-25 compliance.

## Contribution and evolution

Created during the 2026 Amazon Developer Hackathon as a new independent functional demonstration drawing on earlier TitanU agent-orchestration work. Source, live persistent workflows, task UI, deterministic agent chain, and receipt architecture are all included here. Cite source commit dates when describing what was made during the submission period.

## Security

- Default listening address `127.0.0.1` is deliberate.
- All SQL writes use parameter binding, all HTML user content is escaped, and task updates are ID-scoped.
- Strict route mapping, content size limit, request validation, nosniff, CSP, no-referrer and no-cache headers.
- Do **not** expose publicly as-is; put behind authenticated access before remote hosting.
- The project is a workflow demonstration; never present its generated drafts or local task audits as actions on external systems.

## Testing

`python3 -m unittest -v test_app`

## Intellectual property

Copyright © 2026 Julius Hill / Titan Universal AI. Distributed under the MIT License. See `LICENSE`.