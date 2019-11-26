import numpy as np
import cv2
import math
import time
import matplotlib.pyplot as plt
import xlsxwriter
import os
import datetime
from pathlib import Path
from PIL import Image
from nomralizeRGB import *
from circularMask import *
from timeConvert import *
from arcDetect import *
from contorsHighlight import *





#User adjustable variables
videoName = input("Please enter the full video title you wish to inspect:\n")
frameStart = int(input("Please enter the start frame number:\n"))
circularMaskRadius = int(input("The circular mask maskRadius is calculated using frame_width/integer. The smaller the integer, the bigger the mask, and vice versa. Please enter the integer:"))

#String modifications to get rid of extension dot
dirname = videoName.replace(".","")
videodirname = str(os.getcwd()+ "\\" + str(dirname))

#Try make a folder to save screenshots of blockages.
try:
    os.mkdir(dirname)
except:
    print("Folder Already Exists")

#Feed in the video frames
cap = cv2.VideoCapture(videoName)
cap.set(cv2.CAP_PROP_POS_FRAMES, frameStart)

#Initialize background subtraction mask
backgroundSub = cv2.createBackgroundSubtractorMOG2()

#By default, detection function is applied and this is the first run of the software
applyDetection = True

firstRun = True

#Create new excel file and define its headers
workbook = xlsxwriter.Workbook(str(videoName)+'.xlsx')
worksheet = workbook.add_worksheet()
worksheet.write('A1', 'Object ID') 
worksheet.write('B1', 'Object Frame') 
worksheet.write('C1', 'Object Detection Time')
worksheet.write('D1', 'Object Area')
worksheet.write('E1', 'Area Percentage Blocked by The Object')
worksheet.write('F1', 'Object Width')
worksheet.write('G1', 'Object Height')
worksheet.write('H1', 'Object Y location')
worksheet.write('I1', 'Object Y location')
blockageCounter = 2
recordTime = 0
maxNoisePercentage = 50

