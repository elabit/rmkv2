from .local.local import LocalContext
from .specialagent.specialagent import SpecialAgentContext
from .suite.suite import SuiteContext


class ContextFactory:
    def __init__(self, contextname) -> None:
        self.contextname = contextname

    def get_context(self) -> None:
        if self.contextname == "local":
            return LocalContext()
        elif self.contextname == "specialagent":
            return SpecialAgentContext()
        elif self.contextname == "suite":
            return SuiteContext()
        else:
            # TODO: catch this error
            pass
