#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2022 ELABIT GmbH <mail@elabit.de>
# SPDX-License-Identifier: GPL-3.0-or-later


import sys, os, time, atexit, signal
import platform
from abc import ABC, abstractmethod
from pathlib import Path
import re
import psutil


class RMKAgent:
    def __init__(
        self,
        name="robotmk_agent_daemon",
        ctrl_deadman_file_freshness=300,
        ctrl_file_controlled=False,
    ):
        self.name = name
        self.pidfile = self.tmpdir / f"{self.name}.pid"
        self.ctrl_deadman_file_freshness = ctrl_deadman_file_freshness
        # match a python call for robotmk agent fg/bg, but not if the VS Code debugger is attached
        # self.proc_pattern = "(?:(?!debugpy).)*(robotmk|cli).*agent\s[bf]g"

        # if True, the agent will only run if the controller file is fresh
        self.ctrl_file_controlled = ctrl_file_controlled
        # path to the file that gets written by facade plugin at each agent trigger
        self.rmk_ctrl_deadman_file = self.tmpdir / "robotmk_controller_deadman_file"
        # path to file where the agent cann signal the controller the reason for exiting
        self.last_agent_exitmsg_file = self.tmpdir / "robotmk_agent_lastexitcode"

        print(__name__ + ": (Daemon init) " + "tmpdir is: %s" % self.tmpdir)
        print(__name__ + ": (Daemon init) " + "Pidfile is: %s" % self.pidfile)

    @property
    def agentpath(self):
        # TODO:  should be wirhtin CMK Agent later
        # For now, lets use system tmp dir

        if platform.system() == "Windows":
            tmppath = Path(os.getenv("TEMP")) / "robotmk"
        else:
            tmppath = Path("/tmp") / "robotmk"
        return tmppath

    @property
    def logdir(self):
        logpath = self.agentpath / "log"
        logpath.mkdir(parents=True, exist_ok=True)
        return logpath

    @property
    def tmpdir(self):
        tmpdir = self.agentpath / "tmp"
        tmpdir.mkdir(parents=True, exist_ok=True)
        return tmpdir

    @property
    def pid(self):
        return os.getpid()

    def get_pid_from_file(self):
        try:
            with open(self.pidfile, "r") as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None
        return pid

    def kill_all(self, processes):
        for process in processes:
            os.kill(process["pid"], signal.SIGTERM)

    def running_allowed(self):
        if self.ctrl_file_controlled:
            return self.ctrl_deadman_file_is_fresh()
        else:
            return True

    def ctrl_deadman_file_is_fresh(self):
        # if exists
        if not self.rmk_ctrl_deadman_file.exists():
            return False
        else:
            mtime = os.path.getmtime(self.rmk_ctrl_deadman_file)
            now = time.time()
            if now - mtime < self.ctrl_deadman_file_freshness:
                return True
            else:
                return False

    def unlink_pidfile(self):
        """Deletes the PID file"""
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    def touch_pidfile(self):
        try:
            with open(self.pidfile, "w+", encoding="ascii") as f:
                f.write(str(self.pid) + "\n")
        except IOError:
            print(__name__ + ": " + "Could not write PID file %s" % self.pidfile)
            sys.exit(1)
        # deletes the pidfile on exit
        atexit.register(self.unlink_pidfile)

    def exit_with_filecode(self, code, message=""):
        # Writes the exit code and message to a file, so that the controller
        # can read it, and exits
        with open(self.last_agent_exitmsg_file, "w") as f:
            f.write(f"{str(code)} {message}")
        sys.exit(int(code))

    def start(self):
        # It is not the job of Robotmk itself to watch running processes of itself; this
        # must be done by the controller. Robotmk takes care of the PID file only!
        # Ref: 5ea7ddc (robotmk-ctrl.ps1)
        if self.pidfile.exists():
            # TODO: if no process with this pid exists, dont exit but start anyway
            # read pid from file
            pid = self.get_pid_from_file()
            # check if process with this pid exists
            if pid and psutil.pid_exists(pid):
                self.exit_with_filecode(
                    201,
                    "Robotmk Agent exited, Reason: PID file exists, can start only once.",
                )

        print(__name__ + ": (start) " + "Try to start %s" % self.name)
        # The daemon should continuously monitor the deadman file and exit if it is not fresh.
        while self.running_allowed():
            self.touch_pidfile()
            # DUMMY DAEMON CODE
            print(__name__ + ": " + "Robotmk agent is running (PID: %d)" % self.pid)
            for i in range(20):
                if i == 19:
                    # remove all files
                    for file in self.tmpdir.glob("robotmk_output_*.txt"):
                        file.unlink()
                else:
                    filename = "robotmk_output_%d.txt" % i
                    with open(self.tmpdir / filename, "w") as f:
                        f.write("foobar output")
                    time.sleep(0.5)
        # This point is reached only when the while loop is exited and the
        # agent is not allowed to run anymore
        self.unlink_pidfile()
        self.exit_with_filecode(
            202,
            "Robotmk Agent exited, Reason: missing/outdated controller file {self.lastexecfile_path}",
        )

    # def _get_process_list(self):
    #     """Returns a list of Process objects matching the search pattern"""
    #     listOfProcessObjects = []
    #     # Iterate over the all the running process
    #     for proc in psutil.process_iter():
    #         try:
    #             pinfo = proc.as_dict(attrs=["pid", "name", "cmdline"])
    #             # Check if process name contains the given name string.
    #             # if pinfo["cmdline"] and re.match("cli.py", " ".join(pinfo["cmdline"])):
    #             #     pass
    #             if pinfo["cmdline"] and re.match(
    #                 self.proc_pattern, " ".join(pinfo["cmdline"])
    #             ):
    #                 listOfProcessObjects.append(pinfo)
    #         except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
    #             pass
    #     return listOfProcessObjects

    # def is_already_running(self):
    #     """Returns True if PIDfile present"""
    #     processIds = self._get_process_list()
    #     print(processIds)
    #     if len(processIds) > 1:
    #         # Determine foreing pid by removing own pid from list
    #         pids = [p["pid"] for p in processIds]
    #         pids.pop(pids.index(self.pid))
    #         print(
    #             "Other instance(s) of %s already running (PID: %s). Aborting."
    #             % (self.name, str(pids))
    #         )
    #         return True
    #     else:
    #         return False

    def stop(self):
        # Check for a pidfile to see if the daemon already runs
        pid = self.get_pid_from_file()

        if not pid:
            message = "pidfile {0} does not exist. " + "Daemon does not seem to run.\n"
            print(__name__ + ": " + message.format(self.pidfile))
            return  # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            e = str(err.args)
            self.unlink_pidfile()
            sys.exit()
            # delete
            # e = "(22, 'Falscher Parameter', None, 87, None)"
            # kommt manchmal - abfangen: (13, 'Zugriff verweigert', None, 5, None)
            if e.find("No such process") > 0 or re.match(".*22.*87", e):
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print(__name__ + ": " + str(err.args))
                sys.exit(1)

    def restart(self):
        """Restart the daemon."""
        print(__name__ + ": " + "Restarting daemon ... ")
        self.stop()
        self.start()


