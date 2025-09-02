import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime

class TestLogger:
    """Centralized logging for tests"""
    
    def __init__(self, logger_name: str = __name__):
        self.logger = logging.getLogger(logger_name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure logger with appropriate handlers and formatters"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    @asynccontextmanager
    async def log_phase(self, phase_name: str, **context):
        """Context manager for logging test phases with timing"""
        start_time = time.time()
        print(f"=== {phase_name.upper()} ===")
        self.logger.info(f"Starting phase: {phase_name}", extra=context)
        
        try:
            yield
            duration = time.time() - start_time
            print(f" {phase_name} completed in {duration:.2f}s")
            self.logger.info(f"Phase '{phase_name}' completed in {duration:.2f}s")
        except Exception as e:
            duration = time.time() - start_time
            print(f" {phase_name} failed after {duration:.2f}s: {e}")
            self.logger.error(f"Phase '{phase_name}' failed after {duration:.2f}s: {e}")
            raise
    
    def info(self, message: str, **kwargs):
        print(f"   {message}")
        self.logger.info(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        print(f"   ERROR: {message}")
        self.logger.error(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        print(f"   WARNING: {message}")
        self.logger.warning(message, **kwargs)