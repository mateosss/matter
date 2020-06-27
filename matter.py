#!/usr/bin/python3

import sys
import os
import re
from argparse import ArgumentParser
from os.path import dirname, isdir
from subprocess import run, check_call
from shutil import which, rmtree, copytree

# Configuration constants

MIN_PYTHON_VERSION = (3, 6)  # Mainly for f-strings

THEME_NAME = "Matter"
INSTALLER_NAME = __file__
INSTALLER_DIR = dirname(os.path.realpath(INSTALLER_NAME))
INSTALLATION_SOURCE_DIR = f"{INSTALLER_DIR}/{THEME_NAME}"
INSTALLATION_TARGET_DIR = f"/boot/grub/themes/{THEME_NAME}"

GRUB_DEFAULTS_PATH = f"/etc/default/grub"

THEME_TEMPLATE_PATH = f"{INSTALLER_DIR}/theme.txt.template"
GRUB_DEFAULTS_TEMPLATE_PATH = f"{INSTALLER_DIR}/grub.template"

THEME_OVERRIDES_TITLE = f"{THEME_NAME} Theme Overrides"
BEGIN_THEME_OVERRIDES = f"### BEGIN {THEME_OVERRIDES_TITLE}"
END_THEME_OVERRIDES = f"### END {THEME_OVERRIDES_TITLE}"

# Utils


def sh(command):
    "Executes command in shell"
    return run(command, shell=True).returncode


def has_command(command):
    return which(command) is not None


def check_python_version():
    installed = (sys.version_info.major, sys.version_info.minor)
    required = MIN_PYTHON_VERSION
    if installed < required:
        raise Exception(
            f"[Error] Python {required[0]}.{required[1]} or later required."
        )


def check_root_or_prompt():
    if os.geteuid() != 0:
        print(f"[Info] Request root access.")
        exit_code = sh("sudo -v")
        if exit_code != 0:
            raise Exception(
                "[Error] Could not verify root access, you could try with sudo."
            )
        # Relaunch the program with sudo
        args = " ".join(sys.argv[1:])
        child_exit_code = sh(f"sudo {INSTALLER_DIR}/{INSTALLER_NAME} {args}")
        exit(child_exit_code)  # Propagate exit code


def delete_dir(directory):
    if isdir(directory):
        rmtree(directory)


def read_cleaned_grub_defaults():
    # Read previous defaults
    with open(GRUB_DEFAULTS_PATH, "r") as f:
        grub_defaults = f.read()

    # Remove previous theme defaults
    cleaned_grub_defaults = re.sub(
        f"\n*{BEGIN_THEME_OVERRIDES}.*{END_THEME_OVERRIDES}\n*",
        "",
        grub_defaults,
        flags=re.DOTALL,
    )
    return cleaned_grub_defaults


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        "--uninstall", "-u", action="store_true", help=f"uninstall {THEME_NAME}",
    )
    return parser.parse_args()


# Main procedures


def clean_install_dir():
    print("[Info] Clean install directory.")
    if isdir(INSTALLATION_TARGET_DIR):
        rmtree(INSTALLATION_TARGET_DIR)


def prepare_source_dir():
    print("[Info] Build theme from user preferences.")

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


def prepare_target_dir():
    print("[Info] Prepare installation directory.")
    clean_install_dir()


def copy_source_to_target():
    print("[Info] Copy built theme to installation directory.")
    copytree(INSTALLATION_SOURCE_DIR, INSTALLATION_TARGET_DIR)


def update_grub_cfg():
    COMMAND = "update-grub"
    print(f"[Info] Remake grub.cfg with {COMMAND}.")
    assert has_command(COMMAND)
    sh(COMMAND)


def update_grub_defaults():
    print(f"[Info] Patch {GRUB_DEFAULTS_PATH} with {THEME_OVERRIDES_TITLE}.")
    grub_configs = read_cleaned_grub_defaults()

    # Parse grub defaults template, append parsed contents, and write back

    with open(GRUB_DEFAULTS_TEMPLATE_PATH, "r") as f:
        template = f.read()

    context = {"installation_dir": INSTALLATION_TARGET_DIR}
    parsed_extra_grub = template.format(**context)
    grub_configs += (
        f"\n\n{BEGIN_THEME_OVERRIDES}\n{parsed_extra_grub}\n{END_THEME_OVERRIDES}\n\n"
    )

    with open(GRUB_DEFAULTS_PATH, "w") as f:
        f.write(grub_configs)


def clean_grub_defaults():
    print(f"[Info] Clean {THEME_OVERRIDES_TITLE}.")
    cleaned_grub_defaults = read_cleaned_grub_defaults()
    with open(GRUB_DEFAULTS_PATH, "w") as f:
        f.write(cleaned_grub_defaults)


def do_install():
    print(f"[Info] Begin {THEME_NAME} install.")
    check_root_or_prompt()
    prepare_source_dir()
    prepare_target_dir()
    copy_source_to_target()
    update_grub_defaults()
    update_grub_cfg()
    print(f"{THEME_NAME} succesfully installed.")


def do_uninstall():
    print(f"[Info] Begin {THEME_NAME} uninstall.")
    check_root_or_prompt()
    clean_grub_defaults()
    clean_install_dir()
    update_grub_cfg()
    print(f"{THEME_NAME} succesfully uninstalled.")


if __name__ == "__main__":
    check_python_version()
    args = parse_args()
    if args.uninstall:
        do_uninstall()
    else:
        do_install()
