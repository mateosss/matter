# Matter

Minimalist grub theme inspired by material design 2.

![Matter Grub](demo.png)

Based on https://github.com/vinceliuice/grub2-themes

Feel free to request new icons, open issues for any problem you have
and/or submit pull requests.

# Installation

Download the repo as zip and run `sudo ./set-matter.sh`.
Run `sudo ./set-matter.sh -p blue` for blue theme.

# Removal

You can delete or comment this line in your `/etc/default/grub` file to disable the theme
```
GRUB_THEME="/boot/grub/themes/Matter/theme.txt"
```
And then run `sudo update-grub`.

Or alternatively if your distribution doesn't have that command you can run `sudo grub-mkconfig -o /boot/grub/grub.cfg`

Running `sudo ./set_matter.sh` creates a directory in `/boot/grub/themes` called "Matter". If you want to delete the theme completely it is safe remove this directory after completing the steps above.

# Contributing

For adding icons or new functionalities to the script, read
https://github.com/mateosss/matter/wiki
