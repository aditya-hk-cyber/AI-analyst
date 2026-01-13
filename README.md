# Insights MCP

Analytics MCP server + Athena helper utilities for the Dream11 `d11_stitch` warehouse.

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
- [Cursor Integration](#cursor-integration)
- [Running the Server](#running-the-server)
- [Usage](#usage)
- [Available Prompts](#available-prompts)
- [Feedback System](#feedback-system)
- [Production Deployment](#production-deployment)
- [Roadmap](#roadmap)

---

## Quick Start

**For first-time setup:**
1. [Install prerequisites](#prerequisites)
2. [Set up locally](#local-setup)
3. [Configure Cursor](#cursor-integration)
4. Start using the MCP tools in Cursor!

---

## Prerequisites

Before setting up the Insights MCP server, ensure you have:

### Required
- **Python 3.11** (required, not 3.12+)
- **[uv](https://github.com/astral-sh/uv)** - Fast Python package manager
  ```bash
  # Install uv if you don't have it
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **AWS Credentials** - Configured for Athena access via AWS SSO
  ```bash
  # Setup AWS SSO first, then verify credentials
  aws sso login
  aws sts get-caller-identity
  ```
- **Cursor IDE** - For MCP integration

### Optional
- Git (for version control)
- GitHub account (for future feedback PR automation)

---

## Local Setup

### 1. Clone or Navigate to Repository

```bash
cd /Users/dhruvnigam/Projects/insights-mcp
```

### 2. Install Dependencies

```bash
# Install dependencies using uv
uv sync --frozen
```

This will:
- Create a virtual environment
- Install `fastmcp`, `boto3`, and other dependencies
- Set up the package in editable mode

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

The server will start and wait for MCP client connections.

### Running via Cursor (normal usage)

Once configured in `mcp.json`, Cursor automatically starts/stops the server as needed.

---

## Usage

### Available Tools

The MCP server exposes these tools to Cursor:

#### 1. `run_query`
Execute SQL queries against the d11_stitch database.

```python
run_query("SELECT * FROM d11_stitch.timespentonmoment LIMIT 10")
```

- Uses Presto/Trino SQL syntax
- Returns up to 100 rows (configurable)
- Includes execution statistics

#### 2. `list_tables`
List all tables in a database.

```python
list_tables(database="d11_stitch")
```

#### 3. `describe_table`
Get schema information for a table.

```python
describe_table(table="timespentonmoment", database="d11_stitch")
```

#### 4. `get_sample_data`
Get sample rows from a table.

```python
get_sample_data(table="timespentonmoment", limit=5)
```

### Available Resources

Resources provide context from the knowledge base:

- `insights://knowledge/catalog` - Schema catalog
- `insights://knowledge/domain` - Business domain knowledge
- `insights://knowledge/metrics` - Metric definitions
- `insights://knowledge/examples` - Example SQL queries
- `insights://knowledge/queries/*` - Pre-built query templates

---

## Available Prompts

**Tip:** In Cursor, you can type `/` in the chat to see and select available prompts from the MCP server.

### 1. `answer_question`
Guides the agent to answer business questions using SQL queries.

**Usage in Cursor:**
```
How many active users were there last week?
```

Or use slash command: `/answer_question`

The agent automatically follows best practices for query development.

### 2. `create_comprehensive_report`
Creates a detailed markdown report of your analysis session.

**Usage in Cursor:**
```
Can you create a comprehensive report of our analysis?
```

Or use slash command: `/create_comprehensive_report`

**Output:** `reports/report_YYYYMMDD_HHMMSS.md`

**Includes:**
- TL;DR summary
- Executive summary
- Detailed findings
- Key insights and recommendations
- All SQL queries used
- Data quality notes

### 3. `submit_feedback`
Interactive feedback collection to improve the knowledge base.

**Usage in Cursor:**
```
I'd like to submit feedback about this analysis
```

Or use slash command: `/submit_feedback`

The agent will guide you through structured feedback questions.

**Output:** `feedback/user_feedback_YYYYMMDD_HHMMSS.md`

---

## Feedback System

### How It Works

1. **Collect Feedback** - Use `submit_feedback` prompt
2. **Process Feedback** - Run the feedback agent to analyze accumulated feedback
3. **Implement Improvements** - Update knowledge base based on actionable items

### Processing Feedback

After collecting multiple feedback files:

```bash
cd /Users/dhruvnigam/Projects/insights-mcp
uv run insights-mcp-feedback-agent
# or
python3 src/insights_mcp/feedback_agent.py
```

**What it does:**
1. Reads all feedback files in `feedback/`
2. Analyzes them against the current knowledge base
3. Generates categorized actionable items
4. Creates consolidated report: `feedback/consolidated_actionables.md`

### Feedback Files

- **User Feedback:** `feedback/user_feedback_*.md` - Manual feedback from users
- **Consolidated:** `feedback/consolidated_actionables.md` - Processed improvements
- **Sample:** `feedback/sample_feedback.txt` - Example feedback format

See `feedback/README.md` for more details.

---

## Production Deployment

### Deployment Options

#### Option 1: Google Cloud Run (Recommended)

**Pros:**
- Serverless (pay per use)
- Auto-scaling
- Easy HTTPS setup
- Built-in authentication

**Steps:**

1. **Create Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY . .

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8080

# Run server
CMD ["uv", "run", "insights-mcp"]
```

2. **Build and Deploy**

```bash
# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Build image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/insights-mcp

# Deploy to Cloud Run
gcloud run deploy insights-mcp \
  --image gcr.io/YOUR_PROJECT_ID/insights-mcp \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated  # Or use --no-allow-unauthenticated for auth
```

3. **Set Environment Variables**

```bash
# Set AWS credentials as secrets
gcloud run services update insights-mcp \
  --set-env-vars AWS_ACCESS_KEY_ID=YOUR_KEY \
  --set-env-vars AWS_SECRET_ACCESS_KEY=YOUR_SECRET \
  --set-env-vars AWS_DEFAULT_REGION=us-east-1
```

#### Option 2: API Gateway with Cloud Run

For better access control and rate limiting:

1. Deploy to Cloud Run (as above)
2. Create API Gateway configuration
3. Point API Gateway to Cloud Run service
4. Enable authentication and rate limiting

#### Option 3: Self-Hosted

```bash
# On your server
cd /path/to/insights-mcp
uv sync --frozen

# Run with systemd
sudo systemctl enable insights-mcp
sudo systemctl start insights-mcp
```

### Authentication Setup

#### For HTTP MCP Servers

Update your MCP configuration to use HTTP with authentication:

```json
{
  "mcpServers": {
    "insights-mcp": {
      "type": "http",
      "url": "https://your-cloudrun-url.run.app/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

#### Authentication Methods

**1. API Key Authentication**

Add to your `server.py`:

```python
from fastmcp import FastMCP

mcp = FastMCP(
    "InsightsMCP",
    api_key_env="INSIGHTS_API_KEY"  # Checks X-API-Key header
)
```

**2. Google Cloud IAM**

```bash
# Require authentication
gcloud run services update insights-mcp \
  --no-allow-unauthenticated

# Grant access to specific users
gcloud run services add-iam-policy-binding insights-mcp \
  --member="user:someone@example.com" \
  --role="roles/run.invoker"
```

**3. OAuth 2.0**

Use Cloud Run with Identity-Aware Proxy (IAP).

### Environment Variables for Production

Required environment variables:

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_DEFAULT_REGION=us-east-1

# Optional: API Key
INSIGHTS_API_KEY=your-secret-key

# Optional: Database override
ATHENA_DATABASE=d11_stitch
ATHENA_OUTPUT_BUCKET=s3://your-athena-results/
```

### Monitoring and Logs

**Cloud Run:**
```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=insights-mcp"

# View metrics
gcloud monitoring dashboards list
```

**Self-Hosted:**
```bash
# View logs
journalctl -u insights-mcp -f

# Monitor with systemd
systemctl status insights-mcp
```

### Security Best Practices

1. **Never commit credentials** - Use environment variables or secret managers
2. **Use HTTPS** - Always encrypt traffic in production
3. **Enable authentication** - Don't expose APIs publicly without auth
4. **Rate limiting** - Prevent abuse (use API Gateway)
5. **Audit logging** - Log all queries and access
6. **Least privilege** - Use IAM roles with minimal permissions
7. **Regular updates** - Keep dependencies updated

---

## Roadmap

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
