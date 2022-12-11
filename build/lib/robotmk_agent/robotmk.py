#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2022 ELABIT GmbH <mail@elabit.de>
# SPDX-License-Identifier: GPL-3.0-or-later
# This file is part of the Robotmk project (https://www.robotmk.org)

import json
import os
import sys

__version__ = "0.0.1"

def main(mode):
    print("This is mode {mode}")



if __name__ == "__main__":
    main("agent")

def agent():
    print("This is the agent main!")

def specialagent():
    print("This is the special agent main!")

def robot():
    print("This is the robot main!")