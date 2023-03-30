from .target import Target
from ..strategies import RunStrategy
from robotmk.logger import RobotmkLogger


class RemoteTarget(Target):
    def __init__(self, name: str, config: dict, logger: RobotmkLogger):
        super().__init__(name, config)

    def run(self):
        pass

    def output(self):
        pass
