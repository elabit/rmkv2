# Dev Notes


## robotmk-ctrl.ps1

VS Code 
The script has CLI options for `robotmk-ctrl.ps1` (CMK Agent Plugin & call by user) as well as options for `RobotmkAgent.ps1` when called by the Service Control Manager. 
Keep that in mind when Debugging to choose the proper Debugging config. 

## robotmk Python 


### Setup 

pipenv install 
pipenv install -e . 
pipenv shell 

### FLit / bumpversion workflow

Start with a clean bash:

```bash
# enter project dir
cd rmkv2
# install dependencies
pipenv sync --dev
# install editable robotmk to develop 
cd robotmk-agent 
flit install -s
```


Release: 
```
cd robotmk-agent
git add .. ; git commit -m "xxxxx"; bumpversion patch; git add .. ; git commit -m "xxxx"
flit publish --repository testpypi 
flit publish
```

conda.yaml anpassen auf neue Version 

robotmk-ctrl.ps1 => neues RCC env bauen
```


[bumpversion]
current_version = 0.0.7
commit = False
tag = False

[bumpversion:file:robotmk/__init__.py]


```