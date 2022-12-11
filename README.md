

# Robotmk V2

## I. Robotmk as Agent Plugin 

### a) "Output" mode 

- (RCC env creation done in b) )
- `robotmk.ps1` (sync)
  - steht das RCC-env für robotmk bereit?
    - nein 
      - exit (Aufbau erledigt async-Teil) 
    - ja
      - `rcc task run -t robotmk-output` => startet `robotmk.py --mode output`
        - Config aus File 
        - iteriere über Robots, lese Ergebnisse, printe Output 


### b) "Agent" mode

 
- `robotmk-ctrl.ps1` (Process and environment creation, async) 
  - steht das RCC-env für robotmk bereit?
    - nein => RCC env creation
      - Create DETACHED_PROCESS
      - RCC-Env aufbauen: `rcc ht vars` 
      - exit 
    - ja
      - Create DETACHED_PROCESS
      - `rcc task run -t robotmk-agent` => startet `bin/robotmk.py --mode agent` 
- `robotmk agent`
  - Config aus File 
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


## II. Robotmk im Robot-Mode
`ROBOTMK_mode=robot` bzw `--mode=robot`=> Ausführung eines einzelnen Robots (im OS- oder RCC-Python)

- `robotmk`
  - Config aus Environment (alternativ: `-c path/to/robotmk.json --mode robot --run suiteA`)
  - Ausführen der Suite `robotmk.robot` in `$ROBOTDIR/suiteA/`
    - Alternatives .robot-File: Setzen von `suite_file=anothersuite.robot`
    - Aufruf von `robot --param1 ... --name suiteA robotmk.robot`
      - `--name` sorgt dafür, dass die toplevel suite nicht "Robotmk" heißt, sondern so wie die suite
  - Schreiben des Results




## Robotmk as Special Agent 

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





# Prototyping 

- Shell/PS1 basierter Aufbau eines RCC-Environments
  - Validieren eines einsatzfähigen RCC-ENVs
  - holotree.zip shippen
- apscheduler: loop/oneshot mode 
- Robot-Definition für Robotmk-RCC (conda, robot.yml ... )
- Conf2Env

DONE: 
- RobotmkModul => start als commandline tool `robotmk`

# Open Questions

- Wie kann `robotmk.ps1` feststellen, dass das RCC-Env da ist?  
- Wie groß ist ein Robotmk-RCC?
  - 51 MB (standard)
  - 260MB (rpaframework)
- holotree.zip für welche Plattformen
- hat robotmk-ctrl die Zeit das RCC-Env zu bauen? Wird es weggeräumt ? (async)
- Wie kann der Special Agent parametrisiert werden? (JSON ist gesetzt, aber STDIN/commandline args?)
- Kann robotmk-ctrl.ps1 %ROBOCORP_HOME% im system setzen? Windows? Linux? 

# Setup 

pipenv install -e . 
pipenv shell 



# robotmk.yml


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