import os
from abc import ABC, abstractmethod
from robot.rebot import rebot
from pathlib import Path


class RetryStrategyFactory:
    """Factory for execution strategies"""

    def __init__(self, target):
        self.target = target
        self.run = self.target.run_strategy.run

    def create(self):
        """Create the execution strategy"""
        strategy = self.target.suitecfg.get("retry_failed.strategy", "complete")
        if strategy == "complete":
            return CompleteRetry(self.target)
        elif strategy == "incremental":
            return IncrementalRetry(self.target)
        else:
            raise Exception("Unknown retry strategy: %s" % strategy)


class RetryStrategy(ABC):
    """Execution strategy interface for suites"""

    def __init__(self, target):
        self.target = target
        self.target.attempt = 1

    @abstractmethod
    def parametrize(self):
        pass

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def finalize_results(self):
        pass

    @property
    def max_attempts(self):
        """Maximum number of attempts to execute a suite (1st + retries)"""
        return 1 + self.target.suitecfg.get("retry_failed.retry_attempts", 0)


class CompleteRetry(RetryStrategy):
    """Execution strategy for suites with complete re-execution"""

    def __str__(self):
        return "Strategy: Complete"

    def parametrize(self):
        pass

    def run(self):
        """Run the suite and retry cmpletely if necessary."""
        # bla bla bla
        self.target.run_strategy.run()

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

    def run(self):
        """Run the suite and retry failed tests if necessary."""
        for attempt in range(1, self.max_attempts):
            # if self.max_attempts > 1:
            #     self._runner.loginfo(
            #         f" > Starting attempt {attempt}/max {max_exec} ({str(self.reexecution_strategy)})"
            #     )
            # else:
            #     self._runner.loginfo(f" > Starting suite...")
            self.target.attempt = attempt

            # TODO: log the cli args
            rc = self.target.run_strategy.run()
            # if self.max_attempts == 1 or (self.max_attempts > 1 and rc == 0):
            if self.max_attempts == 1 or (self.target.attempt == 1 and rc == 0):
                # if only one attempt allowed or 1st attempt was OK, we are done
                break
            else:
                # more attempts allowed and 1st attempt was not OK
                if rc == 0:
                    # this retry was OK, get out here
                    self.reexecution_strategy.finalize_results()
                    break
                else:
                    if self.target.attempt < self.max_attempts:
                        # Chance for next try. Attempt gets increased, output files get bumped
                        failed_xml = Path(
                            self.target.config.get("common.outdir")
                        ).joinpath(self.target.output_xml)
                        self.target.robotmk_params.update(
                            {"rerunfailed": str(failed_xml)}
                        )
                        rerun_selection = self.target.suitecfg.get(
                            "retry_failed.rerun_selection", {}
                        ).asdict()
                        self.target.robotmk_params.update(rerun_selection)
                        pass
                    else:
                        # ...GAME OVER! => MERGE
                        # TODO: logging
                        # self._runner.loginfo(
                        #     "   Even the last attempt was unsuccessful!"
                        # )
                        self.reexecution_strategy.finalize_results()

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
