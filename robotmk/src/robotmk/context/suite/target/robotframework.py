from .target import LocalTarget
from ..strategies import RunStrategy
from robotmk.logger import RobotmkLogger
from robotmk.config import Config


class RobotFrameworkTarget(LocalTarget):
    def __init__(
        self,
        suiteid: str,
        config: dict,
        logger: RobotmkLogger,
    ):
        super().__init__(suiteid, config, logger)

    def run(self):
        # TODO: Configure the Target to the needs of
        # a Robotframework execution.
        self.run_strategy.run()
        # TODO: hier Ausnahmen und die ganze Logik zur Robot-Ausführung hier rein packen?
