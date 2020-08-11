#!/usr/bin/python3

import sys
import os
import re
import argparse
import urllib.request as request
from urllib.error import HTTPError
from argparse import ArgumentParser, RawTextHelpFormatter
from os.path import dirname, basename, isdir, exists
from subprocess import run, check_call, PIPE
from shutil import which, rmtree, copytree, copyfile

# Configuration constants

MIN_PYTHON_VERSION = (3, 6)  # Mainly for f-strings

THEME_NAME = "Matter"
THEME_DESCRIPTION = (
    "Matter is a minimalist grub theme originally inspired by material design 2.\n"
    "Run this script without arguments for next steps on installing Matter."
)

# Logging utils

def color_string(string, fg=None):
    COLORS = {  # List some colors that may be needed
        "red": "\033[31m",
        "green": "\033[32m",
        "orange": "\033[33m",
        "blue": "\033[34m",
        "cyan": "\033[36m",
        "lightred": "\033[91m",
        "lightgreen": "\033[92m",
        "yellow": "\033[93m",
        "lightblue": "\033[94m",
        "lightcyan": "\033[96m",
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


if exists("/boot/grub"):
    BOOT_GRUB_PATH = "/boot/grub"
elif exists("/boot/grub2"):
    BOOT_GRUB_PATH = "/boot/grub2"
else:
    error("Could not find your grub's boot path (tried /boot/grub and /boot/grub2)")

INSTALLER_ABSPATH = os.path.abspath(__file__)
INSTALLER_NAME = basename(INSTALLER_ABSPATH)
INSTALLER_DIR = dirname(INSTALLER_ABSPATH)
INSTALLATION_SOURCE_DIR = f"{INSTALLER_DIR}/{THEME_NAME}"
INSTALLATION_TARGET_DIR = f"{BOOT_GRUB_PATH}/themes/{THEME_NAME}"

THEME_DEFAULT_HIGHLIGHT = "pink"
THEME_DEFAULT_FOREGROUND = "white"
THEME_DEFAULT_BACKGROUND = "bluegrey-900"
THEME_DEFAULT_FONT_NAME = "Google Sans Regular"
THEME_DEFAULT_FONT = THEME_DEFAULT_FONT_NAME.replace(" ", "_")
THEME_DEFAULT_FONT_SIZE = 32

GRUB_DEFAULTS_PATH = f"/etc/default/grub"
GRUB_CFG_PATH = f"{BOOT_GRUB_PATH}/grub.cfg"
GRUB_MKCONFIG_PATH = which("grub-mkconfig") or which("grub2-mkconfig")
if GRUB_MKCONFIG_PATH is None:
    error("Could not find grub-mkconfig command file (grub2-mkconfig neither)")


THEME_TEMPLATE_PATH = f"{INSTALLER_DIR}/theme.txt.template"
GRUB_DEFAULTS_TEMPLATE_PATH = f"{INSTALLER_DIR}/grub.template"

THEME_OVERRIDES_TITLE = f"{THEME_NAME} Theme Overrides"
BEGIN_THEME_OVERRIDES = f"### BEGIN {THEME_OVERRIDES_TITLE}"
END_THEME_OVERRIDES = f"### END {THEME_OVERRIDES_TITLE}"

ICON_SVG_PATHF = f"{INSTALLER_DIR}/icons/{{}}.svg"
ICON_PNG_PATHF = f"{INSTALLATION_SOURCE_DIR}/icons/{{}}.png"

PALETTE = {
    "red": "f44336",
    "pink": "e91e63",
    "purple": "9c27b0",
    "deeppurple": "673ab7",
    "indigo": "3f51b5",
    "blue": "2196f3",
    "lightblue": "03a9f4",
    "cyan": "00bcd4",
    "teal": "009688",
    "green": "4caf50",
    "lightgreen": "8bc34a",
    "lime": "cddc39",
    "yellow": "ffeb3b",
    "amber": "ffc107",
    "orange": "ff9800",
    "deeporange": "ff5722",
    "brown": "795548",
    "grey": "9e9e9e",
    "bluegrey": "607d8b",
    "white": "ffffff",
    "black": "000000",
    # Custom default colors
    "white-350": "9E9E9E",
    "bluegrey-900": "263238",
}
AVAILABLE_COLORS = list(PALETTE.keys())

MDI_CDN = "https://raw.githubusercontent.com/Templarian/MaterialDesign-SVG/master/svg/"

# Global user arguments set in main()
user_args: argparse.Namespace

# Utils


def sh(command):
    "Executes command in shell and returns its exit status"
    return run(command, shell=True).returncode


def shout(command):
    "Executes command in shell and returns its stdout"
    stdout = run(command, shell=True, stdout=PIPE).stdout.decode("utf-8")
    print(stdout)
    return stdout


def has_command(command):
    return which(command) is not None


def check_python_version():
    installed = (sys.version_info.major, sys.version_info.minor)
    required = MIN_PYTHON_VERSION
    if installed < required:
        error(f"Python {required[0]}.{required[1]} or later required")


def check_root_or_prompt():
    if os.geteuid() != 0:
        info("Request root access")
        exit_code = sh("sudo -v")
        if exit_code != 0:
            error("Could not verify root access, you could try with sudo")
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


def download_icon(icon_name):
    info(f"Download {icon_name}.svg")
    url = f"{MDI_CDN}{icon_name}.svg"
    try:
        with request.urlopen(url) as f:
            response = f.read()
    except HTTPError as err:
        error(f"Couldn't get icon {icon_name} ({err.reason})", f"At URL {err.geturl()}")
    svg_path = ICON_SVG_PATHF.format(icon_name)
    with open(svg_path, "wb") as f:
        f.write(response)
    return svg_path


def get_converted_icons():
    return [
        filename[:-4]  # Remove .png
        for filename in os.listdir(f"{INSTALLATION_SOURCE_DIR}/icons/")
        if filename.endswith(".png")
    ]


def is_icon_downloaded(icon_name):
    svg_path = ICON_SVG_PATHF.format(icon_name)
    return exists(svg_path)


def convert_icon_svg2png(icon_name):
    if not has_command("convert"):
        error(
            "Stop. The `convert` command from imagemagick was not found",
            "Also consider installing `inkscape` for the best results",
        )
    if not has_command("inkscape"):
        warning("Resulting icons could look a bit off, consider installing inkscape")
    color = (
        parse_color(user_args.iconcolor)
        if user_args.iconcolor
        else parse_color(user_args.foreground)
    )
    src_path = ICON_SVG_PATHF.format(icon_name)
    dst_path = ICON_PNG_PATHF.format(icon_name)
    command = (
        r"convert -trim -scale 36x36 -extent 72x72 -gravity center "
        r"-define png:color-type=6 -background none -colorspace sRGB -channel RGB "
        rf"-threshold -1 -density 300 -fill \{color} +opaque none "
        rf"{src_path} {dst_path}"
    )
    exit_code = sh(command)
    if exit_code != 0:
        error("Stop. The convert command returned an error")


def get_available_fonts():
    "Returns the fonts present in /fonts"
    return [
        filename[:-4]  # Remove .ttf
        for filename in os.listdir(f"{INSTALLER_DIR}/fonts/")
        if filename.endswith(".ttf")
    ]


def parse_color(color_string):
    if color_string in AVAILABLE_COLORS:
        color = PALETTE[color_string]
    elif re.match(r"[0-9A-Fa-f]{6}", color_string) is not None:
        color = color_string
    else:
        error(
            f"Invalid color parsed from {color_string}",
            f"Color must be an hex code like C00FFE or one of: {AVAILABLE_COLORS}",
        )
    return f"#{color}"


def check_icon_converted(icon):
    available_icons = get_converted_icons()
    if icon not in available_icons + ["_"]:
        error(f"Invalid icon name: {icon}", f"Icons present are: {available_icons}")
    return icon


def parse_font(font):
    """From a given --font check if available and return its font name
    e.g. Open_Sans_Regular to Open Sans Regular"""
    available_fonts = get_available_fonts()
    if font not in available_fonts:
        error(
            f"Invalid font name: {font}", f"Available font names: {available_fonts}",
        )
    return font.replace("_", " ")


# Procedures


def clean_install_dir():
    info("Clean install directory")
    if isdir(INSTALLATION_TARGET_DIR):
        rmtree(INSTALLATION_TARGET_DIR)


def prepare_source_dir():
    info("Build theme from user preferences")
    # Get user color preferences
    highlight = parse_color(user_args.highlight)
    foreground = parse_color(user_args.foreground)
    background = parse_color(user_args.background)
    fontkey = user_args.font
    fontfile = user_args.fontfile
    fontname = user_args.fontname
    fontsize = user_args.fontsize
    icons = user_args.icons

    # Icon checks
    # Read entries from grub.cfg
    with open(GRUB_CFG_PATH, "r", newline="") as f:
        grub_cfg = f.read()
    # Do icon count match grub entry count?
    entries = get_entry_names(grub_cfg)
    if len(icons) != len(entries):
        error(
            f"You must specify {len(entries)} icons ({len(icons)} provided) for entries:",
            should_exit=False,
        )
        for i, m in enumerate(entries):
            print(f"{i + 1}. {m['entryname']}")
        exit(1)

    # Font checks
    # grub-mkfont present
    grub_mkfont = which("grub-mkfont") or which("grub2-mkfont")
    if grub_mkfont is None:
        error(f"grub-mkfont command not found in your system (grub2-mkfont neither)")
    # Valid font arguments
    if fontfile is None:  # User did not specify custom font file
        fontfile = f"{INSTALLER_DIR}/fonts/{fontkey}.ttf"
        fontname = f"{parse_font(fontkey)} {fontsize}"
    elif not fontfile.endswith(".ttf"):  # font file is not ttf
        error(f"{fontfile} is not a .ttf file")
    elif fontname is None:  # User did, but did not gave its name
        error(
            "--fontname/-fn not specified for given font file.",
            "e.g. 'Open Sans Regular'",
        )
    else:  # User specified a custom fontfile
        fontname = " ".join(fontname)  # e.g. Open Sans Regular
        dst_fontfile = f"{INSTALLER_DIR}/fonts/{fontname.replace(' ', '_')}.ttf"  # e.g. .../Open_Sans_Regular.ttf
        copyfile(fontfile, dst_fontfile)
        fontfile = dst_fontfile
        fontname = f"{fontname} {fontsize}"  # e.g. Open Sans Regular 32

    # Prepare Icons

    # Download not-yet-downloaded icons
    for icon in icons:
        if not is_icon_downloaded(icon) and icon != "_":
            download_icon(icon)

    # Convert icons
    info("Convert icons")
    for icon in icons:
        if icon != "_":
            convert_icon_svg2png(icon)

    # Prepare Font

    # Generate font file
    info("Build font")
    stdout = shout(
        f"{grub_mkfont} -o {INSTALLATION_SOURCE_DIR}/font.pf2 {fontfile} -s {fontsize}"
    )
    if stdout:
        error(
            f"{grub_mkfont} execution was not clean", f"for fontfile: {fontfile}",
        )

    # Prepare Theme.txt

    # Parse theme template with user preferences
    with open(THEME_TEMPLATE_PATH, "r", newline="") as f:
        template = f.read()

    context = {
        "theme_name": THEME_NAME,
        "highlight": highlight,
        "foreground": foreground,
        "background": background,
        "fontname": fontname,
    }
    parsed_theme = template.format(**context)

    theme_file_path = f"{INSTALLATION_SOURCE_DIR}/theme.txt"
    with open(theme_file_path, "w") as f:
        f.write(parsed_theme)


def prepare_target_dir():
    info("Prepare installation directory")
    clean_install_dir()


def copy_source_to_target():
    info("Copy built theme to installation directory")
    copytree(INSTALLATION_SOURCE_DIR, INSTALLATION_TARGET_DIR)


def update_grub_cfg():
    info("Update grub.cfg")
    update_command = which("update-grub") or which("grub-mkconfig") or which("grub2-mkconfig")
    if update_command is None:
        error(f"Command for generating grub.cfg not found (tried update-grub, grub-mkconfig and grub2-mkconfig)")
    command = f"{update_command} -o {GRUB_CFG_PATH}" 
    info(f"Remake grub.cfg with {command}")
    sh(command)


def update_grub_defaults():
    info(f"Patch {GRUB_DEFAULTS_PATH} with {THEME_OVERRIDES_TITLE}")
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
    info(f"Clean {THEME_OVERRIDES_TITLE} from {GRUB_DEFAULTS_PATH}")
    cleaned_grub_defaults = read_cleaned_grub_defaults()
    with open(GRUB_DEFAULTS_PATH, "w") as f:
        f.write(cleaned_grub_defaults)


def clean_grub_mkconfig():
    info(f"Clean {THEME_OVERRIDES_TITLE} from {GRUB_MKCONFIG_PATH}")
    cleaned_grub_mkconfig = read_cleaned_grub_mkconfig()
    with open(GRUB_MKCONFIG_PATH, "w") as f:
        f.write(cleaned_grub_mkconfig)


def get_entry_names(grub_cfg):
    "Gets the entry names from grub.cfg contents"
    pattern = (
        r"(?P<head>(?:submenu|menuentry) ?)"  # menuentry or submenu
        r"(?:\"|')"  # " or '
        r"(?P<entryname>[^\"']*)"  # capture the entry name (without quotes)
        r"(?:\"|')"  # " or '
        r"(?P<tail>[^\{]*\{)"  # The rest of the entry header until a { is found
    )
    matchiter = re.finditer(pattern, grub_cfg)
    matches = list(matchiter)
    return matches


# Main procedures


def do_preinstall_hint():
    info(
        f"[{color_string(THEME_NAME.upper(), fg='pink')} "
        f"{color_string('Grub Theme'.upper(), fg='orange')}]"
    )
    info("Argument -i required. Which icons go to which grub entries?.")
    info("Your grub entries are:")
    do_list_grub_cfg_entries()
    info("Look for icons you like at https://materialdesignicons.com/")
    info("Then install with:")
    info("./matter.py -i icon-for-entry-1 icon-for-entry-2 ...")
    info("Example (with 8 entries, _ means ignore):")
    info("./matter.py -i ubuntu microsoft-windows folder _ _ _ _ cog")


def do_test():
    info("Begin grub2-theme-preview")
    warning(
        "Argument --icons/-i does not have effect when testing",
        "The icon names used are coming from your system's current grub.cfg",
        "This is a feature that may work in the future",
    )
    if not has_command("grub2-theme-preview"):
        error(
            "You need grub2-theme-preview for testing",
            "See https://github.com/hartwork/grub2-theme-preview",
        )
    sh(f"grub2-theme-preview {INSTALLATION_SOURCE_DIR}")


def do_install():
    info(f"Begin {THEME_NAME} install")
    prepare_source_dir()
    check_root_or_prompt()
    prepare_target_dir()
    copy_source_to_target()
    update_grub_defaults()
    do_set_icons()
    update_grub_cfg()
    info(f"{THEME_NAME} succesfully installed")


def do_uninstall():
    info(f"Begin {THEME_NAME} uninstall")
    check_root_or_prompt()
    clean_grub_defaults()
    clean_grub_mkconfig()
    clean_install_dir()
    update_grub_cfg()
    info(f"{THEME_NAME} succesfully uninstalled")


def do_list_grub_cfg_entries():
    # Read current grub cfg
    with open(GRUB_CFG_PATH, "r", newline="") as f:
        grub_cfg = f.read()

    entries = get_entry_names(grub_cfg)

    for i, m in enumerate(entries):
        print(f"{i + 1}. {m['entryname']}")


def do_patch_grub_cfg_icons():
    info(f"Begin {GRUB_CFG_PATH} patch")
    icons = user_args.icons
    if icons is None:
        error("Stop. Unspecified icons (--icons/-i argument)")
    icons = [check_icon_converted(i) for i in icons]

    # Read current grub cfg
    with open(GRUB_CFG_PATH, "r", newline="") as f:
        grub_cfg = f.read()

    entries = get_entry_names(grub_cfg)
    if len(icons) != len(entries):
        error(
            f"You must specify {len(entries)} "
            f"icons ({len(icons)} provided) for entries:",
            should_exit=False,
        )
        for i, m in enumerate(entries):
            print(f"{i + 1}. {m['entryname']}")
        # NOTE: We exit with 0 here to not stop the apt upgrade process
        # eventually it will be solved with an autoremove
        exit(0)

    # Build new grub cfg with given icons
    new_grub_cfg = ""
    next_seek = 0
    for m, i in zip(entries, icons):
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

    info(f"{len(icons)} icons succesfully patched onto {GRUB_CFG_PATH}")


def do_set_icons():
    # Patch grub.cfg
    do_patch_grub_cfg_icons()

    # Patch grub-mkconfig so everytime it executes, it patches grub.cfg
    info(f"Begin {GRUB_MKCONFIG_PATH} patch")
    info(f"Clean old {GRUB_MKCONFIG_PATH} patch if any")

    cmd_icons = " ".join(user_args.icons)
    seticons_call = f"{INSTALLER_DIR}/{INSTALLER_NAME} -so -i {cmd_icons} >&2"
    new_grub_mkconfig = read_cleaned_grub_mkconfig()
    new_grub_mkconfig += (
        f"\n\n{BEGIN_THEME_OVERRIDES}\n{seticons_call}\n{END_THEME_OVERRIDES}\n\n"
    )

    check_root_or_prompt()
    with open(GRUB_MKCONFIG_PATH, "w") as f:
        f.write(new_grub_mkconfig)

    info(
        f"{GRUB_MKCONFIG_PATH} succesfully patched, icons will now persist between grub updates."
    )


# Script arguments


def parse_args():
    parser = ArgumentParser(
        description=THEME_DESCRIPTION,
        epilog=f"[Available colors] are: {', '.join(AVAILABLE_COLORS)}.\n"
        "You can specify your own hex colors as well (e.g. C0FFEE, FF00FF, etc).\n"
        f"[Available fonts] are: {', '.join(get_available_fonts())}\n"
        "You can always specify your own with the -ff argument\n"
        f"[Available icons] can be found at https://materialdesignicons.com/\n"
        "For requests open an issue on:\n"
        "https://github.com/mateosss/matter/issues",
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument(
        "--listentries", "-l", action="store_true", help=f"list grub entries",
    )
    parser.add_argument(
        "--buildonly",
        "-b",
        action="store_true",
        help=f"prepare the theme but do not install it",
    )
    parser.add_argument(
        "--test",
        "-t",
        action="store_true",
        help=f"test the generated theme with grub2-theme-preview",
    )
    parser.add_argument(
        "--icons",
        "-i",
        type=str,
        nargs="*",
        help=f"specify icons for each grub entry listed with -l",
    )
    parser.add_argument(
        "--seticons",
        "-si",
        action="store_true",
        help=f"set grub entries icons given by -i and patch grub-mkconfig for persistence",
    )
    parser.add_argument(
        "--seticons_once",
        "-so",
        action="store_true",
        help=f"set grub entries icons given by -i, will be reverted on next grub update",
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
    parser.add_argument(
        "--iconcolor",
        "-ic",
        type=str,
        help=f"icons fill color, by default same as foreground",
    )
    parser.add_argument(
        "--font",
        "-f",
        type=str,
        help=f"theme font from already downloaded fonts",
        default=THEME_DEFAULT_FONT,
        choices=get_available_fonts(),
    )
    parser.add_argument(
        "--fontfile", "-ff", type=str, help=f"import theme font from custom .ttf file"
    )
    parser.add_argument(
        "--fontname",
        "-fn",
        type=str,
        nargs="*",
        help=f"specify the font name for the given font file",
    )
    parser.add_argument(
        "--fontsize",
        "-fs",
        type=int,
        help=f"theme font size",
        default=THEME_DEFAULT_FONT_SIZE,
    )
    return parser.parse_args()


if __name__ == "__main__":
    check_python_version()
    user_args = parse_args()

    if user_args.listentries:
        do_list_grub_cfg_entries()
    elif user_args.buildonly:
        prepare_source_dir()
    elif user_args.seticons_once:
        do_patch_grub_cfg_icons()
    elif user_args.seticons:
        do_set_icons()
    elif user_args.uninstall:
        do_uninstall()
    elif user_args.icons is None:
        do_preinstall_hint()
    else:
        do_install()

    if user_args.test:
        do_test()
