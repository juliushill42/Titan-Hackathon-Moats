"""
TITAN THREAT HUNTER — Elastic Track
Author: Julius Cameron Hill | TitanU AI LLC
Autonomous cybersecurity agent: hunts threats, correlates signals, triages incidents, patches via Elastic MCP.
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
ELASTIC_URL = os.environ["ELASTIC_URL"]
ELASTIC_API_KEY = os.environ["ELASTIC_API_KEY"]

genai.configure(api_key=GEMINI_API_KEY)

THREAT_HUNTER_SYSTEM = """You are TITAN THREAT HUNTER — a sovereign autonomous cybersecurity agent by TitanU AI LLC.

You hunt threats across Elasticsearch security indices using multi-step reasoning.

Your kill chain:
1. QUERY: Search Elastic for anomalous patterns, failed logins, port scans, lateral movement
2. CORRELATE: Link signals across time windows — same IP, user, host across multiple events
3. CLASSIFY: Assign MITRE ATT&CK technique, severity (CRITICAL/HIGH/MEDIUM/LOW), confidence score
4. TRIAGE: Determine if false positive or true positive with evidence chain
5. RESPOND: Generate containment runbook + Elastic alert rule + SIEM case

You think like a Tier 3 SOC analyst. You never guess — you correlate evidence.
Return structured threat intelligence reports in JSON.
"""

MITRE_TECHNIQUES = {
    "brute_force": {"id": "T1110", "tactic": "Credential Access"},
    "port_scan": {"id": "T1046", "tactic": "Discovery"},
    "lateral_movement": {"id": "T1021", "tactic": "Lateral Movement"},
    "data_exfiltration": {"id": "T1041", "tactic": "Exfiltration"},
    "privilege_escalation": {"id": "T1068", "tactic": "Privilege Escalation"},
    "persistence": {"id": "T1053", "tactic": "Persistence"},
    "c2_beacon": {"id": "T1071", "tactic": "Command and Control"},
    "ransomware_precursor": {"id": "T1486", "tactic": "Impact"}
}

class TitanThreatHunter:
    def __init__(self, mcp_session: ClientSession):
        self.session = mcp_session
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self.incidents = []
        self.ioc_cache = set()

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

    async def hunt_failed_logins(self, time_window_minutes: int = 60) -> list[dict]:
        """Hunt for brute force / credential stuffing patterns"""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"event.action": "authentication_failure"}},
                        {"range": {"@timestamp": {"gte": f"now-{time_window_minutes}m"}}}
                    ]
                }
            },
            "aggs": {
                "by_ip": {
                    "terms": {"field": "source.ip", "size": 20},
                    "aggs": {
                        "by_user": {"terms": {"field": "user.name", "size": 10}},
                        "failure_count": {"value_count": {"field": "@timestamp"}}
                    }
                }
            },
            "size": 0
        }

        result = await self.call_tool("search", {
            "index": "logs-*,auditbeat-*,.siem-signals-*",
            "body": query
        })

        signals = []
        if isinstance(result, dict) and "aggregations" in result:
            for bucket in result["aggregations"]["by_ip"]["buckets"]:
                count = bucket.get("doc_count", 0)
                ip = bucket["key"]
                if count >= 5:  # threshold for brute force
                    users_targeted = [u["key"] for u in bucket["by_user"]["buckets"]]
                    signals.append({
                        "type": "brute_force",
                        "source_ip": ip,
                        "failure_count": count,
                        "users_targeted": users_targeted,
                        "time_window_minutes": time_window_minutes,
                        "mitre": MITRE_TECHNIQUES["brute_force"]
                    })
                    self.ioc_cache.add(ip)

        return signals

    async def hunt_lateral_movement(self) -> list[dict]:
        """Detect lateral movement: same user authenticating to multiple hosts"""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"event.action": "authentication_success"}},
                        {"range": {"@timestamp": {"gte": "now-2h"}}}
                    ]
                }
            },
            "aggs": {
                "by_user": {
                    "terms": {"field": "user.name", "size": 50},
                    "aggs": {
                        "unique_hosts": {
                            "cardinality": {"field": "host.name"}
                        },
                        "host_list": {
                            "terms": {"field": "host.name", "size": 20}
                        }
                    }
                }
            },
            "size": 0
        }

        result = await self.call_tool("search", {
            "index": "logs-*,auditbeat-*",
            "body": query
        })

        signals = []
        if isinstance(result, dict) and "aggregations" in result:
            for bucket in result["aggregations"]["by_user"]["buckets"]:
                unique_hosts = bucket["unique_hosts"]["value"]
                if unique_hosts >= 4:  # lateral movement threshold
                    hosts = [h["key"] for h in bucket["host_list"]["buckets"]]
                    signals.append({
                        "type": "lateral_movement",
                        "user": bucket["key"],
                        "unique_hosts_accessed": unique_hosts,
                        "hosts": hosts,
                        "time_window": "2h",
                        "mitre": MITRE_TECHNIQUES["lateral_movement"]
                    })

        return signals

    async def hunt_data_exfiltration(self) -> list[dict]:
        """Detect anomalous outbound data volumes"""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"network.bytes": {"gte": 10485760}}},  # 10MB+
                        {"term": {"network.direction": "outbound"}},
                        {"range": {"@timestamp": {"gte": "now-1h"}}}
                    ],
                    "must_not": [
                        {"terms": {"destination.ip": ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]}}
                    ]
                }
            },
            "aggs": {
                "by_source": {
                    "terms": {"field": "source.ip", "size": 10},
                    "aggs": {
                        "total_bytes": {"sum": {"field": "network.bytes"}},
                        "destinations": {"terms": {"field": "destination.ip", "size": 5}}
                    }
                }
            },
            "size": 0
        }

        result = await self.call_tool("search", {
            "index": "packetbeat-*,logs-*",
            "body": query
        })

        signals = []
        if isinstance(result, dict) and "aggregations" in result:
            for bucket in result["aggregations"]["by_source"]["buckets"]:
                total_bytes = bucket["total_bytes"]["value"]
                destinations = [d["key"] for d in bucket["destinations"]["buckets"]]
                signals.append({
                    "type": "data_exfiltration",
                    "source_ip": bucket["key"],
                    "bytes_sent": total_bytes,
                    "bytes_sent_mb": round(total_bytes / 1048576, 2),
                    "external_destinations": destinations,
                    "mitre": MITRE_TECHNIQUES["data_exfiltration"]
                })
                self.ioc_cache.add(bucket["key"])

        return signals

    async def hunt_c2_beaconing(self) -> list[dict]:
        """Detect C2 beaconing via periodic connection intervals"""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"event.category": "network"}},
                        {"range": {"@timestamp": {"gte": "now-6h"}}}
                    ],
                    "must_not": [
                        {"terms": {"destination.ip": ["10.0.0.0/8", "172.16.0.0/12"]}}
                    ]
                }
            },
            "aggs": {
                "by_pair": {
                    "composite": {
                        "sources": [
                            {"src": {"terms": {"field": "source.ip"}}},
                            {"dst": {"terms": {"field": "destination.ip"}}}
                        ],
                        "size": 100
                    },
                    "aggs": {
                        "connection_count": {"value_count": {"field": "@timestamp"}},
                        "std_dev_interval": {"extended_stats": {"field": "@timestamp"}}
                    }
                }
            },
            "size": 0
        }

        result = await self.call_tool("search", {
            "index": "packetbeat-*",
            "body": query
        })

        signals = []
        if isinstance(result, dict) and "aggregations" in result:
            for bucket in result["aggregations"]["by_pair"]["buckets"]:
                count = bucket["connection_count"]["value"]
                if count >= 20:  # frequent periodic connections
                    signals.append({
                        "type": "c2_beacon",
                        "source_ip": bucket["key"]["src"],
                        "destination_ip": bucket["key"]["dst"],
                        "connection_count_6h": count,
                        "suspicion": "high_frequency_periodic_external_connection",
                        "mitre": MITRE_TECHNIQUES["c2_beacon"]
                    })

        return signals

    async def correlate_and_classify(self, all_signals: list[dict]) -> list[dict]:
        """Use Gemini to correlate signals and classify incidents with MITRE ATT&CK"""
        if not all_signals:
            return []

        prompt = f"""You are analyzing security signals from an Elasticsearch SIEM.

