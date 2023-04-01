import yaml
from robotmk.config.config import Config
import os

cwd = os.path.dirname(__file__)
robotmk_yml = os.path.join(cwd, "robotmk.yml")
robotmk_env = os.path.join(cwd, "robotmk.env")


def test_defaults():
    cfg = Config()
    cfg.set_defaults({"common": {"a": 1, "b": 2}})
    assert cfg.configdict["common"]["a"] == 1
    assert cfg.configdict["common"]["b"] == 2


def test_read_yml_cfg():
    """Tests if parts of the default config are overwritten by the yml config.
    The default config sets a=1 and b=2, yml changes b to 3."""
    cfg = Config()
    cfg.set_defaults({"common": {"a": 1, "b": 2}})
    cfg.read_yml_cfg(path=robotmk_yml)
    # unchanged
    assert cfg.configdict["common"]["a"] == 1
    # changed
    assert cfg.configdict["common"]["b"] == 3


def test_read_var_env_cfg():
    """Tests if parts of the default config are overwritten by
    - YML config
    - and then again overwritten by environment variables
    The default config sets a=1, b=2, c=3.
    Yml changes b to 3.
    Env changes c to 4."""
    cfg = Config()
    cfg.set_defaults({"common": {"a": 1, "b": 2, "c": 3}})
    cfg.read_yml_cfg(path=robotmk_yml)
    os.environ["ROBOTMK_common_c"] = "4"
    os.environ["ROBOTMK_common_cc"] = "4"
    os.environ["ROBOTMK_common_cff"] = "4"
    os.environ["ROBOTMK_common_chhh"] = "4"
    # now read the variables from environment
    cfg.read_cfg_vars(path=None)
    # unchanged
    assert str(cfg.configdict["common"]["a"]) == "1"
    assert str(cfg.configdict["common"]["b"]) == "3"
    # changed
    assert str(cfg.configdict["common"]["c"]) == "4"


def test_read_var_file_cfg():
    """Tests if parts of the default config are overwritten by
    - YML config
    - variables in a file
    - and then again overwritten by env vars
    The default config sets a=1, b=2, c=3.
    Yml changes b to 3.
    File changes c to 5.
    Env changes c to 55."""
    cfg = Config()
    cfg.set_defaults({"common": {"a": 1, "b": 2, "c": 3}})
    cfg.read_yml_cfg(path=robotmk_yml)
    os.environ["ROBOTMK_common_c"] = "55"
    cfg.read_cfg_vars(path=robotmk_env)
    # unchanged
    assert str(cfg.configdict["common"]["a"]) == "1"
    assert str(cfg.configdict["common"]["b"]) == "3"
    # changed
    assert str(cfg.configdict["common"]["c"]) == "55"


def test_read_var_file_added_cfg():
    """Tests if parts of the default config are overwritten by
    - YML config
    - variables in a file
    - env vars
    - and then again overwritten by added vars
    The default config sets a=1, b=2, c=3.
    Yml changes b to 3.
    File changes c to 5.
    Env changes c to 55.
    Added var changes c to 6."""
    cfg = Config()
    cfg.set_defaults({"common": {"a": 1, "b": 2, "c": 3}})
    cfg.read_yml_cfg(path=robotmk_yml)
    os.environ["ROBOTMK_common_c"] = "55"
    cfg.read_cfg_vars(path=robotmk_env)
    cfg.set("common.c", 66)
    cfg.set("common.d.e.f.g", 77)
    # unchanged
    assert str(cfg.configdict["common"]["a"]) == "1"
    assert str(cfg.configdict["common"]["b"]) == "3"
    # changed
    assert str(cfg.configdict["common"]["c"]) == "66"
    assert str(cfg.configdict["common"]["d"]["e"]["f"]["g"]) == "77"


def test_config_to_yml():
    """Tests if the config can be dumped to a valid YML string"""
    cfg = Config()
    cfg.set_defaults({"common": {"a": 1, "b": 2, "c": 3}})
    cfg.read_yml_cfg(path=robotmk_yml)
    os.environ["ROBOTMK_common_c"] = "4"
    os.environ["ROBOTMK_foo_bar_x"] = "44"
    cfg.read_cfg_vars(path=None)
    # Now read the variables from a file
    cfg.read_cfg_vars(path=robotmk_env)
    # unchanged
    assert str(cfg.configdict["common"]["a"]) == "1"
    assert str(cfg.configdict["common"]["b"]) == "3"
    # changed
    assert str(cfg.configdict["common"]["c"]) == "4"
    yml_str = cfg.to_yml()
    yml = yaml.safe_load(yml_str)
    assert str(yml["foo"]["bar"]["x"]) == "44"


def test_envvar2dict():
    """Tests if only env vars with the prefix ROBOTMK_ are read into the config"""
    cfg = Config()
    os.environ["ROBOTMK_foo_bar1"] = "1"
    os.environ["ROBOTMK_foo_bar2"] = "2"
    os.environ["ROBOTMK_foo_bar3"] = "3"
    os.environ["DONT_foo_bar4"] = "4"
    cfg.read_cfg_vars(path=None)
    assert str(cfg.configdict["foo"]["bar1"]) == "1"
    assert str(cfg.configdict["foo"]["bar2"]) == "2"
    assert str(cfg.configdict["foo"]["bar3"]) == "3"
    # assert not
    assert not "bar4" in cfg.configdict["foo"]


# TODO: split_varstring
# TODO: config validation
