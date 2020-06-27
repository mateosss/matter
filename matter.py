#!/usr/bin/python3

import sys
import os
import re
import argparse
from argparse import ArgumentParser, RawTextHelpFormatter
from os.path import dirname, basename, isdir
from subprocess import run, check_call
from shutil import which, rmtree, copytree

# Configuration constants

MIN_PYTHON_VERSION = (3, 6)  # Mainly for f-strings

THEME_NAME = "Matter"
THEME_DESCRIPTION = (
    "Matter is a minimalist grub theme originally inspired by material design 2.\n"
    "Running this script without arguments will install the theme."
)
THEME_DEFAULT_HIGHLIGHT = "pink"
THEME_DEFAULT_FOREGROUND = "white-350"
THEME_DEFAULT_BACKGROUND = "bluegrey-900"

INSTALLER_NAME = basename(__file__)

INSTALLER_DIR = dirname(os.path.realpath(INSTALLER_NAME))
INSTALLATION_SOURCE_DIR = f"{INSTALLER_DIR}/{THEME_NAME}"
INSTALLATION_TARGET_DIR = f"/boot/grub/themes/{THEME_NAME}"

GRUB_DEFAULTS_PATH = f"/etc/default/grub"
GRUB_CFG_PATH = f"/boot/grub/grub.cfg"
GRUB_MKCONFIG_PATH = which("grub-mkconfig")

THEME_TEMPLATE_PATH = f"{INSTALLER_DIR}/theme.txt.template"
GRUB_DEFAULTS_TEMPLATE_PATH = f"{INSTALLER_DIR}/grub.template"

THEME_OVERRIDES_TITLE = f"{THEME_NAME} Theme Overrides"
BEGIN_THEME_OVERRIDES = f"### BEGIN {THEME_OVERRIDES_TITLE}"
END_THEME_OVERRIDES = f"### END {THEME_OVERRIDES_TITLE}"

# Get available icons from icons/*.png by removing .png extension
AVAILABLE_ICONS = [i[:-4] for i in os.listdir(f"{INSTALLATION_SOURCE_DIR}/icons/")]
PALETTE = {
    "red": "#f44336",
    "pink": "#e91e63",
    "purple": "#9c27b0",
    "deeppurple": "#673ab7",
    "indigo": "#3f51b5",
    "blue": "#2196f3",
    "lightblue": "#03a9f4",
    "cyan": "#00bcd4",
    "teal": "#009688",
    "green": "#4caf50",
    "lightgreen": "#8bc34a",
    "lime": "#cddc39",
    "yellow": "#ffeb3b",
    "amber": "#ffc107",
    "orange": "#ff9800",
    "deeporange": "#ff5722",
    "brown": "#795548",
    "grey": "#9e9e9e",
    "bluegrey": "#607d8b",
    "white": "#ffffff",
    "black": "#000000",
    # Custom default colors
    "white-350": "#9E9E9E",
    "bluegrey-900": "#263238",
}

# Global user arguments set in main()
user_args: argparse.Namespace

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
            f"[Matter Error] Python {required[0]}.{required[1]} or later required."
        )


