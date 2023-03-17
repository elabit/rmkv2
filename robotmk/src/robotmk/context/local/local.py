from ..abstract import AbstractContext
from robotmk.executor.scheduler import Scheduler


class LocalContext(AbstractContext):
    def __init__(self):
        super().__init__()

    def load_config(self, defaults, ymlfile: str, varfile: str) -> None:
        """Load the config for local context.

        Local context can merge the config from
        - OS defaults
        - + YML file (default/custom = --yml)
        - + environment variables
        """
        self.config.set_defaults(defaults)
        self.config.read_yml_cfg(must_exist=True, path=ymlfile)
        self.config.read_cfg_vars(path=None)

    def refresh_config(self) -> bool:
        """Re-loads the config and returns True if it changed"""
        config_copy = copy.deepcopy(self.configdict)
        # re-initializes the config object
        super().__init__(envvar_prefix=self.envvar_prefix)
        config_changed = config_copy != self.configdict
        return config_changed

    def run_default(self):
        """Implements the default action for local context."""
        self.produce_agent_output()
        print("Local context default action = output")
        pass

    def run(self):
        """Implements the run action for local context ()."""
        print("Local context run action")
        self.executor = Scheduler(self.config)
        self.executor.run()
        pass

    def produce_agent_output(self):
        """Implements the agent output for local context."""
        print("Local context agent output")
        pass
