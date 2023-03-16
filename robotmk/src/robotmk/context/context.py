from .local.local import LocalContext
from .specialagent.specialagent import SpecialAgentContext
from .suite.suite import SuiteContext


class ContextFactory:
    def __init__(self, context) -> None:
        self.context = context

    def get_context(self) -> None:
        if self.context == "local":
            return LocalContext()
        elif self.context == "specialagent":
            return SpecialAgentContext()
        elif self.context == "suite":
            return SuiteContext()
        else:
            # TODO: catch this error
            pass
