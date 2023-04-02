from abc import ABC, abstractmethod
import os
from pathlib import Path

from .retry import RetryStrategyFactory, CompleteRetry, IncrementalRetry
from ..target import LocalTarget
from ...strategies import RunStrategy

from robotmk.logger import RobotmkLogger
from robotmk.config import Config

import robot
import mergedeep

from uuid import uuid4
from datetime import datetime

local_tz = datetime.utcnow().astimezone().tzinfo

# This is the "heavy" part of the code. It contains the logic to run RF.
# Here I place all the Robotmk v1 shit.


class RobotFrameworkTarget(LocalTarget):
    def __init__(
        self,
        suiteid: str,
        config: dict,
        logger: RobotmkLogger,
    ):
        super().__init__(suiteid, config, logger)
        self.retry_strategy = RetryStrategyFactory(self).create()
        self.uuid = uuid4().hex
        self.shortuuid = self.uuid[:8]
        self._timestamp = self.get_now_as_epoch()
        # params for RF: global ones & re-execution
        # self.robotmk_params = {"console": "NONE", "report": "NONE"}
        self.robotmk_params = {"report": "NONE"}

    def run(self):
        # TODO: max_parallel is task of scheduler!)
        if self.is_disabled_by_flagfile:
            # TODO: Log skipped
            # reason = self.get_disabled_reason()
            return
        else:
            # TODO: write state with UUID and start_time
            self.robotmk_params.update({"outputdir": self.config.get("common.outdir")})
            self.retry_strategy.run()

    @property
    def is_disabled_by_flagfile(self):
        """The presence of a file DISABLED inside of a Robot suite will prevent
        Robotmk to execute the suite."""
        return self.path.joinpath("DISABLED").exists()

    def get_now_as_dt(self):
        return datetime.now(local_tz)

    def get_now_as_epoch(self):
        return int(self.get_now_as_dt().timestamp())

    @property
    def timestamp(self):
        """Returns the timestamp the suite execution was started. This is
        used for all executions of the suite, including retries in order
        to group the result files."""
        return self._timestamp

    def get_disabled_reason(self) -> str:
        """Report back the reason why the suite was disabled."""
        if self.is_disabled_by_flagfile:
            try:
                with open(self.path.joinpath("DISABLED"), "r") as f:
                    reason = f.read()
                    if len(reason) > 0:
                        return "Reason: " + reason
                    else:
                        return ""
            except:
                return ""

    @property
    def output_filename(self):
        """Returns the output filename string, including the retry number.

        Example:
            robotframework_suite1_978741fb_1680335851
            robotframework_suite1_978741fb_1680335851_retry-1"""
        if self.attempt == 1:
            suite_filename = "robotframework_%s_%s_%s" % (
                self.suiteid,
                self.timestamp,
                self.shortuuid,
            )
        else:
            suite_filename = "robotframework_%s_%s_%s_retry-%d" % (
                self.suiteid,
                self.timestamp,
                self.shortuuid,
                int(self.attempt - 1),
            )
        return suite_filename

    @property
    def output_xml(self):
        return self.output_filename + ".xml"

    @property
    def log_html(self):
        return self.output_filename + ".html"

    @property
    def command(self):
        # Builds the complete commandline to execute the suite.
        # (See https://robot-framework.readthedocs.io/en/latest/autodoc/robot.html#robot.run.run_cli)
        # TODO: Logging
        self.robotmk_params.update(
            {
                "log": self.log_html,
                "output": self.output_xml,
            }
        )

        suite_params = mergedeep.merge(
            self.suitecfg.get("params").asdict(), self.robotmk_params
        )
        arglist = ["robot"]
        for k, v in suite_params.items():
            arg = f"--{k}"
            # create something we can iterate over
            if isinstance(v, str):
                # key:value    => convert to 1 el list
                vlist = [v]
            elif isinstance(v, dict):
                if k == "variable":
                    # key:var-dict => convert to list of varkey:varvalue
                    vlist = list(map(lambda x: f"{x[0]}:{x[1]}", v.items()))
                else:
                    self._suite.logger.warn(
                        f"The Robot Framework parameter {k} is a dict but cannot be converted to cmdline arguments (values: {str(v)})"
                    )
            elif isinstance(v, list):
                if k == "argumentfile" or k == "variablefile":
                    # make the file args absolute file paths
                    v = [str(self._suite.pathdir.joinpath(n)) for n in v]
                # key:list     => no conversion
                vlist = v

            for value in vlist:
                # values which are boolean(-like) are single parameters without option
                if type(value) is bool or value in ["yes", "no", "True", "False"]:
                    arglist.extend([arg])
                else:
                    arglist.extend([arg, value])
        # the path of the robot suite is the very last argument
        arglist.append(str(self.path))
        return arglist

    # Suite timestamp for filenames
    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, t):
        self._timestamp = t
