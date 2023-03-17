from ..abstract import AbstractContext


class SuiteContext(AbstractContext):
    def __init__(self):
        super().__init__()

    def load_config(self, defaults, ymlfile: str, varfile: str) -> None:
        """Load the config for suite context.

        Suite context can merge the config from
        - OS defaults
        - + YML file (default/custom = --yml)
        - + var file (= --vars)
        - + environment variables
        """
        self.config.set_defaults(defaults)
        self.config.read_yml_cfg(must_exist=False)
        self.config.read_cfg_vars(path=varfile)

    def run_default(self):
        """Implements the default action for suite context."""
        # TODO: execute one single suite
        print("Suite context default action = execute single suite ")
        pass

    def run(self):
        """Implements the action for suite context."""
        print("Suite context action")
        pass

    def produce_agent_output(self):
        """Implements the agent output for local context."""
        # NOT IMPLEMENTED
        # print("Local context agent output")
        pass
