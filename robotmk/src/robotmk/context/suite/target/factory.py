from pathlib import Path
from robotmk.logger import RobotmkLogger
from .abstract import Target
from .local import LocalTarget
from .remote import RemoteTarget
from .robotframework import RobotFrameworkTarget
from .rcc import RCCTarget


class TargetFactory:
    def __init__(self, suiteuname: str, config, logger: RobotmkLogger):
        self.suiteuname = suiteuname
        self.config = config
        self.logger = logger

    def create(self) -> Target:
        """Create a target object."""
        otarget = None
        suitecfg = self.config.get("suites.%s" % self.suiteuname)
        if suitecfg == None:
            self.error("Suite '%s' is not part of the config!" % self.suiteuname)

        target_name = suitecfg.get("run.target")
        if target_name == "local":
            path = Path(self.config.get("common.robotdir")).joinpath(
                suitecfg.get("path")
            )
            if path.exists():
                if suitecfg.get("run.rcc", False):
                    otarget = RCCTarget(self.suiteuname, self.config, self.logger)
                else:
                    otarget = RobotFrameworkTarget(
                        self.suiteuname, self.config, self.logger
                    )
            else:
                # TBD: check this if this gets logged...
                self.error("Suite path does not exist: " + str(path))
        elif target_name == "remote":
            otarget = RemoteTarget(self.suiteuname, self.config, self.logger)
        else:
            self.error("Unknown target type for suite %s!" % self.suiteuname)
        return otarget
