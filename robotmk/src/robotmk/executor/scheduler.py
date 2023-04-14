import time, sys, os

from apscheduler.schedulers.background import BackgroundScheduler

# from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
from .abstract import AbstractExecutor
from robotmk.main import Robotmk
import subprocess
from tabulate import tabulate


class Scheduler(AbstractExecutor):
    def __init__(self, config, *args, **kwargs):
        # TODO: Max. number of prcesses must be lower than the number of CPUs
        super().__init__(config)
        self.scheduler = BackgroundScheduler(
            executors={"mydefault": ProcessPoolExecutor(6)}
        )
        self.suitecfg_hashes = {}
        # self.scheduler = BlockingScheduler(
        #     executors={"mydefault": ProcessPoolExecutor(6)}
        # )

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

    def schedule_jobs(self):
        """Updates the scheduler with new jobs and removes old ones"""
        suites = self.config.get("suites")
        current_jobs = set(self.scheduler.get_jobs())
        # remove jobs that are no longer in the config
        for job in current_jobs - set(suites.asdict().keys()):
            self.scheduler.remove_job(job.id)
        # schedule new/changed jobs
        for suiteuname, suitecfg in suites:
            hash = self.config.suite_cfghash(suiteuname)
            if hash == self.suitecfg_hashes.get(suiteuname, {}):
                # The suite config has not changed, so we can skip it
                continue
            else:
                run_env = self.prepare_environment(suiteuname)
                interval = suitecfg.get("scheduling.interval")

                self.scheduler.add_job(
                    self.start_robotmk_process,
                    args=[run_env],
                    trigger="interval",
                    id=suiteuname,
                    seconds=interval,
                    replace_existing=True,
                    # args=[v],
                    max_instances=1,
                )
                self.suitecfg_hashes[suiteuname] = hash

    def run(self):
        """Start the scheduler and update the jobs every 5 seconds"""

        self.schedule_jobs()
        # self.scheduler.add_listener(self.log)
        self.scheduler.start()
        while True:
            # update the jobs every 5 seconds
            time.sleep(5)

            jobs = self.scheduler.get_jobs(jobstore=None)
            table = []
            for job in jobs:
                table.append(
                    [
                        job.id,
                        job.name,
                        # job.args,
                        job.trigger,
                        job.pending,
                        job.next_run_time,
                        job.trigger.interval.total_seconds(),
                    ]
                )
            # print current time
            print(time.strftime("%H:%M:%S", time.localtime()))
            print(
                tabulate(
                    table,
                    headers=[
                        "id",
                        "name",
                        "trigger",
                        "pending",
                        "next_run at",
                        "interval",
                    ],
                )
            )
            print("\n")
