from abc import ABC, abstractmethod


class Job(ABC):
    def __init__(self, job_id, job_data):
        self.job_id = job_id
        self.job_data = job_data

    @abstractmethod
    def run_job(self):
        pass

    @abstractmethod
    def get_jobs_running(self):
        """Returns the number of running jobs currently."""
        pass

    @abstractmethod
    def kill_job(self):
        pass

    @property
    def suiteid(self):
        """Create a unique ID from the Robot path (dir/.robot file) and the tag.
        with underscores for everything but letters, numbers and dot."""
        if bool(self.tag):
            tag_suffix = "_%s" % self.tag
        else:
            tag_suffix = ""
        composite = "%s%s" % (self.path, tag_suffix)
        outstr = re.sub("[^A-Za-z0-9\.]", "_", composite)
        # make underscores unique
        return re.sub("_+", "_", outstr).lower()
