from robotmk.rcc import RCCEnv
from .target import LocalTarget
from ..strategies import RunStrategy
from robotmk.logger import RobotmkLogger
from robotmk.config import Config


class RCCTarget(LocalTarget):
    def __init__(
        self,
        suiteid: str,
        config: dict,
        logger: RobotmkLogger,
    ):
        super().__init__(suiteid, config, logger)

    @property
    def cmdline(self):
        # returns the command line to run a RCC task
        pass

    def run(self):
        # When running Robotmk inside of a RCC, it must be told not
        # to use RCC again. (Otherwise, it would run RCC inside of RCC.)
        self.config.set("suites.suite_default_rcc.run.rcc", False)

        self.run_strategy.run()
