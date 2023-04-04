from abc import ABC, abstractmethod
from dotmap import DotMap
import platform
from robotmk.logger import RobotmkLogger
import subprocess


class RunStrategy(ABC):
    def __init__(self, target) -> None:
        self.target = target

        # self.suiteuname = suiteuname
        # self.config = config
        # self._logger = logger
        # self.debug = self._logger.debug
        # self.info = self._logger.info
        # self.warning = self._logger.warning
        # self.error = self._logger.error
        # self.critical = self._logger.critical

    def run(self):
        """Template method which bundles the linked methods to run.

        The concrete strategy selectivly overrides the methods to implement."""
        rc = max(self.prepare(), self.execute(), self.cleanup())
        return rc

    @abstractmethod
    def prepare(self) -> int:
        """Prepares the given suite."""
        pass

    @abstractmethod
    def execute(self) -> int:
        """Execute the the given suite."""
        pass

    @abstractmethod
    def cleanup(self) -> int:
        """Cleans up the given suite."""
        pass


class Runner(RunStrategy):
    """This Strategy is the only one which executes a 'job' in fact.

    - run a Robot Framework Suite
    - run a RCC task
    """

    def __init__(self, target) -> None:
        super().__init__(target)

    def prepare(self) -> int:
        # nothing to do
        return 0

    def execute(self) -> int:
        result = subprocess.run(self.target.command, capture_output=True)
        stdout_str = result.stdout.decode("utf-8").splitlines()
        stderr_str = result.stderr.decode("utf-8").splitlines()
        result_dict = {
            "args": result.args,
            "returncode": result.returncode,
            "stdout": stdout_str,
            "stderr": stderr_str,
        }
        # TODO: log console output? Save it anyway because a a fatal RF error must be tracable.
        self.target.console_results[self.target.attempt] = result_dict
        return result.returncode

    def cleanup(self) -> int:
        # nothing to do
        return 0

    # def _write_console_output(self, result):


class WindowsTask(RunStrategy):
    """Parent class for Single and Multi desktop strategies.

    Both have in common that they need to create a scheduled task."""

    def __init__(self, target) -> None:
        super().__init__(target)

    @abstractmethod
    def prepare(self) -> int:
        pass

    @abstractmethod
    def execute(self) -> int:
        pass

    @abstractmethod
    def cleanup(self) -> int:
        pass


class WindowsSingleDesktop(WindowsTask):
    """Concrete class to run a suite with UI on Windows.

    ....
    """

    def __init__(self, target) -> None:
        super().__init__(target)

    def prepare(self) -> int:
        # create the scheduled task for the given user
        pass

    def execute(self) -> int:
        # run schtask.exe to run the task
        pass

    def cleanup(self) -> int:
        pass


class WindowsMultiDesktop(WindowsTask):
    """Concrete class to run a suite in a loopback RDP session.

    This will require a Windows Server with RDP enabled and a proper
    MSTC license. Although there is https://github.com/stascorp/rdpwrap
    (https://www.anyviewer.com/how-to/windows-10-pro-remote-desktop-multiple-users-0427.html)
    """

    def __init__(self, target) -> None:
        super().__init__(target)

    def prepare(self) -> int:
        # create RDP file:
        # rdp_file = "loopback.rdp"
        # with open(rdp_file, "w") as f:
        #     f.write(f"""\
        # username:s:{username}
        # password 51:b:{password}
        # full address:s:127.0.0.2
        # """)
        pass

    def execute(self) -> int:
        # Launch the RDP session with the specified command
        # os.system(f"mstsc /v:127.0.0.2 /f /w:800 /h:600 /v:127.0.0.2 /u:{username} /p:{password} /v:{rdp_file} /start:{command}")
        # os.system(f'mstsc /v:127.0.0.1 /f /w:800 /h:600 /u:{username} /p:{password} /v:127.0.0.1 /w:800 /h:600 /v:127.0.0.1 /w:800 /h:600 /admin /restrictedAdmin cmd /c "{command}"')

        pass

    def cleanup(self) -> int:
        # Close the RDP session
        # os.system(f'tscon /dest:console')
        pass


class LinuxMultiDesktop(RunStrategy):
    """Executes a suite with a user interface on Linux."""

    def __init__(self, target) -> None:
        super().__init__(target)

    def prepare(self) -> int:
        pass

    def execute(self) -> int:
        pass

    def cleanup(self) -> int:
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

    def __init__(self, target):
        self.target = target

    def create(self) -> RunStrategy:
        """Creates a run strategy based on the given parameters.

        Returns:
            RunStrategy: The run strategy to use.
        """
        mode = self.target.config.get(
            "suites.%s.run.mode" % self.target.config.get("common.suiteuname")
        )
        _platform = platform.system().lower()
        if mode == "default":
            return Runner(self.target)
        elif mode == "windows-1desktop" and _platform == "windows":
            return WindowsSingleDesktop(self.target)
        elif mode == "windows-ndesktop" and _platform == "windows":
            return WindowsMultiDesktop(self.target)
        elif mode == "linux-ndesktop" and _platform == "linux":
            return LinuxMultiDesktop(self.target)
        else:
            raise ValueError(
                "Invalid combination of platform (%s) and run mode (%s)."
                % (_platform, mode)
            )