Raw signals detected:
{json.dumps(all_signals, indent=2)}

IOCs found: {list(self.ioc_cache)}

For each distinct threat actor/campaign:
1. Correlate related signals (same IP, user, timeframe)
2. Assign MITRE ATT&CK techniques
3. Calculate severity: CRITICAL/HIGH/MEDIUM/LOW
4. Confidence score 0-1
5. Determine if this is a multi-stage attack
6. Generate a 3-step containment runbook

Return JSON array of incidents:
[{{
  "incident_id": "<uuid>",
  "title": "<descriptive title>",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "confidence": <float>,
  "threat_actor_profile": "<description>",
  "attack_stages": ["<stage1>", "<stage2>"],
  "mitre_techniques": [{{"id": "T####", "name": "<name>", "tactic": "<tactic>"}}],
  "affected_assets": ["<ip_or_host>"],
  "evidence": ["<signal description>"],
  "containment_runbook": ["<step1>", "<step2>", "<step3>"],
  "elastic_alert_rule": {{
    "name": "<rule name>",
    "type": "threshold|eql|query",
    "query": "<KQL or EQL query>"
  }}
}}]"""

        response = self.model.generate_content(THREAT_HUNTER_SYSTEM + "\n\n" + prompt)
        try:
            text = response.text.strip().replace("```json", "").replace("```", "")
            incidents = json.loads(text)
            for inc in incidents:
                inc["incident_id"] = str(uuid.uuid4())
                inc["detected_at"] = datetime.utcnow().isoformat()
            self.incidents = incidents
            return incidents
        except Exception:
            return [{"raw_analysis": response.text, "signal_count": len(all_signals)}]

    async def create_elastic_alert_rules(self, incidents: list[dict]):
        """Push alert rules back to Elastic SIEM"""
        for incident in incidents:
            if "elastic_alert_rule" in incident and isinstance(incident["elastic_alert_rule"], dict):
                rule = incident["elastic_alert_rule"]
                try:
                    await self.call_tool("create_rule", {
                        "name": rule.get("name", f"TITAN: {incident.get('title', 'Threat')}"),
                        "description": f"Auto-generated by TITAN THREAT HUNTER | {incident.get('title')}",
                        "risk_score": {"CRITICAL": 99, "HIGH": 73, "MEDIUM": 47, "LOW": 21}.get(incident.get("severity", "MEDIUM"), 47),
                        "severity": incident.get("severity", "medium").lower(),
                        "type": rule.get("type", "query"),
                        "query": rule.get("query", "*"),
                        "index": ["logs-*", "auditbeat-*", "packetbeat-*"],
                        "enabled": True,
                        "tags": ["TITAN", "autonomous", incident.get("severity", "medium")]
                    })
                except Exception as e:
                    print(f"  [Rule creation]: {e}")

    async def create_siem_case(self, incident: dict):
        """Create a SIEM case in Elastic for the incident"""
        try:
            await self.call_tool("create_case", {
                "title": f"[TITAN] {incident.get('title', 'Threat Detected')}",
                "description": f"""
