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
        # TODO: Configure the Target to the needs of
        # a RCC execution.
        self.run_strategy.cmd = "foo"
        self.run_strategy.run()
