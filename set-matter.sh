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
    -f|--font)
    FONT="$2"
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
  # List of supported colors
  supported_colors=(red pink purple deep_purple blue cyan teal green yellow orange gray white)
  
  # Hex values for the supported colors
  red="#F44336"
  pink="#E91E63"
  purple="#9C27B0"
  deep_purple="#673AB7"
  blue="#2196F3"
  cyan="#00BCD4"
  teal="#009688"
  green="#4CAF50"
  yellow="#FFEB3B"
  orange="#FF9800"
  gray="#9E9E9E"
  white="#FFFFFF"

  # Set the chosen color if it is supported
  if [[ " ${supported_colors[@]} " =~ " ${PALETTE} " ]]; then
      echo -e "Setting theme to ${PALETTE}"
      sed -i -E "s/(selected_item_color = )\"#[0-9a-fA-F]+\"/\1\"${!PALETTE}\"/" "${THEME_DIR}/${THEME_NAME}/theme.txt"
  fi

  # Setting available fonts
  # List of supported fonts
  supported_fonts=(poiret-one karla pattaya)

  # Set the chosen font
  if [[ ! " ${FONT} " == "  " ]] && [[ " ${supported_fonts[@] " =~ " ${FONT} " ]]; then
      echo -e "Setting font to ${FONT}"
      grub-mkfont "./Matter/fonts/${FONT}/${FONT}-regular.ttf"
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
