"""This module provides a simple way to read configuration from different sources: 
- YML file
- variables file
- environment variables

There is a special order in which the sources are read:
- 1. OS defaults for each supported OS (Linux, Windows)
- 2. config from file, either
    - a) YML config, either
        - the default config file (robotmk.yml)
        - or a custom config file (given as parameter --yml)
    OR
    - b) variable file (given as parameter --vars)
- 3. environment variables

| context       | yml    | vars |
| ---           | ---    | ---  |
| local         | X      |      |
| suite         | X      | X    |
| specialagent  |        | X    |


"""

# TODO: print environment

import os
import yaml
import mergedeep
from typing import Union

# from collections import namedtuple
from pathlib import Path
from .yml import RobotmkConfigSchema

# TODO: add config validation


class Config:
    def __init__(self, envvar_prefix="ROBOTMK"):
        self._config = {}
        self.envvar_prefix = envvar_prefix
        self.default_cfg = {}
        self.yml_config = {}
        self.env_config = {}

    # 1. Defaults (common/OS specific)
    def set_defaults(self, os_defaults: dict = None) -> None:
        """Sets the defaults for the current OS."""
        self.default_cfg["common"] = {}
        if os_defaults:
            self.default_cfg["common"].update(os_defaults["common"])
        if os.name in os_defaults:
            self.default_cfg["common"].update(os_defaults[os.name])

    # 2.a) YML
    def read_yml_cfg(self, path=None, must_exist=True):
        """Reads a YML config"""
        if path is None:
            # Linux default: /etc/check_mk/robotmk.yml
            # Windows default: C:\Program Data\check_mk\agent\config\robotmk.yml
            ymlfile = (
                Path(self.configdict["common"]["cfgdir"])
                / self.configdict["common"]["robotmk_yml"]
            )
        else:
            ymlfile = Path(path)
            # a custom file path should always exist
            must_exist = True
        if must_exist and not ymlfile.exists():
            raise FileNotFoundError(f"YML config file not found: {ymlfile}")
        else:
            # try to read the file
            ymltemp = {}
            try:
                with open(ymlfile, "r") as f:
                    ymltemp = yaml.load(f, Loader=yaml.FullLoader)
            except Exception as e:
                raise e
            # validate the config
            schema = RobotmkConfigSchema(ymltemp)
            if not schema.validate():
                raise ValueError(
                    f"YML config file {ymlfile} is invalid: {schema.error}"
                )
            else:
                self.yml_config = ymltemp

    # variables (env AND! file)
    def read_cfg_vars(self, path=None, d=None):
        """Reads variables file (if path is given) and/or environment variables.
        Creates a nested dict from vars starting with a certain prefix (given as
        a parameter "envvar_prefix" to the constructor). The prefix is used to
        only read variables that are relevant for the application.
        Each Variable starting with the prefix is split into a list of substrings,
        separated by "_".
        Each split iteration creates a new level in the nested dict.
        If there is a substring starting with double underscore, everything until the
        next double underscore is protected against splitting and used as one single key.
        It then creates a nested dict from them.
        The dict is stored in self.config or in the dict given as parameter d."""
        temp_cfg = {}
        if path:
            # 2.b)
            self.__source_vars_from_file(path)
        # 2.a)
        for k, v in os.environ.items():
            if k.startswith(self.envvar_prefix):
                k = k.replace(self.envvar_prefix + "_", "")
                pieces = self.__split_varstring(k)
                cfg = temp_cfg
                for part in pieces[:-1]:
                    if part not in cfg:
                        cfg[part] = {}
                    cfg = cfg[part]
                cfg[pieces[-1]] = v
        if d is None:
            self.env_config = mergedeep.merge(self.env_config, temp_cfg)
        else:
            return temp_cfg

    @property
    def merged_config_dict(self) -> dict:
        """This property merges the three config sources in the right order."""
        merged_config = mergedeep.merge(
            self.default_cfg, self.yml_config, self.env_config
        )
        return merged_config

    @property
    def configdict(self):
        """This property returns the merged config dict"""
        return self.merged_config_dict

    # @property
    # def configtuple(self):
    #     """This property returns the merged config dict as a named tuple."""
    #     return self.__dict_to_namedtuple(self.merged_config_dict, "config")

    # def __dict_to_namedtuple(self, d, typename):
    #     """Helper function to convert a dict to a named tuple."""
    #     for key, value in d.items():
    #         if isinstance(value, dict):
    #             d[key] = self.__dict_to_namedtuple(value, f"{typename}_{key}")
    #     return namedtuple(typename, d.keys())(*d.values())

    # 2.b)
    def __source_vars_from_file(self, file):
        """Reads variables from a file and sources them in the current environment."""
        try:
            with open(file, "r") as f:
                for line in f:
                    line = line.strip()
                    # Ignore empty lines and lines starting with "#" (comments)
                    if line.strip() and not line.strip().startswith("#"):
                        if line.startswith("export ") or line.startswith("set "):
                            line = line.partition(" ")[2]
                        # Split each line into a key-value pair
                        key, value = line.strip().split("=")
                        # Add the variable to the environment
                        os.environ[key] = value
        except Exception as e:
            raise FileNotFoundError(f"Could not read environment file: {file}")

    def __split_varstring(self, s):
        """Split a string into a list of substrings, separated by "_".
        Double underscores are protecting substring from splitting."""
        pieces = []
        current_piece = ""
        preserved_piece = False
        i = 0
        while i < len(s):
            if s[i : i + 2] == "__":
                # Double underscore, add current piece to list and start a new one
                if current_piece:
                    if not preserved_piece:
                        # add a normal piece, start a preserved one
                        pieces.append(current_piece)
                        current_piece = ""
                        preserved_piece = True
                    else:
                        # add a preserved piece, start a normal one
                        pieces.append(current_piece)
                        current_piece = ""
                        preserved_piece = False
                # Skip the double underscore
                i += 2
            elif s[i] == "_":
                # Single underscore, add current piece to list and start a new one
                if current_piece:
                    if not preserved_piece:
                        pieces.append(current_piece)
                        current_piece = ""
                    else:
                        current_piece += "_"
                i += 1
            else:
                # Add the current character to the current piece
                current_piece += s[i]
                i += 1

        # Add the last piece to the list
        if current_piece:
            pieces.append(current_piece)

        return pieces

    def get(self, *keys):
        d = self._config
        for key in keys:
            if key in d:
                d = d[key]
            else:
                return None
        return d

    def to_environment(self, d=None, envvar_prefix=""):
        """Converts a nested dict to environment variables.
        If no dict is given, self.config is used."""
        if d is None:
            d = self.configtuple
        for k, v in d.items():
            if isinstance(v, dict):
                if "_" in k:
                    k = f"_{k}_"
                self.to_environment(v, envvar_prefix=f"{envvar_prefix}_{k}")
            else:
                print(f"{self.prefix}{envvar_prefix}_{k} = {v}")
                os.environ[f"{self.prefix}{envvar_prefix}_{k}"] = str(v)

    def to_yml(self, file=None) -> Union[str, None]:
        """Dumps the config to a file returns it."""
        if file:
            try:
                with open(file, "w") as f:
                    yaml.dump(self.configdict, f)
            except Exception as e:
                print(f"Could not write to file {file}: {e}")
                return None
        else:
            return yaml.dump(self.configdict)


# c = Confitree(prefix="ROBOTMK")
# c.read_yml_cfg(os.path.join(os.path.dirname(__file__), "robotmk.yml"))
# c.read_env_cfg()
# c.to_environment()
# pass
