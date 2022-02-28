#!/bin/bash
# Getting bigger than small wrapper for ascii image python script
# Calculates single and double strike images
# eric F. January-October 2021
#
# Version history (most recent first)
# dsasciihuge.sh - Make huge, multi-column prints
#                  Modern, command-line options with default values
#
# dsasciibig.sh  - Modifications to use different generating ascii python script
#                  Runs asciibig.py (so far)
#                  asciibig.py has minor modifications from asciiv2wide.py
#                  
# dsasciiwide.sh - Print double strike over one full width of 14.5" paper.
#                  Runs asciivw2ide.py
#
# How to use:
# dsasciihuge.sh FILE.jpg 
# will run with default values, including color map, contrast, and brightness.
#
# Note that "$@" passes all arguments
#
#  options:
#
#  -b BRIGHT   brightness (default 1)
#  -c CONTRAST contrast (default 1)
#  -g          generate 1.5" gaps ( add (PAGES - 1)*PITCH columns to output)
#  -f          flip or mirror the image
#  -i PWIDTH   inches for page width (default is 13.2. Use 13.1 for doublestrike diablo prints, or 8.0? for narrow paper)
#  -l LINESIN  lines per inch (qume can be 6 or 8. diablo is 6, which is default.)
#  -m COLMAP   color map (defaults to 22)
#  -p PITCH    10 or 12 columns / inch (default 10)
#  -r          rotate image 180 degrees
#  -w PAGES    specify width in pages (default 1)

# Notes:
# It would be easier if paper width is specified in tenths of an inch. We could avoid float math in the shell.
# We're going to generate two big text files, then process these into multiple printouts.

# default values
PAGES=1         #Number of pages wide
PITCH=10        #Columns / inch
GAP_FLAG=0      #Generate gaps
COLMAP=22       #Color map (single strike will have blank second cm)
ROT_FLAG=0      #Rotate 180 degrees
CONTRAST=1.0    #Contrast
BRIGHT=1.0      #Brightness
LINEIN=6        #Lines / inch
FLIP_FLAG=0     #Mirror the image
PWIDTH=13.2     #Default page width in inches (for Diablo, need to specify 13.1)

# process command line flags here
# use colon if argument expected
usage() { echo "$0 usage: [-b BRIGHTNESS] [-c CONTRAST] [-i PAPER_WIDTH_INCH] [-l LINES_PER_INCH] [-m COLORMAP] [-p PITCH] [-w PAGES] [-gf] imagefile.jpg" && grep " .)\ #" $0; exit 0; }
[ $# -eq 0 ] && usage
while getopts w:p:gfm:b:c:l:i: flag
do
    case "${flag}" in
        w) PAGES=${OPTARG};;
        p) PITCH=${OPTARG};;
        g) GAP_FLAG=1;;
        m) COLMAP=${OPTARG};;
	b) BRIGHT=${OPTARG};;
	c) CONTRAST=${OPTARG};;
	l) LINESIN=${OPTARG};;
        f) FLIP_FLAG=1;;
	i) PWIDTH=${OPTARG};;
	r) ROT_FLAG=1;;
    esac
done
shift $((OPTIND -1))

FILENAME=$@
FILEBASE=${@%.*}
[ $FLIP_FLAG -eq 1 ] && FILEBASE=$FILEBASE"_FLIP"

# asciibig.py inputs are filename, colormap, rotate_flag, contrast, brightness
# asciihuge.py inputs are filename, colormap, rotate_flag, contrast, brightness, pages, pitch, gap_flag

ASCIIVERSION=asciihuge.py

# Python code generates one large text file, which will be chopped up into separate strips if using multiple pages
python3 $ASCIIVERSION $FILENAME $COLMAP $ROT_FLAG $CONTRAST $BRIGHT $PAGES $PITCH $LINEIN $PWIDTH $GAP_FLAG $FLIP_FLAG > $FILEBASE"1.txt"
python3 $ASCIIVERSION $FILENAME `expr $COLMAP + 1` $ROT_FLAG $CONTRAST $BRIGHT $PAGES $PITCH $LINEIN $PWIDTH $GAP_FLAG $FLIP_FLAG > $FILEBASE"2.txt"

#Process each column of pages

i="0"
while [ $i -lt $PAGES ]; do
    # cut page columns from files 1 and 2

    GAP=$(( $GAP_FLAG * 2 * $PITCH )); echo "GAP = " $GAP

    COLS=$(echo $PITCH*$PWIDTH" / 1" | bc) ; echo "$COLS"
    FIRSTCOL=$(( 1 + $i*($COLS + $GAP) )); echo "FIRSTCOL = " $FIRSTCOL
    LASTCOL=$(( ($i + 1)*$COLS + $i*$GAP )); echo "LASTCOL = " $LASTCOL

    cut -c $FIRSTCOL-$LASTCOL $FILEBASE"1.txt" > $FILEBASE$i"1.txt"
    cut -c $FIRSTCOL-$LASTCOL $FILEBASE"2.txt" > $FILEBASE$i"2.txt"
    
    # merge page column to create doublestrike text
    paste -d "\n" $FILEBASE$i"1.txt" $FILEBASE$i"2.txt" > $FILEBASE$i"ds.txt"

    # strip every other line feed to create doublestrike
    sed -i.bak "N;s/\n/$(printf '\r')/" $FILEBASE$i"ds.txt"
    cat $FILEBASE$i"1.txt" $FILEBASE$i"2.txt"

    # save each strip

    mv $FILEBASE$i"ds.txt" $FILEBASE"_"$(( $i + 1 ))"OF"$PAGES"_"$COLS"_"$COLMAP"_"$ROT_FLAG"_"${BRIGHT/./}"_"${CONTRAST/./}".txt"
    rm $FILEBASE$i"1.txt" $FILEBASE$i"2.txt"
    rm $FILEBASE$i"ds.txt.bak"

    # generate olivettize output
    ~/bin/olivettizewide $FILEBASE"_"$(( $i + 1 ))"OF"$PAGES"_"$COLS"_"$COLMAP"_"$ROT_FLAG"_"${BRIGHT/./}"_"${CONTRAST/./}".txt"

    i=$[$i+1]
done

rm $FILEBASE"1.txt" $FILEBASE"2.txt"

