## Insights MCP

Analytics MCP server + Athena helper utilities for the Dream11 `d11_stitch` warehouse.

### Setup

This repo uses `uv`:

```bash
cd /Users/dhruvnigam/Projects/insights-mcp
uv sync --frozen
```

### Generate knowledge docs (recommended)

This executes the sample SQL queries under `knowledge/queries/` (hard-capped to **100 rows**) and writes:

- `knowledge/catalog.txt`
- `knowledge/domain.txt`
- `knowledge/metrics.txt`
- `knowledge/examples.txt`

Run:

```bash
cd /Users/dhruvnigam/Projects/insights-mcp
uv run insights-mcp-knowledge-gen --include-show-create
```

### Run the MCP server

The server exposes tools like `run_query`, `list_tables`, `describe_table`, `get_sample_data` and resources backed by the generated knowledge docs.

```bash
cd /Users/dhruvnigam/Projects/insights-mcp
uv run insights-mcp
```

### Available Prompts

The MCP server provides several prompts to enhance your workflow:

#### 1. `answer_question`
Guides the agent to answer business questions using SQL queries. Provides structured steps for:
- Finding relevant tables
- Understanding metrics
- Reviewing domain context
- Writing and executing queries

#### 2. `create_comprehensive_report`
Creates a detailed markdown report of your analysis session including:
- TL;DR summary
- Executive summary
- Detailed findings
- Key insights and recommendations
- All SQL queries used
- Data quality notes

Reports are saved to `reports/report_YYYYMMDD_HHMMSS.md`

#### 3. `submit_feedback`
Interactive feedback collection to improve the knowledge base:
- Rate your satisfaction with results
- Report accuracy issues or misunderstandings
- Identify missed tables, schemas, or metrics
- Suggest improvements to documentation

Feedback is saved to `feedback/user_feedback_YYYYMMDD_HHMMSS.md`

**Note**: GitHub integration for automatic PR creation is planned but not yet implemented.

#### 4. `generate_feedback`
Creates comprehensive feedback about the knowledge base effectiveness after answering questions:
- Assesses knowledge availability and quality
- Identifies gaps in catalog, domain, metrics, and examples
- Provides specific suggestions for improvements
- Rates overall effectiveness

Feedback is saved to `feedback/feedback_YYYYMMDD_HHMMSS.md`

### Feedback Agent

Process accumulated feedback and generate actionable improvements:

```bash
cd /Users/dhruvnigam/Projects/insights-mcp
python3 src/insights_mcp/feedback_agent.py
# or if installed: uv run insights-mcp-feedback-agent
```

The feedback agent:
1. Reads all feedback files in `feedback/`
2. Analyzes them against the knowledge base
3. Generates categorized actionable items
4. Creates a consolidated report at `feedback/consolidated_actionables.md`

See `feedback/README.md` for more details.

### Notes

- Athena access assumes your AWS credentials (SSO) are already available in your environment.
- The `run_query` tool enforces a **100-row** cap to avoid returning large result sets.
- Reports and feedback files are gitignored by default but can be committed if needed.


