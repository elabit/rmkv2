from ..abstract import AbstractContext


class SpecialAgentContext(AbstractContext):
    def __init__(self):
        super().__init__()

    def load_config(self, defaults, ymlfile: str, varfile: str) -> None:
        """Load the config for specialagent context.

        This context can merge the config from
        - OS defaults
        - + var file (= --vars)
        - + environment variables

        (There is no YML file for specialagent context!)
        """
        self.config.set_defaults(defaults)
        self.config.read_cfg_vars(path=varfile)

    def run(self):
        # TODO: start the sequencer
        pass
