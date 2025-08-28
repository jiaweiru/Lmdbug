import gradio as gr
from pathlib import Path
from ..core.preview_service import PreviewService
from ..core.logging import get_logger

logger = get_logger(__name__)


class LmdbugInterface:
    """
    Gradio-based web interface for LMDB data preview.
    """

    def __init__(self):
        """Initialize the Lmdbug interface."""
        self.preview_service: PreviewService | None = None
        self.current_db_path: str | None = None
        self.current_protobuf_config: dict[str, str] = {}
        self.initial_db_path: str | None = None
        self.initial_protobuf_config: dict[str, str] | None = None
        self.current_temp_files: list[str] = []

    def create_interface(self) -> gr.Blocks:
        """
        Create and configure the Gradio interface.

        Returns:
            Gradio Blocks interface
        """
        with gr.Blocks(
            title="Lmdbug - LMDB Data Preview Tool", theme=gr.themes.Soft()
        ) as interface:
            gr.Markdown("# Lmdbug - LMDB Data Preview Tool")
            gr.Markdown(
                "Preview LMDB database content with Protobuf deserialization support"
            )

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("## Database Configuration")

                    db_path_input = gr.Textbox(
                        label="LMDB Database Path",
                        placeholder="/path/to/lmdb/database",
                        value=self.initial_db_path,
                    )

                    db_load_btn = gr.Button(
                        "🔄 Load/Reload Database", variant="primary"
                    )

                    gr.Markdown("### Protobuf Configuration (Optional)")

                    protobuf_module_input = gr.Textbox(
                        label="Protobuf Module Path",
                        placeholder="/path/to/your_pb2.py",
                        value=self.initial_protobuf_config.get("module_path", None),
                    )

                    message_class_input = gr.Textbox(
                        label="Message Class Name",
                        placeholder="YourMessageClass",
                        value=self.initial_protobuf_config.get("message_class", None),
                    )

                    protobuf_load_btn = gr.Button(
                        "🔌 Load/Reload Protobuf", variant="secondary"
                    )

                    gr.Markdown("### Current Configuration")
                    config_status = gr.Textbox(
                        label="Status",
                        value="No configuration loaded",
                        interactive=False,
                        max_lines=3,
                    )

                    db_info_display = gr.JSON(label="Database Information", value={})

                    message_type_dropdown = gr.Dropdown(
                        label="Primary Protobuf Message Type",
                        choices=[],
                        value=None,
                        interactive=True,
                    )

                    gr.Markdown("### Custom Processors")
                    processor_file_input = gr.Textbox(
                        label="Custom Processor File Path",
                        placeholder="config_examples/custom_processors.py",
                    )
                    processor_load_btn = gr.Button("🔌 Load Processors")

                    gr.Markdown("### Field Configuration")
                    with gr.Row():
                        config_file_input = gr.Textbox(
                            label="Config File Path",
                            placeholder="config_examples/example_field_config.json",
                            scale=3,
                        )
                        config_load_btn = gr.Button("📁 Load Config", scale=1)
                    
                    field_config_input = gr.Textbox(
                        label="Field Configuration (JSON)",
                        placeholder='{"audio_data": {"processor": "pcm_audio_16khz", "config": {"sample_rate": 16000}}}',
                        lines=5,
                    )
                    field_config_btn = gr.Button("🔧 Apply Field Config")

                with gr.Column(scale=2):
                    gr.Markdown("## Data Preview and Search")

                    with gr.Tabs():
                        with gr.TabItem("Browse"):
                            with gr.Row():
                                preview_count = gr.Number(
                                    label="Number of entries",
                                    value=10,
                                    minimum=1,
                                    maximum=1000,
                                )
                                preview_btn = gr.Button("Preview First Entries")

                            with gr.Row():
                                start_index = gr.Number(
                                    label="Start Index", value=0, minimum=0
                                )
                                index_count = gr.Number(
                                    label="Count", value=10, minimum=1, maximum=1000
                                )
                                index_btn = gr.Button("Browse by Index")

                        with gr.TabItem("Key Search"):
                            exact_key_input = gr.Textbox(
                                label="Exact Key",
                                placeholder="Enter exact key to search",
                            )
                            exact_search_btn = gr.Button("Search Exact Key")

                            prefix_input = gr.Textbox(
                                label="Key Prefix", placeholder="Enter key prefix"
                            )
                            prefix_limit = gr.Number(
                                label="Max Results", value=100, minimum=1, maximum=1000
                            )
                            prefix_search_btn = gr.Button("Search by Prefix")

                            pattern_input = gr.Textbox(
                                label="Key Pattern (substring)",
                                placeholder="Enter pattern to search in keys",
                            )
                            pattern_limit = gr.Number(
                                label="Max Results", value=100, minimum=1, maximum=1000
                            )
                            pattern_search_btn = gr.Button("Search by Pattern")

                    results_display = gr.JSON(
                        label="Results", value=[], show_label=True
                    )

                    with gr.Row():
                        with gr.Column():
                            text_preview = gr.Textbox(
                                label="Text Content",
                                lines=10,
                                max_lines=20,
                                interactive=False
                            )
                        
                        with gr.Column():
                            audio_preview = gr.Audio(
                                label="Audio Content"
                            )
                            
  
                            image_preview = gr.Image(
                                label="Image Content"
                            )

            status_display = gr.Textbox(
                label="Status", value="Ready to load database", interactive=False
            )

            db_load_btn.click(
                fn=self._load_database,
                inputs=[db_path_input],
                outputs=[db_info_display, config_status, status_display],
            )

            protobuf_load_btn.click(
                fn=self._load_protobuf,
                inputs=[protobuf_module_input, message_class_input],
                outputs=[message_type_dropdown, config_status, status_display],
            )

            message_type_dropdown.change(
                fn=self._set_message_type,
                inputs=[message_type_dropdown],
                outputs=[status_display],
            )

            processor_load_btn.click(
                fn=self._load_custom_processors,
                inputs=[processor_file_input],
                outputs=[status_display],
            )

            config_load_btn.click(
                fn=self._load_config_file,
                inputs=[config_file_input],
                outputs=[field_config_input, status_display],
            )

            field_config_btn.click(
                fn=self._apply_field_config,
                inputs=[field_config_input],
                outputs=[status_display],
            )

            preview_btn.click(
                fn=self._preview_first_entries,
                inputs=[preview_count],
                outputs=[results_display, status_display, text_preview, audio_preview, image_preview],
            )

            index_btn.click(
                fn=self._browse_by_index,
                inputs=[start_index, index_count],
                outputs=[results_display, status_display, text_preview, audio_preview, image_preview],
            )

            exact_search_btn.click(
                fn=self._search_exact_key,
                inputs=[exact_key_input],
                outputs=[results_display, status_display, text_preview, audio_preview, image_preview],
            )

            prefix_search_btn.click(
                fn=self._search_by_prefix,
                inputs=[prefix_input, prefix_limit],
                outputs=[results_display, status_display, text_preview, audio_preview, image_preview],
            )

            pattern_search_btn.click(
                fn=self._search_by_pattern,
                inputs=[pattern_input, pattern_limit],
                outputs=[results_display, status_display, text_preview, audio_preview, image_preview],
            )

        return interface

    def set_initial_config(
        self, db_path: str | None = None, protobuf_config: dict[str, str] | None = None
    ):
        """
        Set initial configuration values for the interface.

        Args:
            db_path: Initial database path
            protobuf_config: Initial protobuf configuration with 'module_path' and 'message_class'
        """
        if db_path:
            self.initial_db_path = db_path
        if protobuf_config:
            self.initial_protobuf_config = protobuf_config

    def _load_database(self, db_path: str) -> tuple[dict, str, str]:
        """Load or reload the LMDB database."""
        if not db_path.strip():
            return {}, "Error: Database path is required"

        if not Path(db_path).exists():
            return {}, f"Error: Database path does not exist: {db_path}"

        try:
            # Check if we're switching databases
            if self.current_db_path and self.current_db_path != db_path:
                logger.info(
                    f"Switching database from {self.current_db_path} to {db_path}"
                )

            # Initialize or reinitialize preview service
            self.preview_service = PreviewService(db_path)
            self.current_db_path = db_path

            # Reload protobuf configuration if available
            if self.current_protobuf_config:
                self._reload_protobuf_internal()

            # Get database information
            db_info = self.preview_service.get_database_info()

            status_msg = f"✅ Successfully loaded database: {db_path}"
            if self.current_protobuf_config:
                status_msg += f" (Protobuf: {self.current_protobuf_config.get('message_class', 'N/A')})"

            config_info = self._get_config_status()
            return db_info, config_info, status_msg

        except Exception as e:
            logger.error(f"Failed to load database: {e}")
            config_info = self._get_config_status()
            return {}, config_info, f"Error loading database: {str(e)}"

    def _load_protobuf(
        self, protobuf_module: str, message_class: str
    ) -> tuple[list[str], str, str]:
        """Load or reload protobuf configuration."""
        if not self.preview_service:
            config_info = self._get_config_status()
            return [], config_info, "Error: Load database first"

        if not protobuf_module.strip() or not message_class.strip():
            # Clear protobuf configuration
            self.current_protobuf_config = {}
            config_info = self._get_config_status()
            return [], config_info, "🧹 Protobuf configuration cleared"

        if not Path(protobuf_module).exists():
            return [], f"Error: Protobuf module not found: {protobuf_module}"

        try:
            # Update current configuration
            new_config = {
                "module_path": protobuf_module,
                "message_class": message_class,
            }

            # Check if configuration changed
            config_changed = self.current_protobuf_config != new_config
            if config_changed:
                logger.debug(f"Updating protobuf config: {message_class}")

            self.current_protobuf_config = new_config

            # Load protobuf modules
            modules = [{"path": protobuf_module, "message_class": message_class}]
            self.preview_service.load_protobuf_modules(modules, message_class)

            # Get available message types
            message_types = self.preview_service.get_available_message_types()

            status_msg = f"✅ Successfully loaded protobuf: {message_class}"
            if config_changed:
                status_msg += " (Configuration updated)"
            else:
                status_msg += " (Configuration reloaded)"

            config_info = self._get_config_status()
            return message_types, config_info, status_msg

        except Exception as e:
            logger.error(f"Failed to load protobuf: {e}")
            config_info = self._get_config_status()
            return [], config_info, f"Error loading protobuf: {str(e)}"

    def _reload_protobuf_internal(self):
        """Internal method to reload protobuf after database change."""
        if not self.current_protobuf_config:
            return

        try:
            modules = [
                {
                    "path": self.current_protobuf_config["module_path"],
                    "message_class": self.current_protobuf_config["message_class"],
                }
            ]
            self.preview_service.load_protobuf_modules(
                modules, self.current_protobuf_config["message_class"]
            )
            logger.debug("Protobuf configuration reloaded after database change")
        except Exception as e:
            logger.warning(f"Failed to reload protobuf after database change: {e}")
            self.current_protobuf_config = {}

    def _get_config_status(self) -> str:
        """Get current configuration status for display."""
        status_lines = []

        # Database status
        if self.current_db_path:
            status_lines.append(f"📊 Database: {self.current_db_path}")
        else:
            status_lines.append("🚫 No database loaded")

        # Protobuf status
        if self.current_protobuf_config:
            pb_class = self.current_protobuf_config.get("message_class", "Unknown")
            pb_module = Path(self.current_protobuf_config.get("module_path", "")).name
            status_lines.append(f"🔌 Protobuf: {pb_class} ({pb_module})")
        else:
            status_lines.append("🚫 No protobuf configuration")

        # Message type status
        if self.preview_service:
            try:
                current_type = getattr(
                    self.preview_service, "current_message_type", None
                )
                if current_type:
                    status_lines.append(f"🏷️ Active type: {current_type}")
            except AttributeError:
                pass

        return "\n".join(status_lines)

    def _check_service_loaded(self) -> str | None:
        """Check if preview service is loaded, return error message if not."""
        return "Error: No database loaded" if not self.preview_service else None

    def _set_message_type(self, message_type: str) -> str:
        """Set the primary protobuf message type."""
        if error := self._check_service_loaded():
            return error

        if message_type:
            self.preview_service.set_message_type(message_type)
            return f"Set primary message type to: {message_type}"
        return "No message type selected"

    def _apply_field_config(self, config_json: str) -> str:
        """Apply field configuration from JSON string."""
        if error := self._check_service_loaded():
            return error

        if not self.current_protobuf_config.get("message_class"):
            return "Error: No protobuf message type loaded"

        try:
            if config_json.strip():
                import json
                config = json.loads(config_json)
                self.preview_service.set_field_config(
                    self.current_protobuf_config["message_class"], config
                )
                return f"Applied field config: {config}"
            else:
                # Clear configuration
                self.preview_service.set_field_config(
                    self.current_protobuf_config["message_class"], {}
                )
                return "Cleared field configuration"
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON format - {e}"
        except Exception as e:
            return f"Error applying field config: {e}"

    def _load_custom_processors(self, processor_file_path: str) -> str:
        """Load custom processors from file."""
        if not processor_file_path.strip():
            return "Error: Processor file path is required"

        if not self.preview_service:
            return "Error: Load database first"

        try:
            self.preview_service.load_custom_processors(processor_file_path)
            return f"✅ Successfully loaded custom processors from: {processor_file_path}"
        except Exception as e:
            return f"❌ Error loading processors: {e}"

    def _load_config_file(self, config_file_path: str) -> tuple[str, str]:
        """Load configuration from JSON file."""
        if not config_file_path.strip():
            return "", "Error: Config file path is required"

        if not self.preview_service:
            return "", "Error: Load database first"

        try:
            config = self.preview_service.load_field_config_from_file(config_file_path)
            import json
            config_json = json.dumps(config, indent=2, ensure_ascii=False)
            return config_json, f"✅ Successfully loaded config from: {config_file_path}"
        except Exception as e:
            return "", f"❌ Error loading config: {e}"

    def _preview_first_entries(self, count: int) -> tuple[list[dict], str, str, str | None, str | None]:
        """Preview the first N entries."""
        if error := self._check_service_loaded():
            return [], error, "", None, None

        results = self.preview_service.preview_first_entries(count)
        text_content, audio_path, image_path = self._extract_media_previews(results)
        return results, f"Showing first {len(results)} entries", text_content, audio_path, image_path

    def _browse_by_index(self, start_index: int, count: int) -> tuple[list[dict], str, str, str | None, str | None]:
        """Browse entries by index range."""
        if error := self._check_service_loaded():
            return [], error, "", None, None

        results = self.preview_service.preview_by_index_range(start_index, count)
        text_content, audio_path, image_path = self._extract_media_previews(results)
        return (
            results,
            f"Showing {len(results)} entries starting from index {start_index}",
            text_content, audio_path, image_path
        )

    def _search_exact_key(self, key: str) -> tuple[list[dict], str, str, str | None, str | None]:
        """Search for an exact key."""
        if error := self._check_service_loaded():
            return [], error, "", None, None

        if not key.strip():
            return [], "Error: Key is required", "", None, None

        result = self.preview_service.search_by_key(key)
        if "error" in result:
            return [], f"Key search failed: {result['error']}", "", None, None
        
        text_content, audio_path, image_path = self._extract_media_previews([result])
        return [result], f"Found exact key: {key}", text_content, audio_path, image_path

    def _search_by_prefix(self, prefix: str, limit: int) -> tuple[list[dict], str, str, str | None, str | None]:
        """Search by key prefix."""
        if error := self._check_service_loaded():
            return [], error, "", None, None

        if not prefix.strip():
            return [], "Error: Prefix is required", "", None, None

        results = self.preview_service.search_by_key_prefix(prefix, limit)
        text_content, audio_path, image_path = self._extract_media_previews(results)
        return results, f"Found {len(results)} keys with prefix '{prefix}'", text_content, audio_path, image_path

    def _search_by_pattern(self, pattern: str, limit: int) -> tuple[list[dict], str, str, str | None, str | None]:
        """Search by key pattern."""
        if error := self._check_service_loaded():
            return [], error, "", None, None

        if not pattern.strip():
            return [], "Error: Pattern is required", "", None, None

        results = self.preview_service.search_by_pattern(pattern, limit)
        text_content, audio_path, image_path = self._extract_media_previews(results)
        return results, f"Found {len(results)} keys matching pattern '{pattern}'", text_content, audio_path, image_path

    def _extract_media_previews(self, results: list[dict]) -> tuple[str, str | None, str | None]:
        """Extract media previews from search results."""
        self._cleanup_temp_files()
        
        text_content = ""
        audio_path = None
        image_path = None
        
        for result in results:
            if "media_previews" in result:
                media_previews = result["media_previews"]
                
                if media_previews.get("text"):
                    text_parts = []
                    for text_field in media_previews["text"]:
                        field_name = text_field.get("field_name", "unknown")
                        content = text_field.get("content", "")
                        text_parts.append(f"[{field_name}]\n{content}\n")
                    text_content = "\n".join(text_parts)
                
                if media_previews.get("audio") and not audio_path:
                    audio_path = media_previews["audio"][0].get("temp_path")
                    if audio_path:
                        self.current_temp_files.append(audio_path)
                
                if media_previews.get("image") and not image_path:
                    image_path = media_previews["image"][0].get("temp_path")
                    if image_path:
                        self.current_temp_files.append(image_path)
        
        return text_content, audio_path, image_path

    def _cleanup_temp_files(self):
        """Cleans up current temporary files."""
        if self.current_temp_files:
            if self.preview_service:
                self.preview_service.cleanup_temp_files(self.current_temp_files)
            else:
                from pathlib import Path
                for path in self.current_temp_files:
                    try:
                        if path:
                            path_obj = Path(path)
                            if path_obj.exists():
                                path_obj.unlink()
                                logger.debug(f"Cleaned up temp file: {path}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup temp file {path}: {e}")
            self.current_temp_files.clear()

    def launch(self, **kwargs):
        """
        Launch the Gradio interface.

        Args:
            **kwargs: Additional arguments for gr.Interface.launch()
        """
        interface = self.create_interface()
        try:
            interface.launch(**kwargs)
        finally:
            self._cleanup_temp_files()
            logger.info("Cleaned up temporary files on interface shutdown")
