"""
TITAN PIPELINE ORCHESTRATOR — Fivetran Track
Author: Julius Cameron Hill | TitanU AI LLC
Autonomous ELT intelligence agent: monitors pipelines, heals sync failures, validates data quality, forecasts capacity via Fivetran MCP.
"""

import os
import json
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any
import google.generativeai as genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
FIVETRAN_API_KEY = os.environ["FIVETRAN_API_KEY"]
FIVETRAN_API_SECRET = os.environ["FIVETRAN_API_SECRET"]

genai.configure(api_key=GEMINI_API_KEY)

PIPELINE_SYSTEM = """You are TITAN PIPELINE ORCHESTRATOR — a sovereign autonomous data engineer by TitanU AI LLC.

You are a Staff Data Engineer specializing in ELT pipeline reliability and data quality.

Your domains:
- Pipeline Health: Sync failure diagnosis, schema drift detection, connector health scoring
- Data Quality: Anomaly detection, completeness checks, freshness monitoring, referential integrity
- Capacity Intelligence: Row growth forecasting, MAR (Monthly Active Rows) optimization, cost forecasting
- Schema Management: Breaking change detection, downstream impact analysis, migration planning
- Incident Response: Auto-healing sync failures, re-triggering stale connectors, alerting on SLA breaches
- Business Impact: Map data pipeline failures to downstream dashboards, reports, and ML models

You think end-to-end: source → pipeline → destination → consumers. A broken connector is a broken business decision.
Return structured JSON. Quantify everything. Business impact > technical detail.
"""

CONNECTOR_HEALTH_THRESHOLDS = {
    "sync_lag_hours": 4,
    "failure_rate_pct": 5.0,
    "data_volume_drop_pct": 30.0,
    "schema_drift_tables": 3
}

