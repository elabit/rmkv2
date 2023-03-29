import loguru
from abc import ABC, abstractmethod
from datetime import datetime


class AbstractLogger(ABC):
    def __init__(self):
        if not getattr(self, "logger", None):
            self.logger = loguru.logger
            self.logger.remove()  # Remove default configuration

    def debug(self, message, *args, **kwargs):
        self.logger.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        self.logger.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self.logger.error(message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        self.logger.critical(message, *args, **kwargs)


class RobotmkLogger(AbstractLogger):
    def __init__(self, log_file_path, log_level="INFO"):
        super().__init__()
        self.log_file_path = log_file_path
        # Add the file sink
        self.logger.add(self.log_file_path, level=log_level)


# class JSONLogger(AbstractLogger):
#     """Logging into an internal message stack"""

#     def __init__(self, log_level="INFO"):
#         self.messages = []
#         self.logger.add(
#             {
#                 "sink": lambda msg: self.messages.append(
#                     self.message_to_dict(msg.record), log_level=log_level
#                 )
#             }
#         )

#     @staticmethod
#     def message_to_dict(record):
#         return {
#             **record,
#             "extra": {k: str(v) for k, v in record["extra"].items()},
#             "time": datetime.utcnow().isoformat() + "Z",
#         }
