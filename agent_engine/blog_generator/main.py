import argparse
import asyncio
from agent_logic.orchestrator import BlogOrchestrator 
import sys
sys.dont_write_bytecode = True

def main():
    parser = argparse.ArgumentParser(description="Run BlogOrchestrator")

    parser.add_argument("--author", type=str, required=True,  default=None)
    parser.add_argument("--brand", type=str, required=True,  default=None)
    parser.add_argument("--topics_file", type=str, required=True,  default=None)
    args = parser.parse_args()

    orchestrator = BlogOrchestrator(brand=args.brand)

    result = asyncio.run(
        orchestrator.create_blog_autonomously(
            topics_file=args.topics_file,
            author=args.author
        )
    )
    print(f"Generated markdown file path: {result.get('filepath')}")
    print(f"Platform: {result.get('platform')}")
    print(f"Product: {result.get('product')}")

if __name__ == "__main__":
    main()