class TitanPipelineOrchestrator:
    def __init__(self, mcp_session: ClientSession):
        self.session = mcp_session
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self.connector_health = {}
        self.schema_alerts = []
        self.quality_issues = []

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
            return {"error": str(e), "tool": name}

    async def get_all_connectors(self) -> list[dict]:
        """List all Fivetran connectors"""
        result = await self.call_tool("list_connectors", {"limit": 100})
        if isinstance(result, dict) and "data" in result:
            return result["data"].get("items", [])
        if isinstance(result, list):
            return result
        return []

    async def get_connector_details(self, connector_id: str) -> dict:
        """Get full connector details including sync history"""
        result = await self.call_tool("get_connector", {"connector_id": connector_id})
        return result if isinstance(result, dict) else {}

    async def get_sync_history(self, connector_id: str, limit: int = 20) -> list[dict]:
        """Get recent sync history for a connector"""
        result = await self.call_tool("get_connector_sync_history", {
            "connector_id": connector_id,
            "limit": limit
        })
        if isinstance(result, dict) and "data" in result:
            return result["data"].get("items", [])
        return []

    async def get_schema(self, connector_id: str) -> dict:
        """Get connector schema configuration"""
        result = await self.call_tool("get_connector_schema_config", {
            "connector_id": connector_id
        })
        return result if isinstance(result, dict) else {}

    async def trigger_sync(self, connector_id: str, force: bool = False) -> dict:
        """Trigger a manual sync"""
        result = await self.call_tool("trigger_connector_sync", {
            "connector_id": connector_id,
            "force": force
        })
        return result if isinstance(result, dict) else {"triggered": True}

    async def get_mar_usage(self) -> dict:
        """Get Monthly Active Rows usage across all connectors"""
        result = await self.call_tool("get_usage_details", {
            "period": datetime.utcnow().strftime("%Y-%m")
        })
        return result if isinstance(result, dict) else {}

    async def score_connector_health(self, connector: dict, sync_history: list[dict]) -> dict:
        """Score a connector's health 0-100"""
        connector_id = connector.get("id")
        status = connector.get("status", {})
        service = connector.get("service", "unknown")

        # Calculate metrics
        successful_syncs = [s for s in sync_history if s.get("status") == "SUCCESSFUL"]
        failed_syncs = [s for s in sync_history if s.get("status") in ["FAILURE", "FAILURE_WITH_TASK"]]
        total = len(sync_history)

        failure_rate = (len(failed_syncs) / max(total, 1)) * 100

        # Calculate sync lag
        last_sync = connector.get("succeeded_at") or connector.get("last_sync")
        sync_lag_hours = 999
        if last_sync:
            try:
                last_dt = datetime.fromisoformat(last_sync.replace("Z", "+00:00").replace("+00:00", ""))
                sync_lag_hours = (datetime.utcnow() - last_dt).total_seconds() / 3600
            except Exception:
                pass

        # Health score calculation
        score = 100
        issues = []

        if failure_rate > CONNECTOR_HEALTH_THRESHOLDS["failure_rate_pct"]:
            deduction = min(40, failure_rate * 2)
            score -= deduction
            issues.append(f"High failure rate: {failure_rate:.1f}%")

        if sync_lag_hours > CONNECTOR_HEALTH_THRESHOLDS["sync_lag_hours"]:
            deduction = min(30, sync_lag_hours * 2)
            score -= deduction
            issues.append(f"Sync lag: {sync_lag_hours:.1f}h")

        if status.get("is_historical_sync"):
            score -= 10
            issues.append("Historical sync in progress")

        if status.get("setup_state") != "connected":
            score -= 50
            issues.append(f"Setup state: {status.get('setup_state')}")

        health = {
            "connector_id": connector_id,
            "service": service,
            "health_score": max(0, round(score, 1)),
            "sync_lag_hours": round(sync_lag_hours, 2),
            "failure_rate_pct": round(failure_rate, 2),
            "total_syncs_analyzed": total,
            "successful_syncs": len(successful_syncs),
            "failed_syncs": len(failed_syncs),
            "issues": issues,
            "status": "CRITICAL" if score < 50 else "DEGRADED" if score < 75 else "HEALTHY"
        }

        self.connector_health[connector_id] = health
        return health

    async def detect_schema_drift(self, connector_id: str, schema: dict) -> list[dict]:
        """Detect schema changes that could break downstream consumers"""
        tables = schema.get("schema", {}) if isinstance(schema.get("schema"), dict) else {}
        drift_alerts = []

        for table_name, table_config in tables.items():
            columns = table_config.get("columns", {})
            for col_name, col_config in columns.items():
                # Detect excluded columns that might be needed downstream
                if not col_config.get("enabled", True):
                    drift_alerts.append({
                        "connector_id": connector_id,
                        "table": table_name,
                        "column": col_name,
                        "drift_type": "column_excluded",
                        "severity": "MEDIUM",
                        "impact": "Column excluded from sync — downstream queries may fail"
                    })

                # Detect type changes (Fivetran stores hashed types)
                if col_config.get("is_primary_key") and not col_config.get("enabled", True):
                    drift_alerts.append({
                        "connector_id": connector_id,
                        "table": table_name,
                        "column": col_name,
                        "drift_type": "primary_key_excluded",
                        "severity": "CRITICAL",
                        "impact": "Primary key excluded — incremental syncs will break"
                    })

        self.schema_alerts.extend(drift_alerts)
        return drift_alerts

    async def diagnose_failures(self, connector: dict, sync_history: list[dict]) -> dict:
        """Use Gemini to diagnose sync failures and recommend fixes"""
        failed_syncs = [s for s in sync_history if s.get("status") in ["FAILURE", "FAILURE_WITH_TASK"]]

        if not failed_syncs:
            return {"diagnosis": "No recent failures", "action_needed": False}

        prompt = f"""Diagnose these Fivetran sync failures and provide specific fixes.

CONNECTOR:
Service: {connector.get('service')}
Destination: {connector.get('destination_id')}
Setup State: {connector.get('status', {}).get('setup_state')}
Sync Frequency: {connector.get('sync_frequency')} minutes

FAILED SYNCS:
{json.dumps(failed_syncs[:5], indent=2, default=str)}

CONNECTOR CONFIG:
{json.dumps({k: v for k, v in connector.items() if k not in ['config']}, indent=2, default=str)}

Diagnose:
1. Root cause of failures
2. Category: auth_expired|schema_change|rate_limit|network|destination_error|api_deprecation|data_type_mismatch
3. Is this auto-recoverable or needs manual intervention?
4. Specific fix steps
5. Prevention: config changes to avoid recurrence

Return JSON:
{{
  "root_cause": "<precise cause>",
  "category": "<category>",
  "auto_recoverable": <bool>,
  "manual_steps_needed": ["<step1>", "<step2>"],
  "fix_config_updates": {{}},
  "prevention": "<what to change in Fivetran config>",
  "estimated_data_loss_rows": <int or 0>,
  "business_impact": "<what breaks if this stays down>"
}}"""

        response = self.model.generate_content(PIPELINE_SYSTEM + "\n\n" + prompt)
        try:
            text = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(text)
        except Exception:
            return {"raw_diagnosis": response.text}

    async def forecast_mar_usage(self, mar_data: dict, connectors: list[dict]) -> dict:
        """Forecast Monthly Active Row usage and cost"""
        prompt = f"""Forecast Fivetran MAR (Monthly Active Rows) usage and costs.

CURRENT MAR USAGE:
{json.dumps(mar_data, indent=2, default=str)}

ACTIVE CONNECTORS ({len(connectors)}):
{json.dumps([{
    'service': c.get('service'),
    'sync_frequency': c.get('sync_frequency'),
    'status': c.get('status', {}).get('setup_state')
} for c in connectors[:20]], indent=2)}

Forecast:
1. Current month MAR projection
2. 3-month growth trajectory
3. Top 3 MAR-consuming connectors to optimize
4. Cost optimization opportunities (frequency reduction, selective sync, etc.)
5. Risk of exceeding MAR tier

Return JSON:
{{
  "current_mar_used": <int>,
  "projected_month_end_mar": <int>,
  "month_over_month_growth_pct": <float>,
  "3_month_forecast": {{"month1": <int>, "month2": <int>, "month3": <int>}},
  "top_mar_consumers": [
    {{"service": "<name>", "estimated_mar": <int>, "optimization": "<recommendation>"}}
  ],
  "cost_optimizations": [
    {{"action": "<action>", "estimated_mar_savings": <int>, "estimated_cost_savings_usd": <float>}}
  ],
  "tier_breach_risk": "LOW|MEDIUM|HIGH",
  "recommended_tier": "<tier recommendation>"
}}"""

        response = self.model.generate_content(PIPELINE_SYSTEM + "\n\n" + prompt)
        try:
            text = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(text)
        except Exception:
            return {"raw_forecast": response.text}

    async def generate_data_quality_report(self, connectors: list[dict], health_scores: list[dict]) -> dict:
        """Generate end-to-end data quality and pipeline health report"""
        critical = [h for h in health_scores if h["status"] == "CRITICAL"]
        degraded = [h for h in health_scores if h["status"] == "DEGRADED"]
        healthy = [h for h in health_scores if h["status"] == "HEALTHY"]

        avg_score = sum(h["health_score"] for h in health_scores) / max(len(health_scores), 1)

        prompt = f"""Generate an executive data pipeline health report.

PIPELINE FLEET SUMMARY:
- Total connectors: {len(connectors)}
- Critical: {len(critical)} | Degraded: {len(degraded)} | Healthy: {len(healthy)}
- Average health score: {avg_score:.1f}/100
- Schema alerts: {len(self.schema_alerts)}

CRITICAL CONNECTORS:
{json.dumps(critical, indent=2, default=str)}

SCHEMA DRIFT ALERTS:
{json.dumps(self.schema_alerts[:10], indent=2)}

Provide:
1. Overall data pipeline health grade (A/B/C/D/F)
2. Top 3 risks to data consumers (dashboards, ML models, reports)
3. SLA breach analysis (which pipelines are outside acceptable lag)
4. 30-day reliability trend assessment
5. Top 5 action items ranked by business impact

Return JSON:
{{
  "health_grade": "A|B|C|D|F",
  "fleet_health_score": <0-100>,
  "consumer_risks": [
    {{"risk": "<description>", "affected_consumers": ["<list>"], "severity": "CRITICAL|HIGH|MEDIUM"}}
  ],
  "sla_breaches": [{{"connector": "<service>", "current_lag_hours": <float>, "sla_hours": <int>}}],
  "reliability_trend": "IMPROVING|STABLE|DEGRADING",
  "action_items": [
    {{"priority": 1, "action": "<specific action>", "connector": "<service>", "business_impact": "<impact>", "effort": "LOW|MEDIUM|HIGH"}}
  ]
}}"""

        response = self.model.generate_content(PIPELINE_SYSTEM + "\n\n" + prompt)
        try:
            text = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(text)
        except Exception:
            return {"raw_report": response.text}

    async def run_full_orchestration_cycle(self) -> dict:
        """
        Full autonomous pipeline orchestration:
        1. Inventory all connectors
        2. Score health of each connector
        3. Detect schema drift
        4. Diagnose failures + auto-trigger recovery syncs
        5. Forecast MAR usage
        6. Generate executive data quality report
        """
        print("\n[TITAN PIPELINE ORCHESTRATOR] Starting full orchestration cycle...")
        cycle_start = datetime.utcnow()

        print("  [1/5] Inventorying Fivetran connectors...")
        connectors, mar_data = await asyncio.gather(
            self.get_all_connectors(),
            self.get_mar_usage()
        )
        print(f"  Found {len(connectors)} connectors")

        health_scores = []
        failure_diagnoses = []
        auto_healed = []

        print("  [2/5] Scoring connector health + detecting schema drift...")
        for connector in connectors[:20]:  # top 20
            cid = connector.get("id")
            service = connector.get("service", "unknown")

            sync_history, schema = await asyncio.gather(
                self.get_sync_history(cid, 20),
                self.get_schema(cid)
            )

            health = await self.score_connector_health(connector, sync_history)
            health_scores.append(health)

            # Schema drift detection
            drift = await self.detect_schema_drift(cid, schema)
            if drift:
                print(f"    ⚠️  Schema drift detected in {service}: {len(drift)} issues")

            # Diagnose failures
            if health["status"] in ["CRITICAL", "DEGRADED"] and health["failed_syncs"] > 0:
                print(f"    🔴 Diagnosing failures: {service}")
                diagnosis = await self.diagnose_failures(connector, sync_history)
                failure_diagnoses.append({"connector": service, "diagnosis": diagnosis})

                # Auto-heal if recoverable
                if diagnosis.get("auto_recoverable"):
                    print(f"    ✅ Auto-triggering recovery sync: {service}")
                    await self.trigger_sync(cid, force=True)
                    auto_healed.append(service)

        print("  [3/5] Forecasting MAR usage...")
        mar_forecast = await self.forecast_mar_usage(mar_data, connectors)

        print("  [4/5] Generating data quality report...")
        quality_report = await self.generate_data_quality_report(connectors, health_scores)

        cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()

        critical_connectors = [h for h in health_scores if h["status"] == "CRITICAL"]
        avg_health = sum(h["health_score"] for h in health_scores) / max(len(health_scores), 1)

        return {
            "cycle_id": str(uuid.uuid4()),
            "timestamp": cycle_start.isoformat(),
            "duration_seconds": round(cycle_duration, 2),
            "connectors_analyzed": len(connectors),
            "critical_connectors": len(critical_connectors),
            "connectors_auto_healed": len(auto_healed),
            "schema_alerts": len(self.schema_alerts),
            "avg_fleet_health_score": round(avg_health, 1),
            "health_grade": quality_report.get("health_grade", "N/A"),
            "tier_breach_risk": mar_forecast.get("tier_breach_risk", "N/A"),
            "auto_healed_connectors": auto_healed,
            "failure_diagnoses": failure_diagnoses,
            "mar_forecast": mar_forecast,
            "quality_report": quality_report,
            "health_scores": sorted(health_scores, key=lambda x: x["health_score"]),
            "powered_by": "TITAN PIPELINE ORCHESTRATOR | TitanU AI LLC | Fivetran MCP + Gemini"
        }


