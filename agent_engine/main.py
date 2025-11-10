import argparse
import asyncio
from agent_logic.orchestrator import BlogOrchestrator 

def main():
    parser = argparse.ArgumentParser(description="Run BlogOrchestrator")
    parser.add_argument("--topic", type=str, required=True, help="Blog topic")
    parser.add_argument("--product", type=str, default=None, help="Product name (optional)")

    args = parser.parse_args()

    orchestrator = BlogOrchestrator()
    result = asyncio.run(
        orchestrator.create_blog_autonomously(
            topic=args.topic,
            product_name=args.product
        )
    )

    # Use result here
    print(f"Generated markdown file path: {result.get('filepath')}")

if __name__ == "__main__":
    main()

