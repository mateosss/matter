# Matter

Minimalist grub theme inspired by material design 2.

![Matter Grub](demo.png)

Based on https://github.com/vinceliuice/grub2-themes

Feel free to request new icons, open issues for any problem you have
and/or submit pull requests.

# Installation

Download the repo as a zip and run `sudo ./set-matter.sh`.

## Font color

`sudo ./set-matter.sh -p <color>` is something like `blue`, `red`, `deep-purple`
and so on (read through `set-matter.sh` for other available colors).


# Removal

Comment or delete the following line from your `/etc/default/grub` file to
disable the theme:
```
GRUB_THEME="/boot/grub/themes/Matter/theme.txt"
```
And then run `sudo update-grub` (or `sudo grub-mkconfig -o /boot/grub/grub.cfg`
if you don't have `update-grub`).

You can delete `/boot/grub/themes/Matter` as well.

# Contributing

For adding icons or new functionalities to the script, read
https://github.com/mateosss/matter/wiki
