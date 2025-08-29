import gradio as gr
from pathlib import Path
from ..core.preview_service import PreviewService
from ..core.logging import get_logger

logger = get_logger(__name__)


class LmdbugInterface:
    """Gradio-based web interface for LMDB data preview."""

    def __init__(self):
        self.preview_service: PreviewService | None = None
        self.current_db_path: str | None = None
        self.current_protobuf_config: dict[str, str] = {}
        self.initial_db_path: str | None = None
        self.initial_protobuf_config: dict[str, str] | None = None
        self.current_temp_files: list[str] = []

    def create_interface(self) -> gr.Blocks:
        with gr.Blocks(title="Lmdbug - LMDB Data Preview Tool", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# Lmdbug - LMDB Data Preview Tool")
            gr.Markdown("Preview LMDB database content with Protobuf deserialization support")

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("## Database Configuration")
                    db_path_input = gr.Textbox(label="LMDB Database Path", placeholder="/path/to/lmdb/database", value=self.initial_db_path)
                    db_load_btn = gr.Button("🔄 Load/Reload Database", variant="primary")

                    gr.Markdown("### Protobuf Configuration (Optional)")
                    protobuf_module_input = gr.Textbox(label="Protobuf Module Path", placeholder="/path/to/your_pb2.py", value=self.initial_protobuf_config.get("module_path") if self.initial_protobuf_config else None)
                    message_class_input = gr.Textbox(label="Message Class Name", placeholder="YourMessageClass", value=self.initial_protobuf_config.get("message_class") if self.initial_protobuf_config else None)
                    protobuf_load_btn = gr.Button("🔌 Load/Reload Protobuf", variant="secondary")

                    gr.Markdown("### Current Configuration")
                    config_status = gr.Textbox(label="Status", value="No configuration loaded", interactive=False, max_lines=3)
                    db_info_display = gr.JSON(label="Database Information", value={})
                    message_type_dropdown = gr.Dropdown(label="Primary Protobuf Message Type", choices=[], value=None, interactive=True)

                    gr.Markdown("### Custom Processors")
                    processor_file_input = gr.Textbox(label="Custom Processor File Path", placeholder="config_examples/custom_processors.py")
                    processor_load_btn = gr.Button("🔌 Load Processors")

                    gr.Markdown("### Field Configuration")
                    with gr.Row():
                        config_file_input = gr.Textbox(label="Config File Path", placeholder="config_examples/example_field_config.json", scale=3)
                        config_load_btn = gr.Button("📁 Load Config", scale=1)
                    field_config_input = gr.Textbox(label="Field Configuration (JSON)", placeholder='{"audio_data": {"processor": "pcm_audio_16khz", "config": {"sample_rate": 16000}}}', lines=5)
                    field_config_btn = gr.Button("🔧 Apply Field Config")

                with gr.Column(scale=2):
                    gr.Markdown("## Data Preview and Search")
                    with gr.Tabs():
                        with gr.TabItem("Browse"):
                            with gr.Row():
                                preview_count = gr.Number(label="Number of entries", value=10, minimum=1, maximum=1000)
                                preview_btn = gr.Button("Preview First Entries")
                            with gr.Row():
                                start_index = gr.Number(label="Start Index", value=0, minimum=0)
                                index_count = gr.Number(label="Count", value=10, minimum=1, maximum=1000)
                                index_btn = gr.Button("Browse by Index")

                        with gr.TabItem("Key Search"):
                            exact_key_input = gr.Textbox(label="Exact Key", placeholder="Enter exact key to search")
                            exact_search_btn = gr.Button("Search Exact Key")
                            prefix_input = gr.Textbox(label="Key Prefix", placeholder="Enter key prefix")
                            prefix_limit = gr.Number(label="Max Results", value=100, minimum=1, maximum=1000)
                            prefix_search_btn = gr.Button("Search by Prefix")
                            pattern_input = gr.Textbox(label="Key Pattern (substring)", placeholder="Enter pattern to search in keys")
                            pattern_limit = gr.Number(label="Max Results", value=100, minimum=1, maximum=1000)
                            pattern_search_btn = gr.Button("Search by Pattern")

                    results_display = gr.JSON(label="Results", value=[], show_label=True)
                    with gr.Row():
                        with gr.Column():
                            text_preview = gr.Textbox(label="Text Content", lines=10, max_lines=20, interactive=False)
                        with gr.Column():
                            audio_preview = gr.Audio(label="Audio Content")
                            image_preview = gr.Image(label="Image Content")

            status_display = gr.Textbox(label="Status", value="Ready to load database", interactive=False)

            # Event handlers
            outputs = [results_display, status_display, text_preview, audio_preview, image_preview]
            db_load_btn.click(self._load_database, [db_path_input], [db_info_display, config_status, status_display])
            protobuf_load_btn.click(self._load_protobuf, [protobuf_module_input, message_class_input], [message_type_dropdown, config_status, status_display])
            message_type_dropdown.change(self._set_message_type, [message_type_dropdown], [status_display])
            processor_load_btn.click(self._load_custom_processors, [processor_file_input], [status_display])
            config_load_btn.click(self._load_config_file, [config_file_input], [field_config_input, status_display])
            field_config_btn.click(self._apply_field_config, [field_config_input], [status_display])
            preview_btn.click(self._preview_first_entries, [preview_count], outputs)
            index_btn.click(self._browse_by_index, [start_index, index_count], outputs)
            exact_search_btn.click(self._search_exact_key, [exact_key_input], outputs)
            prefix_search_btn.click(self._search_by_prefix, [prefix_input, prefix_limit], outputs)
            pattern_search_btn.click(self._search_by_pattern, [pattern_input, pattern_limit], outputs)

        return interface

    def set_initial_config(self, db_path: str | None = None, protobuf_config: dict[str, str] | None = None):
        if db_path:
            self.initial_db_path = db_path
        if protobuf_config:
            self.initial_protobuf_config = protobuf_config

    def _load_database(self, db_path: str) -> tuple[dict, str, str]:
        if not db_path.strip():
            return {}, "Error: Database path is required", "Error: Database path is required"
        if not Path(db_path).exists():
            return {}, f"Error: Database path does not exist: {db_path}", f"Error: Database path does not exist: {db_path}"

        try:
            if self.current_db_path and self.current_db_path != db_path:
                logger.info(f"Switching database from {self.current_db_path} to {db_path}")

            self.preview_service = PreviewService(db_path)
            self.current_db_path = db_path

            if self.current_protobuf_config:
                self._reload_protobuf_internal()

            db_info = self.preview_service.get_database_info()
            status_msg = f"✅ Successfully loaded database: {db_path}"
            if self.current_protobuf_config:
                status_msg += f" (Protobuf: {self.current_protobuf_config.get('message_class', 'N/A')})"

            return db_info, self._get_config_status(), status_msg

        except Exception as e:
            logger.error(f"Failed to load database: {e}")
            return {}, self._get_config_status(), f"Error loading database: {str(e)}"

    def _load_protobuf(self, protobuf_module: str, message_class: str) -> tuple[list[str], str, str]:
        if not self.preview_service:
            return [], self._get_config_status(), "Error: Load database first"

        if not protobuf_module.strip() or not message_class.strip():
            self.current_protobuf_config = {}
            return [], self._get_config_status(), "🧹 Protobuf configuration cleared"

        if not Path(protobuf_module).exists():
            return [], self._get_config_status(), f"Error: Protobuf module not found: {protobuf_module}"

        try:
            new_config = {"module_path": protobuf_module, "message_class": message_class}
            config_changed = self.current_protobuf_config != new_config
            self.current_protobuf_config = new_config

            modules = [{"path": protobuf_module, "message_class": message_class}]
            self.preview_service.load_protobuf_modules(modules, message_class)
            message_types = self.preview_service.get_available_message_types()

            status_msg = f"✅ Successfully loaded protobuf: {message_class}"
            status_msg += " (Configuration updated)" if config_changed else " (Configuration reloaded)"

            return message_types, self._get_config_status(), status_msg

        except Exception as e:
            logger.error(f"Failed to load protobuf: {e}")
            return [], self._get_config_status(), f"Error loading protobuf: {str(e)}"

    def _reload_protobuf_internal(self):
        if not self.current_protobuf_config:
            return
        try:
            modules = [{"path": self.current_protobuf_config["module_path"], "message_class": self.current_protobuf_config["message_class"]}]
            self.preview_service.load_protobuf_modules(modules, self.current_protobuf_config["message_class"])
            logger.debug("Protobuf configuration reloaded after database change")
        except Exception as e:
            logger.warning(f"Failed to reload protobuf after database change: {e}")
            self.current_protobuf_config = {}

    def _get_config_status(self) -> str:
        status_lines = []
        status_lines.append(f"📊 Database: {self.current_db_path}" if self.current_db_path else "🚫 No database loaded")
        
        if self.current_protobuf_config:
            pb_class = self.current_protobuf_config.get("message_class", "Unknown")
            pb_module = Path(self.current_protobuf_config.get("module_path", "")).name
            status_lines.append(f"🔌 Protobuf: {pb_class} ({pb_module})")
        else:
            status_lines.append("🚫 No protobuf configuration")

        if self.preview_service:
            try:
                current_type = getattr(self.preview_service, "current_message_type", None)
                if current_type:
                    status_lines.append(f"🏷️ Active type: {current_type}")
            except AttributeError:
                pass

        return "\n".join(status_lines)

    def _check_service_loaded(self) -> str | None:
        return "Error: No database loaded" if not self.preview_service else None

    def _set_message_type(self, message_type: str) -> str:
        if error := self._check_service_loaded():
            return error
        if message_type:
            self.preview_service.set_message_type(message_type)
            return f"Set primary message type to: {message_type}"
        return "No message type selected"

    def _handle_search(self, operation_func, args, success_msg, validation_field=None, validation_value=None):
        if error := self._check_service_loaded():
            return [], error, "", None, None
        if validation_field and not validation_value.strip():
            return [], f"Error: {validation_field} is required", "", None, None
        try:
            result = operation_func(*args)
            if isinstance(result, dict) and "error" in result:
                return [], f"Search failed: {result['error']}", "", None, None
            results = [result] if isinstance(result, dict) else result
            text, audio, image = self._extract_media_previews(results)
            return results, success_msg.format(count=len(results)), text, audio, image
        except Exception as e:
            return [], f"Search failed: {e}", "", None, None

    def _preview_first_entries(self, count):
        return self._handle_search(self.preview_service.preview_first_entries, (count,), "Showing first {count} entries")

    def _browse_by_index(self, start_index, count):
        return self._handle_search(self.preview_service.preview_by_index_range, (start_index, count), f"Showing {{count}} entries from index {start_index}")

    def _search_exact_key(self, key):
        return self._handle_search(self.preview_service.search_by_key, (key,), f"Found exact key: {key}", "Key", key)

    def _search_by_prefix(self, prefix, limit):
        return self._handle_search(self.preview_service.search_by_key_prefix, (prefix, limit), f"Found {{count}} keys with prefix '{prefix}'", "Prefix", prefix)

    def _search_by_pattern(self, pattern, limit):
        return self._handle_search(self.preview_service.search_by_pattern, (pattern, limit), f"Found {{count}} keys matching pattern '{pattern}'", "Pattern", pattern)

    def _apply_field_config(self, config_json: str) -> str:
        if error := self._check_service_loaded():
            return error
        if not self.current_protobuf_config.get("message_class"):
            return "Error: No protobuf message type loaded"
        try:
            import json
            config = json.loads(config_json) if config_json.strip() else {}
            self.preview_service.set_field_config(self.current_protobuf_config["message_class"], config)
            return f"Applied field config: {config}" if config else "Cleared field configuration"
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON format - {e}"
        except Exception as e:
            return f"Error applying field config: {e}"

    def _load_custom_processors(self, processor_file_path: str) -> str:
        if not processor_file_path.strip():
            return "Error: Processor file path is required"
        if error := self._check_service_loaded():
            return error
        try:
            self.preview_service.load_custom_processors(processor_file_path)
            return f"✅ Successfully loaded custom processors from: {processor_file_path}"
        except Exception as e:
            return f"❌ Error loading processors: {e}"

    def _load_config_file(self, config_file_path: str) -> tuple[str, str]:
        if not config_file_path.strip():
            return "", "Error: Config file path is required"
        if error := self._check_service_loaded():
            return "", error
        try:
            import json
            config = self.preview_service.load_field_config_from_file(config_file_path)
            return json.dumps(config, indent=2, ensure_ascii=False), f"✅ Successfully loaded config from: {config_file_path}"
        except Exception as e:
            return "", f"❌ Error loading config: {e}"

    def _extract_media_previews(self, results: list[dict]) -> tuple[str, str | None, str | None]:
        self._cleanup_temp_files()
        text_content, audio_path, image_path = "", None, None
        
        for result in results:
            if "media_previews" not in result:
                continue
            media = result["media_previews"]
            
            if media.get("text"):
                text_parts = [f"[{t.get('field_name', 'unknown')}]\n{t.get('content', '')}\n" for t in media["text"]]
                text_content = "\n".join(text_parts)
            
            if media.get("audio") and not audio_path:
                audio_path = media["audio"][0].get("temp_path")
                if audio_path:
                    self.current_temp_files.append(audio_path)
            
            if media.get("image") and not image_path:
                image_path = media["image"][0].get("temp_path")
                if image_path:
                    self.current_temp_files.append(image_path)

        return text_content, audio_path, image_path

    def _cleanup_temp_files(self):
        if not self.current_temp_files:
            return
        if self.preview_service:
            self.preview_service.cleanup_temp_files(self.current_temp_files)
        else:
            for path in self.current_temp_files:
                try:
                    if path and Path(path).exists():
                        Path(path).unlink()
                        logger.debug(f"Cleaned up temp file: {path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file {path}: {e}")
        self.current_temp_files.clear()

    def launch(self, **kwargs):
        interface = self.create_interface()
        try:
            interface.launch(**kwargs)
        finally:
            self._cleanup_temp_files()
            logger.info("Cleaned up temporary files on interface shutdown")