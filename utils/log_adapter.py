"""
utils/log_adapter.py
--------------------
SimulationLogger — a LoggerAdapter that binds simulation context
(simulation_id, persona, mode) to every log line automatically.

Usage:
    log = get_logger(__name__)                          # no context yet
    log = log.bind(simulation_id="abc-123")             # bind context
    log.info("Pipeline built", question_count=5)        # carries simulation_id
"""

import logging


class SimulationLogger(logging.LoggerAdapter):

    def bind(self, **context) -> "SimulationLogger":
        """Return a new logger with extra context fields attached."""
        return SimulationLogger(self.logger, {**self.extra, **context})

    def process(self, msg, kwargs):
        extra = {**self.extra, **kwargs.pop("extra", {})}
        kwargs["extra"] = extra
        return msg, kwargs

    # Allow passing extra fields as plain kwargs on every log call
    # e.g. log.info("msg", simulation_id="x") instead of log.info("msg", extra={...})
    def _log(self, level: int, msg: str, **kwargs) -> None:
        _standard = {"exc_info", "stack_info", "stacklevel"}
        extra = {k: v for k, v in kwargs.items() if k not in _standard}
        std = {k: v for k, v in kwargs.items() if k in _standard}
        extra.update(self.extra)
        self.logger.log(level, msg, extra=extra, **std)

    def debug(self, msg, *args, **kwargs):    self._log(logging.DEBUG, msg, **kwargs)
    def info(self, msg, *args, **kwargs):     self._log(logging.INFO, msg, **kwargs)
    def warning(self, msg, *args, **kwargs):  self._log(logging.WARNING, msg, **kwargs)
    def error(self, msg, *args, **kwargs):    self._log(logging.ERROR, msg, **kwargs)
    def critical(self, msg, *args, **kwargs): self._log(logging.CRITICAL, msg, **kwargs)