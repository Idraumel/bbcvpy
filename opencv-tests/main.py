import cv2 as cv
import sys
import numpy as np
from pprint import pprint
 
im = cv.imread(cv.samples.findFile("images/light-blue_clear_1.png"))

if im is None:
    sys.exit("Could not read the image.")

imgray = cv.cvtColor(im, cv.COLOR_BGR2GRAY)
imblack = np.zeros(imgray.shape)
ret, thresh = cv.threshold(imgray, 120, 255, cv.THRESH_BINARY)
contours, hierarchy = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
cv.drawContours(im, contours, -1, (0,255,0), 3)
# cv.imwrite('sample_contour.jpg', imblack)

# Constants
# yellow_base 

# for line in imblack:
#     for mat in line:

print(contours)
 
cv.imshow("Display window", thresh)
k = cv.waitKey(0)
 