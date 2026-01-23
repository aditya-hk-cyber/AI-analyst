"""
Insights MCP Server - Analytics MCP server for d11_stitch data warehouse.

Provides tools for querying Athena, exploring schemas, and analytics prompts.
"""

from pathlib import Path

from fastmcp import FastMCP

from .athena import AthenaClient, QueryResult

# Initialize MCP server
mcp = FastMCP(
    "InsightsMCP",
    instructions="""You are an analytics assistant with access to the d11_stitch data warehouse.

Use the available tools to:
- Explore available tables and their schemas
- Run SQL queries to answer data questions
- Get sample data to understand table contents

Resources available for context:
- insights://knowledge/catalog - Schema catalog with table descriptions
- insights://knowledge/domain - Business domain knowledge and terminology
- insights://knowledge/metrics - Metric definitions and computations
- insights://knowledge/examples - Example SQL queries
- insights://knowledge/queries/* - Pre-built SQL query templates

Always check the knowledge resources before writing queries.
Start by understanding what tables are available and their structure.""",
)

# Initialize Athena client
athena = AthenaClient()


# ============== HELPER FUNCTIONS ==============


def format_query_result(result: QueryResult, max_rows: int = 50) -> str:
    """Format query result as a readable string."""
    lines = []

    # Header
    lines.append(f"Query ID: {result.query_execution_id}")
    lines.append(f"Columns: {', '.join(result.columns)}")
    lines.append(f"Total rows: {len(result.rows)}")

    if result.statistics:
        data_scanned = result.statistics.get("DataScannedInBytes", 0)
        exec_time = result.statistics.get("TotalExecutionTimeInMillis", 0)
        lines.append(f"Data scanned: {data_scanned / 1024 / 1024:.2f} MB")
        lines.append(f"Execution time: {exec_time / 1000:.2f}s")

    lines.append("")

    # Data as markdown table
    if result.rows:
        display_rows = result.rows[:max_rows]

        # Header row
        lines.append("| " + " | ".join(result.columns) + " |")
        lines.append("| " + " | ".join(["---"] * len(result.columns)) + " |")

        # Data rows
        for row in display_rows:
            values = [str(row.get(col, "NULL"))[:50] for col in result.columns]
            lines.append("| " + " | ".join(values) + " |")

        if len(result.rows) > max_rows:
            lines.append(f"\n... and {len(result.rows) - max_rows} more rows")

    return "\n".join(lines)


# ============== TOOLS ==============


@mcp.tool()
def run_query(query: str, max_rows: int = 100) -> str:
    """
    Execute a SQL query against the d11_stitch database.

    Args:
        query: SQL query to execute. Use standard Presto/Trino SQL syntax.
        max_rows: Maximum number of rows to return in the response (default: 100)

    Returns:
        Formatted query results with columns, data, and execution statistics.

    Example:
        run_query("SELECT * FROM d11_stitch.timespentonmoment LIMIT 10")
    """
    try:
        max_rows = min(int(max_rows), 100)
        result = athena.execute_query(query, max_rows=max_rows, enforce_limit=True)
        return format_query_result(result, max_rows=max_rows)
    except Exception as e:
        return f"Query failed: {str(e)}"


@mcp.tool()
def list_tables(database: str = "d11_stitch") -> str:
    """
    List all tables available in the specified database.

    Args:
        database: Database name (default: d11_stitch)

    Returns:
        List of table names in the database.
    """
    try:
        tables = athena.list_tables(database)
        return f"Tables in {database}:\n" + "\n".join(f"  - {t}" for t in tables)
    except Exception as e:
        return f"Failed to list tables: {str(e)}"


@mcp.tool()
def describe_table(table: str, database: str = "d11_stitch") -> str:
    """
    Get the schema (columns and types) for a table.

    Args:
        table: Table name to describe
        database: Database name (default: d11_stitch)

    Returns:
        Table schema with column names and data types.
    """
    try:
        schema = athena.describe_table(table, database)
        lines = [f"Schema for {database}.{table}:", ""]
        lines.append("| Column | Type |")
        lines.append("| --- | --- |")
        for row in schema:
            col_name = row.get("col_name", "")
            data_type = row.get("data_type", "")
            # Skip partition info rows
            if col_name and not col_name.startswith("#"):
                lines.append(f"| {col_name} | {data_type} |")
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to describe table: {str(e)}"


