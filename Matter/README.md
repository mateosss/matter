Based on Vimix by Vince Liuice

https://www.gnu.org/software/grub/manual/grub/html_node/Theme-file-format.html

Hay que cambiar cosas de /boot/grub/grub.cfg, esta se regenera cada tanto, habría que hacerlo bien en algún momento mejor

- en grub.cfg al lado de cada "Entrada", hay que poner `--class ICONOAUSAR` sin el .png
- donde dice loadfonts hay que poner la googlesans, y capaz que haga falta tambien en otra parte donde dice /usr/share/grub/fonts poner la googlesans ahi tambien
