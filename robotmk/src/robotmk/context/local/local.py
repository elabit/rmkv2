from pathlib import Path
from ..abstract import AbstractContext

from robotmk.config import Config, RobotmkConfigSchema

from robotmk.executor.scheduler import Scheduler


class LocalContext(AbstractContext):
    def __init__(self):
        super().__init__()
        self.ymlschema = RobotmkConfigSchema

    @property
    def logger(self):
        if not self._logger:
            self._logger = RobotmkLogger(
                Path(self.config.common.logdir).joinpath("robotmk.log"),
                self.config.common.log_level,
            )
        return self._logger

    def load_config(self, defaults, **kwargs) -> None:
        """Load the config for local context.

        Local context can merge the config from
        - OS defaults
        - + YML file (default/custom = --yml)
        - + environment variables
        """
        # self.config = Config()
        self.config.set_defaults(defaults)
        self.config.read_yml_cfg(path=kwargs["ymlfile"], must_exist=True)
        self.config.read_cfg_vars(path=None)
        # TODO: validate later so that config can be dumped
        # self.config.validate(self.ymlschema)

    def refresh_config(self) -> bool:
        """Re-loads the config and returns True if it changed"""
        config_copy = copy.deepcopy(self.configdict)
        # re-initializes the config object
        super().__init__(envvar_prefix=self.envvar_prefix)
        config_changed = config_copy != self.configdict
        return config_changed

    def run_default(self):
        """Implements the default action for local context."""
        # TODO: how do I call the coutputter here?
        print("Local context default action = output")
        pass

    def execute(self, *args, **kwargs):
        """Starts the scheduler."""
        self.executor = Scheduler(self.config)
        self.executor.run()
        pass

    def output(self):
        """Implements the agent output for local context."""
        print("Local context agent output")
        self.outputter = LocalOutput(self.config)
        pass