while(1):

    #Read original frame.
    ret, frame = cap.read()

    if not ret:
        workbook.close()
        break

    #Normalize the frame (Reduce the noise).
    normalizedImage = normRGB(frame)

    #Applying background subtraction.
    bsImage = backgroundSub.apply(normalizedImage)

    #Convert to grayscale.
    grayImage = cv2.cvtColor(normalizedImage, cv2.COLOR_BGR2GRAY)

    #Apply edge detection filter to the image.
    cannyImage = cv2.Canny(grayImage, 200,20)

    #Thresholding the edges.
    ret, thresholdImage = cv2.threshold(cannyImage,0,255,cv2.THRESH_BINARY)

    #Apply distance transform to the thresholded image
    dat = cv2.distanceTransform(thresholdImage, cv2.DIST_L2 ,3)

    #Creating circle mask to the middle of the frame to block all noise.
    size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    
    #Positioning and sizing the circulare mask
    maskRadius = size[1]//circularMaskRadius
    maskCenter = [int(size[0]/2), int(size[1]/2)]

    #Applying circular mask to frame
    mask = create_circular_mask(size[0], size[1], maskCenter, maskRadius)
    mask_area = np.pi*maskRadius**2
    maskedImage = bsImage.copy()
    maskedImage[~mask] = 0

    #Convert video frames to seconds
    seconds = int(cap.get(cv2.CAP_PROP_POS_FRAMES)/cap.get(cv2.CAP_PROP_FPS))
    videoTime = secs_to_HMS(seconds)

    #Detect circles in images to block them from using black mask. This is because sewage pipes usually are connected by rings, which are not defects.
    circles = cv2.HoughCircles(maskedImage,cv2.HOUGH_GRADIENT,1,20, param1=200,param2=20,minRadius= int(maskRadius/2), maxRadius=int(maskRadius))

    #If detection is circle and apply detection is ON, block it by a circle mask.
    if circles is not None and applyDetection:
        circles = np.uint16(np.around(circles))
        for i in circles[0,:]:
            #Draw the outer circle
            cv2.circle(maskedImage,(i[0],i[1]),i[2],(0,0,0),20)
            #Draw the maskCenter of the circle
            arcDenoisedImage = detectArcs(dat, maskedImage, 2, circles)
            contouredImage = highlightContours(arcDenoisedImage)

    #If detection is not a circle and apply detection is ON, measure the detection size
    elif circles is None and applyDetection:
        contouredImage = highlightContours(maskedImage)
        for contour in contouredImage:
            #Get the contours measurements
            [x,y,w,h] = cv2.boundingRect(contour)
            new_blockage_area = w*h
            new_blockage_y = y
            new_blockage_x = x
            new_blockage_h = h
            new_blockage_w = w
            if firstRun:
                nominated_blockage_area = new_blockage_area
                nominatedBlockageY = new_blockage_y
                nominatedBlockageX = new_blockage_x
                nominatedBlockageH = new_blockage_h
                nominatedBlockageW = new_blockage_w
                firstRun = False

            if new_blockage_area > mask_area or new_blockage_area < 200:
                continue
            if new_blockage_area > nominated_blockage_area:
                nominatedBlockageY = new_blockage_y
                nominatedBlockageX = new_blockage_x
                nominatedBlockageH = new_blockage_h
                nominatedBlockageW = new_blockage_w
                nominated_blockage_area = new_blockage_area
                nominated_blockage_area_to_mask_area = (nominated_blockage_area / mask_area)*100
                cv2.rectangle(frame,(nominatedBlockageX,nominatedBlockageY),(nominatedBlockageX+new_blockage_w,nominatedBlockageY+new_blockage_h),(255,0,255),2)
                cv2.imwrite(str(videodirname+"\\"+"Frame_"+str(blockageCounter-1)+"_"+str(videoTime).replace(":","")+".jpg"),frame)
                continue

            if  recordTime != seconds and applyDetection:
                worksheet.write('A'+str(blockageCounter), str(blockageCounter-1)) 
                worksheet.write('B'+str(blockageCounter), str(cap.get(cv2.CAP_PROP_POS_FRAMES))) 
                worksheet.write('C'+str(blockageCounter), str(videoTime).replace(":","")) 
                worksheet.write('D'+str(blockageCounter), str(nominated_blockage_area))
                worksheet.write('E'+str(blockageCounter), str("%.2f" % nominated_blockage_area_to_mask_area))
                worksheet.write('F'+str(blockageCounter), str(nominatedBlockageW))
                worksheet.write('G'+str(blockageCounter), str(nominatedBlockageH))
                worksheet.write('H'+str(blockageCounter), str(nominatedBlockageX))
                worksheet.write('I'+str(blockageCounter), str(nominatedBlockageY))
                blockageCounter = blockageCounter + 1
                recordTime = seconds
                nominated_blockage_area = 0
                nominatedBlockageY = 0
                nominatedBlockageX = 0
                nominatedBlockageH = 0
                nominatedBlockageW = 0


    numWhitePixels = (np.sum(bsImage == 255))
    numBlackPixels = (np.sum(bsImage == 0))
    noisePercentage = (numWhitePixels/numBlackPixels)*100
    font = cv2.FONT_HERSHEY_SIMPLEX

    if noisePercentage < maxNoisePercentage:
        applyDetection = True
        cv2.putText(frame,'Noise: '+str(("%.2f" % noisePercentage))+'%',(0,size[1]-10), font, 0.5, (0,255,255), 2, cv2.LINE_AA)
        cv2.putText(frame,'Detection: ',(int(size[1]/2-60),size[1]-10), font, 0.5, (0,255,255), 2, cv2.LINE_AA)
        cv2.putText(frame,'ON',(int(size[1]/2+30),size[1]-10), font, 0.5, (0,255,0), 2, cv2.LINE_AA)
        cv2.putText(frame,'Video Time: '+str((videoTime)),(int(size[1]/2+270),size[1]-10), font, 0.5, (0,255,255), 2, cv2.LINE_AA)

    else:
        applyDetection = False
        cv2.putText(frame,'Noise: '+str(("%.2f" % noisePercentage)),(0,size[1]-10), font, 0.5, (0,255,255), 2, cv2.LINE_AA)
        cv2.putText(frame,'Detection: ',(int(size[1]/2-60),size[1]-10), font, 0.5, (0,255,255), 2, cv2.LINE_AA)
        cv2.putText(frame,'OFF',(int(size[1]/2+30),size[1]-10), font, 0.5, (0,0,255), 2, cv2.LINE_AA)
        cv2.putText(frame,'Video Time: '+str((videoTime)),(int(size[1]/2+270),size[1]-10), font, 0.5, (0,255,255), 2, cv2.LINE_AA)


    ###Show processed images.
    cv2.imshow('Processed Frame',frame)


    k = cv2.waitKey(30) & 0xff
    if k == 27 or ret:
        workbook.close() 
        break
cap.release()
cv2.destroyAllWindows()      
workbook.close() 