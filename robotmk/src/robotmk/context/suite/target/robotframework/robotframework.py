from abc import ABC, abstractmethod
import os
from pathlib import Path
from ..target import LocalTarget
from ...strategies import RunStrategy
from robotmk.logger import RobotmkLogger
from robotmk.config import Config

import robot
from robot.rebot import rebot

from uuid import uuid4
import datetime

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
        self.retry_strategy = RetryStrategyFactory(self.suitecfg).create()
        self.uuid = uuid4()

    @property
    def is_disabled_by_flagfile(self):
        """The presence of a file DISABLED inside of a Robot suite will prevent
        Robotmk to execute the suite."""
        return self.path.joinpath("DISABLED").exists()

    @property
    def cmdline(self):
        # returns the command line to run a RF suite
        pass

    def run(self):
        # TODO: Skip a disabled suite & log it
        # TODO: write state with UUID and start_time
        # failed handling

        self.run_strategy.run()
        # TODO: hier Ausnahmen und die ganze Logik zur Robot-Ausführung hier rein packen?

    def get_now_as_dt(self):
        return datetime.now(local_tz)

    def get_now_as_epoch(self):
        return int(self.get_now_as_dt().timestamp())

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

    def output_filename(self, timestamp, attempt=None):
        """Create output file name. If attempt is given, it gets appended to the file name."""
        if attempt is None:
            suite_filename = "robotframework_%s_%s" % (self.id, timestamp)
        else:
            suite_filename = "robotframework_%s_%s_attempt-%d" % (
                self.id,
                timestamp,
                attempt,
            )
        return suite_filename

    def bump_output_filenames(self, attempt=None):
        """Parametrize the output files"""
        output_prefix = self.output_filename(str(self.timestamp), attempt)
        self.suite_dict["robot_params"].update(
            {
                "output": "%s_output.xml" % output_prefix,
                "log": "%s_log.html" % output_prefix,
            }
        )

    # Suite timestamp for filenames
    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, t):
        self._timestamp = t


# ----------------------------------------------------------------------------------------------
#   _ __ ___ ______ _____  _____  ___
#  | '__/ _ \______/ _ \ \/ / _ \/ __|
#  | | |  __/     |  __/>  <  __/ (__
#  |_|  \___|      \___/_/\_\___|\___|


class RetryStrategyFactory:
    """Factory for execution strategies"""

    def __init__(self, suitecfg):
        self.suitecfg = suitecfg

    def create(self):
        """Create the execution strategy"""
        strategy = self.suitecfg.get("retry_failed.strategy", "complete")
        if strategy == "complete":
            return CompleteRetry(self.suitecfg)
        elif strategy == "incremental":
            return IncrementalRetry(self.suitecfg)
        else:
            raise Exception("Unknown retry strategy: %s" % strategy)


class RetryStrategy(ABC):
    """Execution strategy interface for suites"""

    def __init__(self, suitecfg):
        self.suitecfg = suitecfg

    @abstractmethod
    def parametrize(self, suite):
        pass

    @abstractmethod
    def finalize_results(self):
        pass

    @property
    def max_attempts(self):
        """Maximum number of attempts to execute a suite (1st + retries)"""
        return 1 + self.suitecfg.get("retry_failed.retry_attempts", 0)


class CompleteRetry(RetryStrategy):
    """Execution strategy for suites with complete re-execution"""

    def __str__(self):
        return "Strategy: Complete"

    def parametrize(self):
        pass

    def finalize_results(self):
        """Only takes the last result into account"""
        # Pretty much the same method as in incremental strategy; however,
        # keep them separate to be able to change them independently
        self.suite.bump_output_filenames()
        outputfiles = self.suite._runner.glob_suite_outputfiles(self.suite)
        outputfiles.sort()
        self.suite._runner.logdebug(
            "Piled up the following result files of complete executions:"
        )
        filenames = [Path(f).name for f in outputfiles]
        for f in filenames:
            self.suite._runner.logdebug(" - %s" % f)
        # rebot wants to print out the generated file names on stdout; write to devnull
        devnull = open(os.devnull, "w")
        rebot(
            *outputfiles,
            outputdir=self.suite.outputdir,
            output=self.suite.output,
            log=self.suite.log,
            report=None,
            merge=True,
            stdout=devnull,
        )
        self.suite._runner.loginfo("Taking the last/best result as:")
        self.suite._runner.loginfo(" - %s" % self.suite.output)
        self.suite._runner.loginfo(" - %s" % self.suite.log)


class IncrementalRetry(RetryStrategy):
    """Provides methods to re-execute suites incrementally (no test interdependency)"""

    def __str__(self):
        return "Strategy: Incremental"

    def parametrize(self):
        """Parametrize the Robot command line which tests to re-execute"""
        # save the current output XML and use it for the rerun
        failed_xml = Path(self.suite.outputdir).joinpath(self.suite.output)
        self.suite.suite_dict["robot_params"].update({"rerunfailed": str(failed_xml)})
        # Attempt 2ff can be filtered, add the parameters to the Robot cmdline
        self.suite.suite_dict["robot_params"].update(self.suite.rerun_selection)

        self.suite._runner.loginfo(
            f"   Reading failed tests from '{failed_xml.name}', setting robot parameters for rexecution"
        )

    def finalize_results(self):
        """Merges the last and best test results into a new final result"""
        self.suite.bump_output_filenames()
        outputfiles = self.suite._runner.glob_suite_outputfiles(self.suite)
        outputfiles.sort()
        self.suite._runner.logdebug("Result files to merge:")
        filenames = [Path(f).name for f in outputfiles]
        for f in filenames:
            self.suite._runner.logdebug(" - %s" % f)
        # rebot wants to print out the generated file names on stdout; write to devnull
        devnull = open(os.devnull, "w")
        rebot(
            *outputfiles,
            outputdir=self.suite.outputdir,
            output=self.suite.output,
            log=self.suite.log,
            report=None,
            merge=True,
            stdout=devnull,
        )
        self.suite._runner.loginfo("Merged results of all reexecutions into:")
        self.suite._runner.loginfo(" - %s" % self.suite.output)
        self.suite._runner.loginfo(" - %s" % self.suite.log)
