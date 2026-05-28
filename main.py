
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from shared.functions.stock_metadata import process_stock_folder


CREW_CHOICES = ["shutter_crew", "shutter_crew_gemini", "sentinel_crew", "style_crew"]

COMMAND_ALIASES = {
    "shutter": "metadata",
}

LEGACY_CREW_HINTS = {
    "shutter_crew": "For shutter crews, use subcommand mode: python main.py shutter --crew <crew_name> --target-folder <path> (or python main.py metadata ...).",
    "shutter_crew_gemini": "For shutter crews, use subcommand mode: python main.py shutter --crew <crew_name> --target-folder <path> (or python main.py metadata ...).",
    "sentinel_crew": "Use: python main.py sentinel_crew --subnet <cidr>",
    "style_crew": "Use: python main.py style_crew --root-directory <path>",
}


def _build_legacy_shutter_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run metadata/shutter flow in legacy mode.")
    parser.add_argument("--crew", choices=["shutter_crew", "shutter_crew_gemini"], default="shutter_crew")
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
    return parser


def _add_shutter_like_parser(
    subparsers: argparse._SubParsersAction,
    command_name: str,
    help_text: str,
    aliases: list[str] | None = None,
) -> None:
    parser = subparsers.add_parser(command_name, help=help_text, aliases=aliases or [])
    parser.add_argument("--crew", choices=["shutter_crew", "shutter_crew_gemini"], default="shutter_crew")
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


def _handle_metadata_like_command(args: argparse.Namespace) -> None:
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

    print("Starting crew: sentinel_crew")
    result = sentinel_crew.kickoff(inputs={"subnet": args.subnet})
    print("\nCrew Result:\n")
    print(result)


def _handle_style_command(args: argparse.Namespace) -> None:
    from crew.style_crew import photo_analysis_crew, style_report_task, style_final_guide_task

    style_data_path = Path(args.style_data_dir)
    if not style_data_path.is_absolute():
        style_data_path = Path.cwd() / style_data_path
    style_data_path.mkdir(parents=True, exist_ok=True)

    # Keep task output files aligned with the runtime workspace selected via --style-data-dir.
    style_report_task.output_file = str(style_data_path / "comprehensive_style_report.json")
    style_final_guide_task.output_file = str(style_data_path / "FINAL_PRO_PRODUCTION_GUIDE.md")

    print("Starting crew: style_crew")
    result = photo_analysis_crew.kickoff(
        inputs={
            "root_directory": args.root_directory,
            "style_data_dir": str(style_data_path),
        }
    )
    print("\nCrew Result:\n")
    print(result)


COMMAND_HANDLERS = {
    "metadata": _handle_metadata_like_command,
    "sentinel_crew": _handle_sentinel_command,
    "style_crew": _handle_style_command,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one of the available crews.")
    parser.add_argument(
        "--crew",
        choices=CREW_CHOICES,
        help="Legacy mode without subcommands. Use subcommands for cleaner help.",
    )

    subparsers = parser.add_subparsers(dest="command")

    _add_shutter_like_parser(
        subparsers,
        "metadata",
        "Run metadata/shutter flow in folder batch mode.",
        aliases=["shutter"],
    )

    sentinel_parser = subparsers.add_parser("sentinel_crew", help="Run sentinel crew.")
    sentinel_parser.add_argument("--subnet", required=True, help="Subnet/CIDR, e.g. 192.168.1.0/24")

    style_parser = subparsers.add_parser("style_crew", help="Run style crew.")
    style_parser.add_argument("--root-directory", required=True, help="Root folder for style processing.")
    style_parser.add_argument(
        "--style-data-dir",
        default="./styleData",
        help="Workspace folder used by style_crew for intermediate and final artifacts.",
    )

    return parser


def run_legacy_mode(args: argparse.Namespace):
    if args.crew in LEGACY_CREW_HINTS:
        raise ValueError(LEGACY_CREW_HINTS[args.crew])
    raise ValueError("Unknown crew mode")


def run_subcommand_mode(args: argparse.Namespace):
    normalized_command = COMMAND_ALIASES.get(args.command, args.command)
    handler = COMMAND_HANDLERS.get(normalized_command)
    if handler is None:
        raise ValueError("Unknown subcommand")
    handler(args)


def main() -> None:
    load_dotenv()

    legacy_argv = sys.argv[1:]
    if "--crew" in legacy_argv:
        crew_index = legacy_argv.index("--crew")
        if crew_index + 1 < len(legacy_argv) and legacy_argv[crew_index + 1] in {"shutter_crew", "shutter_crew_gemini"}:
            legacy_parser = _build_legacy_shutter_parser()
            legacy_args = legacy_parser.parse_args(legacy_argv)
            _handle_metadata_like_command(legacy_args)
            return

    parser = build_parser()
    args = parser.parse_args()

    if args.command:
        run_subcommand_mode(args)
        return

    if args.crew:
        run_legacy_mode(args)
        return

    parser.print_help()


if __name__ == "__main__":
    main()