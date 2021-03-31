#!/usr/bin/env python3
import os
import lxml.etree as ET

def inkscape_export_svg2png(color, src_path, dst_path):
    NS = {"svg" : 'http://www.w3.org/2000/svg'}
    FRAC = 0.7
    TEMPFILE = 'temp.svg'

    dom = ET.parse(src_path)
    root = dom.getroot()
    width, height = int(root.attrib['width']), int(root.attrib['height'])
    interval = (1-FRAC)*width/2

    elements = root.findall('svg:path', namespaces=NS)
    group = ET.SubElement(root, "g")
    for element in elements:
        element.attrib['style'] = f'fill:{color};fill-opacity:1'
        group.append(element)
    group.attrib['transform'] = f"matrix({FRAC},0,0,{FRAC},{interval},{interval})"

    et = ET.ElementTree(root)
    et.write(TEMPFILE, pretty_print=True)

    cmd = f"inkscape --export-filename='{dst_path}' {TEMPFILE} -w 72 2>/dev/null"
    exit_code = os.system(cmd)
    os.remove(TEMPFILE)
    return exit_code

def magick_convert_svg2png(color, src_path, dst_path):
    command = (
        r"convert -trim -scale 36x36 -extent 72x72 -gravity center "
        r"-define png:color-type=6 -background none -colorspace sRGB -channel RGB "
        rf"-threshold -1 -density 300 -fill \{color} +opaque none "
        rf"{src_path} {dst_path}"
        )
    return os.system(command)

if __name__ == '__main__':
    for file in os.listdir('./icons'):
        basename, ext = os.path.splitext(file)
        if ext == '.svg':
            inkscape_export_svg2png('#FFFFFF', f'icons/{basename}.svg', f'icons/INK_{basename}.png')
