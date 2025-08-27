import gradio as gr
from pathlib import Path
from ..core.preview_service import PreviewService
from loguru import logger


class LmdbugInterface:
    """
    Gradio-based web interface for LMDB data preview.
    """
    
    def __init__(self):
        """Initialize the Lmdbug interface."""
        self.preview_service: PreviewService | None = None
        self.current_db_path = ""
        self.initial_db_path = ""
        self.initial_protobuf_config: dict[str, str] | None = None
        
    def create_interface(self) -> gr.Blocks:
        """
        Create and configure the Gradio interface.
        
        Returns:
            Gradio Blocks interface
        """
        with gr.Blocks(title="Lmdbug - LMDB Data Preview Tool", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# Lmdbug - LMDB Data Preview Tool")
            gr.Markdown("Preview LMDB database content with Protobuf deserialization support")
            
            with gr.Row():
                with gr.Column(scale=1):
                    # Database and Protobuf Configuration Section
                    gr.Markdown("## Database Configuration")
                    
                    db_path_input = gr.Textbox(
                        label="LMDB Database Path",
                        placeholder="/path/to/lmdb/database",
                        value=self.initial_db_path
                    )
                    
                    gr.Markdown("### Protobuf Configuration (Optional)")
                    
                    protobuf_module_input = gr.Textbox(
                        label="Protobuf Module Path",
                        placeholder="/path/to/your_pb2.py",
                        value=self.initial_protobuf_config.get('module_path', '') if self.initial_protobuf_config else ""
                    )
                    
                    message_class_input = gr.Textbox(
                        label="Message Class Name",
                        placeholder="YourMessageClass",
                        value=self.initial_protobuf_config.get('message_class', '') if self.initial_protobuf_config else ""
                    )
                    
                    load_btn = gr.Button("Load Database", variant="primary")
                    
                    # Database Info Display
                    db_info_display = gr.JSON(
                        label="Database Information",
                        value={}
                    )
                    
                    # Protobuf Message Type Selection
                    message_type_dropdown = gr.Dropdown(
                        label="Primary Protobuf Message Type",
                        choices=[],
                        value=None,
                        interactive=True
                    )
                
                with gr.Column(scale=2):
                    # Search and Preview Section
                    gr.Markdown("## Data Preview and Search")
                    
                    with gr.Tabs():
                        # Preview Tab
                        with gr.TabItem("Browse"):
                            with gr.Row():
                                preview_count = gr.Number(
                                    label="Number of entries",
                                    value=10,
                                    minimum=1,
                                    maximum=1000
                                )
                                preview_btn = gr.Button("Preview First Entries")
                            
                            with gr.Row():
                                start_index = gr.Number(
                                    label="Start Index",
                                    value=0,
                                    minimum=0
                                )
                                index_count = gr.Number(
                                    label="Count",
                                    value=10,
                                    minimum=1,
                                    maximum=1000
                                )
                                index_btn = gr.Button("Browse by Index")
                        
                        # Key Search Tab
                        with gr.TabItem("Key Search"):
                            exact_key_input = gr.Textbox(
                                label="Exact Key",
                                placeholder="Enter exact key to search"
                            )
                            exact_search_btn = gr.Button("Search Exact Key")
                            
                            prefix_input = gr.Textbox(
                                label="Key Prefix",
                                placeholder="Enter key prefix"
                            )
                            prefix_limit = gr.Number(
                                label="Max Results",
                                value=100,
                                minimum=1,
                                maximum=1000
                            )
                            prefix_search_btn = gr.Button("Search by Prefix")
                            
                            pattern_input = gr.Textbox(
                                label="Key Pattern (substring)",
                                placeholder="Enter pattern to search in keys"
                            )
                            pattern_limit = gr.Number(
                                label="Max Results",
                                value=100,
                                minimum=1,
                                maximum=1000
                            )
                            pattern_search_btn = gr.Button("Search by Pattern")
                    
                    # Results Display
                    results_display = gr.JSON(
                        label="Results",
                        value=[],
                        show_label=True
                    )
                    
                    # Formatted Results Display
                    formatted_display = gr.HTML(
                        label="Formatted View",
                        value="<p>No results to display</p>"
                    )
            
            # Status Messages
            status_display = gr.Textbox(
                label="Status",
                value="Ready to load database",
                interactive=False
            )
            
            # Event Handlers
            load_btn.click(
                fn=self._load_database,
                inputs=[db_path_input, protobuf_module_input, message_class_input],
                outputs=[db_info_display, message_type_dropdown, status_display]
            )
            
            message_type_dropdown.change(
                fn=self._set_message_type,
                inputs=[message_type_dropdown],
                outputs=[status_display]
            )
            
            preview_btn.click(
                fn=self._preview_first_entries,
                inputs=[preview_count],
                outputs=[results_display, formatted_display, status_display]
            )
            
            index_btn.click(
                fn=self._browse_by_index,
                inputs=[start_index, index_count],
                outputs=[results_display, formatted_display, status_display]
            )
            
            exact_search_btn.click(
                fn=self._search_exact_key,
                inputs=[exact_key_input],
                outputs=[results_display, formatted_display, status_display]
            )
            
            prefix_search_btn.click(
                fn=self._search_by_prefix,
                inputs=[prefix_input, prefix_limit],
                outputs=[results_display, formatted_display, status_display]
            )
            
            pattern_search_btn.click(
                fn=self._search_by_pattern,
                inputs=[pattern_input, pattern_limit],
                outputs=[results_display, formatted_display, status_display]
            )
        
        return interface
    
    def set_initial_config(self, db_path: str | None = None, protobuf_config: dict[str, str] | None = None):
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
    
    def _load_database(self, db_path: str, protobuf_module: str, message_class: str) -> tuple[dict, list[str], str]:
        """Load the LMDB database and protobuf configuration."""
        if not db_path.strip():
            return {}, [], "Error: Database path is required"
        
        if not Path(db_path).exists():
            return {}, [], f"Error: Database path does not exist: {db_path}"
        
        # Initialize preview service
        self.preview_service = PreviewService(db_path)
        self.current_db_path = db_path
        
        # Load protobuf module if provided
        status_msg = f"Successfully loaded database: {db_path}"
        if protobuf_module.strip() and message_class.strip():
            if not Path(protobuf_module).exists():
                return {}, [], f"Warning: Protobuf module not found: {protobuf_module}"
            
            modules = [{'path': protobuf_module, 'message_class': message_class}]
            self.preview_service.load_protobuf_modules(modules, message_class)
            status_msg += f" with protobuf: {message_class}"
        
        # Get database information
        db_info = self.preview_service.get_database_info()
        message_types = self.preview_service.get_available_message_types()
        
        return db_info, message_types, status_msg
    
    def _set_message_type(self, message_type: str) -> str:
        """Set the primary protobuf message type."""
        if not self.preview_service:
            return "Error: No database loaded"
        
        if message_type and self.preview_service.set_message_type(message_type):
            return f"Set primary message type to: {message_type}"
        return f"Warning: Invalid message type: {message_type}"
    
    def _preview_first_entries(self, count: int) -> tuple[list[dict], str, str]:
        """Preview the first N entries."""
        if not self.preview_service:
            return [], "<p>No database loaded</p>", "Error: No database loaded"
        
        results = self.preview_service.preview_first_entries(count)
        html = self._format_results_as_html(results)
        status = f"Showing first {len(results)} entries"
        
        return results, html, status
    
    def _browse_by_index(self, start_index: int, count: int) -> tuple[list[dict], str, str]:
        """Browse entries by index range."""
        if not self.preview_service:
            return [], "<p>No database loaded</p>", "Error: No database loaded"
        
        results = self.preview_service.preview_by_index_range(start_index, count)
        html = self._format_results_as_html(results)
        status = f"Showing {len(results)} entries starting from index {start_index}"
        
        return results, html, status
    
    def _search_exact_key(self, key: str) -> tuple[list[dict], str, str]:
        """Search for an exact key."""
        if not self.preview_service:
            return [], "<p>No database loaded</p>", "Error: No database loaded"
        
        if not key.strip():
            return [], "<p>Please enter a key to search</p>", "Error: Key is required"
        
        result = self.preview_service.search_by_key(key)
        results = [result] if 'error' not in result else []
        html = self._format_results_as_html([result])
        
        if 'error' in result:
            status = f"Key search failed: {result['error']}"
        else:
            status = f"Found exact key: {key}"
        
        return results, html, status
    
    def _search_by_prefix(self, prefix: str, limit: int) -> tuple[list[dict], str, str]:
        """Search by key prefix."""
        if not self.preview_service:
            return [], "<p>No database loaded</p>", "Error: No database loaded"
        
        if not prefix.strip():
            return [], "<p>Please enter a prefix to search</p>", "Error: Prefix is required"
        
        results = self.preview_service.search_by_key_prefix(prefix, limit)
        html = self._format_results_as_html(results)
        status = f"Found {len(results)} keys with prefix '{prefix}'"
        
        return results, html, status
    
    def _search_by_pattern(self, pattern: str, limit: int) -> tuple[list[dict], str, str]:
        """Search by key pattern."""
        if not self.preview_service:
            return [], "<p>No database loaded</p>", "Error: No database loaded"
        
        if not pattern.strip():
            return [], "<p>Please enter a pattern to search</p>", "Error: Pattern is required"
        
        results = self.preview_service.search_by_pattern(pattern, limit)
        html = self._format_results_as_html(results)
        status = f"Found {len(results)} keys matching pattern '{pattern}'"
        
        return results, html, status
    
    def _format_results_as_html(self, results: list[dict]) -> str:
        """Format results as HTML for display."""
        if not results:
            return "<p>No results found</p>"
        
        html_parts = []
        
        for i, result in enumerate(results):
            html_parts.append("<div style='border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px;'>")
            html_parts.append(f"<h4>Entry {i + 1}</h4>")
            
            # Key information
            key = result.get('key', 'N/A')
            key_raw = result.get('key_raw', '')
            html_parts.append(f"<p><strong>Key:</strong> <code>{self._escape_html(key)}</code></p>")
            if key_raw and key != key_raw:
                html_parts.append(f"<p><strong>Key (Raw):</strong> <small><code>{key_raw}</code></small></p>")
            
            # Value information
            value_size = result.get('value_size', 0)
            html_parts.append(f"<p><strong>Value Size:</strong> {value_size} bytes</p>")
            
            value_info = result.get('value_info', {})
            
            # Show protobuf deserialization if available
            if 'primary_protobuf' in value_info:
                pb_data = value_info['primary_protobuf']
                if pb_data.get('success'):
                    html_parts.append("<p><strong>Protobuf Data:</strong></p>")
                    html_parts.append(f"<pre style='background: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto;'>{self._escape_html(pb_data.get('json', '{}'))}</pre>")
            
            # Show text preview
            text_preview = value_info.get('text_preview', '')
            if text_preview:
                html_parts.append("<p><strong>Text Preview:</strong></p>")
                html_parts.append(f"<pre style='background: #f9f9f9; padding: 10px; border-radius: 3px; max-height: 150px; overflow: auto;'>{self._escape_html(text_preview)}</pre>")
            
            html_parts.append("</div>")
        
        return ''.join(html_parts)
    
    def _escape_html(self, text: str) -> str:
        """
        Escape HTML characters in text.
        
        Args:
            text: Text to escape
            
        Returns:
            HTML-escaped text
        """
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    def launch(self, **kwargs):
        """
        Launch the Gradio interface.
        
        Args:
            **kwargs: Additional arguments for gr.Interface.launch()
        """
        interface = self.create_interface()
        interface.launch(**kwargs)