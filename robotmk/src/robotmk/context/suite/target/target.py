from abc import ABC, abstractmethod
from pathlib import Path
import json
from ..strategies import RunStrategy, RunStrategyFactory
from uuid import uuid4

from robotmk.logger import RobotmkLogger


# class Target(ABC):
#     """A Target defines the environment where a suite gets executed.

#     It's the abstraction of either
#     - a local Robot suite or ("target: local")
#     - an API call to an external platform ("target: remote") like Robocorp or Kubernetes
#     """

#     def __init__(self, suiteuname: str, config, logger: RobotmkLogger):
#         self.suiteuname = suiteuname
#         self.config = config

#         self.commoncfg = self.config.get("common")

#         self._logger = logger
#         # TODO: Boilerplate alarm
#         self.debug = self._logger.debug
#         self.info = self._logger.info
#         self.warning = self._logger.warning
#         self.error = self._logger.error
#         self.critical = self._logger.critical

#     @abstractmethod
#     def run(self):
#         """Abstract method to run a suite/target."""
#         pass

#     @abstractmethod
#     def output(self):
#         """Abstract method to get the output of a suite/target."""
#         pass


# class LocalTarget(Target):
#     """A FS target is a single RF suite or a RCC task, ready to run from the local filesystem.

#     It also encapsulates the implementation details of the RUN strategy, which is
#     either a headless or a headed execution (RDP, XVFB, Scheduled Task)."""

#     def __init__(
#         self,
#         suiteuname: str,
#         config: dict,
#         logger: RobotmkLogger,
#     ):
#         super().__init__(suiteuname, config, logger)

#         # Store RCC and RF logs in separate folders
#         # TODO: relly needed?
#         # self.config.set(
#         #     "common.logdir",
#         #     "%s/%s" % (self.config.get("basic_cfg.common.logdir"), str(self)),
#         # )

#         self.path = Path(self.config.get("common.robotdir")).joinpath(
#             self.config.get("suitecfg.path")
#         )
#         # TODO: run strategy should not be set in init, because output() always reads results from filesystem
#         self.run_strategy = RunStrategyFactory(self).create()
#         # list of subprocess' results and console output
#         self.console_results = {}

#     @abstractmethod
#     def run(self):
#         """Implementation in subclasses RCCTarget and RobotFrameworkTarget"""
#         pass

#     def output(self):
#         """Read the result artifacts from the filesystem."""
#         with open(self.statefile_fullpath) as f:
#             data = json.load(f)
#             return data

#     @property
#     def pre_command(self):
#         return None

#     @property
#     def main_command(self):
#         return None

#     @property
#     def post_command(self):
#         return None

#     @property
#     def uuid(self):
#         """If a UUID is already part of the suite config, use this. Otherwise generate a new one.

#         The idea is that the UUID is handed over between all robotmk calls and lastly part of the
#         result JSON."""
#         uuid_ = self.config.get("suitecfg.uuid", False)
#         if not uuid_:
#             uuid_ = uuid4().hex
#         return uuid_

#     @property
#     def logdir(self):
#         return self.config.get("common.logdir")

#     @property
#     def resultdir(self):
#         return Path(self.logdir).joinpath("results")

#     @property
#     def statefile_fullpath(self):
#         return str(Path(self.resultdir).joinpath(self.suiteuname + ".json"))

#     @property
#     def is_disabled_by_flagfile(self):
#         """The presence of a file DISABLED inside of a Robot suite will prevent
#         Robotmk to execute the suite, either by RCC or RobotFramework."""
#         return self.path.joinpath("DISABLED").exists()
