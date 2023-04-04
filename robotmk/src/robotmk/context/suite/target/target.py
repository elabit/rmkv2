from abc import ABC, abstractmethod
from dotmap import DotMap
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

    def __init__(self, suiteuname: str, config: DotMap, logger: RobotmkLogger):
        self.suiteuname = suiteuname
        self.config = config
        self.suitecfg = self.config.get("suites.%s" % suiteuname)
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
    """A local target is a single Robot Fremework suite or a RCC task for this suite.

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
        self.config.set(
            "common.logdir", "%s/%s" % (self.config.get("common.logdir"), str(self))
        )

        self.path = Path(self.config.get("common.robotdir")).joinpath(
            self.suitecfg.get("path")
        )
        self.run_strategy = RunStrategyFactory(self).create()
        # list of subprocess' results and console output
        self.console_results = {}

    @property
    def uuid(self):
        return self.suitecfg.get("uuid", uuid4().hex)

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


# ---


# class LocalSuite(Target):
#     """A single Robot Framework suite on Linux and Windows.

#     Also encapsulates the implementation details of
#     whether to run the suite with the OS Python or within
#     a RCC environment."""

#     # self.suitecfg = getattr(self.config.suites, self.suitename)

#     def __init__(self, name: str, config: dict):
#         super().__init__(name, config)
#         self._set_python_strategy()
#         self._set_head_strategy()
#         pass

#     @property
#     def abspath(self):
#         return Path(self.config.path).resolve()

#     def run(self):
#         pass

#     def _set_python_strategy(self):
#         """Sets the python execution strategy.

#         Execution with `RCC` is possible when
#         # 1. the suite is RCC compatible (conda.yml)
#         # 2. feature is available (binary check)
#         # 3. RCC is not disallowed in robotmk.yml
#         # 4. `share-python` is not set on cli (would enforce the same Python)"""

#     def _set_head_strategy(self):
#         """Sets the strategy for this suite:
#         - HeadedWinExecStrategy
#         - HeadedLinExecutionStrategy
#         - HeadlessExecutionStrategy"""
#         self._strategy = strategy
#         self.prepare = self._strategy.prepare
#         self.execute = self._strategy.execute
#         self.cleanup = self._strategy.cleanup


# class RemoteSuite(Target):
#     """A single Robot Framework suite on a remote platform.

#     Its execution is triggered via an API call."""

#     def __init__(self, name: str, config: dict):
#         super().__init__(name)
#         self.config = config

#     def get_jobs_running(self):
#         """Returns the number of running jobs currently."""
#         pass

#     def kill_job(self):
#         pass
