import time, sys, os

from apscheduler.schedulers.background import BackgroundScheduler

# from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
from .abstract import AbstractExecutor
from robotmk.main import Robotmk


class Scheduler(AbstractExecutor):
    def __init__(self, config, *args, **kwargs):
        # TODO: Max. number of prcesses must be lower than the number of CPUs
        super().__init__(config)
        self.scheduler = BackgroundScheduler(
            executors={"mydefault": ProcessPoolExecutor(6)}
        )
        # self.scheduler = BlockingScheduler(
        #     executors={"mydefault": ProcessPoolExecutor(6)}
        # )

    def foo(self, *args, **kwargs):
        print("foo", args, kwargs)
        sys.stdout.flush()

    def log(self, msg):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        # with open(logfile, "a") as f:
        #     f.write(f"{timestamp} [{os.getpid()}] {msg}\n")
        print(f"{timestamp} [{os.getpid()}] {msg}\n")

    def schedule_jobs(self):
        """Updates the scheduler with new jobs and removes old ones"""
        # current_jobs = set(self.scheduler.get_jobs())
        # new_jobs = set(self.config.get("suites", {}))

        # # Remove jobs that are no longer in the config
        # for job in current_jobs - new_jobs:
        #     self.scheduler.remove_job(job.id)
        suites = self.config.get("suites").asdict().keys()
        for suite in suites:
            rmk = Robotmk(
                log_level=self.config.get("common.log_level"),
                contextname="suite",
                default_cfg=self.config.asdict(),
            )
            rmk.config.set("common.suiteuname", suite)
            interval = rmk.config.get("suitecfg.scheduling.interval", None)
            # TODO: skip and log if no interval set
            self.scheduler.add_job(
                # rmk.execute,
                self.foo,
                "interval",
                id=rmk.config.hash,
                seconds=interval,
                replace_existing=True,
                # args=[v],
                # max_instances=1,
            )

    def run(self):
        """Start the scheduler and update the jobs every 5 seconds"""
        # self.scheduler.add_listener(log)

        self.schedule_jobs()
        self.scheduler.add_listener(self.log)
        self.scheduler.start()
        while True:
            # update the jobs every 5 seconds
            time.sleep(5)
        # print("Running tasks: " + str(scheduler.print_jobs()))
