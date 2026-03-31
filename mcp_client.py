import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Windows fix: must be BEFORE any asyncio import
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import asyncio
import argparse
import json
import os
import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

client = anthropic.Anthropic()

def log(msg: str):
    sys.stderr.write(f"{msg}\n")
    sys.stderr.flush()

AGENT_SYSTEM_PROMPT = """
You are an autonomous EDA agent. When given a CSV file path, you:
1. First use get_quick_stats to understand what you're working with
2. Then use run_full_eda_pipeline to generate the complete report
3. Confirm to the user what was done and where the report was saved

Be decisive — don't ask for confirmation, just run the analysis.
If a tool fails, explain the error clearly and suggest a fix.
"""

async def run_agent(csv_filepath: str):
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"],
        env=None
    )

    log(f"\nStarting EDA Agent")
    log(f"Target file: {csv_filepath}\n")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            log("MCP server connected\n")

            tools_result = await session.list_tools()
            tools = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema
                }
                for t in tools_result.tools
            ]
            log(f"Tools available: {[t['name'] for t in tools]}\n")

            messages = [
                {
                    "role": "user",
                    "content": f"Please run a complete EDA analysis on this file: {csv_filepath}"
                }
            ]

            turn = 0
            while True:
                turn += 1
                log(f"--- Agent turn {turn} ---")

                try:
                    response = client.messages.create(
                        model=MODEL,
                        max_tokens=4096,
                        system=AGENT_SYSTEM_PROMPT,
                        tools=tools,
                        messages=messages
                    )
                except anthropic.APIConnectionError as e:
                    log(f"Could not connect to Claude API: {e}")
                    break
                except anthropic.APIStatusError as e:
                    log(f"Claude API error {e.status_code}: {e.message}")
                    break

                log(f"Stop reason: {response.stop_reason}")

                if response.stop_reason == "tool_use":
                    messages.append({
                        "role": "assistant",
                        "content": response.content
                    })

                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            log(f"\nClaude calling: {block.name}")
                            log(f"   With args: {json.dumps(block.input, indent=3)}")

                            result = await session.call_tool(block.name, block.input)
                            if not result.content:
                                result_text = "Tool returned no output"
                            else:
                                result_text = result.content[0].text
                            log(f"   Result preview: {result_text[:100]}...")

                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result_text
                            })

                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })

                elif response.stop_reason == "end_turn":
                    log("\nAgent finished!\n")
                    for block in response.content:
                        if hasattr(block, "text"):
                            print(block.text)
                    break

                else:
                    log(f"Unexpected stop reason: {response.stop_reason}")
                    break

                if turn > 10:
                    log("Max turns reached, stopping.")
                    break


def main():
    parser = argparse.ArgumentParser(description="EDA Agent — Automated Data Analysis")
    parser.add_argument("--file", required=True, help="Path to CSV file (must be inside data/ directory)")
    args = parser.parse_args()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_agent(args.file))
    finally:
        loop.close()


if __name__ == "__main__":
    main()
