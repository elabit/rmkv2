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
        self, name="robotmk_agent_daemon", pidfile=None, ctrl_file_controlled=False
    ):
        self.name = name
        # match a python call for robotmk agent fg/bg, but not if the VS Code debugger is attached
        # self.proc_pattern = "python(?:(?!debugpy).)*(robotmk|cli).*agent\s[bf]g"
        self.proc_pattern = "(?:(?!debugpy).)*(robotmk|cli).*agent\s[bf]g"
        if not pidfile:
            # TODO: find a path that is accessible from insice RCC and outside
            pidfile = "%s.pid" % self.name

            print(__name__ + ": (Daemon init) " + "tmpdir is: %s" % self.tmpdir)
            self.pidfile = self.tmpdir / pidfile
            print(__name__ + ": (Daemon init) " + "Pidfile is: %s" % self.pidfile)
        else:
            self.pidfile = Path(pidfile)
        self.ctrl_file_controlled = ctrl_file_controlled
        self.lastexecfile_path = self.tmpdir / "robotmk_controller_last_execution"

        # if platform.system() == "Linux":
        #     self.fork_strategy = LinuxStrategy(self)
        # elif platform.system() == "Windows":
        #     self.fork_strategy = WindowsStrategy(self)

    # def daemonize(self):
    #     self.fork_strategy.daemonize()
    #     self.write_and_register_pidfile()

    @property
    def tmpdir(self):
        # if env var does not exist, throw exception
        if not os.getenv("CMK_AGENT_DIR"):
            raise Exception(
                "TBD: Environment variable CMK_AGENT_DIR not set. Please set it to the path of the agent directory."
            )
        return Path(os.environ.get("CMK_AGENT_DIR")) / "tmp"

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
            return self.ctrl_file_is_fresh()
        else:
            return True

    def ctrl_file_is_fresh(self):
        # if exists
        if not self.lastexecfile_path.exists():
            return False
        else:
            mtime = os.path.getmtime(self.lastexecfile_path)
            now = time.time()
            if now - mtime < 300:
                return True
            else:
                return False

    def unlink_pidfile(self):
        """Deletes the PID file"""
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    def touch_pidfile(self):
        # TODO: file gets not written! (at least not on windows)
        try:
            with open(self.pidfile, "w+", encoding="ascii") as f:
                f.write(str(self.pid) + "\n")
        except IOError:
            print(__name__ + ": " + "Could not write PID file %s" % self.pidfile)
            sys.exit(1)

        # with open(
        #     "C:\\Users\\vagrant\\Documents\\01_dev\\rmkv2\\agent\\tmp\\foo.pid",
        #     "w+",
        #     encoding="ascii",
        # ) as f:
        #     f.write(str(self.pidfile) + "\n")

        # FIXME: pidfile gets not deleted if daemon was started with Debugger!
        atexit.register(self.unlink_pidfile)

    def start(self):
        if not self.is_already_running():
            print(__name__ + ": (start) " + "Try to start %s" % self.name)
            while self.running_allowed():
                self.touch_pidfile()
                # DUMMY DAEMON CODE
                print(__name__ + ": " + "Daemon is running ... ")
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
            print(
                __name__
                + ": "
                + f"Exiting now, bye! (Reason: missing/outdated controller file {self.lastexecfile_path})"
            )
            self.unlink_pidfile()
            sys.exit(200)
            # TODO: Exit code 200 should signal the controller the reason (so that outdated flag file gets logged)

    def _get_process_list(self):
        """Returns a list of Process objects matching the search pattern"""
        listOfProcessObjects = []
        # Iterate over the all the running process
        for proc in psutil.process_iter():
            try:
                pinfo = proc.as_dict(attrs=["pid", "name", "cmdline"])
                # Check if process name contains the given name string.
                if pinfo["cmdline"] and re.match("cli.py", " ".join(pinfo["cmdline"])):
                    pass
                if pinfo["cmdline"] and re.match(
                    self.proc_pattern, " ".join(pinfo["cmdline"])
                ):
                    listOfProcessObjects.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return listOfProcessObjects

    def is_already_running(self):
        """Returns True if there is another instance running with another PID"""
        processIds = self._get_process_list()
        if len(processIds) > 1:
            # Determine foreing pid by removing own pid from list
            pids = [p["pid"] for p in processIds]
            pids.pop(pids.index(self.pid))
            print(
                "Another instance of %s is already running with PID %d. Aborting."
                % (self.name, pids[0])
            )
            return True
        else:
            return False

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
