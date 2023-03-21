from .abstract import AbstractExecutor
import time


class SuiteRunner(AbstractExecutor):
    def __init__(self, config, *args, **kwargs):
        super().__init__(config)

    def execute(self):
        """Runs a single suite, either locally or remotely (via API call)."""

        print(self.config.common.tmpdir)
        print("SuiteRunner.run()")
        time.sleep(5)
        # iteriere

        # Setze environment variable common_suite = suiteA
        # erzeuge Robotmk("suite"), übergebe Config (muss nicht mehr geladen werden)

        pass
