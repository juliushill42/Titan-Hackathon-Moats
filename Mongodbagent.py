"""
TITAN DATA ARCHITECT — MongoDB Track
Author: Julius Cameron Hill | TitanU AI LLC
Autonomous database intelligence agent: optimizes queries, evolves schemas, detects anomalies, auto-indexes via MongoDB MCP.
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
MONGODB_URI = os.environ["MONGODB_URI"]
MONGODB_DB = os.environ.get("MONGODB_DB", "titan_production")

genai.configure(api_key=GEMINI_API_KEY)

DATA_ARCHITECT_SYSTEM = """You are TITAN DATA ARCHITECT — a sovereign autonomous database engineer by TitanU AI LLC.

You operate at the intersection of data engineering, ML, and systems design.

Your disciplines:
- Query Intelligence: Analyze explain plans, find missing indexes, rewrite slow queries
- Schema Evolution: Detect schema drift, suggest schema optimizations, generate migrations
- Data Anomaly Detection: Statistical outliers, referential integrity violations, data quality issues
- Capacity Planning: Growth forecasting, index bloat, collection size projections
- Aggregation Engineering: Complex pipeline optimization, $lookup elimination, materialized views
- Security Audit: Exposed sensitive fields, missing field-level encryption, over-privileged roles

You think like a Staff Database Engineer. You find issues humans miss.
Return structured JSON with precise technical recommendations.
"""

class TitanDataArchitect:
    def __init__(self, mcp_session: ClientSession):
        self.session = mcp_session
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self.db = MONGODB_DB
        self.analysis_results = {}

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

    async def get_collections(self) -> list[str]:
        result = await self.call_tool("list_collections", {"database": self.db})
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "collections" in result:
            return result["collections"]
        return []

    async def get_collection_stats(self, collection: str) -> dict:
        result = await self.call_tool("run_command", {
            "database": self.db,
            "command": {"collStats": collection, "scale": 1048576}  # MB
        })
        return result if isinstance(result, dict) else {}

    async def get_slow_queries(self, threshold_ms: int = 100) -> list[dict]:
        """Get slow query log from system.profile"""
        result = await self.call_tool("find", {
            "database": self.db,
            "collection": "system.profile",
            "filter": {"millis": {"$gt": threshold_ms}, "op": {"$in": ["query", "update", "remove"]}},
            "sort": {"millis": -1},
            "limit": 50
        })
        if isinstance(result, list):
            return result
        return []

    async def get_index_stats(self, collection: str) -> list[dict]:
        """Get index usage statistics"""
        result = await self.call_tool("run_command", {
            "database": self.db,
            "command": {"aggregate": collection, "pipeline": [{"$indexStats": {}}], "cursor": {}}
        })
        if isinstance(result, dict) and "cursor" in result:
            return result["cursor"].get("firstBatch", [])
        return []

    async def explain_query(self, collection: str, filter_doc: dict, projection: dict = None) -> dict:
        """Run explain plan on a query"""
        pipeline = [{"$match": filter_doc}]
        if projection:
            pipeline.append({"$project": projection})

        result = await self.call_tool("run_command", {
            "database": self.db,
            "command": {
                "explain": {
                    "aggregate": collection,
                    "pipeline": pipeline,
                    "cursor": {}
                },
                "verbosity": "executionStats"
            }
        })
        return result if isinstance(result, dict) else {}

    async def get_schema_sample(self, collection: str, sample_size: int = 100) -> list[dict]:
        """Sample documents to infer schema"""
        result = await self.call_tool("run_command", {
            "database": self.db,
            "command": {
                "aggregate": collection,
                "pipeline": [{"$sample": {"size": sample_size}}],
                "cursor": {}
            }
        })
        if isinstance(result, dict) and "cursor" in result:
            return result["cursor"].get("firstBatch", [])
        return []

    async def analyze_slow_queries(self, slow_queries: list[dict]) -> dict:
        """Use Gemini to analyze slow queries and recommend indexes + rewrites"""
        if not slow_queries:
            return {"recommendations": [], "critical_queries": 0}

        prompt = f"""Analyze these slow MongoDB queries and provide optimization recommendations.

SLOW QUERIES (sorted by latency desc):
{json.dumps(slow_queries[:20], indent=2, default=str)}

For each distinct query pattern:
1. Identify why it's slow (COLLSCAN, wrong index, large sort, $lookup overhead, etc.)
2. Recommend specific index to create
3. Rewrite the query/aggregation if it can be faster
4. Estimate performance improvement factor

