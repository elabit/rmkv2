from abc import ABC, abstractmethod
from pathlib import Path
from uuid import uuid4
from ..strategies import RunStrategy, RunStrategyFactory

from robotmk.logger import RobotmkLogger


class Target(ABC):
    """A Target defines the environment where a suite gets executed.

    It's the abstraction of either
    - a local Robot suite or ("target: local")
    - an API call to an external platform ("target: remote") like Robocorp or Kubernetes
    """

    def __init__(self, suiteuname: str, config, logger: RobotmkLogger):
        self.suiteuname = suiteuname
        self.config = config

        self.commoncfg = self.config.get("common")

        self._logger = logger
        # TODO: Boilerplate alarm
        self.debug = self._logger.debug
        self.info = self._logger.info
        self.warning = self._logger.warning
        self.error = self._logger.error
        self.critical = self._logger.critical

    @abstractmethod
    def run(self):
        """Abstract method to run a suite/target."""
        pass

    @abstractmethod
    def output(self):
        """Abstract method to get the output of a suite/target."""
        pass


class LocalTarget(Target):
    """A local target is a single Robot Framework suite or a RCC task for this suite.

    It also encapsulates the implementation details of the RUN strategy, which is
    either a headless or a headed execution (RDP, XVFB, Scheduled Task)."""

    def __init__(
        self,
        suiteuname: str,
        config: dict,
        logger: RobotmkLogger,
    ):
        super().__init__(suiteuname, config, logger)

        # Store RCC and RF logs in separate folders
        # TODO: relly needed?
        # self.config.set(
        #     "common.logdir",
        #     "%s/%s" % (self.config.get("basic_cfg.common.logdir"), str(self)),
        # )

        self.path = Path(self.config.get("common.robotdir")).joinpath(
            self.config.get("suitecfg.path")
        )
        self.run_strategy = RunStrategyFactory(self).create()
        # list of subprocess' results and console output
        self.console_results = {}

    @property
    def pre_command(self):
        return None

    @property
    def main_command(self):
        return None

    @property
    def post_command(self):
        return None

    @property
    def uuid(self):
        return self.config.get("suitecfg.uuid", uuid4().hex)

    @property
    def logdir(self):
        return self.config.get("common.logdir")

    @property
    def is_disabled_by_flagfile(self):
        """The presence of a file DISABLED inside of a Robot suite will prevent
        Robotmk to execute the suite, either by RCC or RobotFramework."""
        return self.path.joinpath("DISABLED").exists()

    @abstractmethod
    def run(self):
        pass

    def output(self):
        # None of the run strategies used for "run" are needed to get the output,
        # so we can just read the result artifacts from the filesystem.
        pass
