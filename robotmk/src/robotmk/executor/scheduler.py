import time, sys
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
from .abstract import AbstractExecutor


class Scheduler(AbstractExecutor):
    def __init__(self, config, *args, **kwargs):
        # TODO: Max. number of prcesses must be lower than the number of CPUs
        super().__init__(config)
        self.scheduler = BackgroundScheduler(
            executors={"mydefault": ProcessPoolExecutor(6)}
        )

    def __schedule_jobs(self):
        """Updates the scheduler with new jobs and removes old ones"""
        current_jobs = set(self.scheduler.get_jobs())
        new_jobs = set(self.config.get("tasks", []))

        # Remove jobs that are no longer in the config
        for job in current_jobs - new_jobs:
            self.scheduler.remove_job(job.id)

        # Add or update the tasks
        for task in tasklist["tasks"]:
            self.scheduler.add_job(
                # the callable to run
                run_task,
                # the trigger to use (date, interval, cron, etc.)
                "interval",
                # the interval in seconds
                seconds=task["interval"],
                id=task["name"],
                replace_existing=True,
                # the argument to pass to the callable (here: interval)
                args=[task["interval"]],
                # the maximum number of instances of the job that can run at the same time
                # By default, only one job instance is allowed to run.
                max_instances=task["max_instances"],
            )

    def run(self):
        """Start the scheduler and update the jobs every 5 seconds"""
        # self.scheduler.add_listener(log)
        # Start the scheduler
        print("Scheduler.run()")
        sys.exit(0)
        self.scheduler.start()
        while True:
            self.__schedule_jobs()
            time.sleep(5)
            # print("Running tasks: " + str(scheduler.print_jobs()))
