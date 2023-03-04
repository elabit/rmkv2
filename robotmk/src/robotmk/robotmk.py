from context import ContextFactory
from pathlib import Path

# TODOs:
# - add logging
# - add pytests


DEFAULTS = {
    # Default values for the "common" config section
    "common": {
        # "execution_mode": "agent_serial",
        # "agent_output_encoding": "zlib_codec",
        "transmit_html": False,
        "robotmk_yml": "robotmk.yml",
        "log_level": "INFO",
        "log_rotation": 14,
        # "cache_time": 960,
        # "execution_interval": 900,
    },
    # Default values for the "common" config section (Windows)
    "nt": {
        "robotdir": "C:/ProgramData/checkmk/agent/robot",
        "cfgdir": "C:/ProgramData/checkmk/agent/config",
        "logdir": "C:/ProgramData/checkmk/agent/log/robotmk",
        "tmpdir": "C:/ProgramData/checkmk/agent/tmp/robotmk",
    },
    # Default values for the "common" config section (Linux)
    "posix": {
        "robotdir": "/usr/lib/check_mk_agent/robot",
        "cfgdir": "/etc/check_mk",
        "logdir": "/var/log/robotmk",
        "tmpdir": "/tmp/robotmk",
    },
}


class Robotmk:
    """This is the main class of the robotmk package. It is used to create a
    Robotmk instance with a specific context."""

    def __init__(self, context) -> None:
        # context is the strategy to use and in fact a set of factory methods.
        self._context = ContextFactory(context).get_context()
        self.load_config = self._context.load_config
        self.run = self._context.run


if __name__ == "__main__":
    """Create a Robotmk instance"""
    context = "local"
    robotmk = Robotmk(context)
    robotmk.load_config(DEFAULTS)
    robotmk.run()
    pass


# print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

# try:
#     # This is here to simulate application activity (which keeps the main thread alive).
#     while True:
#         time.sleep(2)
# except (KeyboardInterrupt, SystemExit):
#     # Not strictly necessary if daemonic mode is enabled but should be done if possible
#     scheduler.shutdown()
