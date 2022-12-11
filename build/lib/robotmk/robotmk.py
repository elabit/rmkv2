#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2022 ELABIT GmbH <mail@elabit.de>
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of the Robotmk project (https://www.robotmk.org)

import json
import os
import sys
from abc import ABC, abstractmethod

# TODO:
# from robotmk_agent import Daemon


__version__ = "0.0.1"


#


def main(mode):
    print("This is mode {mode}")


class RobotmkAgent:
    """Base class for Robotmk Agent and Special Agent"""

    pass


if __name__ == "__main__":
    main("agent")


def run_agent():
    print("Robotmk is starting the agent routine!")


def run_specialagent():
    print("Robotmk is starting the special agent routine!")


def run_robot():
    print("Robotmk is starting the robot routine!")


def run_output():
    print("Robotmk is starting the output routine!")
