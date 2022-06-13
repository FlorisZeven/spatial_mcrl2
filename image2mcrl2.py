'''
image2mcrl2
Converts an image to an mCRL2 specification

For input arguments, see also the help file invoked by setting the -h flag.
'''
import argparse
import io
from PIL import Image

GREYSCALE = False # default for optimization monochromatic images

# builds the RGB data structure as mCRL2 string, from image data
def build_image_grid(imagefile):
    output = io.StringIO() # create new string builder
    output.write('image = [\n   [') # write start of string

    im = Image.open(imagefile) # prepare the image
    width, height = im.size
    RGB_data = list(im.getdata()) # Extract RGB values as list of triples (R, G, B)
    im.close() # close the image
    
    size = width * height # total amount of pixels
    counter = 0 # holds current pixel index
    for pixel in RGB_data:
        # write RGB values of current pixel: 0 = red, 1 = green, 2 = blue
        # only one value for monochromatic images
        if GREYSCALE:
            output.write(f'{pixel[0]}')
        else:
            output.write(f'RGB({pixel[0]},{pixel[1]},{pixel[2]})')

        if counter == size - 1: # handle last pixel
            output.write(f']\n];')
        elif counter % width == width - 1: # handle new row
            output.write(f'], \n   [')
        else: # otherwise standard separator
            output.write(f', ')
        counter += 1

    result = output.getvalue() # retrieve string from memory buffer
    output.close() # discard the memory buffer
    return result

# builds the .mcrl2 file
def build_mCRL2_spec(imagefile):
    result = '' 
    result += f'''sort
	Grid = List(List(Pixel));\n'''
    if GREYSCALE: # different structure for monochromatic images
        result += f'''\tPixel = Int;\n'''
    else:
        result += f'''\tPixel = struct RGB(
		    red:Intensity,
		    green:Intensity,
		    blue:Intensity
	    ); 
	    \tIntensity = Int;\n'''
    
    result += f'''\nmap
	image: Grid;
	start_x, start_y: Nat;
	size_x,	size_y: Nat;
    
eqn '''
    result += build_image_grid(imagefile)
    result += f'''
    start_x = 0;
    start_y = 0;
    size_x = Int2Nat(#(image.0) - 1);
    size_y = Int2Nat(#(image) - 1);
act
    R;
    report: Pixel;
proc
Grid(x:Nat, y: Nat) = 
    report(image.y.x) . Grid(x,y) 
    + R . Grid(x,y) 
    + (x != 0) 		-> R . Grid(Int2Nat(x-1), y)
    + (x != size_x)	-> R . Grid(Int2Nat(x+1), y)
    + (y != 0) 		-> R . Grid(x, Int2Nat(y-1))
    + (y != size_y) -> R . Grid(x, Int2Nat(y+1))
;
init
    allow ({{R, report}},
    comm(
        {{}}, Grid(start_x, start_y)
    )
);''' # double braces to escape { } characters in f-string
    return result

def write_to_mcrl2(mcrl2spec, basefile):
    mcrl2specfile = basefile + '.mcrl2'
    with open(mcrl2specfile, "w") as file:
        file.write(mcrl2spec)
    return mcrl2specfile

def create_mcrl2_specification(imagefile, greyscale):
    if greyscale:
        global GREYSCALE
        GREYSCALE = True
    mcrl2spec = build_mCRL2_spec(imagefile) # create string containing spec
    basefile = imagefile.rsplit('.', 1)[0] # remove extension by splitting only first dot from right side
    mcrl2specfile = write_to_mcrl2(mcrl2spec, basefile) # write to file

    print(f'[image2mcrl2]    successfully saved mcrl2 specification of {imagefile} to {mcrl2specfile}')
    
    return mcrl2specfile

def check_image_extension(imagefile):
    extension = imagefile.rsplit('.', 1)[1]
    if extension not in ('png', 'jpg', 'jpeg'):
         raise argparse.ArgumentTypeError('wrong image format, known allowed formats: png, jpg, jpeg')
    return imagefile

# If file is called directly, check arguments
if __name__ == '__main__':
    # handle argument parsing and save args to list
    parser = argparse.ArgumentParser()
    parser.add_argument("image", help = "the image to be converted to a mcrl2 specification, allowed formats: png, jpg, jpeg", type=check_image_extension)
    parser.add_argument("--greyscale", help = "optimization for monochromatic images", action = "store_true")
    args = parser.parse_args()

    mcrl2specfile = create_mcrl2_specification(args.image, args.greyscale)
