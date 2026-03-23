#!/bin/bash

#See https://1drv.ms/t/s!Ar_NG6G1HqMenHfZd8a5i9YVO6Eq?e=Hvo1Nn

#Image Magick
#sudo apt install imagemagick

# Script to use image magick to resize edited photos down to fit on the photoframe

# NOTE: On Ubuntu the command is /usr/bin/convert


# Find any files with spaces in the name and remove the space
find . -type f -name "* *" -print0 | xargs -0 -I {} bash -c '
    file="{}"
    new_file="${file// /_}"
    mv "$file" "$new_file"
'

# Replicate the folder structure
for d in `find . -type d | grep -v '^\.$'`
do
  mkdir ../PhotoFrame/$d
done

find . -type d -print0 | xargs -0 -I {} bash -c '
  dir="{}"
  mkdir "\"../PhotoFrame/${dir}\""
'
# Resize the images
for f in `find .  -type f | egrep -ie 'jpg|jpeg'|grep -v '  '`
do echo $f
  magick -quiet $f -resize 1024x768 ~/Processing/Photoframe/$f
done



# On Mortirolo - DO ALL THE IMAGES

# Make folder structure
find . -type d  ! -name '.' -print0 | xargs -0 -I {} bash -c '
  dir="{}"
  mkdir "../PhotoFrame/${dir}"
'

find . -type f -iname "*.jpg" -o -iname "*.jpeg" -print0 |  xargs -0 -I {} bash -c '
    file="{}"
     convert -quiet "${file}" -resize 1024x768 "../PhotoFrame/${file}"
'