#!/bin/bash

ROOT_UID=0
THEME_DIR="/boot/grub/themes"
THEME_DIR_2="/boot/grub2/themes"
THEME_NAME=Matter

echo "Installing Matter grub theme..."

# Parsing parameters
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -p|--palette)
    PALETTE="$2"
    shift # past argument
    shift # past value
    ;;
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

# Check command avalibility
function has_command() {
  command -v $1 > /dev/null
}

# Set the theme 
function set_theme() {
    echo -e "Setting theme to ${PALETTE}"
    sed -i -E 's/(selected_item_color = )"#[0-9a-fA-F]+"/\1"'$1'"/' "${THEME_DIR}/${THEME_NAME}/theme.txt"
}

echo "Checking for root access..."

# Checking for root access and proceed if it is present
if [ "$UID" -eq "$ROOT_UID" ]; then

  # Create themes directory if not exists
  echo "Checking for the existence of themes directory..."
  [[ -d ${THEME_DIR}/${THEME_NAME} ]] && rm -rf ${THEME_DIR}/${THEME_NAME}
  [[ -d ${THEME_DIR_2}/${THEME_NAME} ]] && rm -rf ${THEME_DIR_2}/${THEME_NAME}
  [[ -d /boot/grub ]] && mkdir -p ${THEME_DIR}
  [[ -d /boot/grub2 ]] && mkdir -p ${THEME_DIR_2}

  # Copy theme
  echo "Installing ${THEME_NAME} theme..."
  [[ -d /boot/grub ]] && cp -a ${THEME_NAME} ${THEME_DIR}
  [[ -d /boot/grub2 ]] && cp -a ${THEME_NAME} ${THEME_DIR_2}

  # Setting palette color
  if [ "${PALETTE}" == "red" ]; then
    set_theme "#F44336"
  fi

  if [ "${PALETTE}" == "pink" ]; then
    set_theme "#E91E63"
  fi

  if [ "${PALETTE}" == "purple" ]; then
    set_theme "#9C27B0"
  fi

  if [ "${PALETTE}" == "deep-purple" ]; then
    set_theme "#673AB7"
  fi

  if [ "${PALETTE}" == "blue" ]; then
    set_theme "#2196F3"
  fi

  if [ "${PALETTE}" == "cyan" ]; then
    set_theme "#00BCD4"
  fi

  if [ "${PALETTE}" == "teal" ]; then
    set_theme "#009688"
  fi

  if [ "${PALETTE}" == "green" ]; then
    set_theme "#4CAF50"
  fi

  if [ "${PALETTE}" == "yellow" ]; then
    set_theme "#FFEB3B"
  fi

  if [ "${PALETTE}" == "orange" ]; then
    set_theme "#FF9800"
  fi

  if [ "${PALETTE}" == "gray" ]; then
    set_theme "#9E9E9E"
  fi

  if [ "${PALETTE}" == "white" ]; then
    set_theme "#FFFFFF"
  fi

  # Set theme
  echo -e "Setting ${THEME_NAME} as default..."
  grep "GRUB_THEME=" /etc/default/grub 2>&1 >/dev/null && sed -i '/GRUB_THEME=/d' /etc/default/grub

  [[ -d /boot/grub ]] && echo "GRUB_THEME=\"${THEME_DIR}/${THEME_NAME}/theme.txt\"" >> /etc/default/grub
  [[ -d /boot/grub2 ]] && echo "GRUB_THEME=\"${THEME_DIR_2}/${THEME_NAME}/theme.txt\"" >> /etc/default/grub

  # Update grub config
  echo -e "Updating grub config..."
  if has_command update-grub; then
    update-grub
  elif has_command grub-mkconfig; then
    grub-mkconfig -o /boot/grub/grub.cfg
  elif has_command grub2-mkconfig; then
    grub2-mkconfig -o /boot/efi/EFI/fedora/grub.cfg
  fi

  echo "Done."

else
    echo "Failed. Are you root?"
fi