@mcp.tool()
def get_sample_data(table: str, limit: int = 5, database: str = "d11_stitch") -> str:
    """
    Get a sample of rows from a table to understand its contents.

    Args:
        table: Table name to sample
        limit: Number of rows to return (default: 5, max: 20)
        database: Database name (default: d11_stitch)

    Returns:
        Sample rows from the table.
    """
    limit = min(limit, 20)  # Cap at 20 rows for samples
    try:
        result = athena.get_sample_data(table, limit, database)
        return format_query_result(result, max_rows=limit)
    except Exception as e:
        return f"Failed to get sample data: {str(e)}"


# ============== RESOURCES ==============

def _get_knowledge_path() -> Path:
    """Get the path to the knowledge directory."""
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "knowledge"


def _read_knowledge_file(filepath: Path) -> str:
    """Read a knowledge file and return its content."""
    try:
        return filepath.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.resource("insights://knowledge/catalog")
def get_catalog() -> str:
    """
    Schema catalog for all tables in d11_stitch database.
    Contains table descriptions, column definitions, and relationships.
    """
    path = _get_knowledge_path() / "catalog.txt"
    return _read_knowledge_file(path)


@mcp.resource("insights://knowledge/domain")
def get_domain() -> str:
    """
    Business domain knowledge and terminology.
    Contains definitions, context, and business rules.
    """
    path = _get_knowledge_path() / "domain.txt"
    return _read_knowledge_file(path)


@mcp.resource("insights://knowledge/metrics")
def get_metrics() -> str:
    """
    Metric definitions and computation formulas.
    Contains how key business metrics are calculated.
    """
    path = _get_knowledge_path() / "metrics.txt"
    return _read_knowledge_file(path)


@mcp.resource("insights://knowledge/examples")
def get_examples() -> str:
    """
    Example SQL queries for common analytics tasks.
    Use these as templates for building new queries.
    """
    path = _get_knowledge_path() / "examples.txt"
    return _read_knowledge_file(path)


@mcp.resource("insights://knowledge/queries/spent")
def get_query_spent() -> str:
    """SQL query: Time spent analysis."""
    path = _get_knowledge_path() / "queries" / "_spent.sql"
    return _read_knowledge_file(path)


@mcp.resource("insights://knowledge/queries/chats-predictions-reactions-superchats")
def get_query_chats_etc() -> str:
    """SQL query: Chats, Predictions, reactions, and superchats analysis."""
    path = _get_knowledge_path() / "queries" / "Chats, Predictions, reactions, superchats.sql"
    return _read_knowledge_file(path)


@mcp.resource("insights://knowledge/queries/code")
def get_query_code() -> str:
    """SQL query: Code-related analysis."""
    path = _get_knowledge_path() / "queries" / "Code.sql"
    return _read_knowledge_file(path)


@mcp.resource("insights://knowledge/queries/creator-level-stream-minutes")
def get_query_creator_stream_minutes() -> str:
    """SQL query: Creator level stream minutes analysis."""
    path = _get_knowledge_path() / "queries" / "Creator level strem minutes.sql"
    return _read_knowledge_file(path)


@mcp.resource("insights://knowledge/queries/day-level-creators-streams-moments")
def get_query_day_level() -> str:
    """SQL query: Day level creators, active streams, and moments uploaded."""
    path = _get_knowledge_path() / "queries" / "Day level creatos, active streams, moments uploaded..sql"
    return _read_knowledge_file(path)


# ============== PROMPTS ==============

@mcp.prompt()
def answer_question() -> str:
    """
    Generate a prompt for writing a SQL query to answer a business question.

    Args:
        question: The business question to answer with data
    """
    return f"""You are a pricipal data analyst.Answer the questions by running one or more sql queries."

Steps:
1. Read insights://knowledge/catalog to find relevant tables
2. Check insights://knowledge/metrics for metric definitions
3. Review insights://knowledge/domain for business context
4. Look at insights://knowledge/examples for similar query patterns
5. Check insights://knowledge/queries/* for pre-built templates
6. Write the SQL query using Presto/Trino syntax
7. Execute the query and interpret the results

Important:
- Use appropriate aggregations and filters
- Consider time zones (data is in IST)
- Limit results for large queries
- Add comments explaining the query logic"""


