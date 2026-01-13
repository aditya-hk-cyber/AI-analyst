"""
Feedback Agent - Analyzes feedback files and generates actionable improvements for the knowledge base.
"""

import os
from pathlib import Path
from typing import List, Dict
import json


def load_knowledge_base(knowledge_dir: Path) -> Dict[str, str]:
    """Load all knowledge base files into a dictionary."""
    knowledge = {}
    
    # Load main knowledge files
    for file_name in ["catalog.txt", "domain.txt", "metrics.txt", "examples.txt"]:
        file_path = knowledge_dir / file_name
        if file_path.exists():
            knowledge[file_name] = file_path.read_text(encoding="utf-8")
    
    # Load query files
    queries_dir = knowledge_dir / "queries"
    if queries_dir.exists():
        for query_file in queries_dir.glob("*.sql"):
            knowledge[f"queries/{query_file.name}"] = query_file.read_text(encoding="utf-8")
    
    return knowledge


def analyze_feedback_file(feedback_file: Path, knowledge: Dict[str, str]) -> List[str]:
    """
    Analyze a single feedback file and generate actionable items.
    
    This function analyzes the feedback content against the knowledge base
    and generates specific, actionable improvements.
    """
    print(f"\n{'='*60}")
    print(f"Processing feedback file: {feedback_file.name}")
    print(f"{'='*60}")
    
    feedback_content = feedback_file.read_text(encoding="utf-8")
    
    actionables = []
    
    # Analyze feedback for different types of issues
    feedback_lower = feedback_content.lower()
    
    # Check for catalog-related feedback
    if any(keyword in feedback_lower for keyword in ["catalog", "table", "schema", "column", "missing table", "unclear column"]):
        actionables.append({
            "category": "Catalog",
            "file": feedback_file.name,
            "action": "Review and update catalog.txt based on feedback about tables, schemas, or columns",
            "details": _extract_relevant_section(feedback_content, ["catalog", "table", "schema", "column"])
        })
    
    # Check for domain-related feedback
    if any(keyword in feedback_lower for keyword in ["domain", "business", "terminology", "definition", "context", "unclear"]):
        actionables.append({
            "category": "Domain",
            "file": feedback_file.name,
            "action": "Update domain.txt with missing business context or clarify terminology",
            "details": _extract_relevant_section(feedback_content, ["domain", "business", "terminology", "definition"])
        })
    
    # Check for metrics-related feedback
    if any(keyword in feedback_lower for keyword in ["metric", "calculation", "formula", "computation", "measure"]):
        actionables.append({
            "category": "Metrics",
            "file": feedback_file.name,
            "action": "Review and update metrics.txt with missing or unclear metric definitions",
            "details": _extract_relevant_section(feedback_content, ["metric", "calculation", "formula"])
        })
    
    # Check for examples-related feedback
    if any(keyword in feedback_lower for keyword in ["example", "query", "template", "pattern", "sql"]):
        actionables.append({
            "category": "Examples",
            "file": feedback_file.name,
            "action": "Add or update examples in examples.txt or queries/ directory",
            "details": _extract_relevant_section(feedback_content, ["example", "query", "template", "pattern"])
        })
    
    # Check for general gaps or missing information
    if any(keyword in feedback_lower for keyword in ["gap", "missing", "incomplete", "unavailable", "not found"]):
        actionables.append({
            "category": "General",
            "file": feedback_file.name,
            "action": "Address identified gaps in the knowledge base",
            "details": _extract_relevant_section(feedback_content, ["gap", "missing", "incomplete"])
        })
    
    # If no specific category matches, create a general actionable
    if not actionables:
        actionables.append({
            "category": "General",
            "file": feedback_file.name,
            "action": "Review feedback and identify specific improvements needed",
            "details": feedback_content[:500]  # First 500 chars as context
        })
    
    print(f"Generated {len(actionables)} actionable(s) from {feedback_file.name}")
    return actionables


def _extract_relevant_section(content: str, keywords: List[str]) -> str:
    """Extract relevant sections from feedback content based on keywords."""
    lines = content.split('\n')
    relevant_lines = []
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in keywords):
            # Include the line and some context
            start = max(0, i - 2)
            end = min(len(lines), i + 5)
            relevant_lines.extend(lines[start:end])
    
    if relevant_lines:
        return '\n'.join(relevant_lines[:20])  # Limit to 20 lines
    return content[:500]  # Fallback to first 500 chars


