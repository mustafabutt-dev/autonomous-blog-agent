"""
File Generator MCP Server - Creates markdown files
"""

from fastmcp import FastMCP
import os
from datetime import datetime

mcp = FastMCP("file-generator-server")

@mcp.tool()
def generate_markdown_file(
    title: str,
    content: str,
    keywords: list,
    product_info: dict = None,
    output_dir: str = "output/blogs"
) -> dict:
    """
    Generate and save markdown file
    """
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename
    safe_title = "".join(c if c.isalnum() or c in (' ', '-') else '' for c in title)
    safe_title = safe_title.replace(' ', '-').lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{safe_title}.md"
    filepath = os.path.join(output_dir, filename)
    
    # Create frontmatter
    frontmatter = f"""---
title: "{title}"
date: {datetime.now().isoformat()}
keywords: {', '.join(keywords)}
"""
    
    if product_info:
        frontmatter += f"""product: "{product_info.get('ProductName', '')}"
category: "{product_info.get('Category', '')}"
"""
    
    frontmatter += "---\n\n"
    
    # Write file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
        f.write(content)
    
    return {
        "filename": filename,
        "filepath": filepath,
        "size_bytes": os.path.getsize(filepath),
        "status": "success"
    }

if __name__ == "__main__":
    print(" File Generator MCP Server running on http://127.0.0.1:3004")
    mcp.run()