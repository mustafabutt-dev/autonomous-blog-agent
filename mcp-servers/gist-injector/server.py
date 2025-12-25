"""
Creates Gists for a given code snippet
"""
import sys, os
from fastmcp import FastMCP
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../"))
if PARENT_PATH not in sys.path:
    sys.path.append(PARENT_PATH)
from agent_engine.blog_generator.config import settings
from agent_engine.blog_generator.utils.helpers import extract_all_complete_code_snippets, upload_to_gist, replace_code_snippets_with_gists

# Load your environment (optional if already set)
from dotenv import load_dotenv
load_dotenv()

# Initialize MCP
mcp = FastMCP("gist-injector")

@mcp.tool()
async def gist_injector(content: str, title: str) -> dict:

    try:
        snippets = extract_all_complete_code_snippets(content)

        if len(snippets) == 0:
            print("No complete code snippets foundee!", flush=True, file=sys.stderr)
            return {"jistified_content":content}
        elif len(snippets) == 1:
            # Prepare for gist upload
            code_for_gist = {
                data['filename']: data['code'] 
                for data in snippets.values()
            }
            print(f"token is or not {settings.REPO_PAT}", flush=True, file=sys.stderr)
            # Step 3: Upload to gist
            gist_result = await upload_to_gist(
                code_for_gist,
                description=title,
                token=settings.REPO_PAT,
                gist_name=settings.GIST_NAME
            )
            
            if gist_result.get("success"):
                shortcodes_map = gist_result['shortcodes']
                
                # Step 4: Replace in markdown
                updated_content = replace_code_snippets_with_gists(
                    content,
                    snippets,
                    shortcodes_map
                )
                
                print(f" code snippet replaced with gist.  {updated_content}", flush=True, file=sys.stderr)
                return {"jistified_content":updated_content}
                # Now 'updated_content' has all gist shortcodes
            else:
                print(f"❌ Gist upload failed: {gist_result['error']}", flush=True, file=sys.stderr)
                return {"jistified_content":content}
        else:
            print(f"Multi-task detected", flush=True, file=sys.stderr)
            code_for_gist = {
                data['filename']: data['code'] 
                for data in snippets.values()
            }
            
            # Step 3: Upload to gist
            gist_result = await upload_to_gist(
                code_for_gist,
                description=title,
                token=settings.REPO_PAT,
                gist_name=settings.GIST_NAME
            )
            
            if gist_result.get("success"):
                shortcodes_map = gist_result['shortcodes']
                
                # Step 4: Replace in markdown
                updated_content = replace_code_snippets_with_gists(
                    content,
                    snippets,
                    shortcodes_map
                )
                
                print(f" All code snippets replaced with gists.  {updated_content}", flush=True, file=sys.stderr)
                return {"jistified_content":updated_content}
                # Now 'updated_content' has all gist shortcodes
            else:
                print(f"❌ Gist upload failed: {gist_result['error']}", flush=True, file=sys.stderr)
                return {"jistified_content":content}
    
    except Exception as e:
        print(f"LLM error, using fallback: {e}", file=sys.stderr)
        return {"jistified_content":content}

if __name__ == "__main__":
    mcp.run()