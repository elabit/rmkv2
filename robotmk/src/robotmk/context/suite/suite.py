"""This module encapsulates everyhting related so a single suite 
execution, either locally or remotely."""

from pathlib import Path
from ..abstract import AbstractContext

from robotmk.config.yml import RobotmkConfigSchema

from .target import Target, RobotFrameworkTarget, RCCTarget, RemoteTarget


class SuiteContext(AbstractContext):
    def __init__(self):
        super().__init__()
        self._suite = None
        self._ymlschema = RobotmkConfigSchema

    @property
    def suiteid(self):
        """suiteid under "common" sets the suite to start (suitename + tag)"""
        if self.config.common.suiteid:
            return self.config.common.suiteid
        else:
            # TODO: What if suite is not found?
            pass

    @property
    def target(self) -> Target:
        """Returns a Target object using the Bridge pattern which combines
        - Local Targets (Shared Python/RCC)   with
        - Head Strategies (Headless/Headed, Win/linux)"""
        # TODO: notify the logger initialization as soon as there is config loaded
        # to prevent this call
        if not self._suite:
            self.init_logger()
            # get the dotmap config for the suite to run
            suitecfg = getattr(self.config.suites, self.suiteid, None)
            # Depending on the target, create a local or a remote suite
            if suitecfg.run.target == "local":
                path = Path(self.config.common.robotdir).joinpath(suitecfg.path)
                if path.exists():
                    if suitecfg.run.rcc is True:
                        self._suite = RCCTarget(self.suiteid, self.config, self.logger)
                    else:
                        self._suite = RobotFrameworkTarget(
                            self.suiteid, self.config, self.logger
                        )
                else:
                    self.error("Suite path does not exist: " + str(path))
            elif suitecfg.run.target == "remote":
                self._suite = RemoteTarget(self.suiteid, self.config, self.logger)
            else:
                self.error("Unknown target type for suite %s!" % self.suiteid)
        return self._suite

    def load_config(self, defaults, ymlfile: str, varfile: str) -> None:
        """Load the config for suite context.

        Suite context can merge the config from
        - OS defaults
        - + YML file (default/custom = --yml)
        - + var file (= --vars)
        - + environment variables
        """
        self._config_factory.set_defaults(defaults)
        self._config_factory.read_yml_cfg(path=ymlfile, must_exist=False)
        self._config_factory.read_cfg_vars(path=varfile)
        self.config = self._config_factory.create_config()
        # TODO: validate later so that config can be dumped
        # self.config.validate(self._ymlschema)

    def refresh_config(self) -> bool:
        """Re-loads the config and returns True if it changed"""
        # TODO: implement this
        pass

    def run_default(self):
        """Implements the default action for suite context."""
        # TODO: execute one single suite
        print("Suite context default action = execute single suite ")
        pass

    def execute(self):
        """Runs a single suite, either locally or remotely (via API call)."""
        self.target.run()

    def output(self):
        # TODO: make this possible in CLI
        """Implements the agent output for local context."""
        print("Local context agent output")
        self.outputter = SuiteOutput(self.config)
        pass
