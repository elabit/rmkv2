# Robotmk V2

!!! ALPHA - NOT FOR PRODUCTION !!!

## USAGE

- copy `agent/config/robotmk` into `%Programdata%/checkmk/agent/config/robotmk`
- copy `agent\plugins\robotmk-ctrl.ps1` into `%Programdata%/checkmk/agent/plugins/`

Add to `C:\ProgramData\checkmk\agent\bakery\check_mk.bakery.yml``:


Now start the CMK agent.

`robotmk-ctrl.ps1` (logfile: `C:\ProgramData\checkmk\agent\log\robotmk\robotmk-ctrl.log`) will
- copy itself and the service stub exe to `ProgamData/checkmk/robotmk/RobotmkAgent.exe/.ps1` (is not present)
- Register and start the RobotmkAgent service (if not present/running)
- touch the deadman switch file

`RobotmkAgent.ps1` (logfile: `C:\ProgramData\checkmk\agent\log\robotmk\RobotmkAgent.log`) is started by the service and will
- create the RCC environment for Robotmk (if not present)
- start the Robotmk agent task in RCC
  - the agent runs in a loop and executes Robotmk in sub-processes (not implemented yet)
  - Dummy activity of the Robotmk Agent can be seen in `ProgramData/agent/tmp/robotmk/` (bulk creation of tmp files)
- monitor the deadman switch file (and exit if the file ages out)



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


---


- **SUITE**-Context: `robotmk suite foosuiteA`:
  - if `RCC_possible`:
    - create RCC env
    - source the vars of RC env
  - run the Robot Framework suite
  - store JSON files
  -


- `robotmk suite` + `ROBOTMK_common_suite_suiteA`
  - if RCC is possible:
    - conf2env
    - `ROBOTMK_suites_suiteA__shared_python` = False
    - `rcc task run robotmk robotmk.yml`
- `robotmk suite` + `ROBOTMK_common_suite_suiteA` +  `ROBOTMK_suites_suiteA__shared_python` = False
  - (This omits RCC and uses the same python interpreter)
  - create statefiles
  - handle reexecution
  - run robo_cli with **shared** Python Interpreter inincl. Args
  - write Output



---


## Prototyping

Prio HIGH:
- Windows: anlegen und triggern von Scheduled Tasks für Desktop-Tests
- Logging
  - https://superfastpython.com/multiprocessing-logging-in-python/
- apscheduler: loop/oneshot mode
- ExitHandler Powershell: https://chat.openai.com/chat/738cfffa-39ab-4368-bc20-b1a8e53546d8

Prio MEDIUM:
- holotree.zip shippen

DONE:
- Conf2Env
- Ps1-Facade-Plugin
- Robotmk als Python-Modul
- RobotmkModul => start als commandline tool `robotmk`
- Robot-Definition für Robotmk-RCC (conda, robot.yml ... )
- Shell/PS1 basierter Aufbau eines RCC-Environments
  - Validieren eines einsatzfähigen RCC-ENVs
- robotmk-ctrl.ps1 schreibt jedes mal ``robotmk_controller_last_execution` - wenn zu alt, Ende von Agent-Daemon
- robotmk auf pypi


## Open Questions




- Wie groß ist ein Robotmk-RCC?
  - 51 MB (standard)
  - 260MB (rpaframework)
- Über Bakery auch rcc's settings.yaml konfigurieren
  - proxy
  - logo
- Verlässliches TMP-File für RCC?
- Run-UUID und State in Name von HTML/XML einbauen?
- Vermeide RW-Konflikt, wenn Resultfiles geschrieben werden und gleichzeitig gelesen!
- `rcc interactive configuration` => yaml Profile erzeugen (http proxy, PEM certificates etc. )



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
    scheduling:
      interval: 15
      allow_overlap: true





ROBOTMK_global_mode=suite
ROBOTMK_suites_suiteA_use_rcc=yes
```

## Problem
