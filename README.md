# Robotmk V2

!!! ALPHA - NOT FOR PRODUCTION !!!

## USAGE

- copy `agent/config/robotmk` into `%Programdata%/checkmk/agent/config/robotmk`
- copy `agent\plugins\robotmk-ctrl.ps1` into `%Programdata%/checkmk/agent/plugins/`

Add to `C:\ProgramData\checkmk\agent\bakery\check_mk.bakery.yml``:

```
plugins:
  enabled: true
  execution:
  - async: true
    pattern: $CUSTOM_PLUGINS_PATH$\robotmk-ctrl.ps1
    run: true
```


Now start the CMK agent and watch `C:\ProgramData\checkmk\agent\log\robotmk\robotmk-ctrl-plugin.log` . 
You should see the Phase 1 prcess starting the Phase 2 process. 
The Process list should only show up the Phase 2 process (Phase 1 behaves like a normal Plugin and is meant to run shortly).

The very first start of Phase 2 will take longer because `robotmk-ctrl.ps1` starts rcc.exe to create a new RCC environment for robotmk to run. 
During this process, `rcc_env_creation_in_progress.lock` will be present in `ProgramData/agent/tmp/robotmk/`. 
As long, further executions of `robotmk-ctrl.ps` will not trigger any other environment creations.

After the environment was built, the lockfile in `tmp` gets replaced by `rcc_env_robotmk_agent_ready`. 
The next execution of the controller will start the Robotmk Python agent within the new RCC environment. 
(The Daemon will be responsible to start Robot suites in individual intervals in multiple proceses)
Dummy activity of this Daemon action can be seen in `ProgramData/agent/tmp/robotmk/`.

---

**GOAL**: When the CMK agent gets stopped or executed/triggered from CMK, the Phase 2 process should survive. 

**PROBLEM**: Stopping/executing the Agent kills the Phase2 Powrshell process and Robotmk below of it, although it does not have a parent process id. 

--- 
## I. Robotmk als Agent Plugin  

### a) Robotmk-Plugin im "Agent" mode

Dem Aufruf von `robotmk.py` (in RCC oder nativ über das OS-Python) wird ein Facade-Plugin `robotmk-ctrl.ps1` vorgeschaltet (Windows: Powershell, Linux: Bash).
Es verbirgt die Logik der Erzeugung des RCC-Environments (sofern noch nicht vorhanden).

Außerdem abstrahiert das Facade-Plugin die unter Windows und Linux unterschiedliche Entkoppelung des Robotmk-Daemon-Prozesses vom Agenten-Prozess, der ihn startet. 
**Windows** = "*early decoupling*": `robotmk-ctrl.ps1` kann den Robotmk-Pythonprozess theoretisch direkt entkoppelt (-> POCESS_CREATION_FLAGS) starten. 

**Linux** = "*late decoupling*": `robotmk-ctrl.sh` müsste die Entkoppelung an den Child-Prozess delegieren, der sich mittels "Double-Forking" vom Parent löst. 
Problem: Der Child-Prozess ist entweder das nativ gestartete Pythonscript `robotmk.py` oder das Binary `rcc.exe`. 
Dort jeweils müsste auch die Logik des Double-Forking eingebaut werden. Das führt zu Code duplication - und ist im Fall von RCC auch nicht möglich (3rd Party Code).

TODO: ohne RCC?

Obwohl dieses Problem nur unter Linux existiert (und die Facade-Plugins ohnehin in unterschiedlichen Sprachen programmiert werden müssen), wird eine einheitliche Architektur angestrebt: 
Wird das Facade-Plugin vom Agenten gestartet, entkoppelt es sich grundsätzlich durch einen Aufruf von sich selbst. 

Im Detail:
- Agent startet `robotmk-ctrl.ps1/sh` (Facade-Plugin)
- Entkoppelung: 
  - Windows: 
    - Facade-Plugin startet sich selbst als bereits entkoppelter Prozess mit Parameter "start": `robotmk-ctrl.ps1 start`
  - Linux: 
    - Facade-Plugin startet sich selbst als Subprozess mit Parameter "start": `robotmk-ctrl.sh start`
    - zusätzlicher Schritt: Subprozess entkoppelt sich durch Double-Fork
- `robotmk-ctrl.ps/sh` läuft nun als entkoppelter Prozess. Anhand des Parameters `start` erkennt das Script, dass keine Entkoppelung mehr notwendig ist. 
  - läuft der Robotmk-Prozess bereits || existiert Statefile `robotmk_rcc_env_in_creation`? 
    - ja => exit
    - nein => robotmk-RCC-env bereit?
      - ja => **Starte Robotmk-Task**: `rcc task run -t robotmk-agent` => LOOP ... ... (s.u.)
      - nein => robotmk-RCC-env bauen: 
        - Anlagen v. Statefile: `robotmk_rcc_env_in_creation`
        - hololib-zip vorhanden? 
          - ja => `rc ht import hololib.zip` (lokal)
          - nein => `rcc ht vars` (Internet)

Robotmk-LOOP: 
  - Liest Config aus File 
  - apscheduler loop: stetes Ausführen von due Robots
  - foreach "due robot": `Robot Runner` (multiprocessing)
    - Config: 
      - CONF2ENV 
      - + `ROBOTMK_mode=robot`
      - + `ROBOTMK_robot=suiteA`
    - ist der Robot RCC-kompatibel? 
        - ja: 
          - cd ins Robot-Dir 
          - rufe den Robot in Subprozess im eigenen RCC-environment auf:
            - `rcc task run -t robotmk` => startet `robotmk` im RCC-py => II)
        - nein: rufe den Robot in Subprozess mit dem gleichen Interpreter auf 
            - `robotmk` => II)
  - end of loop: refresh config 


### b) Robotmk-Plugin im "Output" mode 

- Agent startet Facade-Plugin `robotmk-ctrl.ps1/sh` (synchron)
- steht das robotmk-RCC-env bereit?
  - ja => **Starte Robotmk-Task**: `rcc task run -t robotmk-output`
    - liest Config aus File 
    - iteriert über Robots, liest Ergebnisse, printet Output   
  - nein => exit (Aufbau wird von robotmk-ctrl erledigt)

## II. Robotmk im Robot-Mode

`ROBOTMK_mode=robot` bzw `--mode=robot`=> Ausführung **eines einzelnen Robots** (im OS- oder RCC-Python)

- `robotmk`
  - Config aus Environment (alternativ: `-c path/to/robotmk.json --mode robot --run suiteA`)
  - Ausführen der Suite `robotmk.robot` in `$ROBOTDIR/suiteA/`
    - Alternatives .robot-File: Setzen von `suite_file=anothersuite.robot`
    - Aufruf von `robot --param1 ... --name suiteA robotmk.robot`
      - `--name` sorgt dafür, dass die toplevel suite nicht "Robotmk" heißt, sondern so wie die suite
  - Schreiben des Results


## III. Robotmk as Special Agent 

### Trigger Robots 

- Special agent command line func: WATO-JSON >> ENV VARS
- `robotmk`
  - COnfig aus Environemnt (alternativ, z.b. zum Debuggen: `-c /path/to/robotmk-specialagent.json --mode specialagent` 
  - one shot: Ermittlung aller "due robots"
- foreach "due Robot": `Robocorp/K8s API Runner` 
  - API Call ("fire and forget")
- generate Agent output (siehe III.)

### Produce Agent Output 



in Subprozess: 
II) RMK startet mit `--robot suiteA` == mode "robot", run "suiteA"
- Wir sind jetzt bereits im richtigen Python-Kontext (ggf. innerhalb RCC)
- config 
  - von YML 
  - overload von Env (-> mode + suite)
- Robot-Ausführung wie gehabt: 
  - Statefile start
  - `robot %ARGUMENTS% e2e-test.robot`
  - schreibe XML/HTML in $LOG


III) RMK startet mit `output` ODER interner call im Special Agent 

- config ist bereits geladen - alle Suites sind bekannt
- foreach suite: $suite_result.json 
  - Wenn `output`: vom FS
  - Wenn `specialagent`: von API 





## Prototyping 

- Logging f. agent.py
- agent.py schreibt kein pid file
- Process-ID kann nicht ermittelt werden, wenn 
- Detached from agent? 
- Facade-Plugin 
  - Powershell 
    - TODO: Entfernen des Flagfiles im RCC-Postscript?
  - Bash 
- holotree.zip shippen
- apscheduler: loop/oneshot mode 
- Conf2Env

DONE: 
- Ps1-Facade-Plugin
- Robotmk als Python-Modul
- RobotmkModul => start als commandline tool `robotmk`
- Robot-Definition für Robotmk-RCC (conda, robot.yml ... )
- Shell/PS1 basierter Aufbau eines RCC-Environments
  - Validieren eines einsatzfähigen RCC-ENVs
- robotmk-ctrl.ps1 schreibt jedes mal ``robotmk_controller_last_execution` - wenn zu alt, Ende von Agent-Daemon
- robotmk auf pypi




