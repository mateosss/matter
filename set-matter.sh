#!/bin/bash

TARGET_DIR="/boot/grub/themes"
TARGET_DIR_2="/boot/grub2/themes"
THEME_NAME="Matter"
WORKING_DIR=`dirname "$(readlink -f "$0")"`

declare -A COLORS
readonly COLORS=(
  [RED]="#F44336"
  [PINK]="#E91E63"
  [PURPLE]="#9C27B0"
  [DEEP_PURPLE]="#673AB7"
  [BLUE]="#2196F3"
  [CYAN]="#00BCD4"
  [TEAL]="#009688"
  [GREEN]="#4CAF50"
  [YELLOW]="#FFEB3B"
  [ORANGE]="#FF9800"
  [GRAY]="#9E9E9E"
  [WHITE]="#FFFFFF"
)

# Default highlight color
PALETTE="PINK"

# Parsing parameters
while [[ $# -gt 0 ]]; do
  key="$1"

  case $key in
  -p | --palette)
    PALETTE="$2"
    shift # past argument
    shift # past value
    ;;
  -u | --uninstall)
    UNISTALL=1
    shift
    ;;
  -h | --help)
    echo "Usage (run as root): $0 [options]"
    echo
    echo "Options:"
    echo -e "  -p, --palette COLOR\tChanges color palette (Supported colors: ${!COLORS[*]})"
    echo -e "  -h, --help\t\tDisplay this help and exit"
    echo -e "  -u, --uninstall\t\tUninstall Matter"
    exit 0
    ;;
  *) # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
  esac
done
echo $POSITIONAL
set -- "${POSITIONAL[@]}" # restore positional parameters

# Checking for root access
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

function has_command() {
  # Check command avalibility
  command -v $1 >/dev/null
}

function update_grub() {
  # Update grub config
  echo -e "Updating grub config..."
  if has_command update-grub; then
    update-grub
  elif has_command grub-mkconfig; then
    grub-mkconfig -o /boot/grub/grub.cfg
  elif has_command grub2-mkconfig; then
    grub2-mkconfig -o /boot/efi/EFI/fedora/grub.cfg
  fi
}

# Uninstall
if [[ "${UNISTALL}" == "1" ]]; then
  echo "Removing Matter..."
  [[ -d ${TARGET_DIR}/${THEME_NAME} ]] && rm -rf ${TARGET_DIR}/${THEME_NAME}
  [[ -d ${TARGET_DIR_2}/${THEME_NAME} ]] && rm -rf ${TARGET_DIR_2}/${THEME_NAME}

  sed -i '/GRUB_THEME=/d' /etc/default/grub
  sed -i '/# Added by Matter theme/d' /etc/default/grub 

  update_grub
  echo "Done."
  exit 0
fi

# Install
echo "Configuring Matter..."

# Create themes directory if not exists
echo "Checking for the existence of themes directory..."
[[ -d ${TARGET_DIR}/${THEME_NAME} ]] && rm -rf ${TARGET_DIR}/${THEME_NAME}
[[ -d ${TARGET_DIR_2}/${THEME_NAME} ]] && rm -rf ${TARGET_DIR_2}/${THEME_NAME}
[[ -d /boot/grub ]] && mkdir -p ${TARGET_DIR}
[[ -d /boot/grub2 ]] && mkdir -p ${TARGET_DIR_2}

# Set the chosen color if it is supported
if [[ "${!COLORS[*]}" =~ "${PALETTE}" ]]; then
  echo -e "Setting theme to ${PALETTE}"
  sed -i -E "s/(selected_item_color = )\".*\"/\1\"${COLORS[${PALETTE}]}\"/" "${WORKING_DIR}/${THEME_NAME}/theme.txt"
fi

# Copy theme
echo "Installing ${THEME_NAME} theme..."
[[ -d /boot/grub ]] && cp -a ${WORKING_DIR}/${THEME_NAME} ${TARGET_DIR}
[[ -d /boot/grub2 ]] && cp -a ${WORKING_DIR}/${THEME_NAME} ${TARGET_DIR_2}

# Set theme
echo -e "Setting ${THEME_NAME} as default..."
sed -i '/GRUB_THEME=/d' /etc/default/grub

[[ -d /boot/grub ]] && echo "# Added by Matter theme" >> /etc/default/grub
[[ -d /boot/grub2 ]] && echo "# Added by Matter theme" >> /etc/default/grub
[[ -d /boot/grub ]] && echo "GRUB_THEME=\"${TARGET_DIR}/${THEME_NAME}/theme.txt\"" >> /etc/default/grub
[[ -d /boot/grub2 ]] && echo "GRUB_THEME=\"${TARGET_DIR_2}/${THEME_NAME}/theme.txt\"" >> /etc/default/grub

update_grub

# Add default icons
echo "Adding default icons..."
if has_command grub-mkconfig; then
  sed -i -E -e "s/.*(menuentry) '[^']+'(( --class [^ ]+)+)?/& --class play/" /boot/grub/grub.cfg
  sed -i -E -e "s/.*(submenu) '[^']+'(( --class [^ ]+)+)?/& --class folder/" /boot/grub/grub.cfg
elif has_command grub2-mkconfig; then
  sed -i -E -e "s/.*(menuentry) '[^']+'(( --class [^ ]+)+)?/& --class play/" /boot/efi/EFI/fedora/grub.cfg
  sed -i -E -e "s/.*(submenu) '[^']+'(( --class [^ ]+)+)?/& --class folder/" /boot/efi/EFI/fedora/grub.cfg
fi

echo "Done."
