from abc import ABC, abstractmethod
from robotmk.config import Config


class AbstractContext(ABC):
    """Abstract class for context objects. Context objects are used to
    encapsulate the different contexts in which robotmk can be run (local, specialagent, suite).
    """

    def __init__(self):
        self.config = Config()

    @abstractmethod
    def load_config(self, defaults, ymlfile: str, varfile: str) -> None:
        """Depening on the context strategy, the config object loads cfg from different sources."""
        raise NotImplementedError("Subclass must implement abstract method")

    @abstractmethod
    def run_default(self):
        """Encapsulates everything that needs to be done to
        run robotmk when it is run only with context, but without subcommand."""
        raise NotImplementedError("Subclass must implement abstract method")
