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

    def run(self):
        # Change the suite config so that inside of the RCC run
        # a Robot FrameworkTarget is created.
        self.config.set("suites.suite_default_rcc.run.rcc", "foo")
        self.suitecfg.run.rcc = False

        self.run_strategy.run()
