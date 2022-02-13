#!/usr/bin/python3

# Standard library modules
import sys
import os
import re
import json
import argparse
import urllib.request as request
from urllib.error import HTTPError, URLError
from argparse import ArgumentParser, RawTextHelpFormatter
from os.path import dirname, basename, isdir, exists
from shutil import which, rmtree, copytree, copyfile
try:
    from PIL import Image
except:
    has_PIL = False
else:
    has_PIL = True

# Local Matter modules
from utils import *
from svg2png import inkscape_convert_svg2png, magick_convert_svg2png

# Configuration constants

MIN_PYTHON_VERSION = (3, 6)  # Mainly for f-strings

THEME_NAME = "Matter"
THEME_DESCRIPTION = (
    "Matter is a minimalist grub theme originally inspired by material design 2.\n"
    "Run this script without arguments for next steps on installing Matter."
)



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
THEME_DEFAULT_FONT_NAME = "Josefin Sans Regular"
THEME_DEFAULT_FONT = THEME_DEFAULT_FONT_NAME.replace(" ", "_")
THEME_DEFAULT_FONT_SIZE = 32

GRUB_DEFAULTS_PATH = "/etc/default/grub"
GRUB_SCRIPTS_PATH = "/etc/grub.d"
GRUB_CFG_PATH = f"{BOOT_GRUB_PATH}/grub.cfg"
GRUB_MKCONFIG_PATH = which("grub-mkconfig") or which("grub2-mkconfig")
if GRUB_MKCONFIG_PATH is None:
    error("Could not find grub-mkconfig command file (grub2-mkconfig neither)")


THEME_TEMPLATE_PATH = f"{INSTALLER_DIR}/theme.txt.template"
GRUB_DEFAULTS_TEMPLATE_PATH = f"{INSTALLER_DIR}/grub.template"
HOOKCHECK_TEMPLATE_PATH = f"{INSTALLER_DIR}/hookcheck.py.template"

THEME_OVERRIDES_TITLE = f"{THEME_NAME} Theme Overrides"
BEGIN_THEME_OVERRIDES = f"### BEGIN {THEME_OVERRIDES_TITLE}"
END_THEME_OVERRIDES = f"### END {THEME_OVERRIDES_TITLE}"

ICON_SVG_PATHF = f"{INSTALLER_DIR}/icons/{{}}.svg"
ICON_PNG_PATHF = f"{INSTALLATION_SOURCE_DIR}/icons/{{}}.png"

BACKGROUND_TMP_PATHF = f"{INSTALLER_DIR}/bg/{{}}.tmp"
BACKGROUND_PNG_PATHF = f"{INSTALLER_DIR}/bg/{{}}.png"

CONFIG_FILE_PATH = f"{INSTALLER_DIR}/config.json"

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
    except HTTPError as err:  # A subclass of URLError
        error(f"Couldn't get icon {icon_name} ({err.reason})", f"At URL {err.geturl()}")
    except URLError as err:
        error(f"Couldn't get icon {icon_name} ({err.reason})")
    svg_path = ICON_SVG_PATHF.format(icon_name)
    with open(svg_path, "wb") as f:
        f.write(response)
    return svg_path


def download_background(background_path):
    if not has_PIL:
        error("PIL not detected, cannot download background")
    info(f"Downloading background image")
    
    url = f"{background_path}"
    try:
        with request.urlopen(url) as f:
            response = f.read()
    except HTTPError as err:  # A subclass of URLError
        error(f"Couldn't get background image ({err.reason})", f"At URL {err.geturl()}")
    except URLError as err:
        error(f"Couldn't get background image ({err.reason})")
    bg_path = BACKGROUND_TMP_PATHF.format('background_image')
    conv_path = BACKGROUND_PNG_PATHF.format('background_image')
    with open(bg_path, "wb") as f:
        f.write(response)
    im = Image.open(bg_path)
    im.save(conv_path)
    return conv_path



def get_converted_icons():
    return [
        filename[:-4]  # Remove .png
        for filename in os.listdir(f"{INSTALLATION_SOURCE_DIR}/icons/")
        if filename.endswith(".png")
    ]


def is_icon_downloaded(icon_name):
    svg_path = ICON_SVG_PATHF.format(icon_name)
    return exists(svg_path)


