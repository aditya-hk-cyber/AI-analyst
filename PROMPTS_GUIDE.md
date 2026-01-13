# MCP Prompts Guide

Quick reference for all available prompts in the Insights MCP server.

## Available Prompts

### 1. `answer_question`
**Purpose**: Guide the agent to answer business questions using SQL queries

**Use when**: Starting a new analysis or asking data questions

**What it does**:
- Provides structured steps for query development
- Guides through knowledge base resources
- Ensures proper SQL syntax and best practices

**Example usage**: Just start asking questions, and the agent will use this pattern.

---

### 2. `create_comprehensive_report`
**Purpose**: Generate a detailed markdown report of your analysis session

**Use when**: You want to document and share your analysis work

**What it includes**:
- **TL;DR** - Quick summary (3-5 sentences)
- **Executive Summary** - Detailed overview
- **Questions Addressed** - All questions asked
- **Detailed Analysis** - Findings, interpretations, insights per question
- **Key Insights** - Synthesized takeaways
- **Recommendations** - Actionable next steps
- **Data Quality Notes** - Assumptions and caveats
- **Technical Appendix** - Full SQL queries with metadata

**Output**: `reports/report_YYYYMMDD_HHMMSS.md`

**Example prompt**:
```
Can you create a comprehensive report of our analysis?
```

---

### 3. `submit_feedback`
**Purpose**: Interactive feedback collection to improve the knowledge base

**Use when**: You want to provide feedback about the analysis quality

**What it collects**:
1. **Overall Satisfaction** - Were you happy with the results?
2. **Result Accuracy** - Were the results correct?
3. **Understanding** - Any misunderstandings?
4. **Missing Information** - Tables, schemas, or metrics missed?
5. **Knowledge Base Gaps** - What documentation is missing?
6. **Query Quality** - Were the SQL queries good?
7. **Improvement Suggestions** - Specific recommendations
8. **Additional Comments** - Any other feedback

**Output**: `feedback/user_feedback_YYYYMMDD_HHMMSS.md`

**GitHub Integration** (Planned):
- Will automatically create a branch `feedback/{timestamp}`
- Create a Pull Request with the feedback
- Tag with label "user-feedback"

**Current**: Feedback is saved locally and can be manually submitted.

**Example prompt**:
```
I'd like to submit feedback about this analysis
```

---

### 4. `generate_feedback`
**Purpose**: Agent self-assessment of knowledge base effectiveness

**Use when**: After completing an analysis, to evaluate knowledge base quality

**What it generates**:
- **Knowledge Availability Assessment** - Was info sufficient?
- **Knowledge Quality Assessment** - Any conflicts or inconsistencies?
- **Efficiency Assessment** - Could it be faster/easier?
- **Gaps Identification** - Specific missing info by category
- **Enhancement Suggestions** - Concrete improvements
- **Effectiveness Rating** - 1-5 scale with reasoning

**Output**: `feedback/feedback_YYYYMMDD_HHMMSS.md`

**Example prompt**:
```
Please generate feedback about the knowledge base
```

---

## Workflow Example

Here's a typical workflow using all prompts:

### 1. Analysis Phase
```
User: What was the total watch time last week?
[Agent uses answer_question pattern to analyze and respond]
```

### 2. Documentation Phase
```
User: Can you create a comprehensive report?
[Agent generates detailed markdown report]
```

### 3. Feedback Phase
```
User: Please generate feedback about the knowledge base
[Agent creates self-assessment feedback]

User: I'd also like to submit my own feedback
[Interactive feedback collection begins]
```

### 4. Improvement Phase
```bash
# Process all feedback
uv run python src/insights_mcp/feedback_agent.py
# or
uv run insights-mcp-feedback-agent

# Review consolidated_actionables.md
# Implement improvements to knowledge base
```

---

## Tips

1. **Reports are shareable** - The comprehensive reports are designed to be shared with stakeholders

2. **Feedback improves the system** - Both types of feedback help improve the knowledge base over time

3. **Use the feedback agent regularly** - Run it after collecting several feedback files to get consolidated improvement suggestions

4. **Reports and feedback are gitignored** - But you can commit specific ones if needed for documentation

---

## File Locations

- **Reports**: `reports/report_YYYYMMDD_HHMMSS.md`
- **User Feedback**: `feedback/user_feedback_YYYYMMDD_HHMMSS.md`
- **Agent Feedback**: `feedback/feedback_YYYYMMDD_HHMMSS.md`
- **Consolidated Actionables**: `feedback/consolidated_actionables.md`
