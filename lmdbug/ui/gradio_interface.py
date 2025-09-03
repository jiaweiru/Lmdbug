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
        # Create custom theme with better colors
        theme = gr.themes.Glass(
            primary_hue="blue",
            secondary_hue="slate",
            neutral_hue="slate",
            radius_size=gr.themes.sizes.radius_sm,
        ).set(
            button_primary_background_fill="*primary_500",
            button_primary_background_fill_hover="*primary_600",
            button_primary_text_color="white",
            input_background_fill="*neutral_50",
            block_background_fill="*neutral_25",
            panel_background_fill="white",
        )

        # Custom CSS for better styling
        css = """
        .config-input input {
            border-radius: 8px !important;
            border: 2px solid #e5e7eb !important;
            transition: border-color 0.2s ease !important;
        }
        .config-input input:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        }
        .search-input input {
            border-radius: 8px !important;
            border: 2px solid #e5e7eb !important;
        }
        .search-input input:focus {
            border-color: #059669 !important;
            box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.1) !important;
        }
        .entry-selector select {
            border-radius: 8px !important;
        }
        .text-preview textarea {
            border-radius: 8px !important;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
            font-size: 14px !important;
        }
        .gradio-container {
            max-width: 1400px !important;
            margin: 0 auto !important;
        }
        """

        with gr.Blocks(
            title="Lmdbug - LMDB Data Preview Tool", theme=theme, css=css
        ) as interface:
            with gr.Row():
                gr.HTML("""
                <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; margin-bottom: 20px;">
                    <h1 style="color: white; margin: 0; font-size: 2.5em; font-weight: 300;">🗃️ Lmdbug</h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 1.1em;">LMDB Database Preview Tool with Protobuf Support</p>
                </div>
                """)

            with gr.Row():
                with gr.Column(scale=1):
                    gr.HTML(
                        '<h2 style="color: #374151; margin-bottom: 16px; font-size: 1.5em;">⚙️ Configuration</h2>'
                    )
                    db_path_input = gr.Textbox(
                        label="📁 LMDB Database Path",
                        placeholder="/path/to/lmdb/database",
                        value=self.initial_db_path,
                        elem_classes=["config-input"],
                    )

                    with gr.Group():
                        gr.HTML(
                            '<div style="color: #6b7280; font-size: 0.9em; margin-bottom: 8px;">🧠 Protobuf Configuration (Optional)</div>'
                        )
                        with gr.Row():
                            protobuf_module_input = gr.Textbox(
                                label="Module Path",
                                placeholder="/path/to/your_pb2.py",
                                value=self.initial_protobuf_config.get("module_path")
                                if self.initial_protobuf_config is not None
                                else None,
                                scale=2,
                                elem_classes=["config-input"],
                            )
                            message_class_input = gr.Textbox(
                                label="Message Class",
                                placeholder="MessageClass",
                                value=self.initial_protobuf_config.get("message_class")
                                if self.initial_protobuf_config is not None
                                else None,
                                scale=1,
                                elem_classes=["config-input"],
                            )

                    load_btn = gr.Button(
                        "🚀 Load Database", variant="primary", size="lg"
                    )

                    with gr.Group():
                        status_display = gr.HTML(
                            value="<div style='padding: 12px; background: #f0f9ff; border-radius: 8px; border-left: 4px solid #0ea5e9; color: #0c4a6e;'>📊 Ready to load database</div>"
                        )
                        db_info_display = gr.JSON(
                            label="📈 Database Info", value={}, visible=False
                        )

                with gr.Column(scale=2):
                    gr.HTML(
                        '<h2 style="color: #374151; margin-bottom: 16px; font-size: 1.5em;">📊 Data Preview</h2>'
                    )

                    with gr.Group():
                        gr.HTML(
                            '<div style="color: #6b7280; font-size: 0.9em; margin-bottom: 8px;">🔍 Search Database</div>'
                        )
                        with gr.Row():
                            search_input = gr.Textbox(
                                label="Regex Pattern",
                                placeholder="Enter regex pattern",
                                scale=3,
                                elem_classes=["search-input"],
                            )
                            search_btn = gr.Button(
                                "🔍 Search", scale=1, variant="secondary"
                            )

                    with gr.Group():
                        gr.HTML(
                            '<div style="color: #6b7280; font-size: 0.9em; margin-bottom: 8px;">📚 Browse Database</div>'
                        )
                        with gr.Row():
                            entry_count = gr.Number(
                                label="Number of Entries",
                                value=10,
                                minimum=1,
                                maximum=100,
                                scale=1,
                            )
                            browse_btn = gr.Button(
                                "📚 Browse First Entries", scale=2, variant="secondary"
                            )

                    results_display = gr.HTML(
                        label="Results",
                        value="<div style='text-align: center; padding: 40px; color: #6b7280; background: #f9fafb; border-radius: 8px; border: 2px dashed #d1d5db;'>No data loaded. Use 'Browse First Entries' or 'Search' to view database contents.</div>",
                    )

                    with gr.Group():
                        gr.HTML(
                            '<div style="color: #6b7280; font-size: 0.9em; margin-bottom: 8px;">🔎 Entry Preview</div>'
                        )
                        entry_selector = gr.Dropdown(
                            label="Select Entry to Preview",
                            choices=[],
                            value=None,
                            interactive=True,
                            elem_classes=["entry-selector"],
                        )

                    with gr.Row():
                        with gr.Column():
                            with gr.Group():
                                gr.HTML(
                                    '<div style="color: #6b7280; font-size: 0.9em; margin-bottom: 8px;">📝 Text Content</div>'
                                )
                                text_field_selector = gr.Dropdown(
                                    label="Text Field",
                                    choices=[],
                                    value=None,
                                    interactive=True,
                                )
                                text_preview = gr.Textbox(
                                    label="Content",
                                    lines=8,
                                    interactive=False,
                                    placeholder="Select an entry to preview text content.",
                                    elem_classes=["text-preview"],
                                )
                        with gr.Column():
                            with gr.Group():
                                gr.HTML(
                                    '<div style="color: #6b7280; font-size: 0.9em; margin-bottom: 8px;">🎵 Audio Content</div>'
                                )
                                audio_field_selector = gr.Dropdown(
                                    label="Audio Field",
                                    choices=[],
                                    value=None,
                                    interactive=True,
                                )
                                audio_preview = gr.Audio(label="Player")

            # Store results data separately for component updates
            results_data = gr.State([])

            # Entry selector change handler
            entry_selector.change(
                self._update_entry_preview,
                [results_data, entry_selector],
                [
                    text_field_selector,
                    audio_field_selector,
                    text_preview,
                    audio_preview,
                ],
            )

            # Field selector change handlers
            text_field_selector.change(
                self._update_text_preview,
                [results_data, entry_selector, text_field_selector],
                [text_preview],
            )

            audio_field_selector.change(
                self._update_audio_preview,
                [results_data, entry_selector, audio_field_selector],
                [audio_preview],
            )

            # Event handlers
            load_btn.click(
                self._load_database,
                [db_path_input, protobuf_module_input, message_class_input],
                [db_info_display, status_display],
            )

            browse_btn.click(
                self._browse_entries_wrapper,
                [entry_count],
                [
                    results_display,
                    results_data,
                    status_display,
                    entry_selector,
                    text_field_selector,
                    audio_field_selector,
                    text_preview,
                    audio_preview,
                ],
            )

            search_btn.click(
                self._search_data_wrapper,
                [search_input, entry_count],
                [
                    results_display,
                    results_data,
                    status_display,
                    entry_selector,
                    text_field_selector,
                    audio_field_selector,
                    text_preview,
                    audio_preview,
                ],
            )

        return interface

    def set_initial_config(
        self, db_path: str | None = None, protobuf_config: dict[str, str] | None = None
    ):
        if db_path:
            self.initial_db_path = db_path
        if protobuf_config:
            self.initial_protobuf_config = protobuf_config

    def _load_database(
        self, db_path: str, protobuf_module: str, message_class: str
    ) -> tuple[dict, str]:
        if not db_path.strip():
            error_html = "<div style='padding: 12px; background: #fef2f2; border-radius: 8px; border-left: 4px solid #ef4444; color: #dc2626;'>⚠️ Error: Database path is required</div>"
            return {}, error_html

        if not Path(db_path).exists():
            error_html = f"<div style='padding: 12px; background: #fef2f2; border-radius: 8px; border-left: 4px solid #ef4444; color: #dc2626;'>⚠️ Error: Database path does not exist: {db_path}</div>"
            return {}, error_html

        try:
            # Close existing service
            if self.data_service:
                self.data_service.close()

            # Use configuration for processor paths if available
            processor_paths = None
            if self.config:
                processor_paths = self.config.processor_paths

            self.data_service = DataService(db_path, processor_paths=processor_paths)
            self.data_service.open()

            # Load protobuf if provided
            if protobuf_module.strip() and message_class.strip():
                if not Path(protobuf_module).exists():
                    return {}, f"Error: Protobuf module not found: {protobuf_module}"
                self.data_service.load_protobuf_module(protobuf_module, message_class)

            db_info = self.data_service.get_database_info()
            db_name = Path(db_path).name
            entries_count = db_info.get("entries", "unknown")

            success_html = f"""
            <div style='padding: 12px; background: #f0fdf4; border-radius: 8px; border-left: 4px solid #22c55e; color: #15803d;'>
                ✅ Database loaded successfully<br>
                <strong>File:</strong> {db_name}<br>
                <strong>Entries:</strong> {entries_count}
            """

            if protobuf_module.strip():
                success_html += f"<br><strong>Protobuf:</strong> {message_class}"

            success_html += "</div>"

            logger.info(
                f"Database successfully loaded: {db_name}, entries: {entries_count}"
            )
            return db_info, success_html

        except Exception as e:
            logger.warning(
                f"Failed to load database: {e}"
            )  # User input error, not system error
            error_html = f"<div style='padding: 12px; background: #fef2f2; border-radius: 8px; border-left: 4px solid #ef4444; color: #dc2626;'>⚠️ Error: {str(e)}</div>"
            return {}, error_html

    def _search_data(
        self, query: str, limit: int
    ) -> tuple[str, str, list[tuple[str, str]], list[str], list[str], str, str | None]:
        if not self.data_service:
            return (
                self._format_no_data_html("No database loaded"),
                "Error: No database loaded",
                [],
                [],
                [],
                "",
                None,
            )

        if not query.strip():
            return (
                self._format_no_data_html("Search query is required"),
                "Error: Search query is required",
                [],
                [],
                [],
                "",
                None,
            )

        try:
            results = self.data_service.search_keys(query, limit)
            entry_options = self._get_entry_options(results)

            # Get field options and preview from first entry if available
            text_fields = []
            audio_fields = []
            text_preview = ""
            audio_preview = None

            if results:
                first_entry = results[0]
                text_fields = self._get_available_text_fields(first_entry)
                audio_fields = self._get_available_audio_fields(first_entry)
                text_preview = self._extract_text_preview(
                    first_entry, text_fields[0] if text_fields else None
                )
                audio_preview = self._extract_audio_preview(
                    first_entry, audio_fields[0] if audio_fields else None
                )

            return (
                self._format_results_html(results),
                f"Found {len(results)} matches",
                entry_options,
                text_fields,
                audio_fields,
                text_preview,
                audio_preview,
            )
        except Exception as e:
            logger.warning(f"Search failed: {e}")  # User input error, not system error
            return (
                self._format_no_data_html(f"Error: {str(e)}"),
                f"Error: {str(e)}",
                [],
                [],
                [],
                "",
                None,
            )

    def _browse_entries(
        self, count: int
    ) -> tuple[str, str, list[tuple[str, str]], list[str], list[str], str, str | None]:
        if not self.data_service:
            return (
                self._format_no_data_html("No database loaded"),
                "Error: No database loaded",
                [],
                [],
                [],
                "",
                None,
            )

        try:
            results = self.data_service.get_first_entries(count)
            entry_options = self._get_entry_options(results)

            # Get field options and preview from first entry if available
            text_fields = []
            audio_fields = []
            text_preview = ""
            audio_preview = None

            if results:
                first_entry = results[0]
                text_fields = self._get_available_text_fields(first_entry)
                audio_fields = self._get_available_audio_fields(first_entry)
                text_preview = self._extract_text_preview(
                    first_entry, text_fields[0] if text_fields else None
                )
                audio_preview = self._extract_audio_preview(
                    first_entry, audio_fields[0] if audio_fields else None
                )

            return (
                self._format_results_html(results),
                f"Showing first {len(results)} entries",
                entry_options,
                text_fields,
                audio_fields,
                text_preview,
                audio_preview,
            )
        except Exception as e:
            logger.warning(
                f"Browse failed: {e}"
            )  # User operation error, not system error
            return (
                self._format_no_data_html(f"Error: {str(e)}"),
                f"Error: {str(e)}",
                [],
                [],
                [],
                "",
                None,
            )

    def _get_entry_options(self, results: list[dict]) -> list[tuple[str, str]]:
        """Get entry options for selector (display_name, key)."""
        options = []
        for i, result in enumerate(results):
            key = result.get("key", f"entry_{i}")
            # Avoid too long key
            display_name = (
                f"{i + 1}: {key}" if len(key) < 50 else f"{i + 1}: {key[:47]}..."
            )
            options.append((display_name, key))
        return options

    def _get_available_text_fields(self, entry: dict) -> list[str]:
        """Get all available text field names from single entry."""
        field_names = set()
        if "media_preview" in entry and "text" in entry["media_preview"]:
            for text_item in entry["media_preview"]["text"]:
                field_name = text_item.get("field_name", "text")
                field_names.add(field_name)
        return sorted(list(field_names))

    def _extract_text_preview(self, entry: dict, selected_field: str = None) -> str:
        """Extract text content from single entry for preview."""
        if (
            not entry
            or "media_preview" not in entry
            or "text" not in entry["media_preview"]
        ):
            return ""

        for text_item in entry["media_preview"]["text"]:
            if "content" in text_item:
                field_name = text_item.get("field_name", "text")
                # If field is selected, only show that field
                if selected_field and field_name != selected_field:
                    continue
                return text_item[
                    "content"
                ]  # Return content directly, no field label needed

        return ""

    def _get_available_audio_fields(self, entry: dict) -> list[str]:
        """Get all available audio field names from single entry."""
        field_names = set()
        if "media_preview" in entry and "audio" in entry["media_preview"]:
            for audio_item in entry["media_preview"]["audio"]:
                field_name = audio_item.get("field_name", "audio")
                field_names.add(field_name)
        return sorted(list(field_names))

    def _extract_audio_preview(
        self, entry: dict, selected_field: str = None
    ) -> str | None:
        """Extract audio file path from single entry for preview."""
        if (
            not entry
            or "media_preview" not in entry
            or "audio" not in entry["media_preview"]
        ):
            return None

        for audio_item in entry["media_preview"]["audio"]:
            field_name = audio_item.get("field_name", "audio")
            # If field is selected, only show that field
            if selected_field and field_name != selected_field:
                continue
            if "temp_path" in audio_item:
                return audio_item["temp_path"]
        return None

    def _get_entry_by_key(self, results: list[dict], entry_key: str) -> dict | None:
        """Get entry by key from results."""
        for result in results:
            if result.get("key") == entry_key:
                return result
        return None

    def _update_entry_preview(
        self, results: list[dict], selected_entry_key: str
    ) -> tuple[gr.update, gr.update, str, str | None]:
        """Update preview when entry selection changes."""
        if not results or not selected_entry_key:
            return (
                gr.update(choices=[], value=None, interactive=False),
                gr.update(choices=[], value=None, interactive=False),
                "",
                None,
            )

        entry = self._get_entry_by_key(results, selected_entry_key)
        if not entry:
            return (
                gr.update(choices=[], value=None, interactive=False),
                gr.update(choices=[], value=None, interactive=False),
                "",
                None,
            )

        # Check if protobuf is available
        if not self.data_service:
            has_protobuf = False
        else:
            db_info = self.data_service.get_database_info()
            has_protobuf = db_info.get("has_protobuf", False)

        if not has_protobuf:
            return (
                gr.update(choices=[], value=None, interactive=False),
                gr.update(choices=[], value=None, interactive=False),
                "",
                None,
            )

        text_fields = self._get_available_text_fields(entry)
        audio_fields = self._get_available_audio_fields(entry)

        # Get preview with first available field
        text_preview = self._extract_text_preview(
            entry, text_fields[0] if text_fields else None
        )
        audio_preview = self._extract_audio_preview(
            entry, audio_fields[0] if audio_fields else None
        )

        return (
            gr.update(
                choices=text_fields,
                value=text_fields[0] if text_fields else None,
                interactive=True,
            ),
            gr.update(
                choices=audio_fields,
                value=audio_fields[0] if audio_fields else None,
                interactive=True,
            ),
            text_preview,
            audio_preview,
        )

    def _update_text_preview(
        self, results: list[dict], selected_entry_key: str, selected_field: str
    ) -> str:
        """Update text preview based on selected entry and field."""
        if not results or not selected_entry_key or not selected_field:
            return ""

        # Check if protobuf is available
        if not self.data_service:
            return ""

        db_info = self.data_service.get_database_info()
        has_protobuf = db_info.get("has_protobuf", False)

        if not has_protobuf:
            return ""

        entry = self._get_entry_by_key(results, selected_entry_key)
        if not entry:
            return ""

        return self._extract_text_preview(entry, selected_field)

    def _update_audio_preview(
        self, results: list[dict], selected_entry_key: str, selected_field: str
    ) -> str | None:
        """Update audio preview based on selected entry and field."""
        if not results or not selected_entry_key or not selected_field:
            return None

        # Check if protobuf is available
        if not self.data_service:
            return None

        db_info = self.data_service.get_database_info()
        has_protobuf = db_info.get("has_protobuf", False)

        if not has_protobuf:
            return None

        entry = self._get_entry_by_key(results, selected_entry_key)
        if not entry:
            return None

        return self._extract_audio_preview(entry, selected_field)

    def _format_no_data_html(self, message: str) -> str:
        """Format a no-data message as HTML."""
        return f"""
        <div style='text-align: center; padding: 40px; color: #ef4444; background: #fef2f2; border-radius: 8px; border: 2px dashed #fecaca;'>
            <div style='font-size: 1.2em; margin-bottom: 8px;'>⚠️ {message}</div>
        </div>
        """

    def _format_results_html(self, results: list[dict]) -> str:
        """Format results as HTML table."""
        if not results:
            return self._format_no_data_html("No results found")

        html = """
        <div style='background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
            <div style='background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; padding: 12px 16px; font-weight: 600;'>
                📊 Database Results ({} entries)
            </div>
            <div style='max-height: 400px; overflow-y: auto;'>
        """.format(len(results))

        for i, result in enumerate(results):
            key = result.get("key", "Unknown")
            # Truncate long keys
            display_key = key if len(key) < 60 else key[:57] + "..."

            # Determine if protobuf data exists
            has_protobuf = "protobuf" in result
            has_error = "protobuf_error" in result

            bg_color = "#f8fafc" if i % 2 == 0 else "white"

            html += f"""
                <div style='padding: 12px 16px; background: {bg_color}; border-bottom: 1px solid #e5e7eb;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='font-weight: 600; color: #1f2937; margin-bottom: 4px;'>#{i + 1}: {display_key}</div>
            """

            if has_protobuf:
                html += "<div style='color: #059669; font-size: 0.875em;'>✓ Protobuf decoded</div>"
            elif has_error:
                error_msg = result.get("protobuf_error", "Unknown error")
                html += f"<div style='color: #dc2626; font-size: 0.875em;'>✗ Protobuf error: {error_msg[:50]}...</div>"
            else:
                html += (
                    "<div style='color: #6b7280; font-size: 0.875em;'>Raw bytes</div>"
                )

            html += """
                        </div>
                        <div style='color: #6b7280; font-size: 0.875em;'>
                            {} bytes
                        </div>
                    </div>
                </div>
            """.format(len(str(result).encode("utf-8")))

        html += """
            </div>
        </div>
        """

        return html

    def _search_data_wrapper(
        self, query: str, limit: int
    ) -> tuple[str, list, str, gr.update, gr.update, gr.update, str, str | None]:
        """Wrapper for search that returns both HTML and raw data."""
        if not self.data_service:
            empty_html = self._format_no_data_html("No database loaded")
            return (
                empty_html,
                [],
                "Error: No database loaded",
                gr.update(choices=[], value=None),
                gr.update(choices=[], value=None, interactive=False),
                gr.update(choices=[], value=None, interactive=False),
                "",
                None,
            )

        if not query.strip():
            empty_html = self._format_no_data_html("Search query is required")
            return (
                empty_html,
                [],
                "Error: Search query is required",
                gr.update(choices=[], value=None),
                gr.update(choices=[], value=None, interactive=False),
                gr.update(choices=[], value=None, interactive=False),
                "",
                None,
            )

        try:
            results = self.data_service.search_keys(query, limit)
            entry_options = self._get_entry_options(results)

            # Check if protobuf is available
            db_info = self.data_service.get_database_info()
            has_protobuf = db_info.get("has_protobuf", False)

            # Get field options and preview from first entry if available
            text_fields = []
            audio_fields = []
            text_preview = ""
            audio_preview = None

            if results and has_protobuf:
                first_entry = results[0]
                text_fields = self._get_available_text_fields(first_entry)
                audio_fields = self._get_available_audio_fields(first_entry)
                text_preview = self._extract_text_preview(
                    first_entry, text_fields[0] if text_fields else None
                )
                audio_preview = self._extract_audio_preview(
                    first_entry, audio_fields[0] if audio_fields else None
                )

            return (
                self._format_results_html(results),
                results,  # Raw data for other components
                f"Found {len(results)} matches",
                gr.update(choices=entry_options, value=None),
                gr.update(
                    choices=text_fields,
                    value=text_fields[0] if text_fields else None,
                    interactive=has_protobuf,
                ),
                gr.update(
                    choices=audio_fields,
                    value=audio_fields[0] if audio_fields else None,
                    interactive=has_protobuf,
                ),
                text_preview,
                audio_preview,
            )
        except Exception as e:
            logger.warning(f"Search failed: {e}")
            empty_html = self._format_no_data_html(f"Error: {str(e)}")
            return (
                empty_html,
                [],
                f"Error: {str(e)}",
                gr.update(choices=[], value=None),
                gr.update(choices=[], value=None, interactive=False),
                gr.update(choices=[], value=None, interactive=False),
                "",
                None,
            )

    def _browse_entries_wrapper(
        self, count: int
    ) -> tuple[str, list, str, gr.update, gr.update, gr.update, str, str | None]:
        """Wrapper for browse that returns both HTML and raw data."""
        if not self.data_service:
            empty_html = self._format_no_data_html("No database loaded")
            return (
                empty_html,
                [],
                "Error: No database loaded",
                gr.update(choices=[], value=None),
                gr.update(choices=[], value=None, interactive=False),
                gr.update(choices=[], value=None, interactive=False),
                "",
                None,
            )

        try:
            results = self.data_service.get_first_entries(count)
            entry_options = self._get_entry_options(results)

            # Check if protobuf is available
            db_info = self.data_service.get_database_info()
            has_protobuf = db_info.get("has_protobuf", False)

            # Get field options and preview from first entry if available
            text_fields = []
            audio_fields = []
            text_preview = ""
            audio_preview = None

            if results and has_protobuf:
                first_entry = results[0]
                text_fields = self._get_available_text_fields(first_entry)
                audio_fields = self._get_available_audio_fields(first_entry)
                text_preview = self._extract_text_preview(
                    first_entry, text_fields[0] if text_fields else None
                )
                audio_preview = self._extract_audio_preview(
                    first_entry, audio_fields[0] if audio_fields else None
                )

            return (
                self._format_results_html(results),
                results,  # Raw data for other components
                f"Showing first {len(results)} entries",
                gr.update(choices=entry_options, value=None),
                gr.update(
                    choices=text_fields,
                    value=text_fields[0] if text_fields else None,
                    interactive=has_protobuf,
                ),
                gr.update(
                    choices=audio_fields,
                    value=audio_fields[0] if audio_fields else None,
                    interactive=has_protobuf,
                ),
                text_preview,
                audio_preview,
            )
        except Exception as e:
            logger.warning(f"Browse failed: {e}")
            empty_html = self._format_no_data_html(f"Error: {str(e)}")
            return (
                empty_html,
                [],
                f"Error: {str(e)}",
                gr.update(choices=[], value=None),
                gr.update(choices=[], value=None, interactive=False),
                gr.update(choices=[], value=None, interactive=False),
                "",
                None,
            )

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