def convert_icon_svg2png(icon_name, whisper=False):
    if not has_command("inkscape"):
        if not has_command("convert"):
            error(
                "Stop. Both `inkscape` and `convert` command from imagemagick were not found",
                "Consider installing `inkscape` for the best results",
            )
        else:
            command = "convert"
    else:
        command = "inkscape"

    color = (
        parse_color(user_args.iconcolor)
        if user_args.iconcolor
        else parse_color(user_args.foreground)
    )
    src_path = ICON_SVG_PATHF.format(icon_name)
    dst_path = ICON_PNG_PATHF.format(icon_name)

    if command == "convert":
        warning("Resulting icons could look a bit off, consider installing inkscape")
        converter = magick_convert_svg2png
    elif command == "inkscape":
        converter = inkscape_convert_svg2png

    exit_code = converter(color, src_path, dst_path, whisper=whisper)
    if exit_code != 0:
        error(f"Stop. The `{command}` command returned an error")


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
    background = parse_color(
        THEME_DEFAULT_BACKGROUND
        if user_args.background is None
        else user_args.background
    )
    image = (
        user_args.image
        if user_args.downloadbackground is None
        else download_background(user_args.downloadbackground)
    )
    fontkey = user_args.font
    fontfile = user_args.fontfile
    fontname = user_args.fontname
    fontsize = user_args.fontsize
    icons = user_args.icons

    # Image checks
    if image:
        if not exists(image):
            error(f"{image} does not exist")
        if os.path.splitext(image)[1] not in (".png", ".jpg", ".jpeg", ".tga"):
            error("Background image must be one of .png, .jpg, .jpeg or .tga formats.")
        image_name = basename(image)
        copyfile(image, f"{INSTALLATION_SOURCE_DIR}/{image_name}")
        if user_args.background:
            warning(
                f"Both --background and --image arguments specified. Background color {background} will be ignored."
            )
    else:
        image_name = "background.png"

    # Icon checks
    # Get entries from grub.cfg
    entries = get_entry_names()
    # Do icon count match grub entry count?
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
    for i, icon in enumerate(icons):
        if icon != "_":
            if i == 0:
                convert_icon_svg2png(icon)
            else:
                convert_icon_svg2png(icon, whisper=True)

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
        "image_name": image_name,
        "fontname": fontname,
    }
    parsed_theme = template.format(**context)

    if image:
        parsed_theme = parsed_theme.replace("# desktop-image", "desktop-image")

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
    update_command = (
        which("update-grub") or which("grub-mkconfig") or which("grub2-mkconfig")
    )
    if update_command is None:
        error(
            f"Command for generating grub.cfg not found (tried update-grub, grub-mkconfig and grub2-mkconfig)"
        )
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


def clean_hookcheck():
    info(f"Remove hookcheck script from {GRUB_SCRIPTS_PATH}")
    hookcheck = f"{GRUB_SCRIPTS_PATH}/99_matter"
    if exists(hookcheck):
        os.remove(hookcheck)


def get_entry_names():
    "Gets the entry names from grub.cfg contents"
    with open(GRUB_CFG_PATH, "r", newline="") as f:
        grub_cfg = f.read()
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
        f"{color_string('[ ', fg='brightwhite')}"
        f"{color_string(THEME_NAME, fg='brightmagenta')} "
        f"{color_string('Grub Theme'.upper(), fg='lightcyan')}"
        f"{color_string(' ]', fg='brightwhite')}"
    )
    info("Argument -i required. Which icons go to which grub entries?")
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
    do_set_icons(patch_grubcfg=True)
    install_hookcheck()
    update_grub_cfg()
    info(f"{THEME_NAME} successfully installed")


def do_uninstall():
    info(f"Begin {THEME_NAME} uninstall")
    check_root_or_prompt()
    clean_grub_defaults()
    clean_grub_mkconfig()
    clean_hookcheck()
    clean_install_dir()
    update_grub_cfg()
    info(f"{THEME_NAME} successfully uninstalled")


def do_list_grub_cfg_entries():
    # Read current grub cfg
    with open(GRUB_CFG_PATH, "r", newline="") as f:
        grub_cfg = f.read()

    entries = get_entry_names()

    for i, m in enumerate(entries):
        print(f"{i + 1}. {m['entryname']}")


def create_config_file():
    icons = user_args.icons
    # Read current grub cfg
    entries = get_entry_names()

    entries_to_icons = {}
    for icon, entry in zip(icons, entries):
        entryname = entry.group("entryname")
        if entryname in entries_to_icons:
            warning(f"Duplicate entry '{entryname}'. Unexpected behaviour may occur. Consider changing names using Grub Customizer.")
        entries_to_icons[entryname]  = icon

    config = {"icons": entries_to_icons}

    with open(CONFIG_FILE_PATH, 'w') as f:
        f.write(json.dumps(config))


def patch_from_config_file():
    # Read current grub cfg
    current_entries = get_entry_names()

    with open(CONFIG_FILE_PATH) as f:
        config = json.loads(f.read())

    entries_to_icons = config["icons"]

    icons = []
    for entry in current_entries:
        entryname = entry.group("entryname")
        if entryname in entries_to_icons:
            icons.append(entries_to_icons[entryname])
        else:
            warning(
                    f"{entryname} is a new grub menu entry, no icon will be set for it. "
                    f"Rerun matter.py to set icons"
                )
            icons.append("_")

    do_patch_grub_cfg_icons(icons)


