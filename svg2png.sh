#!/bin/bash

DIR=$(dirname $(realpath $0))
SVG_PATH="${DIR}/svg-icons"
PNG_PATH="${DIR}/Matter/icons"

while [ "$1" != "" ]; do
    case $1 in
    -h | --help)
        echo "Usage: $0"
        echo
        echo "Options:"
        echo "  -h --help         Display this help and exit"
        exit 0
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
for file in *.svg; do
    echo "Processing ${file}"
    convert -trim \
        -scale 36x36 \
        -extent 72x72 \
        -gravity center \
        -background none \
        -channel RGB \
        -threshold -1 \
        ${file} "${PNG_PATH}/${file%%.*}.png"
done

echo "Finished!"
