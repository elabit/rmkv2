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
import re
import yaml
from mergedeep import merge, Strategy
from typing import Union
from collections import defaultdict

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

    def __translate_keys(self, name: str) -> list:
        """Translate a key name to a list of keys and respect shorthand 'suitecfg'."""
        keys = name.split(".")
        if keys[0] == "suitecfg":
            suitename = self.configdict["common"]["suiteuname"]
            keys[:1] = ["suites", suitename]
        return keys

    def get(self, name: str, default=None) -> str:
        """Get a value from the object with dot notation.

        Shorthand 'suitecfg' can be used for 'suites.<suiteuname>'.

        Examples:
            cfg.get("common.cfgdir")
            cfg.get("suitecfg.run.rcc")
        """
        keys = self.__translate_keys(name)
        m = self.configdict
        # prev = self.configdict
        try:
            for key in keys:
                # prev = m
                # prev_k = key
                m = m.get(key, {})
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

        Shorthand 'suitecfg' can be used for 'suites.<suiteuname>'.

        Example:
            cfg.set("common.cfgdir", "/etc/check_mk")
            cfg.set("suitecfg.run.rcc", False)
        """
        keys = self.__translate_keys(name)
        cur_dict = self.added_config
        for key in keys[:-1]:
            if not key in cur_dict:
                cur_dict[key] = {}
            cur_dict = cur_dict[key]

        cur_dict[keys[-1]] = value

    # def set(self, name: str, value: any) -> None:
    #     """Set a value in the object with dot notation.

    #     Example:
    #         cfg.set("common.cfgdir", "/etc/check_mk")
    #     """
    #     keys = name.split(".")
    #     cur_dict = self.added_config
    #     for key in keys[:-1]:
    #         if not key in cur_dict:
    #             cur_dict[key] = {}
    #         cur_dict = cur_dict[key]

    #     cur_dict[keys[-1]] = value

    def asdict(self):
        """Returns the config as a dict."""
        return self.configdict

    @property
    def configdict(self):
        """This property merges the three config sources in the right order."""

        return merge(
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
        vars = merge(filevars, envvars)
        # convert flat vars to nested dicts
        vardict = defaultdict(dict)
        for k, v in vars.items():
            vardict = self._var2cfg(k, v, vardict)
            # vardict = merge(vardict, d, strategy=Strategy.TYPESAFE_ADDITIVE)
        self.env_config = merge(self.env_config, vardict)

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
                                cur_dict[key] = value
            except Exception as e:
                raise FileNotFoundError(f"Could not read environment file: {file}")
        return vardict

    def __split_varstring(self, s):
        """Helper function to split a string into a list of substrings, separated by "_".
        A double underscore protects the string from splitting."""
        keys = []
        starti = 0
        i = 0
        while i < len(s):
            poschar = s[i]
            if poschar == "_" or i == len(s) - 1:
                if len(s) > i + 1 and s[i + 1] == "_":
                    # not at and and double underscore in front of us!
                    # skip next underscore and continue until next SINGLE underscore
                    i += 2
                    continue
                else:
                    # Single underscore in front or last piece; add current piece to list (replace __ by _) and start a new one
                    if len(s) > i + 1:
                        # last piece
                        last_single_usc_index = i
                    else:
                        # not last piece
                        last_single_usc_index = i + 1
                    piece = s[starti:last_single_usc_index].replace("__", "_")
                    keys.append(piece)
                    starti = i + 1
            else:
                # Add the current character to the current piece
                pass
            i += 1
        return keys

    def validate(self, schema: RobotmkConfigSchema):
        """Validates the whole config according to the given context schema."""

        schema = RobotmkConfigSchema(self.configdict)
        if not schema.validate():
            raise ValueError(f"Config is invalid: {schema.error}")

    def _var2cfg(self, o_varname, value, vardict) -> dict:
        """Helper function to convert a variable to a dict/list/value entry and assigns the value.

        Value assignments are done in-place, so the vardict is modified."""

        def partition_at_digit(s):
            m = re.search("\d+", s)
            if m:
                return s[: m.start() - 1], int(s[m.start() : m.end()]), s[m.end() + 1 :]
            else:
                return [s, None, None]

        def _str2dict(string, value, vardict=None):
            # vardict = {}
            cur_dict = vardict

            (s_left, s_list_index, s_right) = partition_at_digit(string)

            left_keys = self.__split_varstring(s_left)
            for ki, key in enumerate(left_keys):
                if ki < len(left_keys) - 1:
                    if not key in cur_dict:
                        cur_dict[key] = defaultdict(dict)
                    cur_dict = cur_dict[key]
                    # if vardict.get(key, None):
                    #     vardict = cur_dict[key]
                else:
                    # we have reached the leaf key of left side
                    if not s_list_index is None:
                        if not key in cur_dict:
                            # list index: prepare the list position
                            cur_dict[key] = [None] * (s_list_index + 1)
                        else:
                            # list index: extend the list if necessary
                            if len(cur_dict[key]) < s_list_index + 1:
                                cur_dict[key] = cur_dict[key] + [None] * (
                                    s_list_index + 1 - len(cur_dict[key])
                                )

                        if not s_right:
                            # no subdict inside the list, just add the value
                            cur_dict[key][s_list_index] = value
                        else:
                            # dict inside the list, merge in case of existing dict
                            subdict = _str2dict(s_right, value, vardict)
                            if cur_dict[key][s_list_index]:
                                cur_dict[key][s_list_index] = merge(
                                    cur_dict[key][s_list_index],
                                    subdict,
                                    strategy=Strategy.TYPESAFE_ADDITIVE,
                                )
                    else:
                        # simple value assignment
                        cur_dict[key] = value

                    # cur_dict[key] = [_str2dict(dictparts[di + 1], value)]
                    # cur_dict = cur_dict[key]

            return vardict

        # Remove the ROBOTMK_ prefix
        varname = o_varname.replace(self.envvar_prefix + "_", "")
        # varname = "a_A_1_bar"
        # # varname = "a_A_10"
        # # varname = "a_A"

        # value = "lulu"
        # vardict = {
        #     "a": {
        #         "A": [
        #             None,
        #             {"foo": "la"},
        #         ]
        #     }
        # }
        # vardict = defaultdict(dict)
        # value = "lulu"
        _str2dict(varname, value, vardict)
        return vardict

    def to_environment(self, d=None, prefix=""):
        """Converts a given dict/value or self.configdict to environment variables.

        The rules are:
        - there is no case conversion
        - underscores within key names are replaced by double underscores
        - the prefix is added to the environment variable name
        - dicts are converted to nested environment variables
        - lists get a number appended to their key name"""
        if d is None:
            d = self.configdict
        if isinstance(d, dict):
            for key, value in d.items():
                safe_key = key.replace("_", "__")
                new_prefix = f"{prefix}_{safe_key}"
                self.to_environment(value, prefix=new_prefix)

                # elif isinstance(value, list):
                #     for i, item in enumerate(value):
                #         new_prefix = f"{prefix}_{safe_key}_{i}"
                #         self.to_environment(item, prefix=new_prefix)
                # else:
                #     varname = f"{self.envvar_prefix}{prefix}_{safe_key}"
                #     print(f"{varname} = {value}")
                #     os.environ[varname] = str(value)
        elif isinstance(d, list):
            for i, item in enumerate(d):
                new_prefix = f"{prefix}_{i}"
                self.to_environment(item, prefix=new_prefix)
        else:
            varname = f"{self.envvar_prefix}{prefix}"
            print(f"{varname} = {d}")
            os.environ[varname] = str(d)

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