def do_patch_grub_cfg_icons(icons):

    info(f"Begin {GRUB_CFG_PATH} patch")
    with open(GRUB_CFG_PATH, "r", newline="") as f:
        grub_cfg = f.read()
    # Read current grub cfg
    entries = get_entry_names()

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

    info(f"{len(icons)} icons successfully patched onto {GRUB_CFG_PATH}")


def do_set_icons(patch_grubcfg):

    icons = user_args.icons

    if icons is None:
        error("Stop. Unspecified icons (--icons/-i argument)")
    icons = [check_icon_converted(i) for i in icons]

    # Read current grub cfg
    entries = get_entry_names()
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

    do_patch_grub_cfg_icons(user_args.icons)

    if patch_grubcfg:
        create_config_file()

        # Patch grub-mkconfig so everytime it executes, it patches grub.cfg
        info(f"Begin {GRUB_MKCONFIG_PATH} patch")
        info(f"Clean old {GRUB_MKCONFIG_PATH} patch if any")

        # cmd_icons = " ".join(user_args.icons)
        # seticons_call = f"{INSTALLER_DIR}/{INSTALLER_NAME} -so -i {cmd_icons} >&2"
        seticons_call = f"{INSTALLER_DIR}/{INSTALLER_NAME} --configicons >&2"
        new_grub_mkconfig = read_cleaned_grub_mkconfig()

        # grub-mkconfig is called on upgrade, and on failure it halts.
        # A failure on our part should not halt an upgrade, let's temporarily
        # disable the stop-on-error functionality with set +e. See #67
        new_grub_mkconfig += (
            f"\n\n{BEGIN_THEME_OVERRIDES}\n"
            f"set +e\n"
            f"{seticons_call}\n"
            f"set -e\n"
            f"{END_THEME_OVERRIDES}\n\n"
        )

        check_root_or_prompt()
        with open(GRUB_MKCONFIG_PATH, "w") as f:
            f.write(new_grub_mkconfig)

        info(
            f"{GRUB_MKCONFIG_PATH} successfully patched, icons will now persist between grub updates."
        )


def install_hookcheck():
    info(f"Create hook check script")
    with open(HOOKCHECK_TEMPLATE_PATH, "r", newline="") as f:
        template = f.read()

    cmd_icons = " ".join(user_args.icons)
    # seticons_call = f"{INSTALLER_DIR}/{INSTALLER_NAME} -so -i {cmd_icons} >&2"
    seticons_call = f"{INSTALLER_DIR}/{INSTALLER_NAME} --configicons"

    context = {
        "GRUB_MKCONFIG_PATH": GRUB_MKCONFIG_PATH,
        "THEME_NAME": THEME_NAME,
        "THEME_OVERRIDES_TITLE": THEME_OVERRIDES_TITLE,
        "BEGIN_THEME_OVERRIDES": BEGIN_THEME_OVERRIDES,
        "END_THEME_OVERRIDES": END_THEME_OVERRIDES,
        "SETICONS_CALL": seticons_call,
    }

    parsed_script = template.format(**context)
    script_file_path = f"{GRUB_SCRIPTS_PATH}/99_matter"

    with open(script_file_path, "w") as f:
        f.write(parsed_script)

    # Make it executable by user, group and others
    st = os.stat(script_file_path)
    os.chmod(script_file_path, st.st_mode | 0o111)


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
        default=None,
        # default will be set to THEME_DEFAULT_BACKGROUND
    )
    parser.add_argument(
        "--image",
        "-im",
        type=str,
        help=f"image file to use as background, supported extensions: PNG, JPG, JPEG, TGA",
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
    parser.add_argument(
        "--configicons",
        "-ci",
        action="store_true",
        help="set grub entries icons using config file. "
    )
    parser.add_argument(
        "--downloadbackground",
        "-dlbg",
        type=str,
        help=f"download the background image from the given url",
    )
    return parser.parse_args()


if __name__ == "__main__":
    try:
        check_python_version()
        user_args = parse_args()

        if user_args.listentries:
            do_list_grub_cfg_entries()
        elif user_args.buildonly:
            prepare_source_dir()
        elif user_args.seticons_once:
            do_set_icons(patch_grubcfg=False)
        elif user_args.seticons:
            do_set_icons(patch_grubcfg=True)
        elif user_args.uninstall:
            do_uninstall()
        elif user_args.configicons:
            patch_from_config_file()
        elif user_args.icons is None:
            do_preinstall_hint()
        else:
            do_install()

        if user_args.test:
                do_test()
    except KeyboardInterrupt:
        error("Stop. Script halted by user")
        sys.exit(1)
