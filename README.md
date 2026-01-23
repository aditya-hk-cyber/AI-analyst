## Insights MCP

Analytics MCP server + Athena helper utilities for the Dream11 `d11_stitch` warehouse.

### 1. Setup

This repo uses `uv`:

```bash
cd /Users/dhruvnigam/Projects/insights-mcp
uv sync --frozen
```

This will:
- Create a virtual environment
- Install `fastmcp`, `boto3`, and other dependencies
- Set up the package in editable mode

### 2. AWS Prerequisites

Before setting up the MCP server, ensure you have active AWS credentials with access to the `d11_stitch` warehouse.

#### 2.1 AWS SSO Authentication
This project uses AWS SSO (Single Sign-On) for authentication.

1. **Login to AWS Console**: Ensure you are logged into the **Dream11 3.0** AWS account in your browser.
2. **SSO Login via CLI**: Run the following command and follow the prompts in your browser:

```bash
aws sso login
```

3. **Automatic Credentials**: Once authenticated, the AWS CLI and the MCP server will automatically use your SSO session.

#### 2.2 Verify Credentials
Test your connection to AWS:

```bash
aws sts get-caller-identity
```

### 3. Verify Installation

```bash
# Check if the command is available
uv run insights-mcp --help

# Test AWS connection
uv run python -c "import boto3; print(boto3.client('athena').list_data_catalogs())"
```

---

## Cursor Integration

### Step 1: Locate Your Cursor MCP Configuration

Your Cursor MCP configuration file is at:
```
~/.cursor/mcp.json
```

### Step 2: Add Insights MCP Server

Open `~/.cursor/mcp.json` and add the `insights-mcp` server configuration:

```json
{
  "mcpServers": {
    "insights-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/dhruvnigam/Projects/insights-mcp",
        "run",
        "insights-mcp"
      ]
    },
    // ... your other MCP servers (github, livekit-docs, etc.)
  }
}
```

### Step 3: Restart Cursor

After saving the configuration:
1. Quit Cursor completely (`Cmd+Q` on Mac)
2. Reopen Cursor
3. The Insights MCP server will automatically start when you begin a chat

### Step 4: Verify Integration

In a new Cursor chat, try:
```
Can you list all tables in the d11_stitch database?
```

You should see the MCP server respond with available tables.

### Complete Example Configuration

Here's a complete example of `~/.cursor/mcp.json` with multiple servers:

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer YOUR_GITHUB_TOKEN"
      }
    },
    "livekit-docs": {
      "url": "https://docs.livekit.io/mcp",
      "headers": {}
    },
    "insights-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/dhruvnigam/Projects/insights-mcp",
        "run",
        "insights-mcp"
      ]
    }
  }
}
```

### Troubleshooting Cursor Integration

**Server not starting?**
```bash
# Test the server manually
cd /Users/dhruvnigam/Projects/insights-mcp
uv run insights-mcp
```

**Check Cursor logs:**
- Open Cursor
- Go to `Help` → `Show Logs`
- Look for MCP server errors

**Python version issues?**
```bash
# Verify Python version
uv run python --version  # Should be 3.11.x
```

**AWS credentials not working?**
```bash
# Verify AWS access
aws sts get-caller-identity
```

---

## Running the Server

### Running Standalone (for testing)

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

---

## Roadmap

- Deploy on vm
- Formalize feedback mechanism
- GitHub bot for feedback PRs
- Expand database coverage
- Enhanced query capabilities
- Better report generation
- Production API deployment
- Advanced analytics features
- Collaboration features
- Self-improving knowledge base
- Advanced integrations
