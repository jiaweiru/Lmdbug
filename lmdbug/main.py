"""
Lmdbug - LMDB Data Preview Tool

Main entry point for the application.
"""

from pathlib import Path
import typer
from .ui.gradio_interface import LmdbugInterface
from .core.logging import setup as setup_logging, get_logger
from .core.config import config

logger = get_logger(__name__)


def main(
    db_path: str = typer.Option(
        None, "--db-path", "-d", help="Path to LMDB database directory"
    ),
    protobuf_module: str = typer.Option(
        None,
        "--protobuf-module",
        "-p",
        help="Path to compiled protobuf module (.py file)",
    ),
    message_class: str = typer.Option(
        None, "--message-class", "-m", help="Protobuf message class name"
    ),
    processor_paths: list[str] = typer.Option(
        None,
        "--processor-path",
        help="Path to processor file (can be used multiple times)",
    ),
    port: int = typer.Option(7860, "--port", help="Port to run the web interface on"),
    host: str = typer.Option(
        "127.0.0.1", "--host", help="Host to bind the web interface to"
    ),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level"),
    version: bool = typer.Option(False, "--version", help="Show version and exit"),
):
    """Simple LMDB data preview tool with optional Protobuf support.

    Examples:
      lmdbug                                                    # Basic usage
      lmdbug -d /path/to/db                                     # With database
      lmdbug -d /path/to/db -p proto_pb2.py -m MessageClass     # With protobuf
      lmdbug --processor-path /path/to/custom_processors.py     # With custom processors
    """
    if version:
        typer.echo("Lmdbug version 0.1.0")
        raise typer.Exit()

    # Update configuration from command line arguments
    config.update_from_cli_args(
        db_path=db_path,
        protobuf_module_path=protobuf_module,
        protobuf_message_class=message_class,
        processor_paths=processor_paths,
        ui_host=host,
        ui_port=port,
        log_level=log_level,
    )

    setup_logging(level=config.log_level)

    try:
        if config.db_path:
            if not Path(config.db_path).exists():
                typer.echo(f"✗ Database path does not exist: {config.db_path}")
                raise typer.Exit(1)
            typer.echo(f"✓ Database path: {config.db_path}")
        else:
            typer.echo(
                "⚠ No database path specified. You can set it through the web interface."
            )

        if config.protobuf_module_path:
            if not config.protobuf_message_class:
                typer.echo("✗ --message-class is required when using --protobuf-module")
                raise typer.Exit(1)

            if not Path(config.protobuf_module_path).exists():
                typer.echo(
                    f"✗ Protobuf module does not exist: {config.protobuf_module_path}"
                )
                raise typer.Exit(1)

            typer.echo(
                f"✓ Protobuf module: {config.protobuf_module_path} -> {config.protobuf_message_class}"
            )

        if config.processor_paths:
            for i, processor_path in enumerate(config.processor_paths):
                if not Path(processor_path).exists():
                    typer.echo(
                        f"⚠ Processor file {i + 1} does not exist: {processor_path}"
                    )
                else:
                    typer.echo(f"✓ Processor file {i + 1}: {processor_path}")

        typer.echo("🚀 Starting Lmdbug web interface...")
        typer.echo(f"   Host: {config.ui_host}")
        typer.echo(f"   Port: {config.ui_port}")
        typer.echo(f"   URL: http://{config.ui_host}:{config.ui_port}")

        interface = LmdbugInterface(config)
        logger.info("Lmdbug interface initialized")

        if config.db_path or config.has_protobuf_config or config.processor_paths:
            interface.set_initial_config(
                db_path=config.db_path,
                protobuf_config=config.protobuf_config_dict,
                processor_paths=config.processor_paths,
            )

        interface.launch(
            server_name=config.ui_host,
            server_port=config.ui_port,
            share=False,
            quiet=False,
        )

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
