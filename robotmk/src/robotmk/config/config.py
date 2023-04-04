"""This module provides a simple way to read configuration from different sources: 
- YML file
- variables file
- environment variables

There is a special order in which the sources are read:
- 1. OS defaults for each supported OS (Linux, Windows)
- 2. config from YML file, either
    - the default config file (robotmk.yml)
    OR
    - a custom config file (given as parameter --yml)
- 3. variables from 
    - variable file (given as parameter --vars)
    AND
    - environment variables (ROBOTMK_*)

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
# ["%s:%s" % (v, os.environ[v]) for v in os.environ if v.startswith("ROBO")]


class Config:
    def __init__(self, envvar_prefix: str = "ROBOTMK", initdict: dict = None):
        self.envvar_prefix = envvar_prefix
        if initdict:
            self.default_cfg = initdict
        else:
            self.default_cfg = {}
        self.yml_config = {}
        self.env_config = {}
        # this is a dict of all config values that were added by the user.
        # they are applied last and can overwrite any other config values.
        self.added_config = {}

    def get(self, name: str, default=None) -> str:
        """Get a value from the object with dot notation.

        Example:
            cfg.get("common.cfgdir")
        """
        m = self.configdict
        prev = self.configdict
        try:
            for k in name.split("."):
                prev = m
                prev_k = k
                m = m.get(k, {})
            if type(m) is dict:
                if m:
                    return Config(initdict=m)
                else:
                    return default
            else:
                return m
        except:
            return default

    def set(self, name: str, value: any) -> None:
        """Set a value in the object with dot notation.

        Example:
            cfg.set("common.cfgdir", "/etc/check_mk")
        """
        keys = name.split(".")
        curdict = self.added_config
        for key in keys[:-1]:
            if not key in curdict:
                curdict[key] = {}
            curdict = curdict[key]

        curdict[keys[-1]] = value

    def asdict(self):
        """Returns the config as a dict."""
        return self.configdict

    @property
    def configdict(self):
        """This property merges the three config sources in the right order."""

        return mergedeep.merge(
            self.default_cfg, self.yml_config, self.env_config, self.added_config
        )

    # 1. Defaults (common/OS specific)
    def set_defaults(self, os_defaults: dict = None) -> None:
        """Sets the defaults for the current OS."""
        self.default_cfg["common"] = {}
        if os_defaults:
            self.default_cfg["common"].update(os_defaults["common"])
        if os.name in os_defaults:
            self.default_cfg["common"].update(os_defaults[os.name])

    # 2. YML
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
            config = {}
            try:
                with open(ymlfile, "r") as f:
                    config = yaml.load(f, Loader=yaml.FullLoader)
            except Exception as e:
                raise e

            self.yml_config = config

    # 3. variables (env AND! file)
    def read_cfg_vars(self, path=None):
        """Read ROBOTMK variables from file and/or environment.

        Environment vars have precedence over file vars."""

        filevars = self._filevar2dict(path)
        envvars = self._envvar2dict()
        # a dict with still flat var names
        vars = mergedeep.merge(filevars, envvars)
        # convert flat vars to nested dicts
        vardict = {}
        for k, v in vars.items():
            d = self._var2dict(k, v)
            vardict = mergedeep.merge(vardict, d)
        self.env_config = mergedeep.merge(self.env_config, vardict)

    def _envvar2dict(self) -> dict:
        """Returns all environment variables starting with the ROBOTMK prefix.

        Example:
        {"ROBOTMK_foo_bar": "baz",
         "ROBOTMK_foo_baz": "bar"}
        """
        vardict = {}
        for k, v in os.environ.items():
            if k.startswith(self.envvar_prefix):
                vardict[k] = v
        return vardict

    def _filevar2dict(self, file) -> dict:
        """Returns all variables from a given file (strips 'set' and 'export' statements).

        Example:
        {"ROBOTMK_foo_bar": "baz",
         "ROBOTMK_foo_baz": "bar"}
        """
        vardict = {}
        if file:
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
                            if key.startswith(self.envvar_prefix):
                                vardict[key] = value
            except Exception as e:
                raise FileNotFoundError(f"Could not read environment file: {file}")
        return vardict

    def _var2dict(self, o_varname, value) -> dict:
        """Helper function to convert a variable to a dict and assigns the value."""

        varname = o_varname.replace(self.envvar_prefix + "_", "")
        my_dict = {}
        current_dict = my_dict

        keys = self.__split_varstring(varname)
        for key in keys[:-1]:
            current_dict[key] = {}
            current_dict = current_dict[key]

        current_dict[keys[-1]] = value

        return my_dict

    def __split_varstring(self, s):
        """Helper function to split a string into a list of substrings, separated by "_".
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

    def validate(self, schema: RobotmkConfigSchema):
        """Validates the whole config according to the given context schema."""

        schema = RobotmkConfigSchema(self.configdict)
        if not schema.validate():
            raise ValueError(f"Config is invalid: {schema.error}")

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
