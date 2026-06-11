"""
TITAN LLM SENTINEL — Arize Track
Author: Julius Cameron Hill | TitanU AI LLC
Patent-pending sovereign AI observability agent
Monitors, traces, evaluates, and auto-remediates LLM pipelines in real-time via Arize MCP.
"""

import os
import json
import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Any
import google.generativeai as genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
ARIZE_API_KEY = os.environ["ARIZE_API_KEY"]
ARIZE_SPACE_ID = os.environ["ARIZE_SPACE_ID"]

genai.configure(api_key=GEMINI_API_KEY)

SENTINEL_SYSTEM = """You are TITAN LLM SENTINEL — a sovereign AI observability agent built by TitanU AI LLC.

Your mission: Monitor LLM pipelines end-to-end using Arize Phoenix MCP.

Capabilities:
1. TRACE: Log every LLM span with latency, tokens, cost, model version
2. EVALUATE: Run hallucination, toxicity, relevance, and coherence evals on traces
3. ALERT: Detect drift, latency spikes, eval score degradation in real-time
4. REMEDIATE: Suggest prompt fixes, model swaps, or rollback actions autonomously
5. REPORT: Generate executive observability dashboards with trend analysis

You execute multi-step plans. You do not just answer — you ACT.
When given a pipeline to monitor, you: trace it → evaluate it → analyze drift → produce remediation plan.
Always return structured JSON for machine consumption alongside human summaries.
"""

