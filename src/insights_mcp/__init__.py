"""
InsightsMCP - Analytics MCP server for d11_stitch data warehouse.
"""

from .athena import AthenaClient, QueryResult
from .server import mcp

__all__ = ["mcp", "AthenaClient", "QueryResult"]
