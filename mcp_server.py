import asyncio
import json
import sys

# Windows encoding fix — must be at the very top
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from agent import run_full_pipeline, validate_csv_path
from eda_engine import run_eda
from charts import generate_charts
import pandas as pd

server = Server("eda-agent")

def log(msg: str):
    """
    Safe logging for MCP servers — always use stderr, never stdout.
    stdout is reserved exclusively for MCP JSON communication.
    Any print() to stdout will corrupt the MCP message stream.
    """
    sys.stderr.write(f"{msg}\n")
    sys.stderr.flush()


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="run_full_eda_pipeline",
            description="""
                Run a complete automated EDA pipeline on a CSV file.
                This tool: loads the CSV, computes statistics, generates charts,
                sends everything to Claude for analysis, and saves a full
                professional markdown report. Use this as the primary tool
                when a user wants to analyze a dataset.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the CSV file to analyze (must be inside the data/ directory)"
                    }
                },
                "required": ["filepath"]
            }
        ),
        types.Tool(
            name="get_quick_stats",
            description="""
                Get a quick statistical summary of a CSV file without
                generating a full report. Useful for a fast overview
                before deciding whether to run the full pipeline.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the CSV file (must be inside the data/ directory)"
                    }
                },
                "required": ["filepath"]
            }
        ),
        types.Tool(
            name="generate_charts_only",
            description="""
                Generate and save visualization charts for a CSV file
                without producing a written report. Returns paths to
                the saved chart files.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the CSV file (must be inside the data/ directory)"
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Directory to save charts (default: 'charts')"
                    }
                },
                "required": ["filepath"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "run_full_eda_pipeline":
            filepath = arguments["filepath"]
            log(f"MCP: Running full pipeline on {filepath}")
            output_path = run_full_pipeline(filepath)
            return [types.TextContent(
                type="text",
                text=f"EDA pipeline complete. Report saved to: {output_path}"
            )]

        elif name == "get_quick_stats":
            filepath = arguments["filepath"]
            log(f"MCP: Getting quick stats for {filepath}")
            validated = validate_csv_path(filepath)
            try:
                df = pd.read_csv(validated)
            except pd.errors.ParserError as e:
                raise ValueError(f"Failed to parse CSV: {e}") from e
            except pd.errors.EmptyDataError:
                raise ValueError("The CSV file is empty")
            stats = run_eda(df)
            return [types.TextContent(
                type="text",
                text=json.dumps(stats, indent=2)
            )]

        elif name == "generate_charts_only":
            filepath = arguments["filepath"]
            output_dir = arguments.get("output_dir", "charts")
            log(f"MCP: Generating charts for {filepath}")
            validated = validate_csv_path(filepath)
            try:
                df = pd.read_csv(validated)
            except pd.errors.ParserError as e:
                raise ValueError(f"Failed to parse CSV: {e}") from e
            except pd.errors.EmptyDataError:
                raise ValueError("The CSV file is empty")
            chart_paths = generate_charts(df, output_dir)
            return [types.TextContent(
                type="text",
                text="Charts generated:\n" + "\n".join(chart_paths)
            )]

        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except (ValueError, FileNotFoundError) as e:
        log(f"Input error in {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
    except RuntimeError as e:
        log(f"Runtime error in {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error running {name}: {str(e)}"
        )]


async def main():
    log("EDA Agent MCP Server starting...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
