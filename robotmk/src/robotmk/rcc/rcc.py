import subprocess
import json
from pathlib import Path


class RCCEnv:
    def __init__(self, blueprint_path):
        self.blueprint_path = blueprint_path
        self.blueprint_hash = None

    def calculate_blueprint_hash(self):
        try:
            output = subprocess.check_output(
                ["rcc", "ht", "hash", self.blueprint_path], universal_newlines=True
            )
            self.blueprint_hash = output.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to calculate blueprint hash: {e.stderr.strip()}"
            )

    def is_environment_ready(self):
        if not self.blueprint_hash:
            self.calculate_blueprint_hash()
        try:
            output = subprocess.check_output(
                ["rcc", "ht", "spaces", "--filter", self.blueprint_hash],
                universal_newlines=True,
            )
            spaces = json.loads(output)
            return bool(spaces)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to check environment readiness: {e.stderr.strip()}"
            )

    def check_spaces(self):
        if not self.blueprint_hash:
            self.calculate_blueprint_hash()
        try:
            output = subprocess.check_output(
                ["rcc", "ht", "spaces", "--filter", self.blueprint_hash],
                universal_newlines=True,
            )
            spaces = json.loads(output)
            return spaces
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to check spaces: {e.stderr.strip()}")

    def create_environment(self, name, variables=None):
        if not self.blueprint_hash:
            self.calculate_blueprint_hash()
        cmd = ["rcc", "ht", "vars", "--blueprint", self.blueprint_hash, "--name", name]
        if variables:
            cmd.extend(["--vars", json.dumps(variables)])
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create environment: {e.stderr.strip()}")


class RCCDir:
    @staticmethod
    def is_rcc_compatible(abspath: str):
        """Returns True if the given suite folder is compatible with RCC.
        Such a suite dir must at least contain conda.yml and robot.yml.
        """
        path = Path(abspath)
        if path.joinpath("conda.yml").exists() and path.joinpath("robot.yml").exists():
            return True
        else:
            return False
