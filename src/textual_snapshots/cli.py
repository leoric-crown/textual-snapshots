"""
Command-line interface for textual-snapshots.

Provides professional CLI commands for screenshot capture, comparison,
validation, and conversion with Rich console formatting.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
from rich.table import Table
from rich.traceback import install

# Install rich traceback for better error display
install(show_locals=False)

# Global console instance for rich formatting
console = Console()


class CLIError(Exception):
    """Base exception for CLI errors."""

    pass


def error_exit(message: str, code: int = 1) -> None:
    """Display error message and exit."""
    console.print(f"[red]Error:[/red] {message}")
    sys.exit(code)


def success_message(message: str) -> None:
    """Display success message."""
    console.print(f"[green]✓[/green] {message}")


def warning_message(message: str) -> None:
    """Display warning message."""
    console.print(f"[yellow]⚠[/yellow] {message}")


def info_message(message: str) -> None:
    """Display info message."""
    console.print(message)


def create_progress() -> Progress:
    """Create progress bar with consistent styling."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TimeRemainingColumn(),
        console=console,
    )


def auto_discover_apps(path: Optional[Path] = None, pattern: str = "*.py") -> list[Path]:
    """Auto-discover Textual apps in directory or current directory."""
    search_path = path or Path.cwd()

    if search_path.is_file():
        if is_textual_app(search_path):
            return [search_path]
        else:
            return []

    apps = []
    # Common app file names to check first
    common_names = ["main.py", "app.py", "__main__.py"]

    for name in common_names:
        candidate = search_path / name
        if candidate.exists() and is_textual_app(candidate):
            apps.append(candidate)

    # If no common names found, search with pattern
    if not apps:
        for file_path in search_path.rglob(pattern):
            if file_path.suffix == ".py" and is_textual_app(file_path):
                apps.append(file_path)

    return apps


def is_textual_app(file_path: Path) -> bool:
    """Check if file contains a Textual app."""
    try:
        content = file_path.read_text(encoding="utf-8")
        # Look for Textual imports and App class patterns
        has_textual_import = "from textual" in content or "import textual" in content
        has_app_class = "class" in content and (
            "App)" in content or "App(" in content or "App:" in content
        )
        return has_textual_import and has_app_class
    except (UnicodeDecodeError, FileNotFoundError, PermissionError):
        return False


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Quiet output")
@click.version_option(version="0.1.0", prog_name="textual-snapshot")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool) -> None:
    """Professional visual testing for Textual applications."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet

    if verbose and quiet:
        raise click.UsageError("Cannot use --verbose and --quiet together")


@cli.command()
@click.argument("app_path", type=click.Path(exists=True, path_type=Path), required=False)
@click.option(
    "--context", "-c", default="capture", help="Context name for screenshot (default: capture)"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["svg", "png", "both"], case_sensitive=False),
    default="svg",
    help="Output format (default: svg)",
)
@click.option(
    "--interactions",
    "-i",
    help='Comma-separated interaction sequence (e.g., "click:#button,wait:0.5,press:enter")',
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    help="Output directory (default: screenshots/)",
)
@click.option(
    "--interactive", is_flag=True, help="Interactive app selection when multiple apps found"
)
@click.pass_context
def capture(
    ctx: click.Context,
    app_path: Optional[Path],
    context: str,
    format: str,
    interactions: Optional[str],
    output_dir: Optional[Path],
    interactive: bool,
) -> None:
    """Capture screenshots of Textual applications with auto-discovery."""
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    try:
        # Run the async capture operation
        result = asyncio.run(
            run_capture(
                app_path=app_path,
                context=context,
                output_format=format,
                interactions=interactions,
                output_dir=output_dir,
                interactive=interactive,
                verbose=verbose,
                quiet=quiet,
            )
        )

        if result:
            success_message("Screenshot capture completed successfully")
        else:
            error_exit("Screenshot capture failed")

    except KeyboardInterrupt:
        warning_message("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        if verbose:
            console.print_exception()
        error_exit(f"Capture failed: {e}")


async def run_capture(
    app_path: Optional[Path],
    context: str,
    output_format: str,
    interactions: Optional[str],
    output_dir: Optional[Path],
    interactive: bool,
    verbose: bool,
    quiet: bool,
) -> bool:
    """Run the capture operation asynchronously."""
    from .capture import ScreenshotFormat, capture_app_screenshot

    # Auto-discover apps if no path provided
    if app_path is None:
        if not quiet:
            info_message("Auto-discovering Textual applications...")

        discovered_apps = auto_discover_apps()

        if not discovered_apps:
            error_exit("No Textual applications found. Try specifying an app file directly.")

        if len(discovered_apps) == 1:
            app_path = discovered_apps[0]
            if not quiet:
                info_message(f"Found app: {app_path}")
        else:
            if interactive:
                app_path = select_app_interactive(discovered_apps)
            else:
                # Use first discovered app with warning
                app_path = discovered_apps[0]
                warning_message(f"Multiple apps found, using: {app_path}")
                if verbose:
                    info_message("Other apps found:")
                    for app in discovered_apps[1:]:
                        info_message(f"  - {app}")
                    info_message("Use --interactive for manual selection")

    # Set up output directory
    if output_dir is None:
        output_dir = Path.cwd() / "screenshots"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse interactions if provided
    interaction_list = None
    if interactions:
        interaction_list = [cmd.strip() for cmd in interactions.split(",")]

    # Convert format string to enum
    format_enum = ScreenshotFormat(output_format.lower())

    # Display capture info
    if not quiet:
        table = Table(title="Capture Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("App File", str(app_path))
        table.add_row("Context", context)
        table.add_row("Format", output_format.upper())
        table.add_row("Output Directory", str(output_dir))
        if interaction_list:
            table.add_row("Interactions", str(len(interaction_list)) + " commands")

        console.print(table)
        console.print()

    # Capture screenshot
    with create_progress() as progress:
        task_id = progress.add_task("Capturing screenshot...", total=1)

        try:
            # Import and load the app
            result = await capture_app_screenshot(
                app_source=load_app_from_file(app_path),
                context=context,
                output_format=format_enum,
                interactions=interaction_list,
            )

            progress.update(task_id, advance=1)

            # Display results
            if not quiet:
                console.print(
                    Panel(
                        f"""[green]✓[/green] Screenshot captured successfully

