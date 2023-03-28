from .target import LocalTarget
from ..head import HeadStrategy


class SharedPythonTarget(LocalTarget):
    def __init__(self, name: str, config: dict, head_strategy: HeadStrategy):
        super().__init__(name, config, head_strategy)

    def run(self):
        pass

    def output(self):
        pass
