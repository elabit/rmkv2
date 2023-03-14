from ..context import AbstractContext


class SuiteContext(AbstractContext):
    def __init__(self):
        pass

    def load_config(self, defaults):
        self.config.set_defaults(defaults)
        self.config.read_env_cfg()

    def run(self):
        # TODO: execute one single suite
        pass
