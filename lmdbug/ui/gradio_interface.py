"""
Simplified Gradio interface for LMDB data preview.
"""
import gradio as gr
from pathlib import Path
from ..core.data_service import DataService
from ..core.logging import get_logger
from ..core.config import LmdbugConfig

logger = get_logger(__name__)


class LmdbugInterface:
    """Simple Gradio-based web interface for LMDB data preview."""

    def __init__(self, config: LmdbugConfig | None = None):
        self.config = config
        self.data_service: DataService | None = None
        self.initial_db_path: str | None = None
        self.initial_protobuf_config: dict[str, str] | None = None

    def create_interface(self) -> gr.Blocks:
        with gr.Blocks(
            title="Lmdbug - LMDB Data Preview Tool", theme=gr.themes.Soft()
        ) as interface:
            gr.Markdown("# Lmdbug - LMDB Data Preview Tool")
            gr.Markdown("Simple LMDB database content preview with optional Protobuf support")

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("## Configuration")
                    db_path_input = gr.Textbox(
                        label="LMDB Database Path",
                        placeholder="/path/to/lmdb/database",
                        value=self.initial_db_path,
                    )
                    
                    with gr.Row():
                        protobuf_module_input = gr.Textbox(
                            label="Protobuf Module (Optional)",
                            placeholder="/path/to/your_pb2.py",
                            value=self.initial_protobuf_config.get("module_path")
                            if self.initial_protobuf_config else None,
                            scale=2
                        )
                        message_class_input = gr.Textbox(
                            label="Message Class",
                            placeholder="MessageClass",
                            value=self.initial_protobuf_config.get("message_class")
                            if self.initial_protobuf_config else None,
                            scale=1
                        )
                    
                    load_btn = gr.Button("Load Database", variant="primary")
                    
                    status_display = gr.Textbox(
                        label="Status",
                        value="Ready to load database",
                        interactive=False,
                        max_lines=2,
                    )
                    db_info_display = gr.JSON(label="Database Info", value={})

                with gr.Column(scale=2):
                    gr.Markdown("## Data Preview")
                    
                    with gr.Row():
                        search_input = gr.Textbox(
                            label="Regex Search",
                            placeholder="Enter regex pattern (e.g., user.*, config, test_.*)",
                            scale=3
                        )
                        gr.Markdown("*Supports regex patterns*")
                        search_btn = gr.Button("Search", scale=1)
                    
                    with gr.Row():
                        entry_count = gr.Number(
                            label="Entries to show",
                            value=10,
                            minimum=1,
                            maximum=100,
                            scale=1
                        )
                        browse_btn = gr.Button("Browse First Entries", scale=1)
                    
                    results_display = gr.JSON(label="Results", value=[])
                    
                    with gr.Row():
                        text_preview = gr.Textbox(
                            label="Text Preview",
                            lines=8,
                            interactive=False
                        )
                        audio_preview = gr.Audio(label="Audio Preview")

            # Event handlers
            load_btn.click(
                self._load_database,
                [db_path_input, protobuf_module_input, message_class_input],
                [db_info_display, status_display]
            )
            
            browse_btn.click(
                self._browse_entries,
                [entry_count],
                [results_display, status_display, text_preview, audio_preview]
            )
            
            search_btn.click(
                self._search_data,
                [search_input, gr.State("similarity"), entry_count],
                [results_display, status_display, text_preview, audio_preview]
            )

        return interface

    def set_initial_config(
        self, db_path: str | None = None, protobuf_config: dict[str, str] | None = None
    ):
        if db_path:
            self.initial_db_path = db_path
        if protobuf_config:
            self.initial_protobuf_config = protobuf_config

    def _load_database(self, db_path: str, protobuf_module: str, message_class: str) -> tuple[dict, str]:
        if not db_path.strip():
            return {}, "Error: Database path is required"
        
        if not Path(db_path).exists():
            return {}, f"Error: Database path does not exist: {db_path}"

        try:
            # Close existing service
            if self.data_service:
                self.data_service.close()
            
            # Use configuration for processor paths if available
            processor_paths = None
            if self.config:
                processor_paths = self.config.processor_paths
            
            self.data_service = DataService(
                db_path, 
                processor_paths=processor_paths
            )
            self.data_service.open()
            
            # Load protobuf if provided
            if protobuf_module.strip() and message_class.strip():
                if not Path(protobuf_module).exists():
                    return {}, f"Error: Protobuf module not found: {protobuf_module}"
                self.data_service.load_protobuf_module(protobuf_module, message_class)
            
            db_info = self.data_service.get_database_info()
            status = f"✅ Database loaded: {Path(db_path).name}"
            if protobuf_module.strip():
                status += f" (Protobuf: {message_class})"
            
            logger.info(f"Database successfully loaded: {Path(db_path).name}, entries: {db_info.get('entries', 'unknown')}")
            return db_info, status
            
        except Exception as e:
            logger.warning(f"Failed to load database: {e}")  # User input error, not system error
            return {}, f"Error: {str(e)}"

    def _search_data(self, query: str, _search_type: str, limit: int) -> tuple[list, str, str, str | None]:
        if not self.data_service:
            return [], "Error: No database loaded", "", None
        
        if not query.strip():
            return [], "Error: Search query is required", "", None
        
        try:
            results = self.data_service.search_keys(query, limit)
            text_preview = self._extract_text_preview(results)
            audio_preview = self._extract_audio_preview(results)
            
            return results, f"Found {len(results)} matches", text_preview, audio_preview
        except Exception as e:
            logger.warning(f"Search failed: {e}")  # User input error, not system error
            return [], f"Error: {str(e)}", "", None

    def _browse_entries(self, count: int) -> tuple[list, str, str, str | None]:
        if not self.data_service:
            return [], "Error: No database loaded", "", None
        
        try:
            results = self.data_service.get_first_entries(count)
            text_preview = self._extract_text_preview(results)
            audio_preview = self._extract_audio_preview(results)
            
            return results, f"Showing first {len(results)} entries", text_preview, audio_preview
        except Exception as e:
            logger.warning(f"Browse failed: {e}")  # User operation error, not system error
            return [], f"Error: {str(e)}", "", None

    def _extract_text_preview(self, results: list[dict]) -> str:
        """Extract text content from results for preview."""
        text_parts = []
        for result in results:
            if "media_preview" in result and "text" in result["media_preview"]:
                for text_item in result["media_preview"]["text"]:
                    if "content" in text_item:
                        text_parts.append(f"[{text_item.get('field_name', 'text')}] {text_item['content']}")
                
        return "\n\n".join(text_parts[:3])  # Limit to first 3 text previews

    def _extract_audio_preview(self, results: list[dict]) -> str | None:
        """Extract first audio file path from results."""
        for result in results:
            if "media_preview" in result and "audio" in result["media_preview"]:
                audio_list = result["media_preview"]["audio"]
                if audio_list and "temp_path" in audio_list[0]:
                    return audio_list[0]["temp_path"]
        return None

    def cleanup_temp_files(self):
        """Clean up temporary files."""
        if self.data_service:
            self.data_service.cleanup_temp_files()

    def launch(self, **kwargs):
        interface = self.create_interface()
        try:
            interface.launch(**kwargs)
        finally:
            self.cleanup_temp_files()
            logger.info("Cleaned up temporary files on interface shutdown")