from abc import ABC, abstractmethod


class AbstractExecutor:
    """Abstract class for the executor"""

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def run(self):
        """Abstract method for the default run action of the executor"""
        pass
