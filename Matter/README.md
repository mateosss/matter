Based on Vimix by Vince Liuice

https://www.gnu.org/software/grub/manual/grub/html_node/Theme-file-format.html

You have to change things of /boot/grub/grub.cfg, this is regenerated every so often, but we should do well at some better time.

- In grub.cfg next to each "Entry", you have to put `--class ICON_TO_USE` without the .png
- You have to put the googlesans, where it says loadfonts. You may also need to put it where it says /usr/share/grub/fonts.