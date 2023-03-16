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
        pass

    @abstractmethod
    def run(self):
        """The run method encapsulates everything that needs to be done to
        run robotmk in one of the three contexts."""
        pass
