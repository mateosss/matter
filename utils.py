#!/usr/bin/env python3

from subprocess import run, PIPE
from shutil import which

# Logging utils

def color_string(string, fg=None):
    COLORS = {  # List some colors that may be needed
        "red": "\033[31m",
        "pink": "\033[38;5;206m",
        "green": "\033[32m",
        "orange": "\033[33m",
        "blue": "\033[34m",
        "cyan": "\033[36m",
        "lightred": "\033[91m",
        "lightgreen": "\033[92m",
        "yellow": "\033[93m",
        "lightblue": "\033[94m",
        "lightcyan": "\033[96m",
        "brightwhite": "\u001b[37;1m",
        "brightmagenta": "\u001b[35;1m",
    }
    endcolor = "\033[0m"
    return f"{COLORS.get(fg, '')}{string}{endcolor}"


def info(*lines):
    for line in lines:
        print(f"{color_string('[I] ', fg='cyan')}{line}")


def error(*lines, should_exit=True):
    for line in lines:
        print(f"{color_string('[E] ', fg='lightred')}{line}")
    if should_exit:
        exit(1)

def warning(*lines):
    for line in lines:
        print(f"{color_string('[W] ', fg='yellow')}{line}")


# Shell / external utils


def sh(command):
    "Executes command in shell and returns its exit status"
    return run(command, shell=True).returncode


def shout(command, silence=False):
    "Executes command in shell and returns its stdout"
    stdout = run(command, shell=True, stdout=PIPE).stdout.decode("utf-8")
    if not silence:
        print(stdout)
    return stdout


def has_command(command):
    return which(command) is not None
