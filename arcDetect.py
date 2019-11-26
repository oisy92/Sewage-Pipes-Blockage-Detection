import numpy as np
import cv2
import math
import time

def detectArcs(frame, masked_img, miniInlierDist, circles):
    inlier = 0
    for x in circles:
        circleRadius = x[0][2]
        maxInlierDist = circleRadius/25.0
    if maxInlierDist < miniInlierDist:
        maxInlierDist = miniInlierDist
    for i in range(0, 2*int(3.14159265359), int(1)):
        cX = circleRadius*math.cos(i) + x[0][0]
        cY = circleRadius*math.sin(i) + x[0][1]
        cXindex = np.where(frame == cX)
        cYindex = np.where(frame == cY)

        return masked_img