async def main():
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@fivetran/mcp@latest"],
        env={
            "FIVETRAN_API_KEY": FIVETRAN_API_KEY,
            "FIVETRAN_API_SECRET": FIVETRAN_API_SECRET
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            orchestrator = TitanPipelineOrchestrator(session)

            print("[TITAN PIPELINE ORCHESTRATOR] Fivetran MCP connected")
            report = await orchestrator.run_full_orchestration_cycle()

            print("\n" + "="*60)
            print("PIPELINE ORCHESTRATION REPORT")
            print("="*60)
            summary = {k: v for k, v in report.items() if k not in ["health_scores", "failure_diagnoses", "mar_forecast", "quality_report"]}
            print(json.dumps(summary, indent=2))

            print(f"\nFleet Health: {report['avg_fleet_health_score']:.1f}/100 (Grade: {report['health_grade']})")
            print(f"Auto-healed: {', '.join(report['auto_healed_connectors']) or 'None'}")
            print(f"MAR Tier Risk: {report['tier_breach_risk']}")

            print("\nTop Action Items:")
            for item in report["quality_report"].get("action_items", [])[:5]:
                print(f"  [{item.get('priority')}] {item.get('action')} — {item.get('business_impact')}")


if __name__ == "__main__":
    asyncio.run(main())
