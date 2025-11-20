"""
File Generator MCP Server - Creates markdown files
"""

import sys
import os
from datetime import datetime
from fastmcp import FastMCP

# ---------------------------------------------
# Initialize MCP Server
# ---------------------------------------------

mcp = FastMCP("file-generator-server")

# ---------------------------------------------
# Define MCP Tool
# ---------------------------------------------
@mcp.tool()
def generate_markdown_file(
    title: str,
    content: str,
    output_dir: str = "output/blogs"
) -> dict:
    """
    Generate and save markdown file inside a timestamped folder
    """
    print("generate_markdown_file yes 3 TOOL CALLED (inner)", file=sys.stderr, flush=True)

    # Ensure base output directory exists
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory ensured: {output_dir}", file=sys.stderr, flush=True)

    # Sanitize and format title
    title = title.replace("C#", "CSharp").replace("c#", "CSharp")

    # Remove invalid characters (keep letters, numbers, spaces, hyphens)
    safe_title = "".join(
        c if c.isalnum() or c in (" ", "-") else "" 
        for c in title
    )

    # Convert spaces to hyphens + lowercase
    safe_title = safe_title.replace(" ", "-").lower()

    # Create folder name: YYYY-MM-DD-title
    folder_name = f"{datetime.now().strftime('%Y-%m-%d')}-{safe_title}"
    folder_path = os.path.join(output_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    # File will always be named index.md
    filename = "index.md"
    filepath = os.path.join(folder_path, filename)

    # Write markdown file (LLM already includes frontmatter)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


    print(f" Markdown file created at: {filepath}", file=sys.stderr, flush=True)

    return {
        "folder_name": folder_name,
        "filename": filename,
        "filepath": filepath,
        "status": "success",
    }


# ---------------------------------------------
# Run MCP Server
# ---------------------------------------------
if __name__ == "__main__":
    print(" Starting File Generator MCP Server...", file=sys.stderr, flush=True)
    mcp.run()
