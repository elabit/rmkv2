from ..abstract import AbstractContext


class LocalContext(AbstractContext):
    def __init__(self):
        super().__init__()

    def load_config(self, defaults, ymlfile: str, varfile: str) -> None:
        """Load the config for local context.

        Local context can merge the config from
        - OS defaults
        - + YML file (default/custom = --yml)
        - + environment variables
        """
        self.config.set_defaults(defaults)
        self.config.read_yml_cfg(must_exist=True, path=ymlfile)
        self.config.read_cfg_vars(path=None)

    def run(self):
        # TODO: start the scheduler
        pass
