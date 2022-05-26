from email.mime import base
from pickle import TRUE
import sys
import argparse
from PIL import Image
import timeit
# other scripts
import image2mcrl2
import pbessolve_image
import slcs2modalmuRGB

def check_extension(extension, file): 
    if not file.endswith(extension):
        raise argparse.ArgumentTypeError(f'incorrect extension, expected {extension}')
    return file

def check_image_extension(file):
    extension = file.rsplit('.', 1)[1]
    if extension not in ('png', 'jpg', 'jpeg'):
         raise argparse.ArgumentTypeError('wrong image format, allowed formats: png, jpg, jpeg') # TODO check this
    return file

if __name__ == '__main__':
    # handle argument parsing and save args to list
    parser = argparse.ArgumentParser()
    parser.add_argument("image", help = "the image to be converted to a mcrl2 specification, allowed formats: png, jpg, jpeg", type=check_image_extension) 
    parser.add_argument("slcsformula", help = "the spatial logic formula, in .slcs format", type=lambda f: check_extension('.slcs', f))
    parser.add_argument("--greyscale", help = "optimization for monochromatic images", action = "store_true")
    parser.add_argument("--markcolour", help = "set a custom mark colour with three integers representing its RGB value", nargs=3, type=int)
    args = parser.parse_args()
    
    imagefile = args.image
    slcsfile = args.slcsformula
    greyscale = args.greyscale

    mark_colour = (144,238,144)

    start_time = timeit.default_timer() # timing purposes

    mcrl2file = image2mcrl2.create_mcrl2_specification(imagefile, greyscale)
    mcffile = slcs2modalmuRGB.translate_SLCS_formula(slcsfile, greyscale, TRUE) # Additional argument TRUE to ensure the output is recognizable by mcrl2
    true_coords = pbessolve_image.do_pbessolve(mcrl2file, mcffile)

    print(f'Elapsed time: {timeit.default_timer() - start_time} seconds') # print time elapsed in seconds 

    # custom marking colour
    if args.markcolour is not None:
        mark_colour = (args.markcolour[0], args.markcolour[1], args.markcolour[2])        
    
    with Image.open(imagefile) as im:
        # mark pixels which satisfy the formula
        im = Image.open(imagefile)
        for coord in true_coords:
            im.putpixel(coord, mark_colour)

        # prepare output file name [PATH_IMG]_[FORMULA].png, save it as PNG, and close image
        base_imagefile = imagefile.rsplit('.', 1)[0] # only remove extention from image
        base_slcsfile = slcsfile.rsplit('.', 1)[0]
        if '\\' in base_slcsfile:
            base_slcsfile = base_slcsfile.rsplit('\\', 1)[1] # extract only name from slcs file
        marked_imagefile = f'{base_imagefile}_{base_slcsfile}.png'
        im.save(marked_imagefile, 'PNG') 
        im.close()

    print(f'\n*** successfully saved marked image to {marked_imagefile} ***')