from abc import ABC, abstractmethod
from ..head import HeadStrategy


class Target(ABC):
    """A Target defines the environment where a suite gets executed.

    It's the abstraction of either
    - a local Robot suite or ("target: local")
    - an API call to an external platform ("target: remote") like Robocorp or Kubernetes
    """

    def __init__(self, suite_id: str, config):
        self.suite_id = suite_id
        self.config = getattr(config.suites, suite_id)

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def output(self):
        pass


# ---


class LocalTarget(Target):
    def __init__(self, name: str, config: dict, head_strategy: HeadStrategy):
        super().__init__(name, config)
        self.head_strategy = head_strategy

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def output(self):
        pass


# ---


# class LocalSuite(Target):
#     """A single Robot Framework suite on Linux and Windows.

#     Also encapsulates the implementation details of
#     whether to run the suite with the OS Python or within
#     a RCC environment."""

#     # self.suite_cfg = getattr(self.config.suites, self.suitename)

#     def __init__(self, name: str, config: dict):
#         super().__init__(name, config)
#         self._set_python_strategy()
#         self._set_head_strategy()
#         pass

#     @property
#     def abspath(self):
#         return Path(self.config.path).resolve()

#     def run(self):
#         pass

#     def _set_python_strategy(self):
#         """Sets the python execution strategy.

#         Execution with `RCC` is possible when
#         # 1. the suite is RCC compatible (conda.yml)
#         # 2. feature is available (binary check)
#         # 3. RCC is not disallowed in robotmk.yml
#         # 4. `share-python` is not set on cli (would enforce the same Python)"""

#     def _set_head_strategy(self):
#         """Sets the strategy for this suite:
#         - HeadedWinExecStrategy
#         - HeadedLinExecutionStrategy
#         - HeadlessExecutionStrategy"""
#         self._strategy = strategy
#         self.prepare = self._strategy.prepare
#         self.execute = self._strategy.execute
#         self.cleanup = self._strategy.cleanup


# class RemoteSuite(Target):
#     """A single Robot Framework suite on a remote platform.

#     Its execution is triggered via an API call."""

#     def __init__(self, name: str, config: dict):
#         super().__init__(name)
#         self.config = config

#     def get_jobs_running(self):
#         """Returns the number of running jobs currently."""
#         pass

#     def kill_job(self):
#         pass
