"""
Lmdbug - LMDB Data Preview Tool

Main entry point for the application.
"""

from pathlib import Path
import typer
from .ui.gradio_interface import LmdbugInterface
from .core.logging import setup as setup_logging, get_logger

logger = get_logger(__name__)


def main(
    db_path: str = typer.Argument(None, help="Path to LMDB database directory"),
    protobuf_module: str = typer.Option(
        None,
        "--protobuf-module",
        "-p",
        help="Path to compiled protobuf module (.py file)",
    ),
    message_class: str = typer.Option(
        None, "--message-class", "-m", help="Protobuf message class name"
    ),
    port: int = typer.Option(7860, "--port", help="Port to run the web interface on"),
    host: str = typer.Option(
        "127.0.0.1", "--host", help="Host to bind the web interface to"
    ),
    log_level: str = typer.Option(
        "INFO", "--log-level", help="Logging level (DEBUG, INFO, WARNING, ERROR)"
    ),
    version: bool = typer.Option(False, "--version", help="Show version and exit"),
):
    """
    Lmdbug - LMDB Data Preview Tool with Protobuf Support

    Preview and explore LMDB database content through a web interface.

    Examples:

      # Basic usage with database path
      lmdbug /path/to/lmdb/database

      # With protobuf support
      lmdbug /path/to/lmdb/database --protobuf-module user_pb2.py --message-class User

      # Custom host and port
      lmdbug /path/to/lmdb/database --host 0.0.0.0 --port 8080
    """
    # Show version
    if version:
        typer.echo("Lmdbug version 0.1.0")
        raise typer.Exit()

    # Setup logging
    setup_logging(level=log_level)

    try:
        # Validate database path if provided
        if db_path:
            if not Path(db_path).exists():
                typer.echo(f"✗ Database path does not exist: {db_path}")
                raise typer.Exit(1)
            typer.echo(f"✓ Database path: {db_path}")
        else:
            typer.echo(
                "⚠ No database path specified. You can set it through the web interface."
            )

        # Validate protobuf module if provided
        protobuf_config = None
        if protobuf_module:
            if not message_class:
                typer.echo("✗ --message-class is required when using --protobuf-module")
                raise typer.Exit(1)

            if not Path(protobuf_module).exists():
                typer.echo(f"✗ Protobuf module does not exist: {protobuf_module}")
                raise typer.Exit(1)

            protobuf_config = {
                "module_path": protobuf_module,
                "message_class": message_class,
            }
            typer.echo(f"✓ Protobuf module: {protobuf_module} -> {message_class}")

        # Create and launch the interface
        typer.echo("🚀 Starting Lmdbug web interface...")
        typer.echo(f"   Host: {host}")
        typer.echo(f"   Port: {port}")
        typer.echo(f"   URL: http://{host}:{port}")

        interface = LmdbugInterface()

        # Pre-configure if parameters provided
        if db_path or protobuf_config:
            interface.set_initial_config(
                db_path=db_path, protobuf_config=protobuf_config
            )

        interface.launch(server_name=host, server_port=port, share=False, quiet=False)

    except KeyboardInterrupt:
        typer.echo("\n👋 Lmdbug stopped by user")
    except Exception as e:
        logger.error(f"Failed to start Lmdbug: {e}")
        typer.echo(f"✗ Error: {e}")
        raise typer.Exit(1)


app = typer.Typer(help="Lmdbug - LMDB Data Preview Tool with Protobuf Support")
app.command()(main)


def cli():
    """Entry point for console script."""
    app()


if __name__ == "__main__":
    app()
