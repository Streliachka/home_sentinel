
import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv

from shared.functions.stock_metadata import process_stock_folder


TOP_LEVEL_COMMANDS = {"metadata", "shutter", "sentinel_crew", "style_crew"}
METADATA_CREW_CHOICES = ["shutter_crew", "shutter_crew_gemini"]
CommandHandler = Callable[[argparse.Namespace], None]


def _resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def _first_positional_token(argv: list[str]) -> tuple[int, str] | None:
    for idx, token in enumerate(argv):
        if not token.startswith("-"):
            return idx, token
    return None


def _normalize_argv(argv: list[str]) -> list[str]:
    """Normalizes top-level --crew invocations into the subcommand form."""
    if "--crew" not in argv:
        return argv

    crew_index = argv.index("--crew")
    if crew_index + 1 >= len(argv):
        return argv

    crew_value = argv[crew_index + 1]
    before = argv[:crew_index]
    after = argv[crew_index + 2 :]

    # If a subcommand appears before --crew, keep argv unchanged.
    first_positional = _first_positional_token(argv)
    if first_positional is not None:
        idx, token = first_positional
        if idx < crew_index and token in TOP_LEVEL_COMMANDS:
            return argv

    if crew_value in METADATA_CREW_CHOICES:
        return [*before, "metadata", "--crew", crew_value, *after]

    if crew_value in TOP_LEVEL_COMMANDS:
        return [*before, crew_value, *after]

    return argv


def _add_metadata_parser(
    subparsers: argparse._SubParsersAction,
    command_name: str,
    help_text: str,
    aliases: list[str] | None = None,
) -> None:
    parser = subparsers.add_parser(command_name, help=help_text, aliases=aliases or [])
    parser.add_argument("--crew", choices=METADATA_CREW_CHOICES, default="shutter_crew")
    parser.add_argument("--target-folder", required=True, help="Folder with images to process.")
    parser.add_argument("--output-file", default="./shutterstock_upload.csv", help="CSV output path.")
    parser.add_argument(
        "--ollama-host",
        default=os.getenv("OLLAMA_BASE_URL"),
        help="Ollama base URL. Defaults to OLLAMA_BASE_URL.",
    )
    parser.add_argument(
        "--ollama-model",
        default=os.getenv("VISION_MODEL"),
        help="Vision model name. Defaults to VISION_MODEL.",
    )
    parser.add_argument(
        "--photo-info",
        default=os.getenv("PHOTO_INFO"),
        help="Optional PHOTO_INFO metadata string.",
    )
    parser.add_argument("--delay-sec", type=float, default=4.0, help="Delay between images.")


def _add_sentinel_parser(subparsers: argparse._SubParsersAction) -> None:
    sentinel_parser = subparsers.add_parser("sentinel_crew", help="Run sentinel crew.")
    sentinel_parser.add_argument("--subnet", required=True, help="Subnet/CIDR, e.g. 192.168.1.0/24")


def _add_style_parser(subparsers: argparse._SubParsersAction) -> None:
    style_parser = subparsers.add_parser("style_crew", help="Run style crew.")
    style_parser.add_argument("--root-directory", required=True, help="Root folder for style processing.")
    style_parser.add_argument(
        "--style-data-dir",
        default="./styleData",
        help="Workspace folder used by style_crew for intermediate and final artifacts.",
    )


def _handle_metadata_command(args: argparse.Namespace) -> None:
    from crew.metadata_crew import shutter_crew, shutter_crew_gemini

    if not args.ollama_host:
        raise ValueError("--ollama-host is required (or set OLLAMA_BASE_URL)")
    if not args.ollama_model:
        raise ValueError("--ollama-model is required (or set VISION_MODEL)")
    if args.crew == "shutter_crew_gemini" and shutter_crew_gemini is None:
        raise ValueError("shutter_crew_gemini requires GEMINI_API_KEY and GEMINI_MODEL to be configured.")

    selected = shutter_crew if args.crew == "shutter_crew" else shutter_crew_gemini
    print(f"Starting metadata flow with crew: {args.crew}")
    process_stock_folder(
        folder_path=args.target_folder,
        output_csv_path=args.output_file,
        selected_crew=selected,
        ollama_host=args.ollama_host,
        ollama_model=args.ollama_model,
        photo_info=args.photo_info,
        delay_sec=args.delay_sec,
    )
    print("Metadata batch completed.")


def _handle_sentinel_command(args: argparse.Namespace) -> None:
    from crew.sentinel_crew import sentinel_crew

    if shutil.which("nmap") is None:
        print(
            "sentinel_crew skipped: nmap executable was not found in PATH. "
            "Install Nmap and ensure 'nmap' is available in your shell PATH."
        )
        return

    print("Starting crew: sentinel_crew")
    result = sentinel_crew.kickoff(inputs={"subnet": args.subnet})
    print("\nCrew Result:\n")
    print(result)


def _handle_style_command(args: argparse.Namespace) -> None:
    root_path = _resolve_path(args.root_directory)

    try:
        root_exists = root_path.exists()
        root_is_dir = root_path.is_dir()
    except OSError as exc:
        print(f"Style crew skipped: unable to access root directory '{root_path}': {exc}")
        return

    if not root_exists or not root_is_dir:
        print(f"Style crew skipped: root directory not found or is not a directory: {root_path}")
        return

    try:
        from crew.style_crew import photo_analysis_crew, style_report_task, style_final_guide_task
    except Exception as exc:
        print(f"Style crew initialization failed: {exc}")
        return

    style_data_path = _resolve_path(args.style_data_dir)
    style_data_path.mkdir(parents=True, exist_ok=True)

    # Keep task output files aligned with the runtime workspace selected via --style-data-dir.
    style_report_task.output_file = str(style_data_path / "comprehensive_style_report.json")
    style_final_guide_task.output_file = str(style_data_path / "FINAL_PRO_PRODUCTION_GUIDE.md")

    print("Starting crew: style_crew")
    try:
        result = photo_analysis_crew.kickoff(
            inputs={
                "root_directory": str(root_path),
                "style_data_dir": str(style_data_path),
            }
        )
    except Exception as exc:
        print(f"Style crew execution failed: {exc}")
        return

    print("\nCrew Result:\n")
    print(result)


def _register_commands(subparsers: argparse._SubParsersAction) -> dict[str, CommandHandler]:
    _add_metadata_parser(
        subparsers,
        "metadata",
        "Run metadata/shutter flow in folder batch mode.",
        aliases=["shutter"],
    )
    _add_sentinel_parser(subparsers)
    _add_style_parser(subparsers)

    return {
        "metadata": _handle_metadata_command,
        "sentinel_crew": _handle_sentinel_command,
        "style_crew": _handle_style_command,
    }


def build_parser() -> tuple[argparse.ArgumentParser, dict[str, CommandHandler]]:
    parser = argparse.ArgumentParser(description="Run one of the available crews.")

    subparsers = parser.add_subparsers(dest="command")
    command_handlers = _register_commands(subparsers)

    return parser, command_handlers


def _run_command(args: argparse.Namespace, command_handlers: dict[str, CommandHandler]) -> None:
    handler = command_handlers.get(args.command)
    if handler is None:
        raise ValueError("Unknown subcommand")
    handler(args)


def main() -> None:
    load_dotenv()

    parser, command_handlers = build_parser()
    args = parser.parse_args(_normalize_argv(sys.argv[1:]))

    if args.command:
        _run_command(args, command_handlers)
        return

    parser.print_help()


if __name__ == "__main__":
    main()