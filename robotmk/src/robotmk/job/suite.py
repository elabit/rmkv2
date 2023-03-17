from .job import Job


class Suite(Job):
    """A suite is a job that contains other jobs."""

    def __init__(self):
        super().__init__()
