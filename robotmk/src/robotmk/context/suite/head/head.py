from abc import ABC, abstractmethod


class HeadStrategy(ABC):
    @abstractmethod
    def prepare(self, suite):
        """Prepares the given suite."""
        pass

    @abstractmethod
    def execute(self, suite):
        """Executes the given suite."""
        pass

    @abstractmethod
    def cleanup(self, suite):
        """Cleans up the given suite."""
        pass


class HeadedWindows(HeadStrategy):
    """Executes a suite with a user interface on Windows."""

    def prepare(self, suite):
        pass

    def execute(self, suite):
        pass

    def cleanup(self, suite):
        pass


class HeadedLinux(HeadStrategy):
    """Executes a suite with a user interface on Linux."""

    def prepare(self, suite):
        pass

    def execute(self, suite):
        pass

    def cleanup(self, suite):
        pass


class Headless(HeadStrategy):
    """Executes a suite without any user interaction."""

    def prepare(self, suite):
        pass

    def execute(self, suite):
        pass

    def cleanup(self, suite):
        pass


class HeadFactory:
    """Factory for creating head strategies.

    Creation:
        headless (bool): Whether the suite should be executed headless.
        platform (str): The platform the suite should be executed on."""

    def __init__(self, platform: str, headless: bool):
        self._platform = platform.lower()
        self._headless = headless

    def create_head_strategy(self) -> HeadStrategy:
        """Creates a head strategy based on the given parameters.

        Returns:
            HeadStrategy: The head strategy to use.
        """
        if self._headless:
            return Headless()
        else:
            if self._platform == "windows":
                return HeadedWindows()
            elif self._platform == "linux":
                return HeadedLinux()
            else:
                raise ValueError("Unsupported platform: " + self._platform)
