#!python2.7
# python -m pip install PIL
import os, glob, sys, math, operator, ntpath
from itertools import izip
from operator import itemgetter

from PIL import Image, ImageChops, ImagePalette, ImageOps

THRESHOLD = 18

def lum(pixel):
    return (0.299 * pixel[0] + 0.587 * pixel[1] + 0.114 * pixel[2])
    
    
# If argv is more than 1, then we've been given files and should run on those
if len(sys.argv) > 1:
    mismatch_choice = 0
    images = iter([ntpath.basename(x) for x in sys.argv[1:] if not x.startswith("diff_")])
    print(images)
    print("A--------------")
    print(sys.argv[1:])
else:
    # Ask how to take failures
    print("Run me in a folder of alphabetically listed PNGs, each a pair")
    print("of black-white background pictures. Order  does  not  matter.")
    print("-------------------------------------------------------------")
    print("What to do if there's a mismatch?")
    print("[0/Enter] Skip, [1] Exit, [2] Continue")
    mismatch_choice = raw_input("> ")
    if mismatch_choice == "":
        mismatch_choice = 0
    mismatch_choice = int(mismatch_choice)
    if mismatch_choice > 2:
        mismatch_choice = 2
    # Iterate thru the folder two images at a time.
    # Assume every two files are a matching light-dark pair.
    globs = glob.glob("[!diff_]*.png")
    images = iter(globs)
    print(images)
    print("B--------------")
    print(globs)
for x in images:
    print("")
    imgA = Image.open(x)
    y = images.next()
    imgB = Image.open(y)
    print("A: {}, B: {}".format(x, y))
    
    # Force the modes to match in case they're somehow wrong.
    imgA = imgA.convert("RGB")
    imgB = imgB.convert("RGB")
    
    #xor.save("diff_xor_{}.png".format(x.replace(".png","")))
    # Next we crush the palette of the first image down
    # and then shrink it for performance.
    checker = ( 
        imgA.copy()
        .convert('P', palette=Image.ADAPTIVE, colors=8)
        .convert("RGB")
        )
    checker = checker.resize([int(0.2 * s) for s in checker.size])
    
    # Sort the color palette by the largest amount
    # Then pull the color with the most pixels
    average_color = sorted(checker.getcolors(), key=itemgetter(0), reverse=True)[0][1]
    brightness = lum(average_color)
    # Next check to see whether imgA is light or dark.
    if brightness > 127.0:
        img_bright = imgA
        img_dark = imgB
        print(x +" is bright")
    else:
        img_bright = imgB
        img_dark = imgA
        print(x +" is dark")
    
    # Now make a difference mask.
    diff = ImageOps.invert(ImageChops.difference(img_dark, img_bright)).convert("L")    
    # Normalize the mask. Tho this doesn't seem to do jack shit in actuality.
    diff = ImageOps.autocontrast(diff, cutoff=2)
    # Do a very janky and basic check to try and notice mismatched images.
    # Compare the values of the highest-number pixels.
    # A proper, non-translucent image match will have mostly black and pure white
    # pixels, while an improper match will be mostly below 255.
    
    # Get the color palette of the diff now
    diff_colors = sorted(diff.getcolors(), key=itemgetter(0), reverse=True)
    print(diff_colors[0:4])
    # Calculate how many pixels there are.
    pixel_count = diff.size[0] * diff.size[1]
    # Presume we have more dark pixels. Doesn't matter.
    dark_pixels = diff_colors[0][1]
    light_pixels = diff_colors[1][1]
    pure_white = 0
    try:
        pure_white = [item for item in diff_colors if item[1] > 253][0][0]
    except:
        pass # 8)
    print("{:0.3f}% white pixels".format((float(pure_white) / float(pixel_count)) * 100.0))
    if  (254 >= dark_pixels >= 2) or (254 >= light_pixels >= 2):
        if mismatch_choice == 0:
            print("Mismatch, skipping pair")
            print("!="*39+"!")
            continue
        elif mismatch_choice == 1:
            print("Mismatch, aborting the rest")
            print("!="*39+"!")
            sys.exit()
        elif mismatch_choice == 2:
            print("Mismatch, continuing anyway")
            print("!="*39+"!")
    
    # Invert because we want black background and then apply the mask.
    img_final = img_dark.copy()    
    img_final.putalpha(diff)
    
    # > Do some crazy shit from stack overflow
    #   Create a new RGB image that will be our mask.    
    # > Split img_final into 4 channels, use the alpha channel as the paste mask 
    #   for the new RGB image.    
    # > Get the bounding box of the new image, then apply it to img_final
    imageComponents = img_final.split()
    rgbImage = Image.new("RGB", img_final.size, (0,0,0))
    rgbImage.paste(img_final, mask=img_final.split()[3])
    img_final = img_final.crop(rgbImage.getbbox())
    
    
    
    
    
    print("Final size: {}".format(img_final.size))
    
    img_final.save("diff_{}.png".format(x.replace(".png","")))
    
    print("="*80)
