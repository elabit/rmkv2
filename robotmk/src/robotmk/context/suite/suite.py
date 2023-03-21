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
from .target import SharedPythonTarget, RCCPythonTarget, RemoteTarget


class SuiteContext(AbstractContext):
    def __init__(self):
        super().__init__()
        self.ymlschema = RobotmkConfigSchema
        self._suite = None

    @property
    def suite_id(self):
        """suite_id under "common" sets the suite to start (suitename + tag)"""
        return self.config.common.suite_id

    @property
    def suite(self):
        if not self._suite:
            suite_cfg = getattr(self.config.suites, self.suite_id)
            if suite_cfg.target == "local":
                head_strategy = HeadFactory(
                    platform.system(), suite_cfg.headless
                ).create_head_strategy()
                path = Path(self.config.common.robotdir).joinpath(suite_cfg.path)
                # TODO: Path exists?
                if path.exists():
                    if suite_cfg.shared_python is True and RCCDir.is_rcc_compatible(
                        path
                    ):
                        # OS Python
                        self._suite = SharedPythonTarget(
                            self.suite_id, self.config, head_strategy
                        )
                    else:
                        # RCC Python
                        self._suite = RCCPythonTarget(
                            self.suite_id, self.config, head_strategy
                        )
                else:
                    raise ValueError("Suite path does not exist: " + str(path))
            elif suite_cfg.target == "remote":
                # TODO: implement remote suite
                self._suite = RemoteTarget(self.suite_id, self.config)
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
