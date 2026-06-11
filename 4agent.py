"""
TITAN DEVSECOPS COMMANDER — GitLab Track
Author: Julius Cameron Hill | TitanU AI LLC
Autonomous DevSecOps agent: reviews code, hunts vulnerabilities, heals pipelines, enforces security gates via GitLab MCP.
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
GITLAB_URL = os.environ.get("GITLAB_URL", "https://gitlab.com")
GITLAB_TOKEN = os.environ["GITLAB_TOKEN"]
GITLAB_PROJECT_ID = os.environ["GITLAB_PROJECT_ID"]

genai.configure(api_key=GEMINI_API_KEY)

DEVSECOPS_SYSTEM = """You are TITAN DEVSECOPS COMMANDER — a sovereign autonomous DevSecOps engineer by TitanU AI LLC.

You operate across the full DevSecOps lifecycle:
- SAST: Static analysis finding real vulnerabilities, not noise
- Code Review: Architecture, performance, security — like a senior engineer
- Pipeline Healing: Debug CI failures, fix configs, re-trigger with fixes
- Dependency Audit: CVE mapping, upgrade paths, breaking change analysis
- Security Gates: Block merges with critical vulns, auto-remediate where possible
- Compliance: Enforce OWASP Top 10, CWE/SANS 25, SOC2 controls

You don't flag false positives. You find real issues with real fixes.
Return structured JSON. Be surgical. Be precise.
"""

OWASP_TOP_10 = {
    "A01": "Broken Access Control",
    "A02": "Cryptographic Failures",
    "A03": "Injection",
    "A04": "Insecure Design",
    "A05": "Security Misconfiguration",
    "A06": "Vulnerable and Outdated Components",
    "A07": "Identification and Authentication Failures",
    "A08": "Software and Data Integrity Failures",
    "A09": "Security Logging and Monitoring Failures",
    "A10": "Server-Side Request Forgery"
}

class TitanDevSecOpsCommander:
    def __init__(self, mcp_session: ClientSession):
        self.session = mcp_session
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self.project_id = GITLAB_PROJECT_ID
        self.findings = []

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

    async def get_open_merge_requests(self) -> list[dict]:
        """Fetch all open MRs for review"""
        result = await self.call_tool("list_merge_requests", {
            "project_id": self.project_id,
            "state": "opened",
            "order_by": "updated_at",
            "per_page": 20
        })
        if isinstance(result, list):
            return result
        return []

    async def get_mr_diff(self, mr_iid: int) -> dict:
        """Get full diff for a merge request"""
        result = await self.call_tool("get_merge_request_changes", {
            "project_id": self.project_id,
            "merge_request_iid": mr_iid
        })
        return result if isinstance(result, dict) else {}

    async def get_failed_pipelines(self) -> list[dict]:
        """Fetch recently failed CI/CD pipelines"""
        result = await self.call_tool("list_pipelines", {
            "project_id": self.project_id,
            "status": "failed",
            "per_page": 10
        })
        if isinstance(result, list):
            return result
        return []

    async def get_pipeline_jobs(self, pipeline_id: int) -> list[dict]:
        """Get jobs for a pipeline"""
        result = await self.call_tool("list_pipeline_jobs", {
            "project_id": self.project_id,
            "pipeline_id": pipeline_id
        })
        if isinstance(result, list):
            return result
        return []

    async def get_job_log(self, job_id: int) -> str:
        """Get CI job log output"""
        result = await self.call_tool("get_job_log", {
            "project_id": self.project_id,
            "job_id": job_id
        })
        return str(result)[:8000] if result else ""  # cap at 8k chars

    async def get_project_vulnerabilities(self) -> list[dict]:
        """Fetch open security vulnerabilities from GitLab Security Dashboard"""
        result = await self.call_tool("list_vulnerabilities", {
            "project_id": self.project_id,
            "state": "detected",
            "severity": "critical,high",
            "per_page": 50
        })
        if isinstance(result, list):
            return result
        return []

    async def analyze_code_security(self, mr_iid: int, diff: dict) -> dict:
        """SAST + Code review on MR diff using Gemini"""
        changes = diff.get("changes", [])
        diffs_text = ""
        for change in changes[:10]:  # top 10 changed files
            diffs_text += f"\n--- {change.get('old_path')} → {change.get('new_path')} ---\n"
            diffs_text += change.get("diff", "")[:3000]

        prompt = f"""Perform autonomous DevSecOps review on this merge request diff.

