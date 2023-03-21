from abc import ABC, abstractmethod


class AbstractExecutor:
    """Base class for the executor.

    This is the abstraction class for the executors of
    - local suites (-> SuiteRunner)
    - remote suites=API calls (-> )"""

    def __init__(self, config, *args, **kwargs):
        self.config = config

    @abstractmethod
    def execute(self):
        """Abstract method for the default run action of the executor"""
        pass