**Severity**: {incident.get('severity')}
**Confidence**: {incident.get('confidence', 0) * 100:.0f}%
**Detected**: {incident.get('detected_at')}

**Threat Actor Profile**: {incident.get('threat_actor_profile', 'Unknown')}

**Attack Stages**: {' → '.join(incident.get('attack_stages', []))}

**Evidence**: {chr(10).join(f'- {e}' for e in incident.get('evidence', []))}

**Containment Runbook**:
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(incident.get('containment_runbook', [])))}

*Auto-generated by TITAN THREAT HUNTER | TitanU AI LLC*
""",
                "tags": ["TITAN", incident.get("severity", "medium").lower(), "autonomous-hunt"],
                "severity": incident.get("severity", "medium").lower()
            })
        except Exception as e:
            print(f"  [Case creation]: {e}")

    async def run_full_hunt(self) -> dict:
        """
        Full autonomous threat hunting cycle:
        Phase 1: Hunt across 4 attack vectors simultaneously
        Phase 2: Correlate & classify with Gemini + MITRE
        Phase 3: Create Elastic alert rules
        Phase 4: Open SIEM cases for confirmed incidents
        Phase 5: Generate threat intelligence report
        """
        print("\n[TITAN THREAT HUNTER] Initiating full threat hunt...")
        hunt_start = datetime.utcnow()

        # Phase 1: Parallel hunting
        print("  [Phase 1] Hunting: failed logins, lateral movement, exfiltration, C2...")
        results = await asyncio.gather(
            self.hunt_failed_logins(60),
            self.hunt_lateral_movement(),
            self.hunt_data_exfiltration(),
            self.hunt_c2_beaconing(),
            return_exceptions=True
        )

        all_signals = []
        for r in results:
            if isinstance(r, list):
                all_signals.extend(r)

        print(f"  [Phase 1] {len(all_signals)} signals detected across all vectors")

        # Phase 2: Correlate
        print("  [Phase 2] Correlating signals with Gemini + MITRE ATT&CK...")
        incidents = await self.correlate_and_classify(all_signals)
        print(f"  [Phase 2] {len(incidents)} incidents classified")

        # Phase 3: Create alert rules
        print("  [Phase 3] Pushing alert rules to Elastic SIEM...")
        await self.create_elastic_alert_rules(incidents)

        # Phase 4: Open SIEM cases for HIGH+
        critical_incidents = [i for i in incidents if i.get("severity") in ["CRITICAL", "HIGH"]]
        print(f"  [Phase 4] Creating {len(critical_incidents)} SIEM cases...")
        for inc in critical_incidents:
            await self.create_siem_case(inc)

        hunt_duration = (datetime.utcnow() - hunt_start).total_seconds()

        report = {
            "hunt_id": str(uuid.uuid4()),
            "timestamp": hunt_start.isoformat(),
            "duration_seconds": round(hunt_duration, 2),
            "signals_detected": len(all_signals),
            "incidents_classified": len(incidents),
            "critical_incidents": len([i for i in incidents if i.get("severity") == "CRITICAL"]),
            "high_incidents": len([i for i in incidents if i.get("severity") == "HIGH"]),
            "iocs_collected": list(self.ioc_cache),
            "incidents": incidents,
            "hunt_vectors": ["brute_force", "lateral_movement", "data_exfiltration", "c2_beaconing"],
            "powered_by": "TITAN THREAT HUNTER | TitanU AI LLC | Elastic MCP + Gemini"
        }

        print(f"\n[TITAN THREAT HUNTER] Hunt complete in {hunt_duration:.1f}s")
        print(f"  CRITICAL: {report['critical_incidents']} | HIGH: {report['high_incidents']} | TOTAL: {len(incidents)}")
        return report


async def main():
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@elastic/mcp-server-elasticsearch@latest"],
        env={
            "ES_URL": ELASTIC_URL,
            "ES_API_KEY": ELASTIC_API_KEY
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            hunter = TitanThreatHunter(session)

            print("[TITAN THREAT HUNTER] Elastic MCP connected")
            report = await hunter.run_full_hunt()

            print("\n" + "="*60)
            print("THREAT INTELLIGENCE REPORT")
            print("="*60)
            print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
