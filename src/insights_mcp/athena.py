"""
Athena client for executing queries against the data warehouse.

Uses AWS SSO credentials from the default profile.
"""

import re
import time
from dataclasses import dataclass
from typing import Any

import boto3


@dataclass
class QueryResult:
    """Result of an Athena query."""
    columns: list[str]
    rows: list[dict[str, Any]]
    query_execution_id: str
    state: str
    statistics: dict[str, Any] | None = None


class AthenaClient:
    """Client for executing Athena queries."""

    def __init__(
        self,
        workgroup: str = "data_stitch",
        database: str = "d11_stitch",
        region: str = "us-east-1",
        max_results: int = 100,
        poll_interval: float = 1.0,
        timeout: float = 300.0,
    ):
        self.workgroup = workgroup
        self.database = database
        self.region = region
        # Athena API pagination page size. This is NOT a hard cap on total rows
        # returned unless we enforce it in `_fetch_results`.
        self.max_results = max_results
        self.poll_interval = poll_interval
        self.timeout = timeout
        self._client = boto3.client("athena", region_name=region)

    _NON_WRAPPABLE_PREFIX = re.compile(
        r"^\s*(SHOW|DESCRIBE|EXPLAIN|MSCK|USE|SET|CREATE|DROP|ALTER|INSERT|UPDATE|DELETE)\b",
        re.IGNORECASE,
    )

    @staticmethod
    def _strip_trailing_semicolon(query: str) -> str:
        return query.strip().rstrip(";").strip()

    def _maybe_wrap_with_limit(self, query: str, limit: int) -> str:
        q = self._strip_trailing_semicolon(query)
        if self._NON_WRAPPABLE_PREFIX.search(q):
            return q
        # Wrap to enforce an upper bound on result rows.
        return f"SELECT * FROM (\n{q}\n) AS _q\nLIMIT {int(limit)}"

    def execute_query(
        self,
        query: str,
        *,
        max_rows: int | None = None,
        enforce_limit: bool = False,
    ) -> QueryResult:
        """
        Execute a query and wait for results.

        Args:
            query: SQL query to execute
            max_rows: Maximum number of rows to fetch from Athena results (client-side cap).
            enforce_limit: If True and max_rows is set, wrap the query with a LIMIT to
                enforce a server-side cap where possible.

        Returns:
            QueryResult with columns, rows, and metadata

        Raises:
            TimeoutError: If query exceeds timeout
            RuntimeError: If query fails
        """
        query_to_run = query
        if enforce_limit and max_rows is not None:
            query_to_run = self._maybe_wrap_with_limit(query, max_rows)

        # Start query execution
        response = self._client.start_query_execution(
            QueryString=query_to_run,
            QueryExecutionContext={"Database": self.database},
            WorkGroup=self.workgroup,
        )
        query_execution_id = response["QueryExecutionId"]

        # Wait for completion
        state = self._wait_for_completion(query_execution_id)

        if state != "SUCCEEDED":
            execution = self._client.get_query_execution(
                QueryExecutionId=query_execution_id
            )
            reason = execution["QueryExecution"]["Status"].get(
                "StateChangeReason", "Unknown error"
            )
            raise RuntimeError(f"Query failed: {reason}")

        # Fetch results
        return self._fetch_results(query_execution_id, max_rows=max_rows)

    def _wait_for_completion(self, query_execution_id: str) -> str:
        """Poll until query completes or times out."""
        start_time = time.time()

        while True:
            if time.time() - start_time > self.timeout:
                raise TimeoutError(
                    f"Query {query_execution_id} timed out after {self.timeout}s"
                )

            response = self._client.get_query_execution(
                QueryExecutionId=query_execution_id
            )
            state = response["QueryExecution"]["Status"]["State"]

            if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
                return state

            time.sleep(self.poll_interval)

    def _fetch_results(self, query_execution_id: str, max_rows: int | None = None) -> QueryResult:
        """Fetch query results with pagination, optionally capping total rows returned."""
        columns: list[str] = []
        rows: list[dict[str, Any]] = []
        next_token: str | None = None
        is_first_page = True

        while True:
            if max_rows is not None and len(rows) >= max_rows:
                break

            kwargs: dict[str, Any] = {
                "QueryExecutionId": query_execution_id,
                "MaxResults": self.max_results,
            }
            if next_token:
                kwargs["NextToken"] = next_token

            if max_rows is not None:
                remaining = max_rows - len(rows)
                # First page includes a header row, so request one extra row.
                page_cap = remaining + (1 if is_first_page else 0)
                kwargs["MaxResults"] = max(1, min(int(self.max_results), int(page_cap)))

            response = self._client.get_query_results(**kwargs)
            result_set = response["ResultSet"]

            # Extract column names from first page
            if is_first_page:
                columns = [
                    col["Label"] or col["Name"]
                    for col in result_set["ResultSetMetadata"]["ColumnInfo"]
                ]
                # Skip header row on first page
                data_rows = result_set["Rows"][1:]
                is_first_page = False
            else:
                data_rows = result_set["Rows"]

            # Convert rows to dicts
            for row in data_rows:
                row_data = {}
                for i, cell in enumerate(row.get("Data", [])):
                    value = cell.get("VarCharValue")
                    row_data[columns[i]] = value
                rows.append(row_data)
                if max_rows is not None and len(rows) >= max_rows:
                    break

            next_token = response.get("NextToken")
            if not next_token or (max_rows is not None and len(rows) >= max_rows):
                break

        # Get execution statistics
        execution = self._client.get_query_execution(
            QueryExecutionId=query_execution_id
        )
        statistics = execution["QueryExecution"].get("Statistics")

        return QueryResult(
            columns=columns,
            rows=rows,
            query_execution_id=query_execution_id,
            state="SUCCEEDED",
            statistics=statistics,
        )

    def list_tables(self, database: str | None = None) -> list[str]:
        """List all tables in the database."""
        db = database or self.database
        result = self.execute_query(f"SHOW TABLES IN {db}")
        return [row.get("tab_name", "") for row in result.rows]

    def describe_table(self, table: str, database: str | None = None) -> list[dict]:
        """Get schema information for a table."""
        db = database or self.database
        result = self.execute_query(f"DESCRIBE {db}.{table}", max_rows=500)
        return self._normalize_describe_rows(result)

    def describe_table_fq(self, full_table_name: str) -> list[dict]:
        """Get schema information for a fully-qualified table (db.table)."""
        full_table_name = full_table_name.strip()
        if "." not in full_table_name:
            return self.describe_table(full_table_name)
        db, table = full_table_name.split(".", 1)
        return self.describe_table(table, database=db)

    @staticmethod
    def _normalize_describe_rows(result: QueryResult) -> list[dict[str, Any]]:
        """
        Athena DESCRIBE sometimes returns a single tab-separated column in `col_name`
        even when metadata advertises multiple columns.
        Normalize to `{col_name, data_type, comment}` rows.
        """
        if not result.rows:
            return []
        if "col_name" not in result.columns:
            return result.rows

        # Heuristic: if rows only contain `col_name` with embedded tabs, parse it.
        has_tab = any("\t" in (row.get("col_name") or "") for row in result.rows)
        has_other_cols = any(
            any(k for k in row.keys() if k != "col_name") for row in result.rows
        )
        if not has_tab or has_other_cols:
            return result.rows

        normalized: list[dict[str, Any]] = []
        for row in result.rows:
            raw = (row.get("col_name") or "").rstrip("\n")
            parts = raw.split("\t")
            parts += ["", "", ""]
            normalized.append(
                {
                    "col_name": parts[0].strip(),
                    "data_type": parts[1].strip(),
                    "comment": parts[2].strip(),
                }
            )
        return normalized

    def show_create_table_fq(self, full_table_name: str) -> str:
        """Return the CREATE TABLE statement for a fully-qualified table (db.table)."""
        full_table_name = full_table_name.strip()
        if "." not in full_table_name:
            full_table_name = f"{self.database}.{full_table_name}"
        result = self.execute_query(f"SHOW CREATE TABLE {full_table_name}", max_rows=1000)
        if not result.rows:
            return ""
        # Athena returns a single column (typically `createtab_stmt`) with one line per row.
        col = result.columns[0] if result.columns else None
        lines: list[str] = []
        for row in result.rows:
            if not row:
                continue
            if col and col in row and row[col] is not None:
                lines.append(str(row[col]))
            else:
                lines.append(str(next(iter(row.values()))))
        return "\n".join(lines).rstrip()

    def get_sample_data(
        self, table: str, limit: int = 10, database: str | None = None
    ) -> QueryResult:
        """Get sample rows from a table."""
        db = database or self.database
        return self.execute_query(f"SELECT * FROM {db}.{table} LIMIT {limit}")

    def get_sample_data_fq(self, full_table_name: str, limit: int = 10) -> QueryResult:
        """Get sample rows from a fully-qualified table (db.table)."""
        full_table_name = full_table_name.strip()
        if "." not in full_table_name:
            full_table_name = f"{self.database}.{full_table_name}"
        return self.execute_query(f"SELECT * FROM {full_table_name} LIMIT {int(limit)}")