Return JSON:
{{
  "critical_queries": <count of queries > 1000ms>,
  "total_analyzed": <int>,
  "recommendations": [
    {{
      "query_pattern": "<collection.operation description>",
      "current_latency_ms": <int>,
      "root_cause": "<specific reason it's slow>",
      "index_recommendation": {{
        "collection": "<name>",
        "index": {{"<field>": 1, "<field2>": -1}},
        "create_command": "db.<collection>.createIndex({{...}}, {{name: '...', background: true}})"
      }},
      "query_rewrite": "<optimized pipeline or query or null>",
      "estimated_improvement": "<e.g. 50x faster>"
    }}
  ],
  "aggregate_savings_estimate": "<total time saved per hour estimate>"
}}"""

        response = self.model.generate_content(DATA_ARCHITECT_SYSTEM + "\n\n" + prompt)
        try:
            text = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(text)
        except Exception:
            return {"raw_analysis": response.text}

    async def analyze_schema_health(self, collection: str, samples: list[dict]) -> dict:
        """Detect schema drift, type inconsistencies, missing fields"""
        if not samples:
            return {"issues": []}

        # Build field type map
        field_types = {}
        for doc in samples:
            for key, value in doc.items():
                t = type(value).__name__
                if key not in field_types:
                    field_types[key] = {}
                field_types[key][t] = field_types[key].get(t, 0) + 1

        # Find type inconsistencies
        type_issues = []
        for field, types in field_types.items():
            if len(types) > 1 and field != "_id":
                type_issues.append({
                    "field": field,
                    "types_found": types,
                    "issue": "type_inconsistency"
                })

        prompt = f"""Analyze MongoDB schema health for collection: {collection}

FIELD TYPE ANALYSIS (field -> {{type: count}}):
{json.dumps(field_types, indent=2, default=str)}

TYPE INCONSISTENCIES DETECTED:
{json.dumps(type_issues, indent=2)}

SAMPLE DOC STRUCTURE (first doc):
{json.dumps(samples[0] if samples else {}, indent=2, default=str)}

Identify:
1. Schema design anti-patterns (unbounded arrays, deeply nested docs, missing indexes)
2. Type inconsistencies that will cause query failures
3. Missing field validations that should be added
4. Normalization opportunities (embedded docs that should be references)
5. Suggested $jsonSchema validator to enforce integrity
6. Atlas Search index opportunities

