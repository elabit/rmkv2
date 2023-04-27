import time, sys, os
import json
from copy import deepcopy
from collections import defaultdict
from robotmk.main import Robotmk
from robotmk.context.suite.target.abstract import Target

# from robotmk.context.suite.target.factory import TargetFactory

# from tabulate import tabulate


class Emitter:
    def __init__(self, config, *args, **kwargs):
        self.config = config

    def start_robotmk_process(self, run_env):
        cmd = "robotmk suite run".split(" ")
        result = subprocess.run(cmd, capture_output=True, env=run_env)
        # result = subprocess.run(["echo", "foo"], capture_output=True, env=run_env)
        stdout_str = result.stdout.decode("utf-8").splitlines()
        stderr_str = result.stderr.decode("utf-8").splitlines()
        result_dict = {
            "args": result.args,
            "returncode": result.returncode,
            "stdout": stdout_str,
            "stderr": stderr_str,
        }
        pass

    def prepare_environment(self, suiteuname) -> dict:
        run_env = os.environ.copy()
        added_settings = {
            "common.context": "suite",
            "common.suiteuname": suiteuname,
        }
        # run_env = basic config + added settings
        self.config.cfg_to_environment(self.config.configdict, environ=run_env)
        self.config.dotcfg_to_env(added_settings, environ=run_env)
        return run_env

    def run(self):
        """Iterates over all suites and produces agent output"""

        suites = self.config.get("suites")
        results = RMKResults()
        for suiteuname, suitecfg in suites:
            # TODO: handle logging
            self.config.set("common.suiteuname", suiteuname)
            results.add(TargetFactory(suiteuname, self.config, None).create())

        print(results.all_results())


class RMKResults:
    def __init__(self):
        self.result_dict = defaultdict(list)

    def add(self, target: Target):
        self.result_dict[target.piggybackhost].append(target.output())

    def all_results(self):
        out = []
        out += self.piggyback_results(include_logs=False)
        out.append(f"<<<robotmk:sep(0)>>>")
        for result in self.result_dict.get("localhost", []):
            out.append(json.dumps(result, sort_keys=False, indent=2))
        return "\n".join(out)

    def piggyback_results(self, include_logs=True):
        # Piggyback results are all results which have another host than "localhost"
        # assigned to them.
        # For each host, print the header and after that all suite results.
        # "include_logs = False" is used when all_results must be emitted for the checkmk
        # host where the Robotmk service will be. Even if piggyback results are assigned
        # to another host, it needs to know the runtime data of the suite. XML and console
        # logs are not needed in this case.
        out = []
        pbresults = [
            (host, results)
            for host, results in self.result_dict.items()
            if host != "localhost"
        ]
        for host, results in pbresults:
            # begin of piggyback data
            out.append(f"<<<<{host}>>>>")
            out.append(f"<<<robotmk:sep(0)>>>")
            for result in results:
                if not include_logs:
                    result_short = deepcopy(result)
                    del result_short["output"]
                    result = result_short
                out.append(json.dumps(result, sort_keys=False, indent=2))
            # end of piggyback data
            out.append(f"<<<<>>>>")
        return out


"""
piggybackdaten müssen für PB-Host und den HOst ausgegeben werden

print_agent_output
    all_suites_state = check_suite_statefiles: for suite in suites: 
        lese JSON
        welchem host ist die suite zugeordnet? lese piggybackhost, default: "localhost"
        returne dict mit host als key, result als value
    baue liste aus RMKHostdata


"""
