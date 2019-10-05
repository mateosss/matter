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
    echo -e "Setting theme to red"
    sed -i -E 's/(selected_item_color = )"#[0-9a-fA-F]+"/\1"#F44336"/' "${THEME_DIR}/${THEME_NAME}/theme.txt"
  fi

  if [ "${PALETTE}" == "pink" ]; then
    echo -e "Setting theme to pink"
    sed -i -E 's/(selected_item_color = )"#[0-9a-fA-F]+"/\1"#E91E63"/' "${THEME_DIR}/${THEME_NAME}/theme.txt"
  fi

  if [ "${PALETTE}" == "purple" ]; then
    echo -e "Setting theme to purple"
    sed -i -E 's/(selected_item_color = )"#[0-9a-fA-F]+"/\1"#9C27B0"/' "${THEME_DIR}/${THEME_NAME}/theme.txt"
  fi

  if [ "${PALETTE}" == "deep-purple" ]; then
    echo -e "Setting theme to deep purple"
    sed -i -E 's/(selected_item_color = )"#[0-9a-fA-F]+"/\1"#673AB7"/' "${THEME_DIR}/${THEME_NAME}/theme.txt"
  fi

  if [ "${PALETTE}" == "blue" ]; then
    echo -e "Setting theme to blue"
    sed -i -E 's/(selected_item_color = )"#[0-9a-fA-F]+"/\1"#2196F3"/' "${THEME_DIR}/${THEME_NAME}/theme.txt"
  fi

  if [ "${PALETTE}" == "cyan" ]; then
    echo -e "Setting theme to cyan"
    sed -i -E 's/(selected_item_color = )"#[0-9a-fA-F]+"/\1"#00BCD4"/' "${THEME_DIR}/${THEME_NAME}/theme.txt"
  fi

  if [ "${PALETTE}" == "teal" ]; then
    echo -e "Setting theme to teal"
    sed -i -E 's/(selected_item_color = )"#[0-9a-fA-F]+"/\1"#009688"/' "${THEME_DIR}/${THEME_NAME}/theme.txt"
  fi

  if [ "${PALETTE}" == "green" ]; then
    echo -e "Setting theme to green"
    sed -i -E 's/(selected_item_color = )"#[0-9a-fA-F]+"/\1"#4CAF50"/' "${THEME_DIR}/${THEME_NAME}/theme.txt"
  fi

  if [ "${PALETTE}" == "yellow" ]; then
    echo -e "Setting theme to yellow"
    sed -i -E 's/(selected_item_color = )"#[0-9a-fA-F]+"/\1"#FFEB3B"/' "${THEME_DIR}/${THEME_NAME}/theme.txt"
  fi

  if [ "${PALETTE}" == "orange" ]; then
    echo -e "Setting theme to orange"
    sed -i -E 's/(selected_item_color = )"#[0-9a-fA-F]+"/\1"#FF9800"/' "${THEME_DIR}/${THEME_NAME}/theme.txt"
  fi

  if [ "${PALETTE}" == "gray" ]; then
    echo -e "Setting theme to gray"
    sed -i -E 's/(selected_item_color = )"#[0-9a-fA-F]+"/\1"#9E9E9E"/' "${THEME_DIR}/${THEME_NAME}/theme.txt"
  fi

  if [ "${PALETTE}" == "white" ]; then
    echo -e "Setting theme to white"
    sed -i -E 's/(selected_item_color = )"#[0-9a-fA-F]+"/\1"#FFFFFF"/' "${THEME_DIR}/${THEME_NAME}/theme.txt"
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
