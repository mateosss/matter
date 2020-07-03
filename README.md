# Matter

Minimalist grub theme originally inspired by material design 2.

Feel free open issues for any problem or request you have and/or submit pull
requests.


# Download

[Click here to download Matter zip file](https://github.com/mateosss/matter/archive/master.zip) or just get the repo.

It is **strongly adviced** to put the downloaded files in some folder that will not
get deleted, as the main script `matter.py` is needed for future grub updates
made by your system. Also if you wan't to uninstall matter you should do it from
there as well.

# Usage

## Help

You always can see the command reference with `./matter.py -h`, next up are some
sections that may be useful, or may not be very well documented in the command's
help.

## Quick Start

Following is a Matter installation with default values. Don't worry, it is very
easy to rollback or overwrite this installation later if you wan't to.

The script that does all the work is `matter.py`, so let's start by running it

```none
./matter.py
```

It outputs almost everything you need to know for later, but for now let's focus
on the list it shows, those are your grub entries. It should look similar to
this one:

```sh
1. Ubuntu
2. Windows
3. More Options
4. Ubuntu, with Linux 5.3.0-61-generic
5. Ubuntu, with Linux 5.3.0-61-generic (recovery mode)
6. Ubuntu, with Linux 5.3.0-59-generic
7. Ubuntu, with Linux 5.3.0-59-generic (recovery mode)
10. System Setup
```

Now you should pick some icons from materialdesignicons.com for each entry
listed, (you only need the icon's name, use the search panel and hover over any
icon you like to see its name). In these example I will pick `ubuntu` for entry
1, `microsoft-windows` for 2, `folder` for 3 (as it is a submenu in my
particular case), and `cog` for 10, I don't care about all the remaining entries
so I will just use "`_`" (underscore) for those.

```none
# Installs matter with the icons matching the entries
./matter.py -i ubuntu microsoft-windows folder _ _ _ _ cog
```

**And thats it!** If you reboot now, you should get something like this:

![Quick Start Result](demo.png)

*Tip: If you need to tidy up your grub entries hierarchy and names I recommend using [grub-customizer](https://launchpad.net/grub-customizer) ([tutorial](https://vitux.com/how-to-install-grub-customizer-on-ubuntu/))*

## Uninstall

You can completely remove Matter from your system with `./matter.py -u`

## Fonts

Matter uses `.ttf` fonts and only one, the default, comes prepackaged. You can
specify your own fonts by giving a `.ttf` file, the font name, and an optional
font size like so:

```none
./matter.py -ff ~/Desktop/fonts/Cinzel/Cinzel-Regular.ttf -fn Cinzel Regular -fs 40
```

- `--fontfile/-ff`: The `.ttf` path
- `--fontname/-fn`: The name of the font, in this case `Cinzel Regular` but
  could be `Open Sans Bold` (*Tip: If you don't know the font name, you can
  specify any name, go to the grub, press C to open console, and type lsfonts to
  list the font names*)
- `--fontsize/-fs`: By default it is 32, recommended values are multiples of 4.
- `--font/-f`: This argument is not used in this example as it is used to select
  prepackaged fonts. Note that after giving a ttf file to `-ff`, matter will
  save it as a prepackaged font, so it can be accessed with this flag. See
  prepackaged (available) fonts at the end of `--help/-h` output

*Tip: [Google Fonts](https://fonts.google.com/) is a good place to get fonts*

## Colors

You can specify 4 colors `--foreground/-fg`, `--background/-bg`,
`--iconcolor/-ic` and `--highlight/-hl` (selected text color), there are some
Material Design colors prepackaged that you can see at the end of the
`--help/-h` output, you can also specify custom colors. Here is an example of
the syntax:

```none
./matter.py -hl FFC107 -fg white -bg 2196f3 -ic pink
```

## Testing Without Rebooting

If you install the `pip` package
[`grub2-theme-preview`](https://github.com/hartwork/grub2-theme-preview)
(https://github.com/hartwork/grub2-theme-preview) you can test combinations of
fonts and colors with the `--buildonly/-b` and `--test/-t` flags like so:

```none
./matter.py -t -b -i ubuntu microsoft-windows folder _ _ _ _ _ _ cog \
-hl FFC107 -fg white -bg 2196F3 \
-ff ~/Desktop/fonts/MuseoModerno/static/MuseoModerno-Regular.ttf \
-fn MuseoModerno Regular -fs 40
```
*Note: it will use your system's grub.cfg, so set your icons beforehand*

# What does Matter do to my system files?

Besides the need for the installer files to be in a persistent location, Matter
needs to edit three files:

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
