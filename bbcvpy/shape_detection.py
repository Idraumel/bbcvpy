from PIL import Image

# scan all distinct regions in a binary image
def get_regions(im):
    regions = []

    for y in range(im.size[1]):
        for x in range(im.size[0]):
            coords = (x, y)
            pixel = im.getpixel(coords)
            
            if pixel == 1:
                # check if the pixel is in a known region
                pixel_is_known = get_pixel_is_known(regions, coords)
                if pixel_is_known: continue;

                # scan region
                new_region = scan_region(im, coords)
                regions.append(new_region)

    return regions

# get if a pixel is in a scanned region
def get_pixel_is_known(regions, coords):
    for region in regions:
        for region_pixel_coords in region:
            if region_pixel_coords == coords:
                return True
    return False

def scan_region(im, start_coords):
    region = []
    unscanned_coords = [start_coords]

    # while there are unscanned coordinates, explore their neighbors and add them to unscanned list if valid
    while len(unscanned_coords) > 0:
        # pop first unscanned coords in line
        current_coords = unscanned_coords.pop(0)
        neighbors_coords = get_neighbor_coords(current_coords)

        for neighbor_coords in neighbors_coords:
            # make sure neighbor coords are not out of bounds
            if neighbor_coords[0] < 0 and neighbor_coords[0] > im.size[0] - 1 and neighbor_coords[1] < 0 and neighbor_coords[1] > im.size[1] - 1:
                continue

            pixel = im.getpixel(neighbor_coords)
            
            # if pixel value is 1 and was not already scanned then add to unscanned list
            if pixel == 1 and region.count(neighbor_coords) == 0 and unscanned_coords.count(neighbor_coords) == 0:
                unscanned_coords.append(neighbor_coords)

        # add coords to region
        region.append(current_coords)

    return region

# get edge neighbors of a pixel
def get_neighbor_coords(coords):
    return [
        (coords[0] - 1, coords[1]),
        (coords[0], coords[1] - 1),
        (coords[0] + 1, coords[1]),
        (coords[0], coords[1] + 1)
    ]

def print_regions_metadata(regions):
    i = 0
    print("Regions : ")
    for region in regions:
        print(f"\tRegion {i} - Area in pixels : {len(region)}")
        i += 1