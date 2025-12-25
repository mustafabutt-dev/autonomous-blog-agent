"""
File Generator MCP Server - Creates markdown files with brand-specific paths
"""

import sys
import os
from datetime import datetime
from fastmcp import FastMCP

mcp = FastMCP("file-generator-server")

@mcp.tool()
def generate_markdown_file(
    title: str,
    content: str,
    brand: str,
    output_dir: str = "content/blogPosts"
) -> dict:
    """
    Generate and save markdown file inside a brand-specific, timestamped folder
    
    Args:
        title: Blog post title
        content: Full markdown content (including frontmatter)
        brand: Brand domain (e.g., 'conholdate.com', 'aspose.com', 'groupdocs.com')
        output_dir: Base output directory
        
    Returns:
        Dictionary with folder_name, filename, filepath, brand_folder, and status
    """
    print("generate_markdown_file TOOL CALLED", file=sys.stderr, flush=True)

    # Ensure base output directory exists
    os.makedirs(output_dir, exist_ok=True)
    print(f"Base output directory ensured: {output_dir}", file=sys.stderr, flush=True)

    # Create brand-specific subfolder (sanitize brand name)
    # conholdate.com -> conholdate_com
    # blog.aspose.com -> blog_aspose_com
    brand_safe = brand.replace(".", "_").replace("-", "_")
    brand_dir = os.path.join(output_dir, brand_safe)
    os.makedirs(brand_dir, exist_ok=True)
    print(f"Brand directory ensured: {brand_dir}", file=sys.stderr, flush=True)

    # Sanitize and format title
    title = title.replace("C#", "CSharp").replace("c#", "CSharp")

    # Remove invalid characters (keep letters, numbers, spaces, hyphens)
    safe_title = "".join(
        c if c.isalnum() or c in (" ", "-") else "" 
        for c in title
    )

    # Convert spaces to hyphens + lowercase
    safe_title = safe_title.replace(" ", "-").lower()
    
    # Remove consecutive hyphens
    while "--" in safe_title:
        safe_title = safe_title.replace("--", "-")
    
    # Remove leading/trailing hyphens
    safe_title = safe_title.strip("-")

    # Create folder name: YYYY-MM-DD-title
    folder_name = f"{datetime.now().strftime('%Y-%m-%d')}-{safe_title}"
    folder_path = os.path.join(brand_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    # Create images subfolder
    images_folder = os.path.join(folder_path, "images")
    os.makedirs(images_folder, exist_ok=True)
    print(f"Images folder created at: {images_folder}", file=sys.stderr, flush=True)

    # File will always be named index.md
    filename = "index.md"
    filepath = os.path.join(folder_path, filename)

    # Write markdown file (LLM already includes frontmatter)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Markdown file created at: {filepath}", file=sys.stderr, flush=True)
    print(f"   Brand: {brand} ({brand_safe})", file=sys.stderr, flush=True)
    print(f"   Folder structure:", file=sys.stderr, flush=True)
    print(f"   {output_dir}/", file=sys.stderr, flush=True)
    print(f"   └── {brand_safe}/", file=sys.stderr, flush=True)
    print(f"       └── {folder_name}/", file=sys.stderr, flush=True)
    print(f"           ├── index.md", file=sys.stderr, flush=True)
    print(f"           └── images/", file=sys.stderr, flush=True)

    return {
        "folder_name": folder_name,
        "filename": filename,
        "filepath": filepath,
        "brand_folder": brand_safe,
        "full_path": folder_path,
        "images_folder": images_folder,
        "status": "success",
    }

if __name__ == "__main__":
    mcp.run()