def consolidate_actionables(all_actionables: List[Dict]) -> List[Dict]:
    """
    Consolidate actionables from all feedback files.
    
    Groups similar actionables together and removes duplicates.
    """
    print(f"\n{'='*60}")
    print(f"Consolidating {len(all_actionables)} actionables...")
    print(f"{'='*60}")
    
    # Group by category
    by_category = {}
    for actionable in all_actionables:
        category = actionable["category"]
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(actionable)
    
    consolidated = []
    
    # Consolidate within each category
    for category, items in by_category.items():
        # Group by similar actions
        action_groups = {}
        for item in items:
            action_key = item["action"][:100]  # Use first 100 chars as key
            if action_key not in action_groups:
                action_groups[action_key] = []
            action_groups[action_key].append(item)
        
        # Create consolidated items
        for action_key, group_items in action_groups.items():
            if len(group_items) == 1:
                consolidated.append(group_items[0])
            else:
                # Merge multiple similar items
                files = [item["file"] for item in group_items]
                details = "\n\n---\n\n".join([f"From {item['file']}:\n{item['details']}" for item in group_items])
                
                consolidated.append({
                    "category": category,
                    "file": f"Multiple files ({len(files)}): {', '.join(files[:3])}{'...' if len(files) > 3 else ''}",
                    "action": group_items[0]["action"],
                    "details": details,
                    "priority": "High" if len(group_items) > 2 else "Medium"
                })
    
    return consolidated


def generate_final_report(consolidated_actionables: List[Dict], output_file: Path):
    """Generate a final consolidated report of all actionables."""
    report_lines = [
        "# Consolidated Feedback Actionables",
        "",
        f"Generated from analysis of feedback files.",
        f"Total actionable items: {len(consolidated_actionables)}",
        "",
        "---",
        ""
    ]
    
    # Group by category for better organization
    by_category = {}
    for actionable in consolidated_actionables:
        category = actionable["category"]
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(actionable)
    
    # Write report by category
    for category in sorted(by_category.keys()):
        report_lines.append(f"## {category} Improvements")
        report_lines.append("")
        
        for i, actionable in enumerate(by_category[category], 1):
            priority = actionable.get("priority", "Medium")
            report_lines.append(f"### {i}. {actionable['action']}")
            report_lines.append("")
            report_lines.append(f"**Source**: {actionable['file']}")
            if priority != "Medium":
                report_lines.append(f"**Priority**: {priority}")
            report_lines.append("")
            report_lines.append("**Details:**")
            report_lines.append("```")
            report_lines.append(actionable['details'][:1000])  # Limit details length
            report_lines.append("```")
            report_lines.append("")
            report_lines.append("---")
            report_lines.append("")
    
    # Write summary
    report_lines.append("## Summary")
    report_lines.append("")
    report_lines.append(f"- **Total actionables**: {len(consolidated_actionables)}")
    report_lines.append(f"- **Categories**: {', '.join(sorted(by_category.keys()))}")
    
    high_priority = [a for a in consolidated_actionables if a.get("priority") == "High"]
    if high_priority:
        report_lines.append(f"- **High priority items**: {len(high_priority)}")
    
    report_content = "\n".join(report_lines)
    output_file.write_text(report_content, encoding="utf-8")
    
    print(f"\nFinal report saved to: {output_file}")
    return report_content


def main():
    """Main function to run the feedback agent."""
    # Get paths
    repo_root = Path(__file__).resolve().parents[2]
    feedback_dir = repo_root / "feedback"
    knowledge_dir = repo_root / "knowledge"
    output_file = repo_root / "feedback" / "consolidated_actionables.md"
    
    print("="*60)
    print("Feedback Agent - Knowledge Base Improvement Analyzer")
    print("="*60)
    
    # Check if feedback directory exists
    if not feedback_dir.exists():
        print(f"Error: Feedback directory not found: {feedback_dir}")
        return
    
    # Load knowledge base
    print(f"\nLoading knowledge base from: {knowledge_dir}")
    knowledge = load_knowledge_base(knowledge_dir)
    print(f"Loaded {len(knowledge)} knowledge files")
    
    # Find all feedback files (excluding README.md and output file)
    feedback_files = [
        f for f in feedback_dir.iterdir()
        if f.is_file() and f.name not in ["README.md", "consolidated_actionables.md"]
    ]
    
    if not feedback_files:
        print(f"\nNo feedback files found in {feedback_dir}")
        print("Please add feedback files to the feedback/ directory")
        return
    
    print(f"\nFound {len(feedback_files)} feedback file(s) to process")
    
    # Process each feedback file
    all_actionables = []
    for feedback_file in sorted(feedback_files):
        try:
            actionables = analyze_feedback_file(feedback_file, knowledge)
            all_actionables.extend(actionables)
        except Exception as e:
            print(f"Error processing {feedback_file.name}: {e}")
            continue
    
    if not all_actionables:
        print("\nNo actionables generated from feedback files")
        return
    
    # Consolidate actionables
    consolidated = consolidate_actionables(all_actionables)
    
    # Generate final report
    print(f"\nGenerating consolidated report...")
    report_content = generate_final_report(consolidated, output_file)
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total feedback files processed: {len(feedback_files)}")
    print(f"Total actionables generated: {len(all_actionables)}")
    print(f"Consolidated actionables: {len(consolidated)}")
    print(f"\nReport saved to: {output_file}")
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
