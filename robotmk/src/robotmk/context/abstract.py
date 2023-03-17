from abc import ABC, abstractmethod
from robotmk.config.config import Config


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
    def refresh_config(self):
        """Load the config again, e.g. after a change in the config file."""
        raise NotImplementedError("Subclass must implement abstract method")

    @abstractmethod
    def run_default(self):
        """Encapsulates everything that needs to be done to
        run robotmk when it is run only with context, but without subcommand."""
        raise NotImplementedError("Subclass must implement abstract method")

    @abstractmethod
    def run(self):
        """Encapsulates everything that needs to be done to run robotmk."""
        raise NotImplementedError("Subclass must implement abstract method")

    @abstractmethod
    def produce_agent_output(self):
        """Encapsulates everything that needs to be done to produce agent output."""
        raise NotImplementedError("Subclass must implement abstract method")
