"""This module encapsulates everyhting related so a single suite 
execution, either locally or remotely."""

from pathlib import Path
from ..abstract import AbstractContext

from robotmk.config import Config, RobotmkConfigSchema

from .target import Target, RobotFrameworkTarget, RCCTarget, RemoteTarget


class SuiteContext(AbstractContext):
    def __init__(self):
        super().__init__()
        self._target = None
        self._ymlschema = RobotmkConfigSchema

    @property
    def suiteuname(self):
        """suiteuname under "common" sets the suite to start (suitename + tag)"""
        try:
            suiteuname = self.config.get("common.suiteuname")
        except AttributeError:
            pass
            # TODO: What if suite is not found?
        return suiteuname

    def get_target(self) -> Target:
        """Returns a Target object using the Bridge pattern which combines
        - Local Targets (Shared Python/RCC)   with
        - Head Strategies (Headless/Headed, Win/linux)"""
        # TODO: notify the logger initialization as soon as there is config loaded
        # to prevent this call
        if not self._target:
            self.init_logger()
            # get the dotmap config for the suite to run
            # TODO: what if suite is not part of the config?
            suitecfg = self.config.get("suites.%s" % self.suiteuname)
            if suitecfg == None:
                self.error("Suite '%s' is not part of the config!" % self.suiteuname)

            # Depending on the target, create a local or a remote suite
            target = suitecfg.get("run.target")
            rcc = suitecfg.get("run.rcc")
            if target == "local":
                path = Path(self.config.get("common.robotdir")).joinpath(
                    suitecfg.get("path")
                )
                if path.exists():
                    if rcc is True:
                        self._target = RCCTarget(
                            self.suiteuname, self.config, self.logger
                        )
                    else:
                        self._target = RobotFrameworkTarget(
                            self.suiteuname, self.config, self.logger
                        )
                else:
                    # TBD: check this if this gets logged...
                    self.error("Suite path does not exist: " + str(path))
            elif target == "remote":
                self._target = RemoteTarget(self.suiteuname, self.config, self.logger)
            else:
                self.error("Unknown target type for suite %s!" % self.suiteuname)
        return self._target

    @property
    def target(self) -> Target:
        return self._target

    def load_config(self, defaults, ymlfile: str, varfile: str) -> None:
        """Load the config for suite context.

        Suite context can merge the config from
        - OS defaults
        - + YML file (default/custom = --yml)
        - + var file (= --vars)
        - + environment variables
        """
        self.config = Config()
        self.config.set_defaults(defaults)
        self.config.read_yml_cfg(path=ymlfile, must_exist=False)
        self.config.read_cfg_vars(path=varfile)
        # self._config_factory.set_defaults(defaults)
        # self._config_factory.read_yml_cfg(path=ymlfile, must_exist=False)
        # self._config_factory.read_cfg_vars(path=varfile)
        # self.config = self._config_factory.create_config()
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
        self.get_target().run()

    def output(self):
        # TODO: make this possible in CLI
        """Implements the agent output for local context."""
        print("Local context agent output")
        self.outputter = SuiteOutput(self.config)
        pass
