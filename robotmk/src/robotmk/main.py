"""Robotmk main module

The main module of the Robotmk package, where the Robotmk instance gets
created for the use within the contexts.
It also contains the DEFAULTS dict with all default values for the config. """


import os
import sys
from loguru import logger
from robotmk.context import ContextFactory

# TODOs:
# - add logging
# - add pytests

LOG_LEVELS = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]

DEFAULTS = {
    # Default values for the "common" config section
    "common": {
        "robotmk_yml": "robotmk.yml",
        "log_level": "INFO",
        "log_retention": 14,
    },
    # Default values for the "common" config section (Windows)
    "nt": {
        "cfgdir": "C:/ProgramData/checkmk/agent/config",  # where to find robotmk.yml
        "robotdir": "C:/ProgramData/checkmk/agent/robot",
        "logdir": "C:/ProgramData/checkmk/agent/log/robotmk/",
        "tmpdir": "C:/ProgramData/checkmk/agent/tmp/robotmk",
    },
    # Default values for the "common" config section (Linux)
    "posix": {
        "cfgdir": "/etc/check_mk",  # where to find robotmk.yml
        "robotdir": "/usr/lib/check_mk_agent/robot",
        "logdir": "/var/log/robotmk",
        "tmpdir": "/tmp/robotmk",
    },
}


class Robotmk:
    """This is the main class of the robotmk package. It is used to create a
    Robotmk instance with a specific context.

    Configuration loading (yml, var, env) depends on the context and is only
    done when no config object is passed to the init method."""

    def __init__(
        self,
        log_level=None,
        contextname=None,
        ymlfile: str = None,
        varfile: str = None,
        default_cfg: dict = {},
    ) -> None:
        """context is the strategy to use and in fact a set of factory methods.
        If called from the CLI without context argument, the default context
        will be read from environment variable ROBOTMK_common_context."""

        self._set_context(contextname, log_level)
        self._context.load_config(
            DEFAULTS, ymlfile=ymlfile, varfile=varfile, default_cfg=default_cfg
        )

        # self.run_default = self._context.run_default
        # execute and output are the two main functions of each context:
        self.execute = self._context.execute
        self.output = self._context.output

    @property
    def config(self):
        return self._context.config

    def _set_context(self, contextname: str, log_level: str = None) -> None:
        """Sets the context of the Robotmk instance (=strategy)."""
        if contextname is None:
            contextname = os.environ.get("ROBOTMK_common_context", None)
        if contextname is None:
            raise ValueError(
                "No context given on CLI or set by environment variable ROBOTMK_common_context."
            )
        self._context = ContextFactory(contextname, log_level).get_context()
        self.config.set("common.context", contextname)

        # TODO: Setup Logging here


# print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

# try:
#     # This is here to simulate application activity (which keeps the main thread alive).
#     while True:
#         time.sleep(2)
# except (KeyboardInterrupt, SystemExit):
#     # Not strictly necessary if daemonic mode is enabled but should be done if possible
#     scheduler.shutdown()
