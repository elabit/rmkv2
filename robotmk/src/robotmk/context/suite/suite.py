"""This module encapsulates everyhting related so a single suite 
execution, either locally or remotely."""

from abc import ABC, abstractmethod
import platform
from pathlib import Path
from ..abstract import AbstractContext

# TODO: this is not specific for suite context yet
from robotmk.config.yml import RobotmkConfigSchema
from robotmk.rcc import RCCEnv, RCCDir
from .head import HeadFactory
from .target import Target, SharedPythonTarget, RCCPythonTarget, RemoteTarget


class SuiteContext(AbstractContext):
    def __init__(self):
        super().__init__()
        self.ymlschema = RobotmkConfigSchema
        self._suite = None

    @property
    def suiteid(self):
        """suite_id under "common" sets the suite to start (suitename + tag)"""
        if self.config.common.suiteid:
            return self.config.common.suiteid
        else:
            # TODO: What if suite is not found?
            pass

    @property
    def suite(self) -> Target:
        if not self._suite:
            # get the dotmap config for the suite to run
            suite_cfg = getattr(self.config.suites, self.suiteid)
            # Depending on the target, create a local or a remote suite
            if suite_cfg.target == "local":
                # create a head strategy for this OS / kind of suite
                head_strategy = HeadFactory(
                    platform.system(), suite_cfg.headless
                ).create_head_strategy()
                path = Path(self.config.common.robotdir).joinpath(suite_cfg.path)
                # TODO: What if Path does not exist?
                if path.exists():
                    if suite_cfg.shared_python is True:
                        # Same Python
                        self._suite = SharedPythonTarget(
                            self.suiteid, self.config, head_strategy
                        )
                    else:
                        # run in separate RCC Python
                        self._suite = RCCPythonTarget(
                            self.suiteid, self.config, head_strategy
                        )
                else:
                    raise ValueError("Suite path does not exist: " + str(path))
            elif suite_cfg.target == "remote":
                # TODO: implement remote suite
                self._suite = RemoteTarget(self.suiteid, self.config)
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
        # self.config.validate(self.ymlschema)

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
        self.suite.run()

    def output(self):
        # TODO: make this possible in CLI
        """Implements the agent output for local context."""
        print("Local context agent output")
        self.outputter = SuiteOutput(self.config)
        pass
