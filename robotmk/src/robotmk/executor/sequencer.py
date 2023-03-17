from .abstract import AbstractExecutor


class Sequencer(AbstractExecutor):
    def __init__(self, config):
        # Create the sequencer.

        super().__init__(config)

    def __schedule_jobs(self):
        """Updates the scheduler with new jobs and removes old ones"""
        current_jobs = set(self.scheduler.get_jobs())
        new_jobs = set(self.config.get("tasks", []))

        # Remove jobs that are no longer in the config
        for job in current_jobs - new_jobs:
            self.scheduler.remove_job(job.id)

        # Add or update the tasks
        for task in tasklist["tasks"]:
            pass

    def run(self):
        """Start the scheduler and update the jobs every 5 seconds"""
        # self.scheduler.add_listener(log)
        # Start the scheduler
        self.scheduler.start()
        while True:
            self.__schedule_jobs()
            time.sleep(5)
            # print("Running tasks: " + str(scheduler.print_jobs()))
