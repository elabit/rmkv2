from abc import ABC, abstractmethod


class HeadStrategy(ABC):
    def run(self):
        """Template method which bundles the methods to run."""
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


class Headless(HeadStrategy):
    """Executes a suite without any user interaction."""

    def prepare(self):
        pass

    def execute(self):
        # Call RobotFramework as in former times...
        pass

    def cleanup(self):
        pass


class WindowsScheduledTask(HeadStrategy):
    """Concrete class to run a suite with UI on Windows.

    This is done not by executing the suite itself, but by
    installing and running a Scheduled Task under the user which runs the current desktop.
    """

    def prepare(self):
        # create the scheduled task for the given user
        pass

    def execute(self):
        # run schtask.exe to run the task
        pass

    def cleanup(self):
        pass


class WindowsRDP(HeadStrategy):
    """Concrete class to run a suite in a loopback RDP session.

    This will require a Windows Server with RDP enabled and a proper
    MSTC license. Although there is https://github.com/stascorp/rdpwrap
    (https://www.anyviewer.com/how-to/windows-10-pro-remote-desktop-multiple-users-0427.html)
    """

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


class LinuxXVFB(HeadStrategy):
    """Executes a suite with a user interface on Linux."""

    def prepare(self):
        pass

    def execute(self):
        pass

    def cleanup(self):
        pass


class HeadFactory:
    """Factory for creating different head strategies.

    Strategies:
        - Headless
        - WindowsScheduledTask
        - WindowsRDP
        - LinuxXVFB
    """

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
                return WindowsScheduledTask()
            elif self._platform == "linux":
                return LinuxXVFB()
            else:
                raise ValueError("Unsupported platform: " + self._platform)
