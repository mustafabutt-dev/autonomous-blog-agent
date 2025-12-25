# scripts/run_kra_from_config.py
from __future__ import annotations

import sys
import argparse
import os
import subprocess
from pathlib import Path
from typing import Any, Dict

import yaml  # make sure pyyaml is in requirements.txt


def build_command(engine: Dict[str, Any]) -> list[str]:
    """
    Build the CLI command to run the KRA runner.

    - If engine.use_serp_api / use-serp-api is truthy:
        - use SerpAPI ingestion: pass --use-serp-api and optional --serp-topic
    - Otherwise:
        - require engine.input_file and pass --file <path>
    """
    cmd: list[str] = [
        sys.executable,
        "-m",
        "agent_engine.blog_keyword_analyzer.runner",
    ]

    # Support both snake_case and kebab-case keys in kra_run.yaml
    use_serp_api = bool(engine.get("use_serp_api") or engine.get("use-serp-api"))

    if use_serp_api:
        # Flag only, no value
        cmd.append("--use-serp-api")

        serp_topic = (
            engine.get("serp_topic")
            or engine.get("serp-topic")
            or ""
        )
        if serp_topic:
            cmd.extend(["--serp-topic", serp_topic])
    else:
        input_file = engine.get("input_file")
        if not input_file:
            raise SystemExit(
                "engine.input_file is required in kra_run.yaml when use_serp_api is false."
            )
        cmd.extend(["--file", input_file])

    # Required / common arguments
    cmd.extend(
        [
            "--brand",
            engine["brand"],
            "--product",
            engine["product"],
            "--locale",
            engine.get("locale", "en-US"),
            "--top",
            str(engine.get("top_clusters", 10)),
            "--max-rows",
            str(engine.get("max_rows", 50000)),
        ]
    )

    platform = engine.get("platform")
    if platform:
        cmd.extend(["--platform", platform])

    # Optional: if your CLI supports --no-content-index
    use_content_index = bool(engine.get("use_content_index", True))
    if not use_content_index:
        cmd.append("--no-content-index")

    return cmd


def resolve_blog_content_root(ci_cfg: Dict[str, Any]) -> str | None:
    """
    Decide BLOG_CONTENT_ROOT based on environment:

    - If BLOG_CONTENT_ROOT is already set in env (e.g. by CI workflow), use that.
    - Otherwise, use local_root from kra_run.yaml (for local dev).
    """
    existing = os.getenv("BLOG_CONTENT_ROOT")
    if existing:
        print(f"[KRA] BLOG_CONTENT_ROOT already set in environment: {existing}")
        return existing

    local_root = ci_cfg.get("local_root")
    if local_root:
        print(f"[KRA] Local BLOG_CONTENT_ROOT resolved to: {local_root}")
        return local_root

    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Blog Keyword Analyzer from a kra_run.yaml file."
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        required=True,
        help="Path to kra_run.yaml",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_file():
        raise SystemExit(f"Config file not found: {config_path}")

    cfg: Dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    engine: Dict[str, Any] = cfg["engine"]
    ci_cfg: Dict[str, Any] = cfg.get("content_index") or {}

    cmd = build_command(engine)

    # Build env and wire BLOG_CONTENT_ROOT from kra_run
    env = os.environ.copy()

    blog_root = resolve_blog_content_root(ci_cfg)
    if blog_root:
        env["BLOG_CONTENT_ROOT"] = blog_root

    # Optional: pass debug flag
    if engine.get("debug"):
        env["KRA_DEBUG"] = "1"

    print("[KRA] Using BLOG_CONTENT_ROOT:", env.get("BLOG_CONTENT_ROOT"))
    print("[KRA] Running command:\n  " + " ".join(cmd))

    subprocess.run(cmd, check=True, env=env)


if __name__ == "__main__":
    main()
