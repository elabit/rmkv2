from abc import ABC, abstractmethod
from dotmap import DotMap
import platform
from robotmk.logger import RobotmkLogger


class RunStrategy(ABC):
    def __init__(self, suiteid: str, config: DotMap, logger: RobotmkLogger) -> None:
        self.suiteid = suiteid
        self.config = config
        self._logger = logger
        self.debug = self._logger.debug
        self.info = self._logger.info
        self.warning = self._logger.warning
        self.error = self._logger.error
        self.critical = self._logger.critical

    def run(self):
        """Template method which bundles the linked methods to run.

        The concrete strategy selectivly overrides the methods to implement."""
        self.prepare()
        self.execute()
        self.cleanup()

    @abstractmethod
    def prepare(self):
        """Prepares the given suite."""
        pass

    @abstractmethod
    def execute(self):
        """Execute the the given suite."""
        pass

    @abstractmethod
    def cleanup(self):
        """Cleans up the given suite."""
        pass


class Runner(RunStrategy):
    """This Strategy is the only one which executes a 'job' in fact.

    - run a Robot Framework Suite
    - run a RCC task
    """

    def __init__(self, suiteid: str, config: DotMap, logger: RobotmkLogger) -> None:
        super().__init__(suiteid, config, logger)

    def prepare(self):
        pass

    def execute(self):
        # Call a command.
        pass

    def cleanup(self):
        pass


class WindowsTask(RunStrategy):
    """Parent class for Single and Multi desktop strategies.

    Both have in common that they need to create a scheduled task."""

    def __init__(self, suiteid: str, config: DotMap, logger: RobotmkLogger) -> None:
        super().__init__(suiteid, config, logger)

    @abstractmethod
    def prepare(self):
        pass

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def cleanup(self):
        pass


class WindowsSingleDesktop(WindowsTask):
    """Concrete class to run a suite with UI on Windows.

    ....
    """

    def __init__(self, suiteid: str, config: DotMap, logger: RobotmkLogger) -> None:
        super().__init__(suiteid, config, logger)

    def prepare(self):
        # create the scheduled task for the given user
        pass

    def execute(self):
        # run schtask.exe to run the task
        pass

    def cleanup(self):
        pass


class WindowsMultiDesktop(WindowsTask):
    """Concrete class to run a suite in a loopback RDP session.

    This will require a Windows Server with RDP enabled and a proper
    MSTC license. Although there is https://github.com/stascorp/rdpwrap
    (https://www.anyviewer.com/how-to/windows-10-pro-remote-desktop-multiple-users-0427.html)
    """

    def __init__(self, suiteid: str, config: DotMap, logger: RobotmkLogger) -> None:
        super().__init__(suiteid, config, logger)

    def prepare(self):
        # create RDP file:
        # rdp_file = "loopback.rdp"
        # with open(rdp_file, "w") as f:
        #     f.write(f"""\
        # username:s:{username}
        # password 51:b:{password}
        # full address:s:127.0.0.2
        # """)
        pass

    def execute(self):
        # Launch the RDP session with the specified command
        # os.system(f"mstsc /v:127.0.0.2 /f /w:800 /h:600 /v:127.0.0.2 /u:{username} /p:{password} /v:{rdp_file} /start:{command}")
        # os.system(f'mstsc /v:127.0.0.1 /f /w:800 /h:600 /u:{username} /p:{password} /v:127.0.0.1 /w:800 /h:600 /v:127.0.0.1 /w:800 /h:600 /admin /restrictedAdmin cmd /c "{command}"')

        pass

    def cleanup(self):
        # Close the RDP session
        # os.system(f'tscon /dest:console')
        pass


class LinuxMultiDesktop(RunStrategy):
    """Executes a suite with a user interface on Linux."""

    def __init__(self, suiteid: str, config: DotMap, logger: RobotmkLogger) -> None:
        super().__init__(suiteid, config, logger)

    def prepare(self):
        pass

    def execute(self):
        pass

    def cleanup(self):
        pass


#    __           _
#   / _|         | |
#  | |_ __ _  ___| |_ ___  _ __ _   _
#  |  _/ _` |/ __| __/ _ \| '__| | | |
#  | || (_| | (__| || (_) | |  | |_| |
#  |_| \__,_|\___|\__\___/|_|   \__, |
#                                __/ |
#                               |___/


class RunStrategyFactory:
    """Factory for creating the proper run strategy for a given suite/OS."""

    def __init__(self, suiteid: str, config: DotMap, logger: RobotmkLogger):
        self.suiteid = suiteid
        self.config = config
        self._logger = logger
        # TODO: Boilerplate alarm
        self.debug = self._logger.debug
        self.info = self._logger.info
        self.warning = self._logger.warning
        self.error = self._logger.error
        self.critical = self._logger.critical
        self.platform = platform.system().lower()

    def create_run_strategy(self) -> RunStrategy:
        """Creates a run strategy based on the given parameters.

        Returns:
            RunStrategy: The run strategy to use.
        """
        mode = self.config.get("suites.%s.run.mode" % self.suiteid)
        if mode == "default":
            return Runner(self.suiteid, self.config, self._logger)
        elif mode == "windows-1desktop" and self.platform == "windows":
            return WindowsSingleDesktop(self.suiteid, self.config, self._logger)
        elif mode == "windows-ndesktop" and self.platform == "windows":
            return WindowsMultiDesktop(self.suiteid, self.config, self._logger)
        elif mode == "linux-ndesktop" and self.platform == "linux":
            return LinuxMultiDesktop(self.suiteid, self.config, self._logger)
        else:
            raise ValueError(
                "Invalid combination of platform (%s) and run mode (%s)."
                % (self.platform, mode)
            )
