"""Robotmk main module

The main module of the Robotmk package, where the Robotmk instance gets
created for the use within the contexts.
It also contains the DEFAULTS dict with all default values for the config. """


from robotmk.context import ContextFactory
import os

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

    def __init__(self, contextname=None) -> None:
        # context is the strategy to use and in fact a set of factory methods.
        # If called from the CLI without context argument, the default context
        # will be read from environment variable ROBOTMK_common_context.
        if contextname is None:
            contextname = os.environ.get("ROBOTMK_common_context", "not set")
        if contextname == "not set":
            raise ValueError(
                "No context given on CLI or set by environment variable ROBOTMK_common_context."
            )
        self._context = ContextFactory(contextname).get_context()
        self.load_config = self._context.load_config
        # TODO: Setup Logging here


# print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

# try:
#     # This is here to simulate application activity (which keeps the main thread alive).
#     while True:
#         time.sleep(2)
# except (KeyboardInterrupt, SystemExit):
#     # Not strictly necessary if daemonic mode is enabled but should be done if possible
#     scheduler.shutdown()
