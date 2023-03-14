from ..context import AbstractContext


class LocalContext(AbstractContext):
    def __init__(self):
        super().__init__()

    def load_config(self, defaults):
        self.config.set_defaults(defaults)
        self.config.read_yml_cfg(must_exist=True)
        self.config.read_env_cfg()

    def run(self):
        # TODO: start the scheduler
        pass
