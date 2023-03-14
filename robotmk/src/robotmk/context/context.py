from abc import ABC, abstractmethod
from robotmk.config import Config
import click


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


class AbstractContext(ABC):
    """Abstract class for context objects. Context objects are used to
    encapsulate the different contexts in which robotmk can be run (local, specialagent, suite).
    """

    def __init__(self):
        self.config = Config()

    @abstractmethod
    def load_config():
        pass

    @abstractmethod
    def run(self):
        """The run method encapsulates everything that needs to be done to
        run robotmk in one of the three contexts."""
        pass