## Open Questions


- RCC als Enterprise-Feature? 
- Wie kann `robotmk.ps1` feststellen, dass das RCC-Env da ist?  
- Wie groß ist ein Robotmk-RCC?
  - 51 MB (standard)
  - 260MB (rpaframework)
- holotree.zip für welche Plattformen
- hat robotmk-ctrl die Zeit das RCC-Env zu bauen? Wird es weggeräumt ? (async)
- Wie kann der Special Agent parametrisiert werden? (JSON ist gesetzt, aber STDIN/commandline args?)
- %ROBOCORP_HOME%: Parametrisierbar? Wo ist der Default? 
- Über Bakery auch rcc's settings.yaml konfigurieren 
  - proxy 
  - logo
- Verlässliches TMP-File für RCC? 
- Playwright nur 1 Browser? 
- Run-UUID und State in Name von HTML/XML einbauen? 
- Vermeide RW-Konflikt, wenn Resultfiles geschrieben werden und gleichzeitig gelesen!
- `rcc interactive configuration` => yaml Profile erzeugen (http proxy, PEM certificates etc. )

## Setup 

pipenv install 
pipenv install -e . 
pipenv shell 


## Notizen 
### robotmk.yml


```
global: 
  mode: agent/specialagent/output/suite
  k8s-auth:
    user: foo
    pass: bar
    url: https://foo/api/v2
  robocorp-auth:
    user: foo
    pass: bar
    url: https://foo/api/v2
suites: 
  suiteA: 
    target: fs/robocorp/kubernetes
    use_rcc: yes(default)/no
    suite_file: anothersuitename.robot





ROBOTMK_global_mode=suite
ROBOTMK_suites_suiteA_use_rcc=yes
```


## FLit / bumpversion workflow

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
## Problem 


