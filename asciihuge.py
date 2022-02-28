# asciihuge.py 
# create an ascii image from an RGB image
# This version uses Python 3.6 and the grayscale image routines in pillow
# This is a rewrite from an earelier version using a class for the ascii image
# e.m.f. December 2020

"""
Starting with code from Paul Rickards
For the teleprinter, an entire page is 80 columns by 66 rows
A photo is typically 4:3
for portrait, the ascii output should be 80 columns, 64 rows (5/4)
A square image should be 80 columns, 48 rows

The teleprinter prints 10 characters / inch horizontally and
6 rows / inch vertically. So 11 inches gives 66 total rows max.
The Olivetti actually prints 79 columns reliably.

For wide-format printers: I can set 10 or 12 characters / inch horizontal and
6 or 8 characters / inch vertical
Want to preserve 4:3 aspect ratio
If 132 characters wide (11.12") at 12 char/in
then height is 14.8". With 8 char / in, 119 lines
So, downsample image to 134 wide, 119 high

Example of use:
  asciiv2.py filename colormap rotateflag contrast brightness
  python3 asciiv2.py IMG_9106.jpeg 0 1 1.3 1.5

Currently generates to 80 columns. If need to truncate, use cut:
  cat file | cut -c -79

  can also shift right:
  cat file | cut -c 2-80

Bash wrapper performs a non-POSIX removal of spaces to save TTY wear:
  sed 's/[[:space:]]*$//'
  e.g., a bash script that contains:
  python3 asciiv2.py "$@" | sed 's/[[:space:]]*$//'

Jan 4, 2021  added more character maps
Jan 11, 2021 added notes on page size
Jan 18, 2021 corrected the init method
Aug 24, 2021 modified this version for wide format
Sep 18, 2021 modified for big format
Oct 24, 2021 multipage width images, gaps between pages, new colormaps, new shell wrapper
             many more command line options are passed

Next: need to implement overstrike code (generating ASCII overstrike images)

"""

from PIL import Image, ImageEnhance, ImageOps
import sys, math

"""
An AsciiImage is initially an RGB image, an ASCII colormap, desired constrast,
brightness, and orientation. The first method of AsciiImage converts the image
to grayscale in the orientiation and size of the final printed page. The second
method prints text to stdout by mapping the grayscale image to the specific
ASCII colormap.
"""
class AsciiImage:
    """ ASCII color maps """
    """ Maps with second set as spaces are single strike"""
    # Olivetti character map based on 12/24 analysis of character histogram (0,2,4,6,8)
    maps = [" .\")O&8M",
            "         ",
            " .\"_O&8M",
            "         ",
            " .,:=*#%$",
            "         ",
            " .\"',>\!<L-:;IZ1CT+/UVY=J]()_*GRW2[ESX?D7FH^#49K56P&3ABOQ0%8@",
            "                                                              ",
            "  ..,,::==**##%%$$",
            "                  ",
    # double strike maps (10 and 12)
            "  ,'  (%&8##$",
            " '..H#7-QN6&9",
            "  ' (&#$",
            "  .H7Q69",
    # Older character maps (14, 16, 18)
            " .'T>[+2!)\"3#0$@",
            "                 ",
            " .\"-',T=:<>U^;SX[+/HOM279CQ?DJRWY!GNP)1](ABFZ5\348I%6LV&EK_#*0$@",
            "                                                                 ",
            " .\"-',T=:;<>!U^SX[]+/HNP)(1F5\3I%LV&EK_#*0$@",
            "                                             ",
    # Based on Hammersley (20)
            "  --TTTTTTTT",
            "      --==HH",
    # Modified Hammersley (22) (OLD 14)
            "  --IIIIIIII",
            "      --==HH",
#            " -IIII",
#            "   -=H",
    # Modified Hammersley 3 (24) due to broken petals on non-ASCII prestige elite wheel
            " --11111111",
            "     --==MM",
    # Single based on twitter image posted by Peter Fletcher (26)
            " .;/=IS$",
            "        ",
    # Single based on Paul Bourke, http://paulbourke.net/dataformats/asciiart/ (28, 30)
            " .:-=+*#%@",
            "          ",
            " .'`^\",:;Il!i><~+_-?][}{1)(|\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
            "                                                                       ",
    # Modified Hammersley extended (32)
            "  --==IIHHIIIIHHII",
            "          --====HH",
    # @asr33 PJW (34)
            " ...PPJPJWPJW",
            "  -* //\\\***"
    ]

    
    """ Read in all arguments """
    def __init__(self,args):
        self.image = Image
        try: self.colormap = self.maps[int(args[2])]
        except IndexError:  # default if map choice is out of range
            self.colormap = self.maps[0]
        self.rotateflag = int(args[3])
        self.contrast = float(args[4])
        self.brightness = float(args[5])
        self.pages = int(args[6])
        self.pitch = int(args[7])
        self.rowfreq = int(args[8])
        self.pagewidth = float(args[9])   #pagewidth in inches
        self.gap = int(args[10])
        self.flip = int(args[11])

    def processImage(self):
        """ Image into portrait orientation and apply rotation flag"""
        img = self.image
        width, height = img.size
        columns = int((self.pages*self.pagewidth+self.gap*(self.pages-1)*2)*self.pitch)
        rows = int(columns*(height/width)*(self.rowfreq/self.pitch))
        img = img.rotate(self.rotateflag*180)
        if self.flip : img = ImageOps.mirror(img)

        """ Make grayscale and apply brightness and contrast """
        # Code to split into 3 channels if need to manipulate colors
        """
        r, g, b = img.split()
        r = r.point(lambda i: i * 0.2)
        g = g.point(lambda i: i * 1.0)
        b = b.point(lambda i: i * 0.2)
        # Recombine back to RGB image
        img = Image.merge('RGB', (r, g, b))
        """
        img = img.convert('L')
        img = ImageEnhance.Contrast(img).enhance(self.contrast)
        img = ImageEnhance.Brightness(img).enhance(self.brightness)

        """ Resize final image """
        self.image = img.resize((columns,rows),3)

    def printImage(self):
        width, height = self.image.size
        for y in range(0,height-1,1):
            for x in range(0,width,1):
                brightness = self.image.getpixel((x,y))/256
                brightness = abs(1-brightness) # invert brightness for printing
                                               # dark ink on light paper
                sys.stdout.write(self.colormap[int(brightness*len(self.colormap)-1)])
                sys.stdout.flush()
            print()

"""
 Main program
"""
if __name__ == '__main__':

#    I'm expecting these 11 arguments:
#    $FILENAME $COLMAP $ROT_FLAG $CONTRAST $BRIGHT $PAGES $PITCH $LINEIN $PWIDTH $GAP_FLAG $FLIP_FLAG
    if len(sys.argv) == 12:
        ascii = AsciiImage(sys.argv)
        filename = sys.argv[1]
        try:
            with Image.open(filename) as ascii.image:
                ascii.processImage()
                ascii.printImage()
        except OSError:
            print("Error opening", filename)
    else:
        print("\nusage: ascii.sh filename colormap rotate brightness contrast\n")

