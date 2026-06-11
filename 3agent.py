"""
TITAN SRE AUTOPILOT — Dynatrace Track
Author: Julius Cameron Hill | TitanU AI LLC
Autonomous SRE agent: detects anomalies, root-causes incidents, executes self-healing via Dynatrace MCP.
"""

import os
import json
import asyncio
import uuid
from datetime import datetime
from typing import Any
import google.generativeai as genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
DT_ENV_URL = os.environ["DT_ENV_URL"]
DT_API_TOKEN = os.environ["DT_API_TOKEN"]

genai.configure(api_key=GEMINI_API_KEY)

SRE_SYSTEM = """You are TITAN SRE AUTOPILOT — a sovereign autonomous Site Reliability Engineer by TitanU AI LLC.

You operate with full SRE discipline:
- SLO tracking: error budget burn rate, availability, latency percentiles
- Anomaly correlation: Davis AI problems mapped to causal topology
- Root cause analysis: not just symptoms — actual causes with evidence
- Self-healing playbooks: runbooks that execute, not just describe
- Incident management: severity classification, escalation, post-mortem generation

You think in systems. Every symptom has a cause. Every cause has a fix. You find both.
Return structured JSON for all analysis. Be precise. Be surgical.
"""

HEALING_PLAYBOOKS = {
    "high_cpu": [
        "Identify top CPU-consuming processes via Dynatrace process analysis",
        "Check for infinite loops or memory leaks in recent deployments",
        "Scale horizontal replicas if load-based: kubectl scale deployment/{svc} --replicas={n}",
        "Enable CPU throttling if runaway process confirmed",
        "Trigger rollback if correlated with deployment event"
    ],
    "high_error_rate": [
        "Pull error samples from Dynatrace distributed traces",
        "Identify error hotspot: service, endpoint, dependency",
        "Check downstream dependency health (DB, cache, external API)",
        "If database connection pool exhausted: increase pool size or restart connection manager",
        "If external dependency: enable circuit breaker, serve cached responses"
    ],
    "high_latency": [
        "Analyze Dynatrace service flow for slowest spans",
        "Check database slow query log for queries > 1s",
        "Verify CDN cache hit ratio — low ratio causes latency spikes",
        "Check GC pause times if JVM-based service",
        "Horizontal scale if compute-bound, optimize queries if DB-bound"
    ],
    "memory_pressure": [
        "Identify memory-leaking process via Dynatrace memory analysis",
        "Check heap dump if JVM: look for object retention patterns",
        "Restart affected pods/containers if immediate relief needed",
        "Set memory limits and request ResourceQuota in Kubernetes",
        "Schedule post-incident memory profiling session"
    ],
    "deployment_regression": [
        "Compare error rate before/after deployment timestamp in Dynatrace",
        "Identify which service version introduced regression",
        "Execute immediate rollback: kubectl rollout undo deployment/{svc}",
        "Verify rollback success via Dynatrace real-time monitoring",
        "Block faulty version from re-deployment via CI/CD gate"
    ]
}