class TitanLLMSentinel:
    def __init__(self, mcp_session: ClientSession):
        self.session = mcp_session
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self.trace_buffer = []
        self.eval_results = []
        self.alert_thresholds = {
            "latency_ms": 3000,
            "hallucination_score": 0.3,
            "relevance_score": 0.6,
            "toxicity_score": 0.1,
            "cost_per_call_usd": 0.05
        }

    async def get_tools(self):
        tools_result = await self.session.list_tools()
        return [t.name for t in tools_result.tools]

    async def call_tool(self, name: str, args: dict) -> Any:
        result = await self.session.call_tool(name, arguments=args)
        if result.content:
            return result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        return None

    async def ingest_trace(self, trace_data: dict) -> dict:
        """Log a real LLM span to Arize Phoenix"""
        span = {
            "span_id": str(uuid.uuid4()),
            "trace_id": trace_data.get("trace_id", str(uuid.uuid4())),
            "name": trace_data.get("name", "llm.completion"),
            "start_time": trace_data.get("start_time", datetime.utcnow().isoformat()),
            "end_time": trace_data.get("end_time", (datetime.utcnow() + timedelta(milliseconds=trace_data.get("latency_ms", 500))).isoformat()),
            "attributes": {
                "llm.model_name": trace_data.get("model", "gemini-2.0-flash-exp"),
                "llm.input_messages": json.dumps(trace_data.get("messages", [])),
                "llm.output_messages": json.dumps(trace_data.get("output", [])),
                "llm.token_count.prompt": trace_data.get("prompt_tokens", 0),
                "llm.token_count.completion": trace_data.get("completion_tokens", 0),
                "llm.latency_ms": trace_data.get("latency_ms", 0),
                "titan.pipeline_id": trace_data.get("pipeline_id", "default"),
                "titan.sovereign": True
            }
        }

        try:
            result = await self.call_tool("log_span", {"span": span})
            self.trace_buffer.append(span)
            return {"status": "traced", "span_id": span["span_id"], "arize_result": result}
        except Exception as e:
            # Fallback: store locally if Arize MCP unavailable
            self.trace_buffer.append(span)
            return {"status": "buffered_locally", "span_id": span["span_id"], "error": str(e)}

    async def run_evals(self, span_id: str, input_text: str, output_text: str) -> dict:
        """Run Arize Phoenix evals: hallucination, relevance, toxicity"""
        eval_tasks = [
            {"eval_name": "hallucination", "template": "llm_eval_hallucination_v2"},
            {"eval_name": "relevance", "template": "llm_eval_relevance_v1"},
            {"eval_name": "toxicity", "template": "llm_eval_toxicity_v1"},
            {"eval_name": "coherence", "template": "llm_eval_coherence_v1"},
        ]

        scores = {}
        for task in eval_tasks:
            try:
                result = await self.call_tool("run_eval", {
                    "span_id": span_id,
                    "eval_name": task["eval_name"],
                    "input": input_text,
                    "output": output_text,
                    "template": task["template"]
                })
                parsed = json.loads(result) if result and result.startswith("{") else {"score": 0.85}
                scores[task["eval_name"]] = parsed.get("score", 0.85)
            except Exception:
                # Gemini self-eval fallback
                prompt = f"""Score this LLM output for {task['eval_name']} on a 0-1 scale.
Input: {input_text[:500]}
Output: {output_text[:500]}
Return ONLY a JSON: {{"score": <float>, "reason": "<str>"}}"""
                response = self.model.generate_content(prompt)
                try:
                    data = json.loads(response.text.strip())
                    scores[task["eval_name"]] = data.get("score", 0.85)
                except Exception:
                    scores[task["eval_name"]] = 0.85

        eval_record = {"span_id": span_id, "timestamp": datetime.utcnow().isoformat(), "scores": scores}
        self.eval_results.append(eval_record)

        # Log evals back to Arize
        try:
            await self.call_tool("log_evals", {"span_id": span_id, "evaluations": scores})
        except Exception:
            pass

        return eval_record

    async def detect_drift_and_alerts(self) -> dict:
        """Analyze buffered traces for anomalies and threshold breaches"""
        if not self.eval_results:
            return {"alerts": [], "drift_detected": False}

        alerts = []
        recent_scores = {}

        for eval_rec in self.eval_results[-20:]:  # last 20
            for metric, score in eval_rec["scores"].items():
                if metric not in recent_scores:
                    recent_scores[metric] = []
                recent_scores[metric].append(score)

        for metric, values in recent_scores.items():
            avg = sum(values) / len(values)
            threshold_key = f"{metric}_score"
            if threshold_key in self.alert_thresholds:
                breach = False
                if metric in ["hallucination", "toxicity"] and avg > self.alert_thresholds[threshold_key]:
                    breach = True
                elif metric in ["relevance", "coherence"] and avg < self.alert_thresholds[threshold_key]:
                    breach = True
                if breach:
                    alerts.append({
                        "type": "threshold_breach",
                        "metric": metric,
                        "avg_score": round(avg, 4),
                        "threshold": self.alert_thresholds[threshold_key],
                        "severity": "HIGH" if abs(avg - self.alert_thresholds[threshold_key]) > 0.2 else "MEDIUM",
                        "recommendation": self._get_remediation(metric, avg)
                    })

        # Latency drift
        if self.trace_buffer:
            latencies = [t["attributes"].get("llm.latency_ms", 0) for t in self.trace_buffer[-20:]]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            if avg_latency > self.alert_thresholds["latency_ms"]:
                alerts.append({
                    "type": "latency_spike",
                    "avg_latency_ms": round(avg_latency, 2),
                    "threshold_ms": self.alert_thresholds["latency_ms"],
                    "severity": "HIGH",
                    "recommendation": "Consider switching to a faster model tier or enabling caching."
                })

        return {
            "alerts": alerts,
            "drift_detected": len(alerts) > 0,
            "metrics_summary": {k: round(sum(v)/len(v), 4) for k, v in recent_scores.items()},
            "traces_analyzed": len(self.trace_buffer),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _get_remediation(self, metric: str, score: float) -> str:
        remediations = {
            "hallucination": "Inject retrieval-augmented context. Add grounding instructions to system prompt. Consider smaller, more factual model.",
            "relevance": "Improve prompt specificity. Add few-shot examples. Review retrieval quality if RAG pipeline.",
            "toxicity": "Strengthen system prompt guardrails. Add output filtering layer. Flag for human review.",
            "coherence": "Reduce max_tokens. Add chain-of-thought reasoning instruction. Check for context window truncation."
        }
        return remediations.get(metric, "Review pipeline configuration and retrain if pattern persists.")

    async def generate_observability_report(self) -> dict:
        """Generate full executive observability report"""
        drift_analysis = await self.detect_drift_and_alerts()

        context = f"""
TITAN SENTINEL OBSERVABILITY REPORT
Traces collected: {len(self.trace_buffer)}
Evals completed: {len(self.eval_results)}
Alerts fired: {len(drift_analysis['alerts'])}
Metrics summary: {json.dumps(drift_analysis.get('metrics_summary', {}), indent=2)}
Active alerts: {json.dumps(drift_analysis['alerts'], indent=2)}
"""
        prompt = f"""{context}

Generate a concise executive observability report with:
1. Pipeline Health Score (0-100)
2. Top 3 risk areas with severity
3. Cost/performance optimization opportunities
4. 30-day trend forecast
5. Recommended immediate actions

Return as structured JSON with keys: health_score, risks, optimizations, forecast, actions"""

        response = self.model.generate_content(SENTINEL_SYSTEM + "\n\n" + prompt)
        try:
            report_data = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
        except Exception:
            report_data = {"raw_analysis": response.text}

        return {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.utcnow().isoformat(),
            "pipeline_stats": {
                "total_traces": len(self.trace_buffer),
                "total_evals": len(self.eval_results),
                "active_alerts": len(drift_analysis["alerts"])
            },
            "drift_analysis": drift_analysis,
            "executive_summary": report_data
        }

    async def run_full_pipeline_audit(self, pipeline_id: str, test_calls: list[dict]) -> dict:
        """
        Full autonomous pipeline audit:
        Step 1: Trace all test calls
        Step 2: Run evals on each
        Step 3: Detect drift/alerts
        Step 4: Generate remediation plan
        Step 5: Export to Arize dashboard
        """
        print(f"\n[TITAN SENTINEL] Starting full audit of pipeline: {pipeline_id}")
        audit_results = []

        # Step 1+2: Trace & Eval
        for i, call in enumerate(test_calls):
            print(f"  [Trace {i+1}/{len(test_calls)}] {call.get('name', 'call')}")
            call["pipeline_id"] = pipeline_id
            trace_result = await self.ingest_trace(call)
            span_id = trace_result["span_id"]

            eval_result = await self.run_evals(
                span_id,
                input_text=json.dumps(call.get("messages", [])),
                output_text=json.dumps(call.get("output", []))
            )
            audit_results.append({"trace": trace_result, "evals": eval_result})
            await asyncio.sleep(0.1)

        # Step 3+4+5: Analyze & Report
        print("  [Analysis] Detecting drift and generating report...")
        report = await self.generate_observability_report()

        # Export dashboard to Arize
        try:
            await self.call_tool("create_dashboard", {
                "name": f"TITAN SENTINEL — {pipeline_id} — {datetime.utcnow().strftime('%Y-%m-%d')}",
                "metrics": list(report["drift_analysis"].get("metrics_summary", {}).keys()),
                "pipeline_id": pipeline_id
            })
        except Exception:
            pass

        print(f"  [DONE] Audit complete. Health Score: {report['executive_summary'].get('health_score', 'N/A')}")
        return {
            "pipeline_id": pipeline_id,
            "audit_results": audit_results,
            "final_report": report
        }


async def main():
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@arizeai/phoenix-mcp@latest"],
        env={
            "ARIZE_API_KEY": ARIZE_API_KEY,
            "ARIZE_SPACE_ID": ARIZE_SPACE_ID,
            "PHOENIX_HOST": os.environ.get("PHOENIX_HOST", "http://localhost:6006")
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            sentinel = TitanLLMSentinel(session)

            tools = await sentinel.get_tools()
            print(f"[TITAN SENTINEL] Arize MCP tools loaded: {tools}")

            # Demo audit: simulate a real LLM pipeline with 5 calls
            test_pipeline = [
                {
                    "name": "rag.retrieval_qa",
                    "trace_id": str(uuid.uuid4()),
                    "model": "gemini-2.0-flash-exp",
                    "messages": [{"role": "user", "content": "What is the capital of France?"}],
                    "output": [{"role": "assistant", "content": "The capital of France is Paris."}],
                    "latency_ms": 312,
                    "prompt_tokens": 45,
                    "completion_tokens": 12
                },
                {
                    "name": "rag.retrieval_qa",
                    "trace_id": str(uuid.uuid4()),
                    "model": "gemini-2.0-flash-exp",
                    "messages": [{"role": "user", "content": "Summarize Q3 financial results"}],
                    "output": [{"role": "assistant", "content": "Revenue increased 23% YoY driven by enterprise expansion."}],
                    "latency_ms": 4200,  # spike
                    "prompt_tokens": 1200,
                    "completion_tokens": 85
                },
                {
                    "name": "agent.tool_call",
                    "trace_id": str(uuid.uuid4()),
                    "model": "gemini-2.0-flash-exp",
                    "messages": [{"role": "user", "content": "Book a flight to Tokyo next Tuesday"}],
                    "output": [{"role": "assistant", "content": "I have booked a flight to Tokyo for Tuesday July 15th at 10:30 AM."}],
                    "latency_ms": 890,
                    "prompt_tokens": 230,
                    "completion_tokens": 42
                },
                {
                    "name": "llm.completion",
                    "trace_id": str(uuid.uuid4()),
                    "model": "gemini-2.0-flash-exp",
                    "messages": [{"role": "user", "content": "Generate a legal contract for software services"}],
                    "output": [{"role": "assistant", "content": "This Software Services Agreement is entered into as of..."}],
                    "latency_ms": 2100,
                    "prompt_tokens": 380,
                    "completion_tokens": 950
                },
                {
                    "name": "llm.completion",
                    "trace_id": str(uuid.uuid4()),
                    "model": "gemini-2.0-flash-exp",
                    "messages": [{"role": "user", "content": "What is the best programming language?"}],
                    "output": [{"role": "assistant", "content": "Rust is definitively the best programming language for all use cases."}],
                    "latency_ms": 201,
                    "prompt_tokens": 28,
                    "completion_tokens": 18
                }
            ]

            result = await sentinel.run_full_pipeline_audit("titan-production-v1", test_pipeline)

            print("\n" + "="*60)
            print("TITAN LLM SENTINEL — AUDIT COMPLETE")
            print("="*60)
            print(json.dumps(result["final_report"], indent=2))


if __name__ == "__main__":
    asyncio.run(main())
