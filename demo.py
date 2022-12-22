#!/usr/bin/env python

# Demonstate the use

# Preparations:
# 1. open "C:\\Users\\vagrant\\Documents\\01_dev\\rmkv2\\agent" in explorer


import os
import sys
from pathlib import Path
import shutil
from time import sleep
import re
import subprocess
from timeit import default_timer
from datetime import timedelta

CMK_AGENT_DIR = Path(
    os.getenv("CMK_AGENT_DIR", "C:\\Users\\vagrant\\Documents\\01_dev\\rmkv2\\agent")
)
AGENT_TMP_DIR = CMK_AGENT_DIR / "tmp"
RCC_DIR = Path(os.getenv("ROBOCORP_HOME"))
ROBOTMK_RCCLIBDIR = CMK_AGENT_DIR / "lib/rcc_robotmk"
RCCEXE = CMK_AGENT_DIR / "bin/rcc.exe"
RCC_HOMES = Path("C:/Users/vagrant/Documents/rc_homes")


def main():
    build_with_internet("rcc_via_internet", export=False)
    build_with_hololib("rcc_hololib_zip")
    pass


def build_with_internet(home, export):
    headline("Building RCC via internet in %s" % home)
    set_rcc_home(home)
    tabula_rasa()
    set_hololib_active(False)
    robotmk_ctrl()
    wait_for_rcc(export=export)


def build_with_hololib(home):
    headline("Building RCC via hololib.zip in %s" % home)
    build_with_internet(home, export=True)

    set_rcc_home(home)
    tabula_rasa()
    set_hololib_active(True)
    robotmk_ctrl()
    wait_for_rcc(export=False)
    # set_hololib_active(False)


def rcc_ht_check():
    log("rcc ht check...")
    command = [str(RCCEXE), "ht", "check"]
    ret = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ).stdout.decode()
    print(ret)


def set_rcc_home(dir):
    os.environ["ROBOCORP_HOME"] = str(RCC_HOMES / dir)
    log("ROBOCORP_HOME = %s" % os.environ["ROBOCORP_HOME"])


def rcc_ht_hash(conda_yaml):
    log("rcc ht hash...")
    command = [str(RCCEXE), "ht", "hash", str(conda_yaml)]
    ret = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ).stdout.decode()
    match = re.match("Blueprint hash for.*is (?P<blueprint>[A-Za-z0-9]*)\.", ret)
    if match:
        return match.group("blueprint")
    else:
        return ""


def rcc_ht_catalogs():
    # log("rcc ht catalogs...")
    command = [str(RCCEXE), "ht", "catalogs"]
    out = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ).stdout.decode()
    return out


def rcc_ht_export(robot_yaml, zipfile):
    log("rcc ht export...")
    command = [
        str(RCCEXE),
        "ht",
        "export",
        "--robot",
        str(robot_yaml),
        "--zipfile",
        str(zipfile),
    ]
    while True:  # try until success
        ret = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = ret.stdout.decode()
        print(output)
        rc = ret.returncode
        if rc == 0:
            break
        else:
            sleep(0.2)


def rcc_ht_vars(robot_yaml):
    log("rcc ht vars...")
    command = [str(RCCEXE), "ht", "vars", "--robot", str(robot_yaml)]
    ret = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = ret.stdout.decode()
    # print(output)
    rc = ret.returncode
    if rc == 0:
        print("RCC env is ready to use!")
    else:
        print("RCC env is NOT ready to use! Some error occured.")


def wait_for_rcc(export=False):
    # get blueprint for conda.yml
    print("ROBOCORP_HOME = %s" % os.environ["ROBOCORP_HOME"])

    blueprint = rcc_ht_hash(str(ROBOTMK_RCCLIBDIR / "conda.yaml"))
    print("Blueprint: %s" % blueprint)

    tic = default_timer()
    command = [str(RCCEXE), "ht", "catalogs"]
    print("Waiting...")
    while True:
        # get catalogs available
        if blueprint in rcc_ht_catalogs():
            print("Blueprint %s was found in catalogs!" % blueprint)
            break
        else:
            sleep(0.5)
            print(".", end="")
    # TODO: Why does
    rcc_ht_vars(str(ROBOTMK_RCCLIBDIR / "robot.yaml"))
    tac = default_timer()
    elapsed = timedelta(seconds=tac - tic)
    print(f"Elapsed time: {elapsed}")
    # ask if export command should be executed
    # answer = input("Execute holotree export? [y/n] ")
    if export == True:
        # rcc_ht_hash(str(ROBOTMK_RCCLIBDIR / "conda.yaml"))
        rcc_ht_export(
            str(ROBOTMK_RCCLIBDIR / "robot.yaml"),
            str(ROBOTMK_RCCLIBDIR / "hololib.zip"),
        )


def set_hololib_active(state):
    # if active, rename hololib.zip to hololib.zip
    hl_active = ROBOTMK_RCCLIBDIR / "hololib.zip"
    hl_inactive = ROBOTMK_RCCLIBDIR / "hololib_.zip"
    if state:
        if hl_active.exists():
            hl_active.unlink()
        if hl_inactive.exists():
            shutil.copy(str(hl_inactive), str(hl_active))
        else:
            raise Exception("Inactive hololib.zip does not exist, nothing to activate.")
    else:
        # if exists
        if hl_active.exists():
            hl_active.unlink()
        else:
            pass


def rmdir(directory):
    directory = Path(directory)
    for item in directory.iterdir():
        if item.is_dir():
            rmdir(item)
        else:
            item.unlink()
    directory.rmdir()


def robotmk_ctrl():
    log(">>> Starting Controller")
    os.environ["RMK_CTRL"] = "1"
    robotmk()


def robotmk_agent():
    log(">>> Starting Agent")
    os.environ["RMK_CTRL"] = "0"
    robotmk


def robotmk():
    os.system("powershell.exe -File %s" % (CMK_AGENT_DIR / "plugins/robotmk-ctrl.ps1"))


def tabula_rasa():
    del_dir(os.environ["ROBOCORP_HOME"])
    rcc_ht_check()
    cleanup_dir(AGENT_TMP_DIR)
    set_hololib_active(False)


def del_dir(dir):
    log("Deleting dir: %s" % dir)
    if os.path.exists(dir):
        rmdir(dir)


def cleanup_dir(dir):
    log("Cleaning up files in dir: %s" % dir)
    for file in os.listdir(dir):
        file_path = Path(os.path.join(dir, file))
        if os.path.isfile(file_path):
            # delete file
            file_path.unlink()


def headline(text):
    print("===={}====".format(text))


def log(text):
    print("> %s" % text)


if __name__ == "__main__":
    main()
