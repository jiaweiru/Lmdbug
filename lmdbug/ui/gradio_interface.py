"""
Simplified Gradio interface for LMDB data preview.
"""

import gradio as gr
from dataclasses import dataclass, field
from pathlib import Path
from weakref import WeakSet
from ..core.data_service import DataService
from ..core.logging import get_logger
from ..core.config import LmdbugConfig

logger = get_logger()


@dataclass
class InterfaceSession:
    service: DataService | None = None
    results: list[dict] = field(default_factory=list)


class LmdbugInterface:
    """Simple Gradio-based web interface for LMDB data preview."""

    def __init__(self, config: LmdbugConfig | None = None):
        self.config = config
        self.initial_db_path: str | None = None
        self.initial_protobuf_config: dict[str, str] | None = None
        self.initial_processor_paths: list[str] | None = None
        self._active_services: WeakSet = WeakSet()

    def _ensure_session(self, session: InterfaceSession | None) -> InterfaceSession:
        """Return a session object, creating one if needed."""
        if session is None:
            session = InterfaceSession()
        return session

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
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

        :root {
            --ink-900: #0f172a;
            --ink-700: #334155;
            --ink-500: #64748b;
            --brand-600: #0ea5a4;
            --brand-500: #14b8a6;
            --brand-200: #99f6e4;
            --accent-500: #f97316;
            --card: #ffffff;
            --card-2: #f8fafc;
            --line: #e2e8f0;
        }

        body, .gradio-container {
            font-family: 'Space Grotesk', 'Segoe UI', Tahoma, sans-serif !important;
            color: var(--ink-900);
        }

        .gradio-container {
            max-width: 1400px !important;
            margin: 0 auto !important;
            background:
                radial-gradient(1200px 600px at 10% -10%, #e0f2fe 0%, transparent 60%),
                radial-gradient(1000px 700px at 110% 0%, #fef3c7 0%, transparent 55%),
                linear-gradient(180deg, #f8fafc 0%, #ffffff 60%);
            border-radius: 24px;
            padding: 24px;
        }

        .app-hero {
            background: linear-gradient(135deg, #0ea5a4 0%, #22d3ee 60%, #f97316 120%);
            border-radius: 18px;
            padding: 22px 26px;
            box-shadow: 0 16px 40px rgba(15, 23, 42, 0.12);
        }

        .app-hero h1 {
            font-size: 2.4rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            margin: 0 0 6px 0;
            color: #0b1220;
        }

        .app-hero p {
            margin: 0;
            color: rgba(15, 23, 42, 0.7);
            font-size: 1.02rem;
        }

        .section-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--ink-900);
            margin-bottom: 10px;
        }

        .section-subtitle {
            color: var(--ink-500);
            font-size: 0.92rem;
            margin-bottom: 8px;
        }

        .gr-group, .gr-box {
            background: var(--card) !important;
            border: 1px solid var(--line) !important;
            border-radius: 16px !important;
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06) !important;
        }

        .config-input input, .search-input input, .entry-selector select {
            border-radius: 10px !important;
            border: 1px solid #cbd5e1 !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        }

        .config-input input:focus, .search-input input:focus {
            border-color: var(--brand-600) !important;
            box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.18) !important;
        }

        .text-preview textarea {
            border-radius: 10px !important;
            font-family: 'JetBrains Mono', 'Consolas', monospace !important;
            font-size: 13px !important;
        }

        .gr-button {
            border-radius: 10px !important;
            font-weight: 600 !important;
            letter-spacing: 0.01em;
            border: 1px solid transparent !important;
        }

        .gr-button.primary {
            background: linear-gradient(135deg, #0ea5a4, #22d3ee) !important;
            color: #041b1e !important;
            box-shadow: 0 8px 18px rgba(14, 165, 164, 0.25) !important;
        }

        .gr-button.secondary {
            background: #f1f5f9 !important;
            color: var(--ink-700) !important;
            border-color: #e2e8f0 !important;
        }

        .results-card {
            border-radius: 14px !important;
            background: var(--card-2) !important;
            border: 1px dashed #cbd5e1 !important;
        }

        @media (max-width: 900px) {
            .gradio-container {
                padding: 14px;
                border-radius: 18px;
            }
            .app-hero {
                padding: 18px 18px;
            }
            .app-hero h1 {
                font-size: 2rem;
            }
        }
        """

        with gr.Blocks(
            title="Lmdbug - LMDB Data Preview Tool", theme=theme, css=css
        ) as interface:
            with gr.Row():
                gr.HTML("""
                <div class="app-hero">
                    <h1>🗃️ Lmdbug</h1>
                    <p>LMDB Database Preview Tool with Protobuf Support</p>
                </div>
                """)

            with gr.Row():
                with gr.Column(scale=1):
                    gr.HTML('<div class="section-title">⚙️ Configuration</div>')
                    db_path_input = gr.Textbox(
                        label="📁 LMDB Database Path",
                        placeholder="/path/to/lmdb/database",
                        value=self.initial_db_path,
                        elem_classes=["config-input"],
                    )

                    with gr.Group():
                        gr.HTML(
                            '<div class="section-subtitle">🧠 Protobuf Configuration (Optional)</div>'
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

                    with gr.Group():
                        gr.HTML(
                            '<div class="section-subtitle">⚙️ Processor Configuration (Optional)</div>'
                        )
                        processor_paths_input = gr.Textbox(
                            label="Processor File Paths",
                            placeholder="/path/to/custom_processors.py (one per line)",
                            value="\n".join(self.initial_processor_paths)
                            if self.initial_processor_paths
                            else None,
                            lines=3,
                            elem_classes=["config-input"],
                        )

                    load_btn = gr.Button(
                        "🚀 Load Database", variant="primary", size="lg"
                    )

                    with gr.Group():
                        status_display = gr.HTML(
                            value="<div style='padding: 12px; background: #ecfeff; border-radius: 10px; border-left: 4px solid #14b8a6; color: #0f172a;'>📊 Ready to load database</div>"
                        )
                        db_info_display = gr.JSON(
                            label="📈 Database Info", value={}, visible=False
                        )

                with gr.Column(scale=2):
                    gr.HTML('<div class="section-title">📊 Data Preview</div>')

                    with gr.Group():
                        gr.HTML(
                            '<div class="section-subtitle">🔍 Search Database</div>'
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
                            '<div class="section-subtitle">📚 Browse Database</div>'
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
                            random_btn = gr.Button(
                                "Browse Random Entries", scale=2, variant="secondary"
                            )

                    results_display = gr.HTML(
                        label="Results",
                        value="<div class='results-card' style='text-align: center; padding: 40px; color: #64748b;'>No data loaded. Use 'Browse First Entries', 'Browse Random Entries', or 'Search' to view database contents.</div>",
                    )

                    with gr.Group():
                        gr.HTML('<div class="section-subtitle">🔎 Entry Preview</div>')
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
                                    '<div class="section-subtitle">📝 Text Content</div>'
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
                                    '<div class="section-subtitle">🎵 Audio Content</div>'
                                )
                                audio_field_selector = gr.Dropdown(
                                    label="Audio Field",
                                    choices=[],
                                    value=None,
                                    interactive=True,
                                )
                                audio_preview = gr.Audio(label="Player")

            # Store session-specific data service and results
            session_state = gr.State(None)

            # Entry selector change handler
            entry_selector.change(
                self._update_entry_preview,
                [session_state, entry_selector],
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
                [session_state, entry_selector, text_field_selector],
                [text_preview],
            )

            audio_field_selector.change(
                self._update_audio_preview,
                [session_state, entry_selector, audio_field_selector],
                [audio_preview],
            )

            # Event handlers
            load_btn.click(
                self._load_database,
                [
                    db_path_input,
                    protobuf_module_input,
                    message_class_input,
                    processor_paths_input,
                    session_state,
                ],
                [
                    db_info_display,
                    status_display,
                    entry_selector,
                    text_field_selector,
                    audio_field_selector,
                    text_preview,
                    audio_preview,
                    session_state,
                ],
            )

            browse_btn.click(
                self._browse_entries_wrapper,
                [entry_count, session_state],
                [
                    results_display,
                    status_display,
                    entry_selector,
                    text_field_selector,
                    audio_field_selector,
                    text_preview,
                    audio_preview,
                    session_state,
                ],
            )

            random_btn.click(
                self._browse_random_entries_wrapper,
                [entry_count, session_state],
                [
                    results_display,
                    status_display,
                    entry_selector,
                    text_field_selector,
                    audio_field_selector,
                    text_preview,
                    audio_preview,
                    session_state,
                ],
            )

            search_btn.click(
                self._search_data_wrapper,
                [search_input, entry_count, session_state],
                [
                    results_display,
                    status_display,
                    entry_selector,
                    text_field_selector,
                    audio_field_selector,
                    text_preview,
                    audio_preview,
                    session_state,
                ],
            )

        return interface

    def set_initial_config(
        self,
        db_path: str | None = None,
        protobuf_config: dict[str, str] | None = None,
        processor_paths: list[str] | None = None,
    ):
        if db_path:
            self.initial_db_path = db_path
        if protobuf_config:
            self.initial_protobuf_config = protobuf_config
        if processor_paths:
            self.initial_processor_paths = processor_paths

    def _load_database(
        self,
        db_path: str,
        protobuf_module: str,
        message_class: str,
        processor_paths: str,
        session: InterfaceSession | None,
    ) -> tuple[
        dict,
        str,
        gr.update,
        gr.update,
        gr.update,
        str,
        str | None,
        InterfaceSession,
    ]:
        session_obj = self._ensure_session(session)
        clear_entry_update = self._safe_dropdown_update([], None, interactive=False)
        clear_text_update = self._safe_dropdown_update([], None, interactive=False)
        clear_audio_update = self._safe_dropdown_update([], None, interactive=False)
        clear_text_preview = ""
        clear_audio_preview = None

        db_path_value = db_path.strip()
        if not db_path_value:
            error_html = "<div style='padding: 12px; background: #fef2f2; border-radius: 8px; border-left: 4px solid #ef4444; color: #dc2626;'>⚠️ Error: Database path is required</div>"
            return (
                {},
                error_html,
                clear_entry_update,
                clear_text_update,
                clear_audio_update,
                clear_text_preview,
                clear_audio_preview,
                session_obj,
            )

        if not Path(db_path_value).exists():
            error_html = f"<div style='padding: 12px; background: #fef2f2; border-radius: 8px; border-left: 4px solid #ef4444; color: #dc2626;'>⚠️ Error: Database path does not exist: {db_path_value}</div>"
            return (
                {},
                error_html,
                clear_entry_update,
                clear_text_update,
                clear_audio_update,
                clear_text_preview,
                clear_audio_preview,
                session_obj,
            )

        parsed_processor_paths = None
        processor_paths_value = processor_paths or ""
        new_service: DataService | None = None

        try:
            if processor_paths_value.strip():
                parsed_processor_paths = [
                    path.strip()
                    for path in processor_paths_value.strip().split("\n")
                    if path.strip()
                ]
                for path in parsed_processor_paths:
                    if not Path(path).exists():
                        error_html = f"<div style='padding: 12px; background: #fef2f2; border-radius: 8px; border-left: 4px solid #ef4444; color: #dc2626;'>⚠️ Error: Processor file does not exist: {path}</div>"
                        return (
                            {},
                            error_html,
                            clear_entry_update,
                            clear_text_update,
                            clear_audio_update,
                            clear_text_preview,
                            clear_audio_preview,
                            session_obj,
                        )

            processor_paths_to_use = parsed_processor_paths
            if not processor_paths_to_use and self.config:
                processor_paths_to_use = self.config.processor_paths

            new_service = DataService(
                db_path_value, processor_paths=processor_paths_to_use
            )
            new_service.open()

            if processor_paths_to_use is not None:
                new_service.reload_processors()

            protobuf_module_value = protobuf_module.strip()
            message_class_value = message_class.strip()

            if protobuf_module_value and message_class_value:
                if not Path(protobuf_module_value).exists():
                    raise FileNotFoundError(
                        f"Protobuf module not found: {protobuf_module_value}"
                    )
                new_service.load_protobuf_module(
                    protobuf_module_value, message_class_value
                )

            db_info = new_service.get_database_info()
            db_name = Path(db_path_value).name
            entries_count = db_info.get("entries", "unknown")

            success_html = f"""
            <div style='padding: 12px; background: #f0fdf4; border-radius: 8px; border-left: 4px solid #22c55e; color: #15803d;'>
                ✅ Database loaded successfully<br>
                <strong>File:</strong> {db_name}<br>
                <strong>Entries:</strong> {entries_count}
            """

            if protobuf_module_value:
                success_html += f"<br><strong>Protobuf:</strong> {message_class_value}"

            success_html += "</div>"

            if session_obj.service and session_obj.service is not new_service:
                self._active_services.discard(session_obj.service)
                session_obj.service.close()

            session_obj.service = new_service
            session_obj.results = []
            self._active_services.add(new_service)

            logger.info(
                f"Database successfully loaded: {db_name}, entries: {entries_count}"
            )
            return (
                db_info,
                success_html,
                clear_entry_update,
                clear_text_update,
                clear_audio_update,
                clear_text_preview,
                clear_audio_preview,
                session_obj,
            )

        except Exception as e:
            logger.warning(
                f"Failed to load database: {e}"
            )  # User input error, not system error
            if new_service is not None:
                try:
                    new_service.close()
                except Exception:
                    logger.debug("Failed to close partially initialized service")
            error_html = f"<div style='padding: 12px; background: #fef2f2; border-radius: 8px; border-left: 4px solid #ef4444; color: #dc2626;'>⚠️ Error: {str(e)}</div>"
            return (
                {},
                error_html,
                clear_entry_update,
                clear_text_update,
                clear_audio_update,
                clear_text_preview,
                clear_audio_preview,
                session_obj,
            )

    def _search_data(
        self, query: str, limit: int, session: InterfaceSession | None
    ) -> tuple[
        str,
        str,
        list[tuple[str, str]],
        list[str],
        list[str],
        str,
        str | None,
        bool,
        InterfaceSession,
    ]:
        session_obj = self._ensure_session(session)

        service = session_obj.service
        if not service:
            session_obj.results = []
            return (
                self._format_no_data_html("No database loaded"),
                "Error: No database loaded",
                [],
                [],
                [],
                "",
                None,
                False,
                session_obj,
            )

        if not query.strip():
            session_obj.results = []
            return (
                self._format_no_data_html("Search query is required"),
                "Error: Search query is required",
                [],
                [],
                [],
                "",
                None,
                False,
                session_obj,
            )

        try:
            results = service.search_keys(query, limit)
            entry_options = self._get_entry_options(results)

            # Get field options and preview from first entry if available
            text_fields = []
            audio_fields = []
            text_preview = ""
            audio_preview = None
            has_protobuf = service.get_database_info().get("has_protobuf", False)

            session_obj.results = results

            return (
                self._format_results_html(results),
                f"Found {len(results)} matches",
                entry_options,
                text_fields,
                audio_fields,
                text_preview,
                audio_preview,
                has_protobuf,
                session_obj,
            )
        except Exception as e:
            logger.warning(f"Search failed: {e}")  # User input error, not system error
            session_obj.results = []
            return (
                self._format_no_data_html(f"Error: {str(e)}"),
                f"Error: {str(e)}",
                [],
                [],
                [],
                "",
                None,
                False,
                session_obj,
            )

    def _browse_entries(
        self, count: int, session: InterfaceSession | None
    ) -> tuple[
        str,
        str,
        list[tuple[str, str]],
        list[str],
        list[str],
        str,
        str | None,
        bool,
        InterfaceSession,
    ]:
        session_obj = self._ensure_session(session)

        service = session_obj.service
        if not service:
            session_obj.results = []
            return (
                self._format_no_data_html("No database loaded"),
                "Error: No database loaded",
                [],
                [],
                [],
                "",
                None,
                False,
                session_obj,
            )

        try:
            results = service.get_first_entries(count)
            entry_options = self._get_entry_options(results)

            # Get field options and preview from first entry if available
            text_fields = []
            audio_fields = []
            text_preview = ""
            audio_preview = None
            has_protobuf = service.get_database_info().get("has_protobuf", False)

            session_obj.results = results

            return (
                self._format_results_html(results),
                f"Showing first {len(results)} entries",
                entry_options,
                text_fields,
                audio_fields,
                text_preview,
                audio_preview,
                has_protobuf,
                session_obj,
            )
        except Exception as e:
            logger.warning(
                f"Browse failed: {e}"
            )  # User operation error, not system error
            session_obj.results = []
            return (
                self._format_no_data_html(f"Error: {str(e)}"),
                f"Error: {str(e)}",
                [],
                [],
                [],
                "",
                None,
                False,
                session_obj,
            )

    def _browse_random_entries(
        self, count: int, session: InterfaceSession | None
    ) -> tuple[
        str,
        str,
        list[tuple[str, str]],
        list[str],
        list[str],
        str,
        str | None,
        bool,
        InterfaceSession,
    ]:
        session_obj = self._ensure_session(session)

        service = session_obj.service
        if not service:
            session_obj.results = []
            return (
                self._format_no_data_html("No database loaded"),
                "Error: No database loaded",
                [],
                [],
                [],
                "",
                None,
                False,
                session_obj,
            )

        try:
            results = service.get_random_entries(count)
            entry_options = self._get_entry_options(results)

            # Get field options and preview from first entry if available
            text_fields = []
            audio_fields = []
            text_preview = ""
            audio_preview = None
            has_protobuf = service.get_database_info().get("has_protobuf", False)

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

            session_obj.results = results

            return (
                self._format_results_html(results),
                f"Showing {len(results)} random entries",
                entry_options,
                text_fields,
                audio_fields,
                text_preview,
                audio_preview,
                has_protobuf,
                session_obj,
            )
        except Exception as e:
            logger.warning(
                f"Random browse failed: {e}"
            )  # User operation error, not system error
            session_obj.results = []
            return (
                self._format_no_data_html(f"Error: {str(e)}"),
                f"Error: {str(e)}",
                [],
                [],
                [],
                "",
                None,
                False,
                session_obj,
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

    def _safe_dropdown_update(
        self,
        choices: list,
        value: str | None,
        interactive: bool,
    ) -> gr.update:
        """Return a dropdown update with a value guaranteed to be in choices."""
        normalized_choices = [choice for choice in choices if choice is not None]
        allowed_values = set()
        for choice in normalized_choices:
            if isinstance(choice, tuple) and len(choice) == 2:
                allowed_values.add(choice[1])
            else:
                allowed_values.add(choice)
        safe_value = value if value is None or value in allowed_values else None
        return gr.update(
            choices=normalized_choices,
            value=safe_value,
            interactive=interactive and bool(normalized_choices),
        )

    def _get_available_text_fields(self, entry: dict) -> list[str]:
        """Get all available text field names from single entry."""
        field_names = set()
        if "media_preview" in entry and "text" in entry["media_preview"]:
            for text_item in entry["media_preview"]["text"]:
                field_name = text_item.get("field_name", "text")
                if not field_name:
                    field_name = "text"
                field_names.add(field_name)
        return sorted(list(field_names), key=lambda x: x != "text")

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
                if not field_name:
                    field_name = "audio"
                field_names.add(field_name)
        return sorted(list(field_names), key=lambda x: x != "audio")

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
        self, session: InterfaceSession | None, selected_entry_key: str
    ) -> tuple[gr.update, gr.update, str, str | None]:
        """Update preview when entry selection changes."""
        session_obj = self._ensure_session(session)
        results = session_obj.results

        if not results or not selected_entry_key:
            return (
                self._safe_dropdown_update([], None, interactive=False),
                self._safe_dropdown_update([], None, interactive=False),
                "",
                None,
            )

        entry = self._get_entry_by_key(results, selected_entry_key)
        if not entry:
            return (
                self._safe_dropdown_update([], None, interactive=False),
                self._safe_dropdown_update([], None, interactive=False),
                "",
                None,
            )

        # Check if protobuf is available
        service = session_obj.service
        if not service:
            has_protobuf = False
        else:
            db_info = service.get_database_info()
            has_protobuf = db_info.get("has_protobuf", False)

        if not has_protobuf:
            return (
                self._safe_dropdown_update([], None, interactive=False),
                self._safe_dropdown_update([], None, interactive=False),
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
            self._safe_dropdown_update(
                text_fields, text_fields[0] if text_fields else None, interactive=True
            ),
            self._safe_dropdown_update(
                audio_fields, audio_fields[0] if audio_fields else None, interactive=True
            ),
            text_preview,
            audio_preview,
        )

    def _update_text_preview(
        self,
        session: InterfaceSession | None,
        selected_entry_key: str,
        selected_field: str,
    ) -> str:
        """Update text preview based on selected entry and field."""
        session_obj = self._ensure_session(session)
        results = session_obj.results

        if not results or not selected_entry_key or not selected_field:
            return ""

        # Check if protobuf is available
        service = session_obj.service
        if not service:
            return ""

        db_info = service.get_database_info()
        has_protobuf = db_info.get("has_protobuf", False)

        if not has_protobuf:
            return ""

        entry = self._get_entry_by_key(results, selected_entry_key)
        if not entry:
            return ""

        return self._extract_text_preview(entry, selected_field)

    def _update_audio_preview(
        self,
        session: InterfaceSession | None,
        selected_entry_key: str,
        selected_field: str,
    ) -> str | None:
        """Update audio preview based on selected entry and field."""
        session_obj = self._ensure_session(session)
        results = session_obj.results

        if not results or not selected_entry_key or not selected_field:
            return None

        # Check if protobuf is available
        service = session_obj.service
        if not service:
            return None

        db_info = service.get_database_info()
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
        self, query: str, limit: int, session: InterfaceSession | None
    ) -> tuple[
        str,
        str,
        gr.update,
        gr.update,
        gr.update,
        str,
        str | None,
        InterfaceSession,
    ]:
        """Wrapper for search that returns HTML + component updates."""

        (
            results_html,
            status_message,
            entry_options,
            text_fields,
            audio_fields,
            text_preview,
            audio_preview,
            has_protobuf,
            session_obj,
        ) = self._search_data(query, limit, session)

        entry_update = self._safe_dropdown_update(entry_options, None, interactive=True)
        if has_protobuf:
            text_update = self._safe_dropdown_update(
                text_fields, text_fields[0] if text_fields else None, interactive=True
            )
            audio_update = self._safe_dropdown_update(
                audio_fields, audio_fields[0] if audio_fields else None, interactive=True
            )
        else:
            text_update = self._safe_dropdown_update([], None, interactive=False)
            audio_update = self._safe_dropdown_update([], None, interactive=False)

        return (
            results_html,
            status_message,
            entry_update,
            text_update,
            audio_update,
            text_preview,
            audio_preview,
            session_obj,
        )

    def _browse_entries_wrapper(
        self, count: int, session: InterfaceSession | None
    ) -> tuple[
        str,
        str,
        gr.update,
        gr.update,
        gr.update,
        str,
        str | None,
        InterfaceSession,
    ]:
        """Wrapper for browse that returns HTML + component updates."""

        (
            results_html,
            status_message,
            entry_options,
            text_fields,
            audio_fields,
            text_preview,
            audio_preview,
            has_protobuf,
            session_obj,
        ) = self._browse_entries(count, session)

        entry_update = self._safe_dropdown_update(entry_options, None, interactive=True)
        if has_protobuf:
            text_update = self._safe_dropdown_update(
                text_fields, text_fields[0] if text_fields else None, interactive=True
            )
            audio_update = self._safe_dropdown_update(
                audio_fields, audio_fields[0] if audio_fields else None, interactive=True
            )
        else:
            text_update = self._safe_dropdown_update([], None, interactive=False)
            audio_update = self._safe_dropdown_update([], None, interactive=False)

        return (
            results_html,
            status_message,
            entry_update,
            text_update,
            audio_update,
            text_preview,
            audio_preview,
            session_obj,
        )

    def _browse_random_entries_wrapper(
        self, count: int, session: InterfaceSession | None
    ) -> tuple[
        str,
        str,
        gr.update,
        gr.update,
        gr.update,
        str,
        str | None,
        InterfaceSession,
    ]:
        """Wrapper for random browse that returns HTML + component updates."""

        (
            results_html,
            status_message,
            entry_options,
            text_fields,
            audio_fields,
            text_preview,
            audio_preview,
            has_protobuf,
            session_obj,
        ) = self._browse_random_entries(count, session)

        entry_update = self._safe_dropdown_update(entry_options, None, interactive=True)
        if has_protobuf:
            text_update = self._safe_dropdown_update(
                text_fields, text_fields[0] if text_fields else None, interactive=True
            )
            audio_update = self._safe_dropdown_update(
                audio_fields, audio_fields[0] if audio_fields else None, interactive=True
            )
        else:
            text_update = self._safe_dropdown_update([], None, interactive=False)
            audio_update = self._safe_dropdown_update([], None, interactive=False)

        return (
            results_html,
            status_message,
            entry_update,
            text_update,
            audio_update,
            text_preview,
            audio_preview,
            session_obj,
        )

    def cleanup_temp_files(self):
        """Clean up temporary files."""
        for service in list(self._active_services):
            try:
                service.close()
            except Exception:
                logger.debug("Failed to close data service during cleanup")
            finally:
                self._active_services.discard(service)

    def launch(self, **kwargs):
        interface = self.create_interface()
        try:
            interface.launch(**kwargs)
        finally:
            self.cleanup_temp_files()
            logger.info("Cleaned up temporary files on interface shutdown")