@mcp.prompt()
def generate_feedback() -> str:
    """
    Generate feedback about the MCP server's knowledge base.

    Args:
        question_answered: The question or task that was just completed
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return f"""You just completed answering a question.

Now, create a comprehensive feedback report about your experience with the knowledge base.
Save this feedback as a markdown file at: /Users/dhruvnigam/Projects/insights-mcp/feedback/feedback_{timestamp}.md

Your feedback report should include the following sections:

## Question/Task Completed

## Knowledge Availability Assessment
- Was there sufficient information in the knowledge resources to answer this question?
- Which knowledge resources were most helpful (catalog, domain, metrics, examples, queries)?
- What information was missing or incomplete?
- Did you have to make assumptions due to missing information?

## Knowledge Quality Assessment
- Was there any conflicting or contradictory information across different resources?
- Were there any inconsistencies in terminology, definitions, or metric calculations?
- Were the examples and query templates relevant and accurate for this task?
- Was the documentation clear and easy to understand?

## Efficiency and Usability
- What specific information, if available, would have made this task easier or faster?
- Did you have to query multiple tables to piece together information?
- Were there any redundant or unclear sections in the knowledge base?

## Gaps and Missing Information
Identify specific gaps in each knowledge area:
- **Catalog gaps**: Missing table documentation, unclear column descriptions, missing relationships
- **Domain gaps**: Missing business context, unclear terminology, missing definitions
- **Metrics gaps**: Missing metric definitions, unclear calculation logic, missing formulas
- **Examples gaps**: Missing query patterns, outdated examples, lack of complex query examples

## Suggestions for Knowledge Base Enhancement
Provide specific, actionable suggestions:
- New sections to add to catalog.txt (be specific about which tables/columns)
- Additional metrics to document in metrics.txt (include suggested formulas)
- Business context to add to domain.txt (be specific about which areas)
- New example queries for examples.txt (provide actual SQL examples)
- New query templates to add to the queries/ directory (describe what they should do)

## Overall Effectiveness Rating
Rate the overall effectiveness of the current knowledge base for this specific task:
- **Rating**: [1-5 scale where 1=Poor, 5=Excellent]
- **Reasoning**: Explain your rating
- **Top 3 Improvements**: List the three most impactful improvements that would increase this rating

---

Be specific, detailed, and constructive. Include concrete examples wherever possible.
Use actual table names, column names, and SQL snippets in your suggestions."""


@mcp.prompt()
def create_comprehensive_report() -> str:
    """
    Create a comprehensive markdown report of the discussion and analysis.
    
    This prompt guides the creation of a detailed report documenting the entire
    conversation, results, and queries used.
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return f"""Create a comprehensive markdown report documenting this discussion and analysis.

Save the report as: /Users/dhruvnigam/Projects/insights-mcp/reports/report_{timestamp}.md

The report should follow this structure:

# Analysis Report

## TL;DR

Provide a concise 3-5 sentence summary covering:
- The main question(s) asked
- Key findings/insights
- Critical metrics or numbers
- Main recommendations (if applicable)

## Executive Summary

A more detailed summary (1-2 paragraphs) that provides context and highlights the most important findings.

## Questions Addressed

List all questions that were asked during this discussion:
1. [First question]
2. [Second question]
3. ...

## Detailed Analysis

For each question, provide:

### Question 1: [Question text]

**Context**: Brief context about why this question was asked

**Findings**: 
- Present the results in a clear, structured way
- Use tables, bullet points, or numbered lists as appropriate
- Highlight key insights and patterns
- Include relevant numbers, percentages, trends

**Interpretation**:
- What do these results mean?
- Any surprising or notable patterns?
- Business implications

**Visualizations** (if applicable):
- Describe what charts or graphs would be useful
- Suggest how to visualize the data

---

[Repeat for each question]

## Key Insights

Synthesize the findings into key insights:
1. [First major insight]
2. [Second major insight]
3. ...

## Recommendations

Based on the analysis, provide actionable recommendations:
1. [First recommendation]
2. [Second recommendation]
3. ...

## Data Quality Notes

Document any data quality issues, assumptions, or caveats:
- Missing data
- Assumptions made
- Limitations of the analysis
- Areas requiring further investigation

## Technical Appendix

### Queries Used

For each query, provide:

#### Query 1: [Brief description]

**Purpose**: What this query was meant to find

**SQL Query**:
```sql
[Full SQL query here]
```

**Tables Used**:
- `database.table_name`: Description of what this table contains
- ...

**Results Summary**:
- Rows returned: X
- Data scanned: X MB
- Execution time: X seconds

---

[Repeat for each query]

### Metrics Calculated

List any custom metrics or calculations:
- **Metric Name**: Formula and explanation
- ...

### References

List the knowledge base resources consulted:
- insights://knowledge/catalog
- insights://knowledge/metrics
- [etc.]

---

**Report Generated**: {datetime.now().strftime("%B %d, %Y at %H:%M:%S")}

Make the report professional, well-formatted, and easy to read. Use appropriate markdown formatting including headers, tables, code blocks, and lists."""