# class ForkStrategy(ABC):
#     def __init__(self, daemon):
#         self.daemon = daemon

#     @abstractmethod
#     def daemonize(self):
#         pass


# class LinuxStrategy(ForkStrategy):
#     def daemonize(self):

#         try:
#             # FORK I) the child process
#             pid = os.fork()
#             if pid > 0:
#                 # exit the parent process
#                 sys.exit(0)
#         except OSError as err:
#             sys.stderr.write("fork #1 failed: {0}\n".format(err))
#             sys.exit(1)

#         # executed as child process
#         # decouple from parent environment, start new session
#         # with no controlling terminals
#         os.chdir("/")
#         os.setsid()
#         os.umask(0)

#         # FORK II) the grandchild process
#         try:
#             pid = os.fork()
#             if pid > 0:
#                 # exit the child process
#                 sys.exit(0)
#         except OSError as err:
#             sys.stderr.write("fork #2 failed: {0}\n".format(err))
#             sys.exit(1)

#         # here we are the grandchild process,
#         # daemonize it, connect fds to /dev/null stream
#         sys.stdout.flush()
#         sys.stderr.flush()
#         si = open(os.devnull, "r")
#         so = open(os.devnull, "a+")
#         se = open(os.devnull, "a+")

#         os.dup2(si.fileno(), sys.stdin.fileno())
#         os.dup2(so.fileno(), sys.stdout.fileno())
#         os.dup2(se.fileno(), sys.stderr.fileno())


# class WindowsStrategy(ForkStrategy):
#     def daemonize(self):
#         # On Windows, use ProcessCreationFlags to detach this process from the caller
#         print(__name__ + ": " + "On windows, there is nothing to daemonize....")
#         pass