MR !{mr_iid} Changes:
{diffs_text}

Analyze for:
1. SECURITY VULNERABILITIES: SQL injection, XSS, command injection, insecure deserialization, hardcoded secrets, SSRF, path traversal, insecure crypto, auth bypasses
2. OWASP TOP 10 violations
3. CODE QUALITY: N+1 queries, missing error handling, race conditions, resource leaks, performance cliffs
4. SECRETS DETECTION: API keys, passwords, tokens in code
5. DEPENDENCY RISKS: Outdated/vulnerable imports

For each finding provide:
- severity: CRITICAL|HIGH|MEDIUM|LOW|INFO
- owasp_category: A01-A10 if applicable
- cwe_id: CWE number
- file: filename
- line: approximate line number
- description: precise technical description
- evidence: exact code snippet
- fix: specific code fix

Ignore stylistic issues. Only real security and quality findings.

Return JSON:
{{
  "critical_count": <int>,
  "high_count": <int>,
  "should_block_merge": <bool>,
  "findings": [
    {{
      "id": "<uuid>",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "type": "security|quality|secret",
      "owasp": "<A0X or null>",
      "cwe": "<CWE-XXX or null>",
      "file": "<filename>",
      "line": <int>,
      "title": "<short title>",
      "description": "<technical description>",
      "evidence": "<code snippet>",
      "fix": "<specific fix>"
    }}
  ],
  "security_score": <0-100>,
  "review_summary": "<2 sentence summary>"
}}"""

        response = self.model.generate_content(DEVSECOPS_SYSTEM + "\n\n" + prompt)
        try:
            text = response.text.strip().replace("```json", "").replace("```", "")
            result = json.loads(text)
            for f in result.get("findings", []):
                f["id"] = str(uuid.uuid4())
            return result
        except Exception:
            return {"raw_review": response.text, "mr_iid": mr_iid}

    async def post_mr_review(self, mr_iid: int, analysis: dict) -> bool:
        """Post security review as MR comment"""
        findings = analysis.get("findings", [])
        critical = [f for f in findings if f.get("severity") == "CRITICAL"]
        high = [f for f in findings if f.get("severity") == "HIGH"]

        should_block = analysis.get("should_block_merge", False)
        score = analysis.get("security_score", 0)

        comment_body = f"""## 🛡️ TITAN DEVSECOPS COMMANDER — Security Review

**Security Score: {score}/100** | {'🔴 MERGE BLOCKED' if should_block else '🟡 Review Required' if high else '🟢 Approved'}

**Summary:** {analysis.get('review_summary', 'Analysis complete.')}

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | {analysis.get('critical_count', len(critical))} |
| 🟠 HIGH | {analysis.get('high_count', len(high))} |
| 🟡 MEDIUM | {len([f for f in findings if f.get('severity') == 'MEDIUM'])} |

"""

        for f in findings[:10]:  # top 10 findings
            sev_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵", "INFO": "⚪"}.get(f.get("severity"), "⚪")
            owasp = f" | {OWASP_TOP_10.get(f.get('owasp', ''), '')}" if f.get("owasp") else ""
            comment_body += f"""
<details>
<summary>{sev_emoji} [{f.get('severity')}] {f.get('title', 'Finding')} — {f.get('file', '')}:{f.get('line', '?')}{owasp}</summary>

**Description:** {f.get('description', '')}

**Evidence:**
```
{f.get('evidence', '')}
```

**Fix:**
```
{f.get('fix', '')}
```

