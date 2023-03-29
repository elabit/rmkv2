from robotmk.rcc import RCCEnv
from .target import LocalTarget
from ..head import HeadStrategy
from robotmk.logger import RobotmkLogger


class RCCTarget(LocalTarget):
    def __init__(
        self,
        suiteid: str,
        config: dict,
        logger: RobotmkLogger,
    ):
        super().__init__(suiteid, config, logger)