def check_root_or_prompt():
    if os.geteuid() != 0:
        print(f"[Matter Info] Request root access.")
        exit_code = sh("sudo -v")
        if exit_code != 0:
            raise Exception(
                "[Matter Error] Could not verify root access, you could try with sudo."
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
    with open(GRUB_DEFAULTS_PATH, "r", newline="") as f:
        grub_defaults = f.read()

    # Remove previous theme defaults
    cleaned_grub_defaults = re.sub(
        f"\n*{BEGIN_THEME_OVERRIDES}.*{END_THEME_OVERRIDES}\n*",
        "",
        grub_defaults,
        flags=re.DOTALL,
    )
    return cleaned_grub_defaults


def read_cleaned_grub_mkconfig():
    assert (
        GRUB_MKCONFIG_PATH is not None
    ), "grub-mkconfig command is not present in your system"

    # Read previous defaults
    with open(GRUB_MKCONFIG_PATH, "r", newline="") as f:
        grub_mkconfig = f.read()

    # Remove previous theme defaults
    cleaned_grub_mkconfig = re.sub(
        f"\n*{BEGIN_THEME_OVERRIDES}.*{END_THEME_OVERRIDES}\n*",
        "",
        grub_mkconfig,
        flags=re.DOTALL,
    )
    return cleaned_grub_mkconfig


def parse_color(color_string):
    color = color_string if color_string.startswith("#") else PALETTE[color_string]
    assert (
        re.match(r"\#[0-9A-Fa-f]{6}", color) is not None
    ), f"Invalid color parsed from {color_string}"
    return color


# Procedures


def clean_install_dir():
    print("[Matter Info] Clean install directory.")
    if isdir(INSTALLATION_TARGET_DIR):
        rmtree(INSTALLATION_TARGET_DIR)


def prepare_source_dir():
    print("[Matter Info] Build theme from user preferences.")

    # Get user color preferences
    highlight = parse_color(user_args.highlight)
    foreground = parse_color(user_args.foreground)
    background = parse_color(user_args.background)

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
    print("[Matter Info] Prepare installation directory.")
    clean_install_dir()


def copy_source_to_target():
    print("[Matter Info] Copy built theme to installation directory.")
    copytree(INSTALLATION_SOURCE_DIR, INSTALLATION_TARGET_DIR)


def update_grub_cfg():
    COMMAND = "update-grub"
    print(f"[Matter Info] Remake grub.cfg with {COMMAND}.")
    assert has_command(COMMAND)
    sh(COMMAND)


def update_grub_defaults():
    print(f"[Matter Info] Patch {GRUB_DEFAULTS_PATH} with {THEME_OVERRIDES_TITLE}.")
    grub_configs = read_cleaned_grub_defaults()

    # Parse grub defaults template, append parsed contents, and write back

    with open(GRUB_DEFAULTS_TEMPLATE_PATH, "r", newline="") as f:
        template = f.read()

    context = {"installation_dir": INSTALLATION_TARGET_DIR}
    parsed_extra_grub = template.format(**context)
    grub_configs += (
        f"\n\n{BEGIN_THEME_OVERRIDES}\n{parsed_extra_grub}\n{END_THEME_OVERRIDES}\n\n"
    )

    with open(GRUB_DEFAULTS_PATH, "w") as f:
        f.write(grub_configs)


def clean_grub_defaults():
    print(f"[Matter Info] Clean {THEME_OVERRIDES_TITLE} from {GRUB_DEFAULTS_PATH}.")
    cleaned_grub_defaults = read_cleaned_grub_defaults()
    with open(GRUB_DEFAULTS_PATH, "w") as f:
        f.write(cleaned_grub_defaults)


def clean_grub_mkconfig():
    print(f"[Matter Info] Clean {THEME_OVERRIDES_TITLE} from {GRUB_MKCONFIG_PATH}.")
    cleaned_grub_mkconfig = read_cleaned_grub_mkconfig()
    with open(GRUB_MKCONFIG_PATH, "w") as f:
        f.write(cleaned_grub_mkconfig)


# Main procedures


def do_install():
    print(f"[Matter Info] Begin {THEME_NAME} install.")
    check_root_or_prompt()
    prepare_source_dir()
    prepare_target_dir()
    copy_source_to_target()
    update_grub_defaults()
    update_grub_cfg()
    print(f"[Matter Info] {THEME_NAME} succesfully installed.")


def do_uninstall():
    print(f"[Matter Info] Begin {THEME_NAME} uninstall.")
    check_root_or_prompt()
    clean_grub_defaults()
    clean_grub_mkconfig()
    clean_install_dir()
    update_grub_cfg()
    print(f"[Matter Info] {THEME_NAME} succesfully uninstalled.")


def do_list_grub_cfg_entries():
    # Read current grub cfg
    with open(GRUB_CFG_PATH, "r", newline="") as f:
        grub_cfg = f.read()

    # Capture entry matches
    pattern = r'(?P<head>(?:submenu|menuentry) ?)"(?P<entryname>.*)"(?P<tail>.*\{)'
    matchiter = re.finditer(pattern, grub_cfg)
    matches = list(matchiter)

    for i, m in enumerate(matches):
        print(f"{i + 1}. {m['entryname']}")


def do_patch_grub_cfg_icons(icons=None):
    print(f"[Matter Info] Begin {GRUB_CFG_PATH} patch.")
    icons = icons if icons is not None else user_args.seticons_once
    assert icons is not None

    # Read current grub cfg
    with open(GRUB_CFG_PATH, "r", newline="") as f:
        grub_cfg = f.read()

    # Capture entry matches
    pattern = r'(?P<head>(?:submenu|menuentry) ?)"(?P<entryname>.*)"(?P<tail>.*\{)'
    matchiter = re.finditer(pattern, grub_cfg)
    matches = list(matchiter)

    if len(icons) != len(matches):
        print(
            f"[Matter Error] You must specify {len(matches)} icons ({len(icons)} provided) for entries:"
        )
        for i, m in enumerate(matches):
            print(f"{i + 1}. {m['entryname']}")
        exit(1)

    # Build new grub cfg with given icons
    new_grub_cfg = ""
    next_seek = 0
    for m, i in zip(matches, icons):
        mstart, mend = m.span()
        new_grub_cfg += grub_cfg[next_seek:mstart]
        icon_class = f" --class {i} " if i != "_" else ""
        new_grub_cfg += f'{m["head"]}"{m["entryname"]}"{icon_class}{m["tail"]}'
        next_seek = mend
    new_grub_cfg += grub_cfg[mend:]

    # Write new grub cfg back
    check_root_or_prompt()
    with open(GRUB_CFG_PATH, "w") as f:
        f.write(new_grub_cfg)

    print(f"[Matter Info] {len(icons)} icons succesfully patched onto {GRUB_CFG_PATH}.")


def do_set_icons():
    # Patch grub.cfg
    icons = user_args.seticons or []
    do_patch_grub_cfg_icons(icons)

    # Patch grub-mkconfig so everytime it executes, it patches grub.cfg
    print(f"[Matter Info] Begin {GRUB_MKCONFIG_PATH} patch.")
    print(f"[Matter Info] Clean old {GRUB_MKCONFIG_PATH} patch if any.")
    cmd_icons = " ".join(icons)
    seticons_call = f"{INSTALLER_DIR}/{INSTALLER_NAME} -so {cmd_icons} >&2"
    new_grub_mkconfig = read_cleaned_grub_mkconfig()
    new_grub_mkconfig += (
        f"\n\n{BEGIN_THEME_OVERRIDES}\n{seticons_call}\n{END_THEME_OVERRIDES}\n\n"
    )

    check_root_or_prompt()
    with open(GRUB_MKCONFIG_PATH, "w") as f:
        f.write(new_grub_mkconfig)

    print(
        f"[Matter Info] {GRUB_MKCONFIG_PATH} succesfully patched, icons should now persist between grub updates."
    )


# Script arguments


def parse_args():
    parser = ArgumentParser(
        description=THEME_DESCRIPTION,
        epilog=f"Available colors are: {', '.join(PALETTE.keys())}.\n"
        "You can specify your own hex colors as well (e.g. \\#C0FFEE, \\#FF00FF, etc).\n"
        f"Available icons are: {', '.join(AVAILABLE_ICONS)}\n"
        "\nFor adding more icons you can do it yourself following this guide:\n"
        "https://github.com/mateosss/matter/wiki/How-to-Contribute-an-Icon\n"
        "Or request it (or any other thing) by opening an issue on:\n"
        "https://github.com/mateosss/matter/issues",
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument(
        "--listentries", "-l", action="store_true", help=f"list grub entries",
    )
    parser.add_argument(
        "--seticons",
        "-si",
        type=str,
        nargs="*",
        help=f"set grub entries icons and patch grub-mkconfig for persistence",
    )
    parser.add_argument(
        "--seticons_once",
        "-so",
        type=str,
        nargs="*",
        help=f"set grub entries icons, will be reverted on next grub update",
    )
    parser.add_argument(
        "--uninstall", "-u", action="store_true", help=f"uninstall {THEME_NAME}",
    )
    parser.add_argument(
        "--highlight",
        "-hl",
        type=str,
        help=f"selected text color",
        default=THEME_DEFAULT_HIGHLIGHT,
    )
    parser.add_argument(
        "--foreground",
        "-fg",
        type=str,
        help=f"main text color",
        default=THEME_DEFAULT_FOREGROUND,
    )
    parser.add_argument(
        "--background",
        "-bg",
        type=str,
        help=f"solid background color",
        default=THEME_DEFAULT_BACKGROUND,
    )
    return parser.parse_args()


if __name__ == "__main__":
    check_python_version()
    user_args = parse_args()

    if user_args.listentries:
        do_list_grub_cfg_entries()
    elif user_args.seticons is not None:
        do_set_icons()
    elif user_args.seticons_once is not None:
        do_patch_grub_cfg_icons()
    elif user_args.uninstall:
        do_uninstall()
    else:
        do_install()
