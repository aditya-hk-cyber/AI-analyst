"""
Generate analyst-facing knowledge docs from sample Athena queries.

Outputs:
- knowledge/catalog.txt: table catalog + schemas for tables referenced by queries
- knowledge/domain.txt: domain glossary & key entities (from queries + inferred schema)
- knowledge/metrics.txt: metric definitions & computation notes (from queries)
- knowledge/examples.txt: annotated queries + preview outputs
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .athena import AthenaClient, QueryResult


@dataclass(frozen=True)
class QueryFile:
    name: str
    path: Path
    sql: str


TABLE_REF_RE = re.compile(r"\b(d11_[a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\b")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _knowledge_dir() -> Path:
    return _repo_root() / "knowledge"


def _queries_dir() -> Path:
    return _knowledge_dir() / "queries"


def _read_query_files(dir_path: Path) -> list[QueryFile]:
    files = sorted(dir_path.glob("*.sql"), key=lambda p: p.name.lower())
    out: list[QueryFile] = []
    for p in files:
        sql = p.read_text(encoding="utf-8").strip()
        if not sql:
            continue
        out.append(QueryFile(name=p.stem, path=p, sql=sql))
    return out


def _extract_table_refs(sql: str) -> list[str]:
    refs = {f"{m.group(1)}.{m.group(2)}" for m in TABLE_REF_RE.finditer(sql)}
    return sorted(refs)


def _format_markdown_table(columns: list[str], rows: list[dict[str, Any]], max_rows: int) -> str:
    if not columns:
        return ""
    lines: list[str] = []
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for row in rows[:max_rows]:
        values = [str(row.get(col, "NULL"))[:80] for col in columns]
        lines.append("| " + " | ".join(values) + " |")
    if len(rows) > max_rows:
        lines.append(f"\n... and {len(rows) - max_rows} more rows (truncated)")
    return "\n".join(lines)


def _format_query_result_preview(result: QueryResult, max_rows: int = 20) -> str:
    lines: list[str] = []
    if result.statistics:
        scanned = result.statistics.get("DataScannedInBytes", 0)
        exec_ms = result.statistics.get("TotalExecutionTimeInMillis", 0)
        lines.append(f"- Query ID: {result.query_execution_id}")
        lines.append(f"- Rows returned (client-capped): {len(result.rows)}")
        lines.append(f"- Data scanned: {scanned / 1024 / 1024:.2f} MB")
        lines.append(f"- Execution time: {exec_ms / 1000:.2f}s")
    else:
        lines.append(f"- Query ID: {result.query_execution_id}")
        lines.append(f"- Rows returned (client-capped): {len(result.rows)}")
    lines.append("")
    lines.append(_format_markdown_table(result.columns, result.rows, max_rows=max_rows))
    return "\n".join(lines).strip()


def _format_schema(describe_rows: list[dict[str, Any]]) -> str:
    """
    Athena DESCRIBE returns a set of rows including '# Partition Information'.
    We preserve the whole output, but render columns in a clean table.
    """
    cols: list[tuple[str, str, str]] = []
    partition_cols: list[tuple[str, str, str]] = []
    in_partition = False

    for row in describe_rows:
        col_name = (row.get("col_name") or "").strip()
        data_type = (row.get("data_type") or "").strip()
        comment = (row.get("comment") or "").strip()

        if not col_name:
            continue
        if col_name.startswith("#"):
            in_partition = col_name.lower().startswith("# partition")
            continue
        if in_partition:
            partition_cols.append((col_name, data_type, comment))
        else:
            cols.append((col_name, data_type, comment))

    def render_table(rows: list[tuple[str, str, str]]) -> str:
        if not rows:
            return "_(none)_"
        lines = ["| Column | Type | Comment |", "| --- | --- | --- |"]
        for c, t, cm in rows:
            lines.append(f"| {c} | {t} | {cm} |")
        return "\n".join(lines)

    out = ["**Columns**", "", render_table(cols), ""]
    out += ["**Partition columns**", "", render_table(partition_cols)]
    return "\n".join(out).strip()


def _columns_from_schema(describe_rows: list[dict[str, Any]]) -> list[tuple[str, str]]:
    cols: list[tuple[str, str]] = []
    for row in describe_rows:
        col_name = (row.get("col_name") or "").strip()
        data_type = (row.get("data_type") or "").strip()
        if not col_name or col_name.startswith("#"):
            continue
        cols.append((col_name, data_type))
    return cols


def _infer_grain(columns: list[tuple[str, str]]) -> str:
    names = {c[0].lower() for c in columns}
    if "hour_bucket" in names or "hour_of_day" in names:
        return "hour"
    if "day_ist" in names or "eventdate" in names:
        return "day"
    if "rec_updated_at" in names or "recupdatedat" in names:
        return "event-time"
    return "unknown"


def _table_description(table_ref: str) -> str:
    # Keep these descriptions conservative: "seems to" and "used for".
    return {
        "d11_stitch.daylevel_metric": "Daily rollup of core engagement + streaming + monetization metrics (used as the primary day-level fact).",
        "d11_stitch.daylevel_engagedpaid": "Daily rollup of engaged/paid users and interaction counts (chats, reactions, predictions, etc).",
        "d11_stitch.cjusers": "Daily user count for the CJ cohort (exact definition needs confirmation; used as a daily users series).",
        "d11_stitch.day_hour_watchtime": "Watch time (seconds) aggregated by day/hour for watch-along streams.",
        "d11_stitch.timespentonmoment": "Cumulative watch minutes on moments by hourly bucket (take last bucket per day for daily total).",
        "d11_stitch.moment_raw": "Daily moments uploaded and total uploaded duration (seconds).",
        "d11_stitch.sportan_userid_new": "List of SPORTAN user IDs (used to exclude internal/special accounts).",
        "d11_transactions.dreambucks_account_ledger": "Transactional DreamBucks ledger (debits/credits) used to compute DB spend and purchases.",
        "d11_transactions.live_streaming_stream": "Raw livestream records (start/end, status, influencer/creator).",
        "d11_transactions.dream11_userregistration": "User registration table; used here to identify SPORTAN users by `usertype`.",
    }.get(table_ref, "Referenced by sample queries.")


def generate_docs(
    *,
    athena: AthenaClient,
    query_files: list[QueryFile],
    row_limit: int,
    preview_rows: int,
    include_show_create: bool,
) -> dict[str, str]:
    # Collect table refs from all queries
    table_refs: set[str] = set()
    for q in query_files:
        table_refs.update(_extract_table_refs(q.sql))
    all_tables = sorted(table_refs)

    # Describe schemas
    schemas: dict[str, list[dict[str, Any]]] = {}
    create_ddls: dict[str, str] = {}
    for t in all_tables:
        try:
            schemas[t] = athena.describe_table_fq(t)
        except Exception as e:
            schemas[t] = [{"col_name": "__ERROR__", "data_type": str(e), "comment": ""}]
        if include_show_create:
            try:
                ddl = athena.show_create_table_fq(t)
                if ddl:
                    create_ddls[t] = ddl
            except Exception:
                pass

    # Execute queries (capped)
    executed: dict[str, QueryResult | None] = {}
    exec_errors: dict[str, str] = {}
    for q in query_files:
        try:
            executed[q.name] = athena.execute_query(q.sql, max_rows=row_limit, enforce_limit=True)
        except Exception as e:
            executed[q.name] = None
            exec_errors[q.name] = str(e)

    # ---------------- catalog.txt ----------------
    catalog_lines: list[str] = []
    catalog_lines.append("# Data catalog (generated)")
    catalog_lines.append("")
    catalog_lines.append("This is generated from the SQL templates in `knowledge/queries/` by describing every referenced table.")
    catalog_lines.append("")
    catalog_lines.append("## Tables referenced by sample queries")
    catalog_lines.append("")
    for t in all_tables:
        catalog_lines.append(f"### `{t}`")
        catalog_lines.append("")
        if t in create_ddls:
            catalog_lines.append("**DDL (SHOW CREATE TABLE)**")
            catalog_lines.append("")
            catalog_lines.append("```sql")
            catalog_lines.append(create_ddls[t].rstrip())
            catalog_lines.append("```")
            catalog_lines.append("")
        catalog_lines.append(_format_schema(schemas.get(t, [])))
        catalog_lines.append("")

    # ---------------- domain.txt ----------------
    domain_lines: list[str] = []
    domain_lines.append("# Domain knowledge (generated)")
    domain_lines.append("")
    domain_lines.append("Dream11 watch-along resembles Twitch-style livestreaming:")
    domain_lines.append("- Users watch creators' streams during matches, chat, react, and participate in predictions/group goals.")
    domain_lines.append("- Users can pay using DreamBucks (DB).")
    domain_lines.append("- Creators upload short highlight clips (“moments”) from live streams.")
    domain_lines.append("")
    domain_lines.append("## Key concepts")
    domain_lines.append("")
    domain_lines.append("- **IST vs UTC**: Most metrics are reported in IST; queries often convert using `+ INTERVAL '330' MINUTE` or `AT TIME ZONE 'Asia/Kolkata'`.")
    domain_lines.append("- **Sportan**: Some queries exclude SPORTAN (internal/special) users; treat SPORTAN-exclusion as an important filter when reporting public metrics.")
    domain_lines.append("- **Grain**: Many base metrics are day-level in IST (`eventdate`, `day_ist`). Stream data may span days and must be split across days.")
    domain_lines.append("")
    domain_lines.append("## Table cheat sheet (from sample queries)")
    domain_lines.append("")
    for t in all_tables:
        cols = _columns_from_schema(schemas.get(t, []))
        grain = _infer_grain(cols)
        domain_lines.append(f"### `{t}`")
        domain_lines.append("")
        domain_lines.append(_table_description(t))
        domain_lines.append("")
        domain_lines.append(f"- **Grain (inferred)**: {grain}")
        if cols:
            domain_lines.append("- **Key columns**:")
            # show up to 12 columns; prefer time + id-like fields first
            preferred = ["day_ist", "eventdate", "hour_bucket", "hour_of_day", "id", "userid", "customer_id", "influencerid"]
            ordered: list[tuple[str, str]] = []
            used: set[str] = set()
            for p in preferred:
                for c, tpe in cols:
                    if c.lower() == p and c.lower() not in used:
                        ordered.append((c, tpe))
                        used.add(c.lower())
            for c, tpe in cols:
                if c.lower() in used:
                    continue
                ordered.append((c, tpe))
            for c, tpe in ordered[:12]:
                domain_lines.append(f"  - `{c}` ({tpe})")
        domain_lines.append("")
    domain_lines.append("")

    # ---------------- metrics.txt ----------------
    metrics_lines: list[str] = []
    metrics_lines.append("# Metrics (generated)")
    metrics_lines.append("")
    metrics_lines.append("This section describes the *intent* and *computation* patterns from the sample queries.")
    metrics_lines.append("")
    metrics_lines.append("## Engagement / activity")
    metrics_lines.append("")
    metrics_lines.append("- **DAU**: `d11_stitch.daylevel_metric.dau` (and related `livestream_dau`, `moment_dau`, `fantasy_dau`) aggregated by `eventdate` (IST).")
    metrics_lines.append("- **Chats / reactions / predictions / superchats / groupgoals**: `d11_stitch.daylevel_metric.{normal_chats,reaction,prediction,superchats,groupgoal}`.")
    metrics_lines.append("- **Engaged users / paid users**: `d11_stitch.daylevel_engagedpaid.{engaged_users,paid_users}` (joined to day by IST date in the sample query).")
    metrics_lines.append("- **CJ users**: `d11_stitch.cjusers.users` by `eventdate` (definition of CJ should be confirmed).")
    metrics_lines.append("")
    metrics_lines.append("## Watch time")
    metrics_lines.append("")
    metrics_lines.append("- **Watch minutes (watch-along)**: sum of `watch_seconds / 60` from `d11_stitch.day_hour_watchtime`, grouped to day (see `knowledge/queries/Code.sql`).")
    metrics_lines.append("- **Moments watchtime**: daily value from `d11_stitch.timespentonmoment.total_watch_min_cum` by taking the last `hour_bucket` per `day_ist` (see `knowledge/queries/Code.sql`).")
    metrics_lines.append("- **Total watch minutes**: `watch_minutes_watch_along + moments_watchtime`.")
    metrics_lines.append("")
    metrics_lines.append("## Streaming supply")
    metrics_lines.append("")
    metrics_lines.append("- **Total stream minutes**: from `d11_transactions.live_streaming_stream` where `streamstatus='COMPLETED'` and start/end present; convert to IST, split streams across days, then sum seconds per day / 60 (see `Creator level strem minutes.sql`).")
    metrics_lines.append("- **Covered hours**: per IST day, the total time where at least one stream is live (event sweep using +1 at start, -1 at end).")
    metrics_lines.append("- **Distinct streams / creators**: `d11_stitch.daylevel_metric.{distinct_streams,distinct_creators}` (often easier than recomputing from raw).")
    metrics_lines.append("")
    metrics_lines.append("## DreamBucks (DB) spend/purchase")
    metrics_lines.append("")
    metrics_lines.append("- **Public DB spent**: from `d11_transactions.dreambucks_account_ledger` where `lower(transaction_type)='debit'`, excluding SPORTAN users via `d11_stitch.sportan_userid_new` (see `knowledge/queries/_spent.sql`).")
    metrics_lines.append("- **Public DB purchased**: credits with `source_id = 3`, excluding meta `DreamCoins converted to DreamBucks`, excluding SPORTAN (see `knowledge/queries/_spent.sql`).")
    metrics_lines.append("")
    metrics_lines.append("## Common pitfalls")
    metrics_lines.append("")
    metrics_lines.append("- **Timezone alignment**: join on the formatted IST date consistently (many sample queries use `DATE_FORMAT(ts AT TIME ZONE 'Asia/Kolkata', '%Y-%m-%d')`).")
    metrics_lines.append("- **Overnight streams**: never allocate full duration to start day; always split across days (sample uses `SEQUENCE(date_trunc('day', start_ist), date_trunc('day', end_ist), INTERVAL '1' DAY)`).")
    metrics_lines.append("- **SPORTAN filtering**: replicate SPORTAN-exclusion logic when reporting public creator metrics or public user spend.")
    metrics_lines.append("")

    # ---------------- examples.txt ----------------
    examples_lines: list[str] = []
    examples_lines.append("# Example queries (generated)")
    examples_lines.append("")
    examples_lines.append("All query previews are capped to 100 rows (and 20 rows shown in this doc).")
    examples_lines.append("")
    for q in query_files:
        examples_lines.append(f"## {q.name}")
        examples_lines.append("")
        examples_lines.append("**SQL**")
        examples_lines.append("")
        examples_lines.append("```sql")
        examples_lines.append(q.sql.rstrip())
        examples_lines.append("```")
        examples_lines.append("")
        refs = _extract_table_refs(q.sql)
        if refs:
            examples_lines.append("**Tables referenced**")
            examples_lines.append("")
            for t in refs:
                examples_lines.append(f"- `{t}`")
            examples_lines.append("")
        if q.name in exec_errors:
            examples_lines.append("**Execution error**")
            examples_lines.append("")
            examples_lines.append(f"`{exec_errors[q.name]}`")
            examples_lines.append("")
        else:
            res = executed.get(q.name)
            if res is not None:
                examples_lines.append("**Result preview**")
                examples_lines.append("")
                examples_lines.append(_format_query_result_preview(res, max_rows=preview_rows))
                examples_lines.append("")

    return {
        "catalog.txt": "\n".join(catalog_lines).rstrip() + "\n",
        "domain.txt": "\n".join(domain_lines).rstrip() + "\n",
        "metrics.txt": "\n".join(metrics_lines).rstrip() + "\n",
        "examples.txt": "\n".join(examples_lines).rstrip() + "\n",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate knowledge docs from sample Athena queries.")
    parser.add_argument("--row-limit", type=int, default=100, help="Hard cap on rows fetched per query.")
    parser.add_argument("--preview-rows", type=int, default=20, help="Rows shown per query in examples.txt.")
    parser.add_argument("--include-show-create", action="store_true", help="Include SHOW CREATE TABLE DDL in catalog.")
    parser.add_argument("--workgroup", default="data_stitch")
    parser.add_argument("--database", default="d11_stitch")
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    qdir = _queries_dir()
    query_files = _read_query_files(qdir)
    if not query_files:
        raise SystemExit(f"No .sql files found in {qdir}")

    athena = AthenaClient(workgroup=args.workgroup, database=args.database, region=args.region)
    docs = generate_docs(
        athena=athena,
        query_files=query_files,
        row_limit=max(1, min(args.row_limit, 100)),
        preview_rows=max(1, min(args.preview_rows, 50)),
        include_show_create=bool(args.include_show_create),
    )

    out_dir = _knowledge_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in docs.items():
        (out_dir / filename).write_text(content, encoding="utf-8")

    print(f"Wrote {len(docs)} files to {out_dir}")


if __name__ == "__main__":
    main()


