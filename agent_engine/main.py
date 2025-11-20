import argparse
import asyncio
from agent_logic.orchestrator import BlogOrchestrator 
import sys
sys.dont_write_bytecode = True

def main():
    parser = argparse.ArgumentParser(description="Run BlogOrchestrator")
    parser.add_argument("--topic", type=str, required=True, help="Blog topic")
    parser.add_argument("--product", type=str, required=True,  default=None, help="Product name (optional)")
    parser.add_argument("--platform", type=str, required=True,  default="aspose",
                        help="Platform: aspose | groupdocs | conholdate")
    parser.add_argument("--keyword_source", type=str, required=True,  default="auto",
                        help="Keyword Source: auto | manual")
    args = parser.parse_args()

    orchestrator = BlogOrchestrator(platform=args.platform)

    result = asyncio.run(
        orchestrator.create_blog_autonomously(
            topic=args.topic,
            product_name=args.product,
            keyword_source=args.keyword_source
        )
    )

    print(f"Generated markdown file path: {result.get('filepath')}")
    print(f"Platform: {result.get('platform')}")
    print(f"Product: {result.get('product')}")

if __name__ == "__main__":
    main()
