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

    def run_default(self):
        """Implements the default action for specialagent context."""
        # TODO: start the sequencer
        print("Specialagent context default action = trigger APIs and output")
        pass

    def run(self):
        """Implements the run action for specialagent context."""
        print("Specialagent context run action")
        pass

    def produce_agent_output(self):
        """Implements the agent output for local context."""
        print("Specialagent context output")
        pass