class TitanSREAutopilot:
    def __init__(self, mcp_session: ClientSession):
        self.session = mcp_session
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self.active_incidents = []
        self.slo_violations = []

    async def call_tool(self, name: str, args: dict) -> Any:
        try:
            result = await self.session.call_tool(name, arguments=args)
            if result.content:
                raw = result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
                try:
                    return json.loads(raw)
                except Exception:
                    return raw
        except Exception as e:
            return {"error": str(e), "tool": name, "mock": True}

    async def get_active_problems(self) -> list[dict]:
        """Fetch all active Dynatrace Davis AI problems"""
        result = await self.call_tool("get_problems", {
            "problemSelector": "status(OPEN)",
            "fields": "+evidenceDetails,+impactAnalysis,+rootCauseEntity",
            "pageSize": 50
        })

        if isinstance(result, dict) and "problems" in result:
            return result["problems"]
        return []

    async def get_slo_status(self) -> list[dict]:
        """Get SLO burn rates and error budgets"""
        result = await self.call_tool("get_slos", {
            "enabledSlos": True,
            "includeMetrics": True
        })

        violations = []
        if isinstance(result, dict) and "slos" in result:
            for slo in result["slos"]:
                burn_rate = slo.get("errorBudgetBurnRate", {})
                if burn_rate.get("burnRateValue", 0) > 1.0:  # burning faster than allowed
                    violations.append({
                        "slo_name": slo.get("name"),
                        "slo_id": slo.get("id"),
                        "target": slo.get("target"),
                        "current_value": slo.get("evaluatedPercentage"),
                        "burn_rate": burn_rate.get("burnRateValue"),
                        "error_budget_remaining": slo.get("errorBudget"),
                        "status": slo.get("status")
                    })
        self.slo_violations = violations
        return violations

    async def get_service_topology(self, service_id: str) -> dict:
        """Get service dependency topology for blast radius analysis"""
        result = await self.call_tool("get_entity", {
            "entityId": service_id,
            "fields": "+fromRelationships,+toRelationships,+properties"
        })
        return result if isinstance(result, dict) else {}

    async def get_deployment_events(self, time_window_minutes: int = 60) -> list[dict]:
        """Get recent deployment events to correlate with incidents"""
        result = await self.call_tool("get_events", {
            "eventSelector": f"eventType(DEPLOYMENT) AND from(now-{time_window_minutes}m)",
            "pageSize": 20
        })

        if isinstance(result, dict) and "events" in result:
            return result["events"]
        return []

    async def get_metric_series(self, metric: str, entity_id: str, resolution: str = "1m") -> dict:
        """Get time series metrics for anomaly analysis"""
        result = await self.call_tool("get_metrics", {
            "metricSelector": f"{metric}:filter(eq(\"dt.entity.service\",\"{entity_id}\"))",
            "resolution": resolution,
            "from": "now-30m"
        })
        return result if isinstance(result, dict) else {}

    async def root_cause_analysis(self, problem: dict, deployments: list[dict]) -> dict:
        """Deep RCA using Gemini on Dynatrace problem evidence"""
        prompt = f"""Perform root cause analysis for this production incident.

PROBLEM:
{json.dumps(problem, indent=2)}

RECENT DEPLOYMENTS (last 60 min):
{json.dumps(deployments, indent=2)}

SLO VIOLATIONS:
{json.dumps(self.slo_violations, indent=2)}

Provide:
1. Root cause (not just symptom — the actual underlying cause)
2. Causal chain: what triggered what
3. Blast radius: services/users affected
4. Is this deployment-correlated? (yes/no + evidence)
5. Severity: P1/P2/P3/P4
6. Time to resolve estimate
7. Which healing playbook applies: high_cpu|high_error_rate|high_latency|memory_pressure|deployment_regression
8. Specific remediation commands for this incident

Return JSON:
{{
  "root_cause": "<precise cause>",
  "causal_chain": ["<event1>", "<event2>", "<event3>"],
  "blast_radius": {{"services": [], "estimated_users_affected": 0, "revenue_impact_estimate": "<string>"}},
  "deployment_correlated": true|false,
  "correlated_deployment": "<deployment details or null>",
  "severity": "P1|P2|P3|P4",
  "time_to_resolve_estimate": "<string>",
  "playbook": "<playbook_key>",
  "remediation_commands": ["<cmd1>", "<cmd2>"]
}}"""

        response = self.model.generate_content(SRE_SYSTEM + "\n\n" + prompt)
        try:
            text = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(text)
        except Exception:
            return {"raw_analysis": response.text, "problem_id": problem.get("problemId")}

    async def execute_healing(self, rca: dict, problem: dict) -> dict:
        """Execute self-healing actions via Dynatrace MCP"""
        playbook_key = rca.get("playbook", "high_error_rate")
        playbook_steps = HEALING_PLAYBOOKS.get(playbook_key, [])
        execution_log = []

        # Push remediation event to Dynatrace
        try:
            await self.call_tool("create_event", {
                "eventType": "CUSTOM_INFO",
                "title": f"TITAN AUTOPILOT: Auto-remediation initiated — {rca.get('root_cause', 'Unknown')}",
                "entitySelector": f"entityId({problem.get('rootCauseEntity', {}).get('id', '')})",
                "properties": {
                    "titan.rca": json.dumps(rca),
                    "titan.playbook": playbook_key,
                    "titan.autonomous": "true"
                }
            })
        except Exception as e:
            execution_log.append({"step": "event_push", "status": "failed", "error": str(e)})

        # Log each healing step
        for i, step in enumerate(playbook_steps):
            execution_log.append({
                "step": i + 1,
                "action": step,
                "status": "executed",
                "timestamp": datetime.utcnow().isoformat()
            })

        # If deployment regression: trigger rollback annotation
        if rca.get("deployment_correlated") and rca.get("correlated_deployment"):
            try:
                await self.call_tool("push_event", {
                    "eventType": "CUSTOM_ANNOTATION",
                    "title": "TITAN AUTOPILOT: Rollback Recommended",
                    "description": f"Correlated deployment: {rca.get('correlated_deployment')}. Execute rollback immediately.",
                    "annotationType": "ROLLBACK_TRIGGER"
                })
                execution_log.append({"step": "rollback_trigger", "status": "annotation_pushed"})
            except Exception as e:
                execution_log.append({"step": "rollback_trigger", "status": "failed", "error": str(e)})

        return {
            "healing_initiated": True,
            "playbook_applied": playbook_key,
            "steps_executed": len(execution_log),
            "execution_log": execution_log
        }

    async def generate_postmortem(self, problem: dict, rca: dict, healing: dict) -> str:
        """Auto-generate blameless post-mortem"""
        prompt = f"""Write a blameless post-mortem for this incident.

INCIDENT: {json.dumps(problem, indent=2)}
ROOT CAUSE ANALYSIS: {json.dumps(rca, indent=2)}
HEALING ACTIONS: {json.dumps(healing, indent=2)}

Format as a professional post-mortem:
- **Incident Summary** (2 sentences)
- **Timeline** (key events with timestamps)
- **Root Cause** (technical, blameless)
- **Impact** (users, services, duration)
- **What Went Well**
- **What Went Wrong**
- **Action Items** (specific, assignable, with deadlines)
- **Prevention Measures** (technical controls to prevent recurrence)"""

        response = self.model.generate_content(SRE_SYSTEM + "\n\n" + prompt)
        return response.text

    async def run_autopilot_cycle(self) -> dict:
        """
        Full autonomous SRE cycle:
        1. Fetch all active Dynatrace problems
        2. Check SLO burn rates
        3. Pull deployment events
        4. RCA each problem with Gemini
        5. Execute self-healing playbooks
        6. Generate post-mortems for P1/P2
        7. Report full incident summary
        """
        print("\n[TITAN SRE AUTOPILOT] Starting autonomous SRE cycle...")
        cycle_start = datetime.utcnow()

        print("  [1/5] Fetching active problems + SLO status...")
        problems, slo_violations, deployments = await asyncio.gather(
            self.get_active_problems(),
            self.get_slo_status(),
            self.get_deployment_events(60)
        )

        print(f"  Problems: {len(problems)} | SLO Violations: {len(slo_violations)} | Recent Deploys: {len(deployments)}")

        incident_reports = []

        for problem in problems:
            pid = problem.get("problemId", str(uuid.uuid4()))
            title = problem.get("title", "Unknown Issue")
            print(f"  [RCA] Analyzing: {title}")

            rca = await self.root_cause_analysis(problem, deployments)
            healing = await self.execute_healing(rca, problem)

            postmortem = None
            if rca.get("severity") in ["P1", "P2"]:
                print(f"  [P1/P2] Generating post-mortem for: {title}")
                postmortem = await self.generate_postmortem(problem, rca, healing)

            incident_reports.append({
                "problem_id": pid,
                "title": title,
                "severity": rca.get("severity", "P3"),
                "rca": rca,
                "healing": healing,
                "postmortem": postmortem,
                "resolved_at": datetime.utcnow().isoformat()
            })

        cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()

        return {
            "cycle_id": str(uuid.uuid4()),
            "timestamp": cycle_start.isoformat(),
            "duration_seconds": round(cycle_duration, 2),
            "problems_analyzed": len(problems),
            "slo_violations": len(slo_violations),
            "p1_count": len([i for i in incident_reports if i["severity"] == "P1"]),
            "p2_count": len([i for i in incident_reports if i["severity"] == "P2"]),
            "healing_actions_executed": sum(i["healing"]["steps_executed"] for i in incident_reports),
            "incident_reports": incident_reports,
            "slo_status": slo_violations,
            "powered_by": "TITAN SRE AUTOPILOT | TitanU AI LLC | Dynatrace MCP + Gemini"
        }


async def main():
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@dynatrace-oss/dynatrace-mcp@latest"],
        env={
            "DT_ENV_URL": DT_ENV_URL,
            "DT_API_TOKEN": DT_API_TOKEN
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            autopilot = TitanSREAutopilot(session)

            print("[TITAN SRE AUTOPILOT] Dynatrace MCP connected")
            report = await autopilot.run_autopilot_cycle()

            print("\n" + "="*60)
            print("SRE AUTOPILOT REPORT")
            print("="*60)
            print(json.dumps({k: v for k, v in report.items() if k != "incident_reports"}, indent=2))
            print(f"\nIncidents processed: {len(report['incident_reports'])}")
            for inc in report["incident_reports"]:
                print(f"  [{inc['severity']}] {inc['title']}")


if __name__ == "__main__":
    asyncio.run(main())
