#!/usr/bin/python3

import sys
import os
import re
from os.path import dirname, isdir
from subprocess import run, check_call
from shutil import which, rmtree, copytree

# Configuration constants

MIN_PYTHON_VERSION = (3, 6)  # Mainly for f-strings

THEME_NAME = "Matter"
INSTALLER_DIR = dirname(os.path.realpath(__file__))
INSTALLATION_SOURCE_DIR = f"{INSTALLER_DIR}/{THEME_NAME}"
INSTALLATION_TARGET_DIR = f"/boot/grub/themes/{THEME_NAME}"

GRUB_DEFAULTS_PATH = f"/etc/default/grub"

THEME_TEMPLATE_PATH = f"{INSTALLER_DIR}/theme.txt.template"
GRUB_DEFAULTS_TEMPLATE_PATH = f"{INSTALLER_DIR}/grub.template"


def sh(command):
    "Executes command in shell"
    return run(command, shell=True).returncode


def has_command(command):
    return which(command) is not None


def update_grub_cfg():
    COMMAND = "update-grub"
    print("[Info] Making grub.cfg with update-grub...")
    assert has_command(COMMAND)
    sh(COMMAND)


def check_python_version():
    installed = (sys.version_info.major, sys.version_info.minor)
    required = MIN_PYTHON_VERSION
    if installed < required:
        raise Exception(
            f"[Error] Python {required[0]}.{required[1]} or later required."
        )


def check_root_or_prompt():
    if os.geteuid() != 0:
        print(f"{THEME_NAME} installer needs root access.")
        exit_code = sh("sudo -v")
        if exit_code != 0:
            raise Exception(
                "[Error] Could not verify root access, you could try with sudo."
            )
        # Relaunch the program with sudo
        child_exit_code = sh(f"sudo {INSTALLER_DIR}/matter.py")
        exit(child_exit_code)  # Propagate exit code


def prepare_source_folder():
    "Applies any transformation related to the source folder to copy from"

    # Temporary settings until user args are implemented
    highlight = "#E91E63"  # pink
    foreground = "#CCCCCC"  # white
    background = "#263238"  # dark-gray

    # Parse theme template with user preferences
    with open(THEME_TEMPLATE_PATH, "r", newline="") as f:
        template = f.read()

    context = {
        "theme_name": THEME_NAME,
        "highlight": highlight,
        "foreground": foreground,
        "background": background,
    }
    parsed_theme = template.format(**context)

    theme_file_path = f"{INSTALLATION_SOURCE_DIR}/theme.txt"
    with open(theme_file_path, "w") as f:
        f.write(parsed_theme)


def prepare_target_folder():
    "Applies any transformation related to the target installation folder"
    # Clean installation dir
    if isdir(INSTALLATION_TARGET_DIR):
        rmtree(INSTALLATION_TARGET_DIR)


def copy_source_to_target():
    copytree(INSTALLATION_SOURCE_DIR, INSTALLATION_TARGET_DIR)


def update_grub_defaults():
    # Read previous defaults
    with open(GRUB_DEFAULTS_PATH, "r") as f:
        grub_configs = f.read()

    # Remove previous theme defaults
    tag_title = f"{THEME_NAME} Theme Overrides"
    begin_tag = f"### BEGIN {tag_title}"
    end_tag = f"### END {tag_title}"
    grub_configs = re.sub(f"\n*{begin_tag}.*{end_tag}\n*", "", grub_configs, flags=re.DOTALL)

    # Parse grub defaults template, append parsed contents, and write back

    with open(GRUB_DEFAULTS_TEMPLATE_PATH, "r") as f:
        template = f.read()

    context = {"installation_dir": INSTALLATION_TARGET_DIR}
    parsed_extra_grub = template.format(**context)
    grub_configs += f"\n\n{begin_tag}\n{parsed_extra_grub}\n{end_tag}\n\n"

    with open(GRUB_DEFAULTS_PATH, "w") as f:
        f.write(grub_configs)


if __name__ == "__main__":
    check_python_version()
    check_root_or_prompt()

    prepare_source_folder()
    prepare_target_folder()

    copy_source_to_target()

    update_grub_defaults()
    update_grub_cfg()
