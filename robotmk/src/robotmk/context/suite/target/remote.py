from .target import Target
from ..head import HeadStrategy


class RemoteTarget(Target):
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)

    def run(self):
        pass

    def output(self):
        pass