[bold]Path:[/bold] {result.screenshot_path}
[bold]Size:[/bold] {result.file_size_bytes:,} bytes
[bold]Format:[/bold] {result.format}
[bold]Timestamp:[/bold] {result.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}""",
                        title="Capture Complete",
                        expand=False,
                    )
                )

            return True

        except Exception as e:
            progress.stop()
            raise CLIError(f"Failed to capture screenshot: {e}") from e


def select_app_interactive(apps: list[Path]) -> Path:
    """Interactive app selection."""
    console.print("\n[bold]Multiple Textual applications found:[/bold]")

    for i, app in enumerate(apps, 1):
        console.print(f"  {i}. {app}")

    while True:
        try:
            choice: int = click.prompt("\nSelect app number", type=int)
            if 1 <= choice <= len(apps):
                return apps[choice - 1]
            else:
                console.print(f"[red]Please enter a number between 1 and {len(apps)}[/red]")
        except (ValueError, click.Abort):
            error_exit("Invalid selection")


def load_app_from_file(app_path: Path) -> Any:
    """Load Textual app class from Python file."""
    import importlib.util
    import sys

    # Load module from file
    spec = importlib.util.spec_from_file_location("app_module", app_path)
    if spec is None or spec.loader is None:
        raise CLIError(f"Could not load module from {app_path}")

    module = importlib.util.module_from_spec(spec)

    # Add parent directory to sys.path temporarily
    parent_dir = str(app_path.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise CLIError(f"Could not execute module {app_path}: {e}") from e

    # Find App class
    from textual.app import App

    app_classes = []
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and issubclass(obj, App) and obj is not App:
            app_classes.append(obj)

    if not app_classes:
        raise CLIError(f"No Textual App class found in {app_path}")

    if len(app_classes) > 1:
        warning_message(f"Multiple App classes found, using: {app_classes[0].__name__}")

    return app_classes[0]


@cli.command()
@click.argument("baseline", type=click.Path(exists=True, path_type=Path))
@click.argument("current", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=0.95,
    help="Similarity threshold (0.0-1.0, default: 0.95)",
)
@click.option("--recursive", "-r", is_flag=True, help="Compare directories recursively")
@click.option(
    "--output-report", type=click.Path(path_type=Path), help="Output comparison report to JSON file"
)
@click.pass_context
def compare(
    ctx: click.Context,
    baseline: Path,
    current: Path,
    threshold: float,
    recursive: bool,
    output_report: Optional[Path],
) -> None:
    """Compare screenshots for regression detection."""
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    try:
        result = run_compare(
            baseline=baseline,
            current=current,
            threshold=threshold,
            recursive=recursive,
            output_report=output_report,
            verbose=verbose,
            quiet=quiet,
        )

        if result:
            success_message("Screenshot comparison completed")
        else:
            error_exit("Screenshot comparison failed or differences found")

    except KeyboardInterrupt:
        warning_message("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        if verbose:
            console.print_exception()
        error_exit(f"Comparison failed: {e}")


def run_compare(
    baseline: Path,
    current: Path,
    threshold: float,
    recursive: bool,
    output_report: Optional[Path],
    verbose: bool,
    quiet: bool,
) -> bool:
    """Run the comparison operation."""
    import json

    from .comparison import calculate_file_similarity

    results = []

    # Handle directory comparison
    if baseline.is_dir() and current.is_dir():
        if recursive:
            baseline_files = list(baseline.rglob("*.svg")) + list(baseline.rglob("*.png"))
        else:
            baseline_files = [f for f in baseline.iterdir() if f.suffix.lower() in [".svg", ".png"]]

        if not quiet:
            info_message(f"Comparing {len(baseline_files)} files...")

        with create_progress() as progress:
            task_id = progress.add_task("Comparing screenshots...", total=len(baseline_files))

            for baseline_file in baseline_files:
                # Find corresponding current file
                relative_path = baseline_file.relative_to(baseline)
                current_file = current / relative_path

                if current_file.exists():
                    similarity = calculate_file_similarity(baseline_file, current_file)
                    results.append(
                        {
                            "baseline": str(baseline_file),
                            "current": str(current_file),
                            "similarity": similarity,
                            "passed": similarity >= threshold,
                        }
                    )
                else:
                    results.append(
                        {
                            "baseline": str(baseline_file),
                            "current": "MISSING",
                            "similarity": 0.0,
                            "passed": False,
                        }
                    )

                progress.update(task_id, advance=1)

    # Handle single file comparison
    elif baseline.is_file() and current.is_file():
        similarity = calculate_file_similarity(baseline, current)
        results.append(
            {
                "baseline": str(baseline),
                "current": str(current),
                "similarity": similarity,
                "passed": similarity >= threshold,
            }
        )

    else:
        raise CLIError("Both paths must be files or both must be directories")

    # Display results table
    if not quiet:
        display_comparison_results(results, threshold)

    # Save report if requested
    if output_report:
        report_data = {
            "threshold": threshold,
            "summary": {
                "total": len(results),
                "passed": sum(1 for r in results if r["passed"]),
                "failed": sum(1 for r in results if not r["passed"]),
            },
            "results": results,
        }

        output_report.parent.mkdir(parents=True, exist_ok=True)
        with open(output_report, "w") as f:
            json.dump(report_data, f, indent=2)

        if not quiet:
            info_message(f"Report saved to: {output_report}")

    # Return success if all comparisons passed
    return all(result["passed"] for result in results)


def display_comparison_results(results: list[dict[str, Any]], threshold: float) -> None:
    """Display comparison results in a Rich table."""
    table = Table(title="Comparison Results")
    table.add_column("File", style="cyan")
    table.add_column("Similarity", justify="right")
    table.add_column("Status", justify="center")
    table.add_column("Notes")

    for result in results:
        baseline_name = Path(result["baseline"]).name
        similarity = result["similarity"]

        if result["current"] == "MISSING":
            status = "[red]✗[/red]"
            similarity_str = "N/A"
            notes = "File missing"
        elif result["passed"]:
            status = "[green]✓[/green]"
            similarity_str = f"{similarity:.3f}"
            notes = "Passed"
        else:
            status = "[red]✗[/red]"
            similarity_str = f"{similarity:.3f}"
            notes = f"Below threshold ({threshold:.3f})"

        table.add_row(baseline_name, similarity_str, status, notes)

    console.print(table)

    # Summary
    passed = sum(1 for r in results if r["passed"])
    total = len(results)

    if passed == total:
        console.print(f"\n[green]✓ All {total} comparisons passed[/green]")
    else:
        console.print(f"\n[red]✗ {total - passed} of {total} comparisons failed[/red]")


@cli.command()
@click.option(
    "--from",
    "source_format",
    type=click.Choice(["pytest-textual-snapshot"], case_sensitive=False),
    default="pytest-textual-snapshot",
    help="Source format to migrate from (default: pytest-textual-snapshot)",
)
@click.option("--dry-run", is_flag=True, help="Preview migration without making changes")
@click.option(
    "--source-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path.cwd(),
    help="Source directory containing screenshots to migrate",
)
@click.pass_context
def migrate(ctx: click.Context, source_format: str, dry_run: bool, source_dir: Path) -> None:
    """Migrate screenshots from other testing frameworks."""
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    try:
        result = run_migrate(
            source_format=source_format,
            dry_run=dry_run,
            source_dir=source_dir,
            verbose=verbose,
            quiet=quiet,
        )

        if result:
            if dry_run:
                success_message("Migration preview completed - no changes made")
            else:
                success_message("Migration completed successfully")
        else:
            error_exit("Migration failed")

    except KeyboardInterrupt:
        warning_message("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        if verbose:
            console.print_exception()
        error_exit(f"Migration failed: {e}")


def run_migrate(
    source_format: str, dry_run: bool, source_dir: Path, verbose: bool, quiet: bool
) -> bool:
    """Run the migration operation."""

    if source_format == "pytest-textual-snapshot":
        return migrate_from_pytest_textual_snapshot(source_dir, dry_run, verbose, quiet)
    else:
        raise CLIError(f"Unsupported source format: {source_format}")


def migrate_from_pytest_textual_snapshot(
    source_dir: Path, dry_run: bool, verbose: bool, quiet: bool
) -> bool:
    """Migrate from pytest-textual-snapshot format."""
    import shutil

    # Look for pytest-textual-snapshot directories
    snapshot_dirs = []
    for directory in source_dir.rglob("*"):
        if directory.is_dir() and (
            "snapshot" in directory.name.lower() or "test" in directory.name.lower()
        ):
            svg_files = list(directory.glob("*.svg"))
            if svg_files:
                snapshot_dirs.append(directory)

    if not snapshot_dirs:
        if not quiet:
            warning_message("No pytest-textual-snapshot directories found")
        return True

    if not quiet:
        info_message(f"Found {len(snapshot_dirs)} snapshot directories")

    # Create migration plan
    migration_plan: list[dict[str, Any]] = []
    target_dir = source_dir / "screenshots"

    for snapshot_dir in snapshot_dirs:
        svg_files = list(snapshot_dir.glob("*.svg"))
        for svg_file in svg_files:
            # Generate new filename with timestamp
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"{svg_file.stem}_migrated_{timestamp}.svg"
            target_path = target_dir / new_name

            migration_plan.append(
                {"source": svg_file, "target": target_path, "size": svg_file.stat().st_size}
            )

    # Display migration plan
    if not quiet:
        table = Table(title="Migration Plan" + (" (DRY RUN)" if dry_run else ""))
        table.add_column("Source", style="cyan")
        table.add_column("Target", style="green")
        table.add_column("Size", justify="right")

        for plan_item in migration_plan[:10]:  # Show first 10
            table.add_row(
                str(plan_item["source"].relative_to(source_dir)),
                str(plan_item["target"].relative_to(source_dir)),
                f"{plan_item['size']:,} bytes",
            )

        if len(migration_plan) > 10:
            table.add_row("...", "...", f"... and {len(migration_plan) - 10} more")

        console.print(table)

    if dry_run:
        if not quiet:
            console.print(f"\n[yellow]DRY RUN:[/yellow] Would migrate {len(migration_plan)} files")
        return True

    # Execute migration
    if not migration_plan:
        if not quiet:
            info_message("No files to migrate")
        return True

    target_dir.mkdir(parents=True, exist_ok=True)

    with create_progress() as progress:
        task_id = progress.add_task("Migrating files...", total=len(migration_plan))

        for plan_item in migration_plan:
            try:
                shutil.copy2(plan_item["source"], plan_item["target"])
                progress.update(task_id, advance=1)
            except Exception as e:
                progress.stop()
                raise CLIError(f"Failed to migrate {plan_item['source']}: {e}") from e

    if not quiet:
        success_message(f"Migrated {len(migration_plan)} files to {target_dir}")

    return True


@cli.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--to",
    "target_format",
    type=click.Choice(["png", "svg"], case_sensitive=False),
    required=True,
    help="Target format for conversion",
)
@click.option(
    "--quality",
    type=click.Choice(["low", "medium", "high"]),
    default="high",
    help="Quality setting for PNG output (default: high)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    help="Output directory (default: converted/)",
)
@click.option("--batch", is_flag=True, help="Process multiple files (if input_path is directory)")
@click.pass_context
def convert(
    ctx: click.Context,
    input_path: Path,
    target_format: str,
    quality: str,
    output_dir: Optional[Path],
    batch: bool,
) -> None:
    """Convert screenshots between formats (SVG/PNG)."""
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    try:
        result = run_convert(
            input_path=input_path,
            target_format=target_format,
            quality=quality,
            output_dir=output_dir,
            batch=batch,
            verbose=verbose,
            quiet=quiet,
        )

        if result:
            success_message("Conversion completed successfully")
        else:
            error_exit("Conversion failed")

    except KeyboardInterrupt:
        warning_message("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        if verbose:
            console.print_exception()
        error_exit(f"Conversion failed: {e}")


def run_convert(
    input_path: Path,
    target_format: str,
    quality: str,
    output_dir: Optional[Path],
    batch: bool,
    verbose: bool,
    quiet: bool,
) -> bool:
    """Run the conversion operation."""

    # Set up output directory
    if output_dir is None:
        output_dir = input_path.parent / "converted"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect files to convert
    files_to_convert = []

    if input_path.is_file():
        files_to_convert.append(input_path)
    elif input_path.is_dir() and batch:
        # Find files with opposite extension
        source_ext = ".png" if target_format == "svg" else ".svg"
        files_to_convert = list(input_path.rglob(f"*{source_ext}"))
    else:
        raise CLIError("For directory input, use --batch flag")

    if not files_to_convert:
        if not quiet:
            warning_message("No files found to convert")
        return True

    if not quiet:
        info_message(f"Converting {len(files_to_convert)} files to {target_format.upper()}...")

    # Convert files
    with create_progress() as progress:
        task_id = progress.add_task("Converting files...", total=len(files_to_convert))

        for file_path in files_to_convert:
            try:
                if target_format == "png":
                    convert_svg_to_png_with_fallback(file_path, output_dir, quality)
                else:
                    convert_png_to_svg(file_path, output_dir)

                progress.update(task_id, advance=1)

            except Exception as e:
                progress.stop()
                raise CLIError(f"Failed to convert {file_path}: {e}") from e

    if not quiet:
        success_message(f"Converted {len(files_to_convert)} files to {output_dir}")

    return True


def convert_svg_to_png_with_fallback(svg_path: Path, output_dir: Path, quality: str) -> None:
    """Convert SVG to PNG using high-quality browser conversion with librsvg fallback."""
    from .conversion import (
        check_browser_availability,
        convert_svg_to_png_sync,
    )

    # Try high-quality browser conversion first
    if check_browser_availability():
        try:
            convert_svg_to_png_sync(svg_path, output_dir, quality)
            return
        except Exception as e:
            # Log browser conversion failure but don't fail completely
            import logging

            logging.getLogger(__name__).warning(
                f"Browser conversion failed, falling back to librsvg: {e}"
            )

    # Fallback to original librsvg implementation
    convert_svg_to_png_librsvg(svg_path, output_dir, quality)


def convert_svg_to_png_librsvg(svg_path: Path, output_dir: Path, quality: str) -> None:
    """Convert SVG to PNG using rsvg-convert (legacy fallback)."""
    import subprocess

    output_path = output_dir / f"{svg_path.stem}.png"

    # Quality settings for librsvg
    dpi_map = {"low": 72, "medium": 150, "high": 300}
    dpi = dpi_map[quality]

    # Use rsvg-convert if available
    try:
        subprocess.run(
            [
                "rsvg-convert",
                "--dpi-x",
                str(dpi),
                "--dpi-y",
                str(dpi),
                "--format",
                "png",
                "--output",
                str(output_path),
                str(svg_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        from .conversion import get_fallback_conversion_message

        raise CLIError(
            get_fallback_conversion_message()
            + "\n\n"
            + "rsvg-convert not found. Install with: brew install librsvg (macOS) or apt-get install librsvg2-bin (Linux)"
        ) from None
    except subprocess.CalledProcessError as e:
        raise CLIError(f"rsvg-convert failed: {e.stderr}") from e


def convert_png_to_svg(png_path: Path, output_dir: Path) -> None:
    """Convert PNG to SVG (embed PNG in SVG wrapper)."""
    import base64

    from PIL import Image

    output_path = output_dir / f"{png_path.stem}.svg"

    # Open PNG and get dimensions
    with Image.open(png_path) as img:
        width, height = img.size

    # Read PNG as base64
    with open(png_path, "rb") as f:
        png_data = base64.b64encode(f.read()).decode("ascii")

    # Create SVG wrapper
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <image x="0" y="0" width="{width}" height="{height}" xlink:href="data:image/png;base64,{png_data}"/>
</svg>'''

    output_path.write_text(svg_content)


def main() -> None:
    """Main CLI entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Fatal error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
