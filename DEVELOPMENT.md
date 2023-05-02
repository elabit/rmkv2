# Dev Notes


## robotmk-ctrl.ps1

VS Code 
The script has CLI options for `robotmk-ctrl.ps1` (CMK Agent Plugin & call by user) as well as options for `RobotmkAgent.ps1` when called by the Service Control Manager. 
Keep that in mind when Debugging to choose the proper Debugging config. 

## robotmk Python 

```
export ROBOTMK_common_path__prefix=$HOME/Documents/01_dev/rmkv2
```

### FLit

Start with a clean bash:

```bash
# enter project dir
cd rmkv2
# install dependencies
pipenv sync --dev
# install editable version to test robotmk in console
pipenv shell 
cd robotmk-agent 
flit install -s
```

VS Code: 


### Release/bumpversion


```
[bumpversion]
current_version = 0.0.7
commit = False
tag = False

[bumpversion:file:robotmk/__init__.py]
```

```
cd robotmk-agent
git add .. ; git commit -m "xxxxx"; bumpversion patch; git add .. ; git commit -m "xxxx"
flit publish --repository testpypi 
flit publish
```

conda.yaml anpassen auf neue Version 

Es dauert einige Zeit, bis das neue Release publish ist!
- sofort aktuell: https://pypi.org/project/robotmk/
- ca. 2 Minuten: https://libraries.io/pypi/robotmk/versions

robotmk-ctrl.ps1 => neues RCC env bauen

