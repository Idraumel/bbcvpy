from PIL import Image
from clock_manager import ClockManager
import shape_detection

#---------------CONSTANTS---------------#

INPUT_PATH = "../images/input"
OUTPUT_PATH = "../images/output"

# Notes : This method is too static, find a way to (semi-)automatically adapt to context
# red ball detection
RB_R_CHANNEL_MIN = 125
RB_G_CHANNEL_MAX = 75
RB_B_CHANNEL_MAX = 125

# yellow ball detection
YB_R_CHANNEL_MIN = 125
YB_G_CHANNEL_MIN = 125
YB_B_CHANNEL_MAX = 75

# black ball detection
BB_R_CHANNEL_MAX = 75
BB_G_CHANNEL_MAX = 75
BB_B_CHANNEL_MAX = 75

# white ball detection
WB_R_CHANNEL_MIN = 175
WB_G_CHANNEL_MIN = 175
WB_B_CHANNEL_MIN = 175

#---------------MAIN---------------#

clock_manager = ClockManager()

im = Image.open(f"{INPUT_PATH}/light-blue_clear_1.png")
im = im.convert("RGB")

# STEP 1 : create masks for balls of each color
red_ball_mask = Image.new("1", im.size, 0)
yellow_ball_mask = Image.new("1", im.size, 0)
black_ball_mask = Image.new("1", im.size, 0)
white_ball_mask = Image.new("1", im.size, 0)

# create mask for each type of ball
def create_color_masks():
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            coords = (x, y)
            pixel = im.getpixel(coords)
            
            if pixel[0] > RB_R_CHANNEL_MIN and pixel[1] < RB_G_CHANNEL_MAX and pixel[2] < RB_B_CHANNEL_MAX:
                red_ball_mask.putpixel(coords, 1)
            
            if pixel[0] > YB_R_CHANNEL_MIN and pixel[1] > YB_G_CHANNEL_MIN and pixel[2] < YB_B_CHANNEL_MAX:
                yellow_ball_mask.putpixel(coords, 1)

            if pixel[0] < BB_R_CHANNEL_MAX and pixel[1] < BB_G_CHANNEL_MAX and pixel[2] < BB_B_CHANNEL_MAX:
                black_ball_mask.putpixel(coords, 1)

            if pixel[0] > WB_R_CHANNEL_MIN and pixel[1] > WB_G_CHANNEL_MIN and pixel[2] > WB_B_CHANNEL_MIN:
                white_ball_mask.putpixel(coords, 1)

    red_ball_mask.save(f"{OUTPUT_PATH}/red_ball_mask.png")

    yellow_ball_mask.save(f"{OUTPUT_PATH}/yellow_ball_mask.png")

    black_ball_mask.save(f"{OUTPUT_PATH}/black_ball_mask.png")

    white_ball_mask.save(f"{OUTPUT_PATH}/white_ball_mask.png")

clock_manager.start_clock()
create_color_masks()
execution_time = clock_manager.stop_clock()
print(f"Execution time for color mask creation : {execution_time} sec")

# STEP 2 : Scan binary images for regions
# TODO : Execute for each ball color
clock_manager.start_clock()
regions = shape_detection.get_regions(red_ball_mask)
execution_time = clock_manager.stop_clock()
print(f"Execution time for red ball mask region scanning : {execution_time} sec")
print(f"\t number of found regions : {len(regions)}")
shape_detection.print_regions_metadata(regions)

# TODO : Build a class which represents output data of image processing - regions and all of their metadata

# DONE : retrieve all (white) regions in a given binary image
# TODO : for a given region, compute 
#   - 1. perimeter (length of convex hull of the set(region)),
#   - 2. area, (in pixels?)
#   - 3. diameter (greatest distance between 2 points of the shape's border),
#   - 4. elongation

# STEP 3 : Compute geometry properties for each region