@mcp.prompt()
def submit_feedback() -> str:
    """
    Collect structured feedback from the user about their experience.
    
    This prompt guides an interactive feedback collection process and prepares
    a feedback submission (GitHub integration to be added).
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return f"""Let's collect your feedback about this analysis session.

I'll ask you a series of questions to understand your experience. Please answer them, and I'll create a structured feedback document.

## Questions:

### 1. Overall Satisfaction
Were you happy with the results you received? (Yes/No/Partially)

### 2. Result Accuracy
Do you believe the results were accurate? If not, please describe:
- What seemed incorrect?
- What numbers or findings didn't match your expectations?
- Were there any obvious errors in the data?

### 3. Understanding and Communication
Was there any misunderstanding about:
- What you were asking for?
- How the data was interpreted?
- The context or scope of the analysis?

Please describe what could have been clearer.

### 4. Missing Information
Did the agent miss any relevant:
- **Tables**: Were there tables that should have been consulted but weren't?
- **Schemas**: Was the understanding of table schemas incomplete or incorrect?
- **Metrics**: Were there metrics that should have been calculated differently?
- **Business Context**: Was important business logic or context overlooked?

Please be specific about what was missed.

### 5. Knowledge Base Gaps
What information would have helped the agent do better:
- Missing table documentation?
- Unclear metric definitions?
- Missing example queries?
- Insufficient business context?

### 6. Query Quality
Were the SQL queries:
- Efficient and well-written?
- Easy to understand?
- Appropriate for the questions asked?

Any issues with the queries used?

### 7. Suggestions for Improvement
What specific improvements would make future analyses better:
- New tables to document in catalog.txt
- Metrics to add to metrics.txt
- Business rules to add to domain.txt
- Example queries to add to examples.txt

### 8. Additional Comments
Any other feedback, suggestions, or observations?

---

After collecting your responses, I'll create a structured feedback document and prepare it for submission.

**What happens next:**

Once you're satisfied with your feedback, I'll:

1. Create a formatted feedback file at: `/Users/dhruvnigam/Projects/insights-mcp/feedback/user_feedback_{timestamp}.md`

2. **[PLACEHOLDER: GitHub Integration]**
   - Automatically create a new branch: `feedback/{timestamp}`
   - Commit the feedback file
   - Open a Pull Request in the insights-mcp repository
   - Tag it with label: "user-feedback"
   
   *Note: GitHub integration is pending implementation. For now, the feedback file will be saved locally and can be manually submitted.*

3. The feedback will be processed by the feedback agent during the next run

Please provide your responses to the questions above, and I'll format them into a proper feedback document."""


# ============== MAIN ==============


def main():
    """Run the MCP server."""
    print("Starting InsightsMCP server...")
    mcp.run()


if __name__ == "__main__":
    main()
