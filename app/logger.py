import logging
import os
import json
from datetime import datetime
from typing import Any, Dict
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Custom Theme for Institutional Audit
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "critical": "bold white on red",
    "success": "bold green",
    "layer": "bold magenta",
    "ticker": "bold blue"
})

console = Console(theme=custom_theme)

class PipelineLogger:
    """Institutional-grade Rich Pipeline Tracer for Forensic Analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger("quantstock_pipeline")
        self.logger.setLevel(logging.DEBUG)
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            # 1. Terminal Handler (Rich)
            rich_handler = RichHandler(
                console=console,
                rich_tracebacks=True,
                markup=True,
                show_path=False
            )
            self.logger.addHandler(rich_handler)
            
            # 2. Forensic File Handler
            fh = logging.FileHandler("logs/pipeline.log", encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

    def log_event(self, ticker: str, layer: str, status: str, message: str):
        """Standardized log entry for pipeline state changes"""
        # Terminal (Rich Markup)
        self.logger.info(f"[[ticker]{ticker}[/]] [[layer]{layer}[/]] [[success]{status}[/]] {message}")

    def log_payload(self, ticker: str, layer: str, label: str, data: Any):
        """Log structured JSON payloads for forensic analysis"""
        try:
            if hasattr(data, 'model_dump_json'):
                json_str = data.model_dump_json(indent=2)
            elif isinstance(data, (dict, list)):
                json_str = json.dumps(data, indent=2)
            else:
                json_str = str(data)
            
            # Write full structure to file only (prevent terminal bloat)
            with open("logs/pipeline.log", "a", encoding="utf-8") as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"PAYLOAD: [{ticker.upper()}] [{layer}] [{label}]\n")
                f.write(f"TIMESTAMP: {datetime.now().isoformat()}\n")
                f.write(f"{'-'*80}\n")
                f.write(json_str)
                f.write(f"\n{'='*80}\n")
            
            self.logger.debug(f"[[ticker]{ticker}[/]] [[layer]{layer}[/]] [Payload logged: {label}]")
        except Exception as e:
            self.logger.error(f"Failed to log payload for {ticker}: {e}")

    def log_error(self, ticker: str, layer: str, message: str):
        """Log critical pipeline errors"""
        self.logger.error(f"[[ticker]{ticker}[/]] [[layer]{layer}[/]] [bold red]CRITICAL FAILURE[/]: {message}")

# Singleton Instance
pipeline_logger = PipelineLogger()