{f'**CWE:** {f.get("cwe")}' if f.get("cwe") else ""}
</details>
"""

        comment_body += "\n\n*🤖 Powered by TITAN DEVSECOPS COMMANDER | TitanU AI LLC*"

        try:
            await self.call_tool("create_merge_request_note", {
                "project_id": self.project_id,
                "merge_request_iid": mr_iid,
                "body": comment_body
            })

            if should_block:
                await self.call_tool("update_merge_request", {
                    "project_id": self.project_id,
                    "merge_request_iid": mr_iid,
                    "labels": "security-blocked,titan-review"
                })

            return True
        except Exception as e:
            print(f"  [Comment failed]: {e}")
            return False

    async def diagnose_pipeline_failure(self, pipeline: dict) -> dict:
        """Diagnose why a pipeline failed and generate fix"""
        pipeline_id = pipeline.get("id")
        jobs = await self.get_pipeline_jobs(pipeline_id)

        failed_jobs = [j for j in jobs if j.get("status") == "failed"]
        logs = {}
        for job in failed_jobs[:3]:  # top 3 failed jobs
            log = await self.get_job_log(job["id"])
            logs[job.get("name", str(job["id"]))] = log

        prompt = f"""Diagnose this CI/CD pipeline failure and generate a fix.

PIPELINE: {json.dumps(pipeline, indent=2)}

FAILED JOBS AND LOGS:
{json.dumps({k: v[-3000:] for k, v in logs.items()}, indent=2)}

Diagnose:
1. Root cause of failure (exact error)
2. Which category: dependency|test_failure|build_error|infrastructure|config|flaky_test
3. Is this flaky (intermittent) or deterministic?
4. Specific fix: code change, config update, or retry strategy
5. .gitlab-ci.yml changes needed if any

Return JSON:
{{
  "pipeline_id": {pipeline_id},
  "root_cause": "<precise error>",
  "category": "<category>",
  "is_flaky": <bool>,
  "diagnosis": "<detailed explanation>",
  "fix_type": "code_change|config_update|retry|dependency_upgrade",
  "fix_description": "<what to change>",
  "gitlab_ci_patch": "<yaml snippet if needed or null>",
  "can_auto_retry": <bool>
}}"""

        response = self.model.generate_content(DEVSECOPS_SYSTEM + "\n\n" + prompt)
        try:
            text = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(text)
        except Exception:
            return {"raw_diagnosis": response.text, "pipeline_id": pipeline_id}

    async def auto_retry_flaky_pipeline(self, pipeline_id: int) -> bool:
        """Retry a flaky pipeline"""
        try:
            await self.call_tool("retry_pipeline", {
                "project_id": self.project_id,
                "pipeline_id": pipeline_id
            })
            return True
        except Exception:
            return False

    async def create_security_issue(self, vulnerability: dict) -> bool:
        """Create a GitLab issue for a critical vulnerability"""
        try:
            await self.call_tool("create_issue", {
                "project_id": self.project_id,
                "title": f"[TITAN SECURITY] {vulnerability.get('name', 'Critical Vulnerability')} — {vulnerability.get('severity', 'CRITICAL')}",
                "description": f"""## Security Vulnerability

**Severity:** {vulnerability.get('severity')}
**Scanner:** {vulnerability.get('scanner', {}).get('name', 'TITAN DevSecOps')}
**Location:** {vulnerability.get('location', {}).get('file', 'Unknown')}

### Description
{vulnerability.get('description', '')}

### Solution
{vulnerability.get('solution', 'Review and remediate immediately.')}

### CVE
{vulnerability.get('identifiers', [{}])[0].get('external_id', 'N/A') if vulnerability.get('identifiers') else 'N/A'}

