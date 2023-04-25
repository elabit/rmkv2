import yaml
import time
import os
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-s", help="Run the scheduler", action="store_true")
parser.add_argument("-i", help="Interval in seconds", type=int, default=5)

args = parser.parse_args()

logfile = Path(os.path.dirname(os.path.abspath(__file__))) / "scheduler.log"


def run_task(interval):
    # get absolute path of this file
    filename = Path(os.path.dirname(os.path.abspath(__file__))) / os.path.basename(
        __file__
    )

    os.system(f"python {filename} -i {interval}")


def start_scheduler():
    cwd = Path(os.path.dirname(os.path.abspath(__file__)))

    with open(cwd / "tasks.yml") as f:
        tasklist = yaml.safe_load(f)

    print("CPUS: " + str(os.cpu_count()))

    # Create the scheduler. Max. number of prcesses must be lower than the number of CPUs
    scheduler = BackgroundScheduler(executors={"mydefault": ProcessPoolExecutor(6)})

    # Add the task to the scheduler
    for task in tasklist["tasks"]:
        scheduler.add_job(
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

    scheduler.add_listener(log)

    # Start the scheduler
    scheduler.start()

    while True:
        time.sleep(1)
        # print("Running tasks: " + str(scheduler.print_jobs()))


def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open(logfile, "a") as f:
        f.write(f"{timestamp} [{os.getpid()}] {msg}\n")


if __name__ == "__main__":
    # echo pid
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    # run_task()
    if args.s:
        start_scheduler()
    else:
        # write own pid and timestamp to logfile
        log(f"Interval: {args.i} seconds")
        sleeptime = args.i + 5
        log(f"Sleeptime: {sleeptime}")
        time.sleep(sleeptime)
        log("END")
