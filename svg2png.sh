#!/bin/bash

DIR=$(dirname $(realpath $0))
SVG_PATH="${DIR}/svg-icons"
PNG_PATH="${DIR}/Matter/icons"
CONVERT="convert \
    -trim \
    -scale 36x36 \
    -extent 72x72 \
    -gravity center \
    -define png:color-type=6 \
    -background none \
    -colorspace sRGB \
    -channel RGB \
    -threshold -1 \
    -density 300"

while [ "$1" != "" ]; do
    case $1 in
    -h | --help)
        echo "Usage: $0"
        echo
        echo "Options:"
        echo -e "  -h, --help\tDisplay this help and exit"
        echo -e "  -i, --icon\tSelect a specific icon name to convert"
        exit 0
        ;;
    -i | --install)
        ICON="$2"
        shift # past argument
        shift # past value
        ;;
    esac
    shift
done

if $(command -v convert) >/dev/null; then
    echo "Error: convert not found"
    echo "Install imagemagick to continue"
    exit 1
fi

echo "Starting conversion ..."

cd ${SVG_PATH}

if [[ -z "$ICON" ]]; then
    for file in *.svg; do
        echo "Processing ${file}"
        $CONVERT ${file} "${PNG_PATH}/${file%%.*}.png"
    done
else
    echo "Processing ${ICON}"
    $CONVERT ${ICON}.svg "${PNG_PATH}/${ICON}.png"
fi

echo "Finished!"
