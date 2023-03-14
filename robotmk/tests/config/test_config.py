import pytest
from robotmk.config import Config
import os


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
    cfg.read_yml_cfg(os.path.join(os.path.dirname(__file__), "robotmk.yml"))
    assert cfg.configdict["common"]["a"] == 1
    assert cfg.configdict["common"]["b"] == 3


def test_read_env_cfg():
    """Tests if parts of the default config are overwritten by the yml config
    and then again overwritten by the environment.
    The default config sets a=1, b=2, c=3.
    Yml changes b to 3.
    Env changes c to 4."""
    cfg = Config()
    cfg.set_defaults({"common": {"a": 1, "b": 2, "c": 3}})
    cfg.read_yml_cfg(os.path.join(os.path.dirname(__file__), "robotmk.yml"))
    os.environ["ROBOTMK_common_c"] = "4"
    cfg.read_env_cfg()
    assert str(cfg.configdict["common"]["a"]) == "1"
    assert str(cfg.configdict["common"]["b"]) == "3"
    assert str(cfg.configdict["common"]["c"]) == "4"


# TODO: config validation
