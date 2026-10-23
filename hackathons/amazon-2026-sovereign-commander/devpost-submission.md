# Devpost submission draft — TitanU Sovereign Agent Commander

**Status:** prepared copy only. The existing Devpost draft #1500852 remains unsubmitted. Must not claim to be a real Alexa integration.

**Hackathon:** Build, Ship, Shape: Amazon Developer Hackathon  
**Primary track:** Alexa+ — simulated Alexa+ experience (explicitly permitted in the official rules)  
**Project name:** TitanU Sovereign Agent Commander  
**Tagline:** One command. Four specialist agents. Real local workflows, live task updates, and verifiable execution receipts.  
**Code:** https://github.com/juliushill42/Titan-Hackathon-Moats/tree/main/hackathons/amazon-2026-sovereign-commander  
**Technology:** Python 3, SQLite, standard-library HTTP, JavaScript, HTML, CSS, optional browser SpeechRecognition.  
**New or existing:** This independent simulation was built October 22, 2026; it draws on earlier TitanU EAISWARM agent-orchestration research without claiming the prior EAISWARM platform was developed during the contest.

## Inspiration

Ordinary people deserve to delegate their work without signing away control of their data, infrastructure, or outcomes. TitanU Sovereign Agent Commander experiments with a local-first interaction: a spoken goal is dispatched through distinct stages, each with an observable result, and every execution produces a verifiable receipt.

## What it does

The app is a functioning **Alexa+-style simulated experience**, with browser speech capture when available and reliable text commands everywhere. Four actual workflows operate on task records persisted in a local SQLite database:

1. **Plan my day:** real priority-based task scheduling into workday timeblocks.
2. **Check launch readiness:** inspect open launch tasks, count explicit blockers, identify the next one to clear.
3. **Draft customer follow-up:** assemble an email draft from outstanding customer work; no email is sent.
4. **Portfolio brief:** aggregate real workstreams into an inspectable executive summary.

Every command passes through an intent router, task reader, specialist executor, and evidence verifier. The transcript displays the stages and offers a downloadable JSON record. Add a task or mark one done; the next execution uses the changed data.

## How we built it

The service is implemented in Python's standard library with threaded HTTP, bound to loopback by default. SQLite WAL mode stores tasks, commands, agent events, and results. The web interface is a responsive HTML/CSS/JavaScript command deck with optional browser speech recognition. The deterministic design keeps actions reproducible, visible, and testable without paid credentials, fabricated device calls, or pretending to run an unavailable LLM. A one-file self-extracting Bootstrap installer and a Dockerfile are supplied.

## Challenges and learning

The design deliberately distinguishes an **Alexa+ simulation** from a live device or Alexa account integration. The open standard MCP-server track would require protocol version 2025-11-25 and Streamable HTTP; this entry claims neither. Browser speech recognition availability varies, so the text-command interface remains first-class. Agent receipts make it possible to check a command's exact data flow instead of taking a chatbot response on faith.

## Accomplishments

- Four working, state-driven agent workflows.
- Persistent task data and JSON audit receipts.
- New tasks flow into subsequent plans and project briefs.
- Unrecognized operations are rejected rather than invented.
- Ten automated tests passed, including real HTTP end-to-end interaction.
- Isolated, new source code and a one-command installer, without changing the existing EAISWARM runtime.

## What's next

The next step is adapting the same auditable execution pattern to standards-compliant MCP Streamable HTTP integrations and carefully permissioned real-world connectors. External actions should remain visible and approval-gated.

## How judges can run it

```bash
python3 app.py
# Open http://127.0.0.1:8787
python3 -m unittest -v test_app
```

Or download the self-contained installer supplied in the artifact and run `bash titanu-amazon-commander-bootstrap.sh start`. The project runs locally and requires no credentials or paid APIs. No external actions or emails are sent.

## Product feedback answers (draft)

**Q1 Which tools, APIs and SDKs were used and for what?** Python standard library HTTP for the local command API; SQLite for transactional task and evidence persistence; browser SpeechRecognition for optional voice capture; native HTML/CSS/JavaScript for the interactive command center. This is the permitted simulated Alexa+ experience path. No live Amazon devices, Alexa credentials, or Amazon SDKs were used.

**Q2 What worked well?** The server ran without installing third-party Python packages. SQLite preserved changes across HTTP calls, and the agent outputs were reproducible from the same stored tasks. The text fallback worked independent of speech recognition availability. Ten automated tests passed, including HTTP API creation, execution, receipt retrieval, and state updates.

**Q3 What needs work?** Browser speech recognition depends on browser capabilities and may use vendor services; an on-device speech engine would better meet strict local-only voice goals. The simulation is not connected to real Amazon devices; direct Alexa integration and live MCP interoperability are future development areas, not demonstrated capabilities.

**Q4 How was onboarding?** Starting from a Python 3.10+ environment, `python3 app.py` exposes the local UI without an API key or cloud account. Six example tasks are populated once on first launch. A reviewer can add tasks, run commands, and inspect receipts from the browser.

**Q5 Would you build with these devices/services again?** We would explore an actual Alexa+ integration, provided a future interface supports explicit user permissions and observable tool execution. This project did not test or benchmark Amazon's live devices or SDKs, so we cannot yet evaluate their reliability.

**AI tools used:** ChatGPT helped design, implement, and test the independent simulation. The shipped runtime itself is deterministic and does not make generative-model calls.

## Three-minute demo storyboard

- 0:00–0:20 — State the problem and clearly identify the Alexa+-style **simulation**.
- 0:20–0:45 — Show persistent task list; add an explicit launch blocker.
- 0:45–1:10 — Speak or type “Alexa, plan my day”; point to generated timeblocks and specialist chain.
- 1:10–1:40 — “Alexa, check launch readiness”; resolve a blocker and rerun to show the live count updating.
- 1:40–2:05 — “Alexa, draft a customer follow-up”; display the unsent draft.
- 2:05–2:35 — “Alexa, give me a portfolio brief”; open a JSON execution receipt.
- 2:35–2:55 — Show tests passing and close with the independent GitHub source path.

## Before final submission

- User approval of official rules, eligibility, and Devpost terms (explicit).
- Choose Individual vs Organization, residence/eligibility checkboxes, and learning classification with user affirmation.
- Grant **private repo** read access to the Devpost/Amazon reviewers listed in the official contest rules or create a separately licensed public repo with explicit IP approval.
- Record and publish a real functioning demo video to public YouTube/Vimeo, under three minutes.
- Review feedback against actual hands-on usage; fill all mandatory custom fields; submit with explicit confirmation.
- Verify Devpost status **Submitted**, not merely draft.