---
*Auto-created by TITAN DEVSECOPS COMMANDER | TitanU AI LLC*""",
                "labels": "security,titan,critical",
                "confidential": True
            })
            return True
        except Exception:
            return False

    async def run_full_devsecops_cycle(self) -> dict:
        """
        Full autonomous DevSecOps cycle:
        1. Review all open MRs for security vulnerabilities
        2. Diagnose all failed pipelines
        3. Create issues for critical vulns from security dashboard
        4. Auto-retry flaky pipelines
        5. Generate DevSecOps report
        """
        print("\n[TITAN DEVSECOPS] Starting autonomous DevSecOps cycle...")
        cycle_start = datetime.utcnow()

        print("  [1/4] Fetching MRs, pipelines, and vulnerabilities...")
        mrs, failed_pipelines, vulnerabilities = await asyncio.gather(
            self.get_open_merge_requests(),
            self.get_failed_pipelines(),
            self.get_project_vulnerabilities()
        )

        print(f"  Open MRs: {len(mrs)} | Failed Pipelines: {len(failed_pipelines)} | Vulnerabilities: {len(vulnerabilities)}")

        mr_reports = []
        print(f"  [2/4] Security reviewing {len(mrs)} merge requests...")
        for mr in mrs[:5]:  # top 5 MRs
            mr_iid = mr.get("iid")
            title = mr.get("title", "")
            print(f"    Reviewing MR !{mr_iid}: {title[:60]}")
            diff = await self.get_mr_diff(mr_iid)
            analysis = await self.analyze_code_security(mr_iid, diff)
            posted = await self.post_mr_review(mr_iid, analysis)
            mr_reports.append({
                "mr_iid": mr_iid,
                "title": title,
                "security_score": analysis.get("security_score", 0),
                "critical_findings": analysis.get("critical_count", 0),
                "blocked": analysis.get("should_block_merge", False),
                "review_posted": posted
            })

        pipeline_reports = []
        print(f"  [3/4] Diagnosing {len(failed_pipelines)} failed pipelines...")
        for pipeline in failed_pipelines[:5]:
            diagnosis = await self.diagnose_pipeline_failure(pipeline)
            retried = False
            if diagnosis.get("is_flaky") and diagnosis.get("can_auto_retry"):
                retried = await self.auto_retry_flaky_pipeline(pipeline["id"])
            pipeline_reports.append({
                "pipeline_id": pipeline.get("id"),
                "ref": pipeline.get("ref"),
                "root_cause": diagnosis.get("root_cause"),
                "category": diagnosis.get("category"),
                "auto_retried": retried
            })

        vuln_issues_created = 0
        print(f"  [4/4] Creating issues for {len(vulnerabilities)} critical vulnerabilities...")
        for vuln in vulnerabilities[:10]:
            if await self.create_security_issue(vuln):
                vuln_issues_created += 1

        cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
        blocked_mrs = [r for r in mr_reports if r["blocked"]]

        return {
            "cycle_id": str(uuid.uuid4()),
            "timestamp": cycle_start.isoformat(),
            "duration_seconds": round(cycle_duration, 2),
            "mr_reviews": len(mr_reports),
            "mrs_blocked": len(blocked_mrs),
            "pipelines_diagnosed": len(pipeline_reports),
            "pipelines_auto_retried": len([p for p in pipeline_reports if p["auto_retried"]]),
            "vuln_issues_created": vuln_issues_created,
            "avg_security_score": round(sum(r["security_score"] for r in mr_reports) / max(len(mr_reports), 1), 1),
            "mr_reports": mr_reports,
            "pipeline_reports": pipeline_reports,
            "powered_by": "TITAN DEVSECOPS COMMANDER | TitanU AI LLC | GitLab MCP + Gemini"
        }


async def main():
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@gitlab-org/gitlab-mcp@latest"],
        env={
            "GITLAB_URL": GITLAB_URL,
            "GITLAB_PERSONAL_ACCESS_TOKEN": GITLAB_TOKEN
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            commander = TitanDevSecOpsCommander(session)

            print("[TITAN DEVSECOPS] GitLab MCP connected")
            report = await commander.run_full_devsecops_cycle()

            print("\n" + "="*60)
            print("DEVSECOPS COMMANDER REPORT")
            print("="*60)
            print(json.dumps({k: v for k, v in report.items() if k not in ["mr_reports", "pipeline_reports"]}, indent=2))
            print("\nMR Security Summary:")
            for mr in report["mr_reports"]:
                status = "🔴 BLOCKED" if mr["blocked"] else "🟢 OK"
                print(f"  {status} MR !{mr['mr_iid']} | Score: {mr['security_score']}/100 | Critical: {mr['critical_findings']}")


if __name__ == "__main__":
    asyncio.run(main())
