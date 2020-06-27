# Matter

Minimalist grub theme inspired by material design 2.

![Matter Grub](demo.png)

Feel free to request new icons, open issues for any problem you have
and/or submit pull requests.


# Download

[Click here to download Matter zip file](https://github.com/mateosss/matter/archive/master.zip) or just get the repo.

# Usage

## Typical Installation Example

*The image above is a screenshot of this installation.*

You need to customize your grub entries order and folders with something like
[grub-customizer](https://launchpad.net/grub-customizer)
([tutorial](https://vitux.com/how-to-install-grub-customizer-on-ubuntu/)), then:

```sh
./matter.py
./matter.py -si
./matter.py -si ubuntu windows folder _ _ _ _ settings
```

Last command assumes the order of the grub entries shown in `./matter.py -si`
were as follows:

```sh
1. Ubuntu
2. Windows
3. More Options
4. ├ Ubuntu, with Linux 5.3.0-61-generic
5. ├ Ubuntu, with Linux 5.3.0-61-generic (recovery mode)
6. ├ Ubuntu, with Linux 5.3.0-59-generic
7. └ Ubuntu, with Linux 5.3.0-59-generic (recovery mode)
8. System Setup
```

The "`_`" (underscore) characters tell to not try to set any icon for the
respective entries (4, 5, 6 and 7 in this case).

## Installation in General

```sh
# Installation
./matter.py

# Icons
## List your grub entries and available icons
./matter.py -si
## Will set entry X to iconX (one of the available icons just shown)
./matter.py -si icon1 icon2 ...

# Uninstall
./matter.py -u

# Install with Custom Colors
# Note: The "#" symbol below is part of the command, not a comment
./matter.py -hl orange -fg \\#CCCCCC -bg black
# You can see all premade colors like orange and black, and what each flag is with the help command as shown below

# Help
./matter.py -h

```

# What does Matter do to my system files?

Matter needs to edit three files:

1. `/etc/default/grub`: For setting theme and resolution.
2. `/boot/grub/grub.cfg`: For setting icons.
3. `/usr/sbin/grub-mkconfig`: For making icons persistent across grub updates.

Also it places the theme files in `/boot/grub/themes/Matter/`, this one is
standard to grub themes in general.

Both **(1)** and **(3)** are clearly distinguished with special `BEGIN`/`END`
comments at the end of file. **(2)** Adds a `--class` flag to each entry, but it
can be rebuilt as new from `grub-mkconfig`.

*All of these modifications are **completely** cleaned up by uninstalling with
the script*

# Contributing

For adding icons or new functionalities to the script, read
https://github.com/mateosss/matter/wiki

# Thanks

- Original theme based on https://github.com/vinceliuice/grub2-themes
- Icons from https://materialdesignicons.com/
