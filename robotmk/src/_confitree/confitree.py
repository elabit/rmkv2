# Confitree is a python module that provides a simple way to read configuration from
# different sources.

# The configuration is read from the following sources in the following order:
# 1. OS defaults, provided by class instances for each supported OS (Linux, Windows)
# 2. read from config.yml
# 3. read from environment variables

# Step 3 creates a nested dict from environment vars starting with a certain
# prefix (given as a parameter "prefix" to the constructor). The prefix is used to only read
# variables that are relevant for the application.
# Each Variable starting with the prefix is split into a list of substrings, separated by "_".
# Each split iteration creates a new level in the nested dict.
# If there is a substring starting with double underscore, everything until the
# next double underscore is protected against splitting and used as one single key.


# TODO: print environment

import os
import yaml
import mergedeep


class Confitree:
    def __init__(self, prefix=None):
        self._config = {}
        self.prefix = prefix
        self.os_default_cfg = {}
        self.yml_config = {}
        self.env_config = {}
        self.merged_config = None

    # 1. OS defaults
    def set_os_defaults(self, os_defaults):
        """Sets the defaults for the current OS."""
        self.os_default_cfg = os_defaults

    # 2. YML
    def read_yml_cfg(self, path):
        """Reads a YML config"""
        with open(path, "r") as f:
            self.yml_config = yaml.load(f, Loader=yaml.FullLoader)

    # 3. Env.
    def read_env_cfg(self, d=None):
        """Reads environment variables and creates a nested dict from them.
        The dict is stored in self.config or in the dict given as parameter d."""
        temp_cfg = {}
        for k, v in os.environ.items():
            if k.startswith(self.prefix):
                k = k.replace(self.prefix + "_", "")
                pieces = self.split_varstring(k)
                cfg = temp_cfg
                for part in pieces[:-1]:
                    if part not in cfg:
                        cfg[part] = {}
                    cfg = cfg[part]
                cfg[pieces[-1]] = v
        if d is None:
            self.env_config = temp_cfg
        else:
            return temp_cfg

    @property
    def config(self):
        """This property merges the three config sources in the right order."""
        self.merged_config = mergedeep.merge(
            self.os_default_cfg, self.yml_config, self.env_config
        )
        return self.merged_config

    def split_varstring(self, s):
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

    def to_environment(self, d=None, prefix=""):
        """Converts a nested dict to environment variables.
        If no dict is given, self.config is used."""
        if d is None:
            d = self.config
        for k, v in d.items():
            if isinstance(v, dict):
                if "_" in k:
                    k = f"_{k}_"
                self.to_environment(v, prefix=f"{prefix}_{k}")
            else:
                print(f"{self.prefix}{prefix}_{k} = {v}")
                os.environ[f"{self.prefix}{prefix}_{k}"] = str(v)


c = Confitree(prefix="ROBOTMK")
c.read_yml_cfg(os.path.join(os.path.dirname(__file__), "robotmk.yml"))
c.read_env_cfg()
c.to_environment()
pass
