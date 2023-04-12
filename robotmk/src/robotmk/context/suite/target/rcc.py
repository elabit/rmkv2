from .target import LocalTarget
from ..strategies import RunStrategy
from robotmk.logger import RobotmkLogger
from robotmk.config import Config


class RCCTarget(LocalTarget):
    def __init__(
        self,
        suiteuname: str,
        config: dict,
        logger: RobotmkLogger,
    ):
        super().__init__(suiteuname, config, logger)

    def __str__(self) -> str:
        return "rcc"

    @property
    def command(self):
        """The command will be used by the Run strategy (self.target.command).

        In RCC target, the commandline gets buuilt to execute a RCC task (=Robotmk inside of RCC)
        """
        arglist = [
            "rcc",
            "task",
            "run",
            "--controller",
            "robotmk",
            "--space",
            self.suiteuname,
            "-t",
            "robotmk",
            "-r",
            str(self.path.joinpath("robot.yaml")),
        ]

        return arglist

    def run(self):
        # Before we blow up the whole thing, we should check if the suite is RCC compatible and allowed to run
        if self.is_disabled_by_flagfile:
            # TODO: Log skipped
            # reason = self.get_disabled_reason()
            return
        if not self.is_rcc_compatible:
            # TODO: log suite not compatible with RCC
            pass
        else:
            # When running Robotmk inside of a RCC, it must be told not
            # to use RCC again. (Otherwise, it would run RCC inside of RCC.)
            self.config.set("suitecfg.run.rcc", False)
            # The wrapping RCC process gives his uuid to the inner Robotmk process
            self.config.set("suitecfg.uuid", self.uuid)
            self.config.to_environment()
            self.rc = self.run_strategy.run()

            b'"/home/simonmeggle/Documents/01_dev/rmkv2/agent/robots/suiteA/robot.yaml" as robot.yaml is:\n# For more details on the format and content:\n# https://github.com/robocorp/rcc/blob/master/docs/recipes.md#what-is-in-robotyaml\n\ntasks:\n  # Task names here are used when executing the bots, so renaming these is recommended.\n  robotmk:\n    shell: robotmk\n\ncondaConfigFile: conda.yaml\n\nenvironmentConfigs:\n  - environment_windows_amd64_freeze.yaml\n  - environment_linux_amd64_freeze.yaml\n  - environment_darwin_amd64_freeze.yaml\n  - conda.yaml\n\nartifactsDir: output  \n\nPATH:\n  - .\nPYTHONPATH:\n  - .\n\nignoreFiles:\n  - .gitignore\n\n####  Progress: 01/13  v11.30.0     0.002s  Fresh [private mode] holotree environment 1fd704a1-107a-6a6d-5077-637f69e4e792.\n####  Progress: 02/13  v11.30.0     0.007s  Holotree blueprint is "bf7f8a568809a6ca" [linux_amd64].\n####  Progress: 12/13  v11.30.0     0.141s  Restore space from library [with 7 workers].\nInstallation plan is: /home/simonmeggle/robocorp/holotree/d7e2678_716b162_694a8d27/rcc_plan.log\nEnvironment configuration descriptor is: /home/simonmeggle/robocorp/holotree/d7e2678_716b162_694a8d27/identity.yaml\n####  Progress: 13/13  v11.30.0     0.702s  Fresh holotree done [with 7 workers].\nWanted  Version  Origin  |  No.  |  Available         Version    Origin       |  Status\n------  -------  ------  +  ---  +  ---------         -------    ------       +  ------\n-       -        -       |    1  |  _libgcc_mutex     0.1        conda-forge  |  N/A\n-       -        -       |    2  |  _openmp_mutex     4.5        conda-forge  |  N/A\n-       -        -       |    3  |  bzip2             1.0.8      conda-forge  |  N/A\n-       -        -       |    4  |  ca-certificates   2022.12.7  conda-forge  |  N/A\n-       -        -       |    5  |  ld_impl_linux-64  2.40       conda-forge  |  N/A\n-       -        -       |    6  |  libffi            3.4.2      conda-forge  |  N/A\n-       -        -       |    7  |  libgcc-ng         12.2.0     conda-forge  |  N/A\n-       -        -       |    8  |  libgomp           12.2.0     conda-forge  |  N/A\n-       -        -       |    9  |  libnsl            2.0.0      conda-forge  |  N/A\n-       -        -       |   10  |  libsqlite         3.40.0     conda-forge  |  N/A\n-       -        -       |   11  |  libuuid           2.38.1     conda-forge  |  N/A\n-       -        -       |   12  |  libzlib           1.2.13     conda-forge  |  N/A\n-       -        -       |   13  |  ncurses           6.3        conda-forge  |  N/A\n-       -        -       |   14  |  openssl           3.1.0      conda-forge  |  N/A\n-       -        -       |   15  |  pip               22.1.2     conda-forge  |  N/A\n-       -        -       |   16  |  psutil            5.9.4      pypi         |  N/A\n-       -        -       |   17  |  python            3.9.13     conda-forge  |  N/A\n-       -        -       |   18  |  readline          8.2        conda-forge  |  N/A\n-       -        -       |   19  |  robotmk           0.0.44     pypi         |  N/A\n-       -        -       |   20  |  setuptools        67.6.1     conda-forge  |  N/A\n-       -        -       |   21  |  sqlite            3.40.0     conda-forge  |  N/A\n-       -        -       |   22  |  tk                8.6.12     conda-forge  |  N/A\n-       -        -       |   23  |  tzdata            2023c      conda-forge  |  N/A\n-       -        -       |   24  |  wheel             0.40.0     conda-forge  |  N/A\n-       -        -       |   25  |  xz                5.2.6      conda-forge  |  N/A\n------  -------  ------  +  ---  +  ---------         -------    ------       +  ------\nWanted  Version  Origin  |  No.  |  Available         Version    Origin       |  Status\n\n--\nTraceback (most recent call last):\n  File "/home/simonmeggle/robocorp/holotree/d7e2678_716b162_694a8d27/bin/robotmk", line 5, in <module>\n    from robotmk.cli.cli import main\n  File "/home/simonmeggle/robocorp/holotree/d7e2678_716b162_694a8d27/lib/python3.9/site-packages/robotmk/cli/cli.py", line 5, in <module>\n    import click\nModuleNotFoundError: No module named \'click\'\nError: exit status 1\n'

    @property
    def is_rcc_compatible(self):
        """Returns True if the given suite folder is compatible with RCC.
        Such a suite dir must at least contain conda.yml and robot.yml.
        """
        if (
            self.path.joinpath("conda.yaml").exists()
            and self.path.joinpath("robot.yaml").exists()
        ):
            return True
        else:
            return False

    # def calculate_blueprint_hash(self):
    #     try:
    #         output = subprocess.check_output(
    #             ["rcc", "ht", "hash", self.blueprint_path], universal_newlines=True
    #         )
    #         self.blueprint_hash = output.strip()
    #     except subprocess.CalledProcessError as e:
    #         raise RuntimeError(
    #             f"Failed to calculate blueprint hash: {e.stderr.strip()}"
    #         )

    # def is_environment_ready(self):
    #     if not self.blueprint_hash:
    #         self.calculate_blueprint_hash()
    #     try:
    #         output = subprocess.check_output(
    #             ["rcc", "ht", "spaces", "--filter", self.blueprint_hash],
    #             universal_newlines=True,
    #         )
    #         spaces = json.loads(output)
    #         return bool(spaces)
    #     except subprocess.CalledProcessError as e:
    #         raise RuntimeError(
    #             f"Failed to check environment readiness: {e.stderr.strip()}"
    #         )

    # def check_spaces(self):
    #     if not self.blueprint_hash:
    #         self.calculate_blueprint_hash()
    #     try:
    #         output = subprocess.check_output(
    #             ["rcc", "ht", "spaces", "--filter", self.blueprint_hash],
    #             universal_newlines=True,
    #         )
    #         spaces = json.loads(output)
    #         return spaces
    #     except subprocess.CalledProcessError as e:
    #         raise RuntimeError(f"Failed to check spaces: {e.stderr.strip()}")

    # def create_environment(self, name, variables=None):
    #     if not self.blueprint_hash:
    #         self.calculate_blueprint_hash()
    #     cmd = ["rcc", "ht", "vars", "--blueprint", self.blueprint_hash, "--name", name]
    #     if variables:
    #         cmd.extend(["--vars", json.dumps(variables)])
    #     try:
    #         subprocess.check_call(cmd)
    #     except subprocess.CalledProcessError as e:
    #         raise RuntimeError(f"Failed to create environment: {e.stderr.strip()}")