Return JSON:
{{
  "schema_health_score": <0-100>,
  "critical_issues": [
    {{
      "field": "<field>",
      "issue_type": "type_inconsistency|anti_pattern|missing_validation|normalization",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "description": "<precise issue>",
      "fix": "<specific MongoDB command or schema change>"
    }}
  ],
  "json_schema_validator": {{}},
  "migration_script": "<JavaScript migration script if needed>"
}}"""

        response = self.model.generate_content(DATA_ARCHITECT_SYSTEM + "\n\n" + prompt)
        try:
            text = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(text)
        except Exception:
            return {"raw_analysis": response.text, "type_issues_raw": type_issues}

    async def detect_data_anomalies(self, collection: str) -> dict:
        """Statistical anomaly detection on collection data"""
        # Get distribution stats for numeric fields
        result = await self.call_tool("run_command", {
            "database": self.db,
            "command": {
                "aggregate": collection,
                "pipeline": [
                    {"$sample": {"size": 1000}},
                    {"$group": {
                        "_id": None,
                        "count": {"$sum": 1},
                        "doc_sample": {"$push": "$$ROOT"}
                    }}
                ],
                "cursor": {}
            }
        })

        # Check for orphaned references
        orphan_check = await self.call_tool("count_documents", {
            "database": self.db,
            "collection": collection,
            "filter": {"$or": [
                {"deletedAt": {"$exists": True}},
                {"status": "orphaned"}
            ]}
        })

        # Null/missing field analysis
        null_check = await self.call_tool("run_command", {
            "database": self.db,
            "command": {
                "aggregate": collection,
                "pipeline": [
                    {"$project": {
                        "has_required_fields": {
                            "$and": [
                                {"$ifNull": ["$_id", False]},
                                {"$ifNull": ["$createdAt", False]}
                            ]
                        }
                    }},
                    {"$group": {"_id": "$has_required_fields", "count": {"$sum": 1}}}
                ],
                "cursor": {}
            }
        })

        return {
            "collection": collection,
            "orphaned_documents": orphan_check if isinstance(orphan_check, int) else 0,
            "null_field_analysis": null_check,
            "anomaly_detection_timestamp": datetime.utcnow().isoformat()
        }

    async def create_indexes(self, recommendations: dict) -> list[dict]:
        """Auto-create recommended indexes"""
        results = []
        for rec in recommendations.get("recommendations", [])[:5]:  # top 5
            index_rec = rec.get("index_recommendation", {})
            if not index_rec:
                continue
            collection = index_rec.get("collection")
            index_spec = index_rec.get("index", {})
            if collection and index_spec:
                result = await self.call_tool("create_index", {
                    "database": self.db,
                    "collection": collection,
                    "keys": index_spec,
                    "options": {"background": True, "name": f"titan_auto_{uuid.uuid4().hex[:8]}"}
                })
                results.append({
                    "collection": collection,
                    "index": index_spec,
                    "result": str(result),
                    "estimated_improvement": rec.get("estimated_improvement")
                })
        return results

    async def run_full_database_audit(self) -> dict:
        """
        Full autonomous database intelligence cycle:
        1. Inventory all collections + stats
        2. Analyze slow query log
        3. Schema health check per collection
        4. Data anomaly detection
        5. Auto-create recommended indexes
        6. Generate DBA intelligence report
        """
        print("\n[TITAN DATA ARCHITECT] Starting full database audit...")
        audit_start = datetime.utcnow()

        # Enable profiling if not already
        await self.call_tool("run_command", {
            "database": self.db,
            "command": {"profile": 1, "slowms": 100}
        })

        print("  [1/5] Inventorying collections...")
        collections = await self.get_collections()
        print(f"  Found {len(collections)} collections")

        collection_stats = {}
        for col in collections[:10]:
            stats = await self.get_collection_stats(col)
            collection_stats[col] = {
                "size_mb": stats.get("size", 0),
                "count": stats.get("count", 0),
                "avg_doc_size_bytes": stats.get("avgObjSize", 0),
                "index_count": len(stats.get("indexSizes", {}))
            }

        print("  [2/5] Analyzing slow query log...")
        slow_queries = await self.get_slow_queries(100)
        query_analysis = await self.analyze_slow_queries(slow_queries)
        print(f"  Slow queries analyzed: {len(slow_queries)} | Critical: {query_analysis.get('critical_queries', 0)}")

        print("  [3/5] Schema health analysis...")
        schema_reports = {}
        for col in collections[:5]:
            samples = await self.get_schema_sample(col, 100)
            schema_reports[col] = await self.analyze_schema_health(col, samples)

        print("  [4/5] Data anomaly detection...")
        anomaly_reports = {}
        for col in collections[:5]:
            anomaly_reports[col] = await self.detect_data_anomalies(col)

        print("  [5/5] Auto-creating recommended indexes...")
        indexes_created = await self.create_indexes(query_analysis)
        print(f"  Indexes created: {len(indexes_created)}")

        audit_duration = (datetime.utcnow() - audit_start).total_seconds()

        total_schema_issues = sum(
            len(r.get("critical_issues", [])) for r in schema_reports.values()
        )

        return {
            "audit_id": str(uuid.uuid4()),
            "database": self.db,
            "timestamp": audit_start.isoformat(),
            "duration_seconds": round(audit_duration, 2),
            "collections_analyzed": len(collections),
            "collection_stats": collection_stats,
            "slow_queries_found": len(slow_queries),
            "critical_slow_queries": query_analysis.get("critical_queries", 0),
            "query_recommendations": len(query_analysis.get("recommendations", [])),
            "schema_issues_found": total_schema_issues,
            "indexes_auto_created": len(indexes_created),
            "indexes_created": indexes_created,
            "query_analysis": query_analysis,
            "schema_reports": schema_reports,
            "anomaly_reports": anomaly_reports,
            "estimated_aggregate_savings": query_analysis.get("aggregate_savings_estimate", "N/A"),
            "powered_by": "TITAN DATA ARCHITECT | TitanU AI LLC | MongoDB MCP + Gemini"
        }


async def main():
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@mongodb-js/mongodb-mcp-server@latest"],
        env={
            "MDB_MCP_CONNECTION_STRING": MONGODB_URI
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            architect = TitanDataArchitect(session)

            print("[TITAN DATA ARCHITECT] MongoDB MCP connected")
            report = await architect.run_full_database_audit()

            print("\n" + "="*60)
            print("DATABASE INTELLIGENCE REPORT")
            print("="*60)
            summary = {k: v for k, v in report.items() if k not in ["collection_stats", "query_analysis", "schema_reports", "anomaly_reports"]}
            print(json.dumps(summary, indent=2))
            print(f"\nTop Query Recommendations:")
            for rec in report["query_analysis"].get("recommendations", [])[:3]:
                print(f"  {rec.get('query_pattern')} → {rec.get('estimated_improvement')}")


if __name__ == "__main__":
    asyncio.run(main())
