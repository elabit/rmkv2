# Development Notes

## Robotmk Controller (Powershell)

VS Code
The script has CLI options for `robotmk-ctrl.ps1` (CMK Agent Plugin & call by user) as well as options for `RobotmkAgent.ps1` when called by the Service Control Manager.
Keep that in mind when Debugging to choose the proper Debugging config.


---


## Robotmk agent/specialagent (Python)

### Quickstart

#### Step 1: Install requirements

- pipenv
-

#### Step 2: Create Python environment

Use `pipenv sync --dev` to create a venv with the dev dependencies.

#### Step 3: install Robotmk editable

After the venv has beend created and entered, install the Robotmk package as *editable*:

```
cd robotmk
flit install -s
```

`robotmk -h` should now be executable.

#### Step 4: configure environment variables

By default, Robotmk assumes the following default configuration:
- Windows:
  - `cfgdir`: `C:/ProgramData/checkmk/agent/config` (=> `robotmk.yml`)
  - `robotdir`: `C:/ProgramData/checkmk/agent/robot`
  - `logdir`: `C:/ProgramData/checkmk/agent/log/robotmk`
- Linux:
  - `cfgdir`: `/etc/check_mk` (=> `robotmk.yml`)
  - `robotdir`: `/usr/lib/check_mk_agent/robot`,
  - `logdir`: `/var/log/robotmk`

`robotmk.yml` is the central configuration file. It can be read from another location and/or certain keys can be overriden by environment variables.

If `ROBOTMK_common_path__prefix` is set, it prefixes path configuration values (`cfgdir`,`logdir`,`tmpdir`,`resultdir` and `robotdir`), if they are set *relative*. (Absolute paths are always taken as they are).

For local development you need to set these two environment variables:

```
# set path prefix
export ROBOTMK_common_path__prefix="/home/simonmeggle/Documents/01_dev/rmkv2"
# set relative path to robotmk.yml
export ROBOTMK_common_cfgdir="robotmk/tests/yml"
```

See `robotmk/.cli.env` for an example.

Hint: `agent` context of Robotmk requires a YML file to be loaded, where `suite` and `specialagent` can load their configuration completely from environment variables.

#### Step 5: VS Code debugging

`.vscode/launch.json` contains debug configurations for every execution context.

With the environment variables set in step 4, the YML configuration is always loaded from `./robotmk/tests/yml/robotmk.yml`.

### Committing work

[Pre-Commit](https://pre-commit.com) is used to execute hooks before commits can be done to the repo.

The config file `.pre-commit-config.yaml` contains configure hooks for:

- removing trailing whitespace
- fixing EOF
- linting YML
- large file additions
- black formatting

The hooks are executed automatically before every commit, manual execution can be done with:

    pre-commit run --all-files

### Release

`robotmk/release.sh` is used to create new versions of Robotmk on PyPi:

```
./release.sh patch "This is a small patch commit"
./release.sh minor "This is a minor patch commit"
./release.sh major "This is a major patch commit"

```

The following files are updated automatically on each release:

- `src/robotmk/__init__.py` => `__version__` variable
- `../agent/robots/suiteA/conda.yaml` => Robotmk package version to install inside of RCC runs
