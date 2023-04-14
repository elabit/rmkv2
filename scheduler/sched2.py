import os
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ProcessPoolExecutor


def job(task_id):
    print(f"Task {task_id} running in process ID: {os.getpid()}")


scheduler = BackgroundScheduler(executors={"mydefault": ProcessPoolExecutor(6)})

# Schedule multiple instances of the job
for i in range(1, 6):
    scheduler.add_job(
        job,
        "interval",
        seconds=2,
        id=f"task{i}",
        replace_existing=True,
        args=[i],
        max_instances=1,
    )

scheduler.start()

try:
    # Keep the main thread alive
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    scheduler.shutdown()
