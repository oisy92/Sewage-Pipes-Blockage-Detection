import numpy as np
import cv2
from PIL import Image
import math
import time

import matplotlib.pyplot as plt
import xlsxwriter
import os
import datetime
from pathlib import Path


    #####                       ##### 
    #####                       ##### 
    #####                       ##### 
    #####  Variable Defintions  #####
    #####                       ##### 
    #####                       ##### 
    #####                       ##### 

#Define Directory and populate list with video names
os.chdir("C:/Users/oisy9/Documents/Videos/")
list = os.listdir()
#Main loop
for file in list:
    #User adjustable
    start_frame_number = 4000
    #String modifications to get rid of extension dot
    videoname = str(file)
    videoname = "2014 Mildura Clean and View CCTV SMN53821.MPG"
    dirname = videoname.replace(".","")
    videodirname = str(os.getcwd()+ "\\" + str(dirname))
    try:
        os.mkdir(dirname)
    except:
        print("Folder Already Exists")
    cap = cv2.VideoCapture(videoname)
    height= 0
    cvimg= 0
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame_number)
    backgroundSub = cv2.createBackgroundSubtractorMOG2()
    miniInlierDist = 2
    applyDetection = True
    firstRun = True
    #Create new excel file and define its headers
    workbook = xlsxwriter.Workbook(str(videoname)+'.xlsx')
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
    max_noise_percentage = 50


    #####                       ##### 
    #####                       ##### 
    #####                       ##### 
    #####  Function Defintions  #####
    #####                       ##### 
    #####                       ##### 
    #####                       ##### 


    def create_circular_mask(w, h, center=None, radius=None):

        if center is None: # use the middle of the image
            center = [int(w/2), int(h/2)]
        if radius is None: # use the smallest distance between the center and image walls
            radius = min(center[0], center[1], w-center[0], h-center[1])

        Y, X = np.ogrid[:h, :w]
        dist_from_center = np.sqrt((X - center[0])**2 + (Y-center[1])**2)

        mask = dist_from_center <= radius
        return mask

    def normRGB(frame):
        def normalizeRed(intensity):
            iI      = intensity
            minI    = 86
            maxI    = 230
            minO    = 0
            maxO    = 255
            iO      = (iI-minI)*(((maxO-minO)/(maxI-minI))+minO)

            return iO

        # Method to process the green band of the image
        def normalizeGreen(intensity):
            iI      = intensity
            minI    = 90
            maxI    = 225
            minO    = 0
            maxO    = 255
            iO      = (iI-minI)*(((maxO-minO)/(maxI-minI))+minO)

            return iO

        # Method to process the blue band of the image
        def normalizeBlue(intensity):
            iI      = intensity
            minI    = 100
            maxI    = 210
            minO    = 0
            maxO    = 255
            iO      = (iI-minI)*(((maxO-minO)/(maxI-minI))+minO)

            return iO

        # Create an image object
        imageObject     = Image.fromarray(frame[..., ::-1])

        # Split the red, green and blue bands from the Image
        multiBands      = imageObject.split()

        # Apply point operations that does contrast stretching on each color band
        normalizedRedBand      = multiBands[0].point(normalizeRed)
        normalizedGreenBand    = multiBands[1].point(normalizeGreen)
        normalizedBlueBand     = multiBands[2].point(normalizeBlue)
        
        # Create a new image from the contrast stretched red, green and blue brands
        normalizedImage = Image.merge("RGB", (normalizedRedBand, normalizedGreenBand, normalizedBlueBand))

        cvimg = np.array(normalizedImage)[..., ::-1]

        return cvimg

    def secs_to_HMS(secs):
        if secs < 3600:
            return (datetime.timedelta(seconds = secs))


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


    def highlightContours(masked_img):
        ret,thresh = cv2.threshold(masked_img,127,255,0)
        contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        return contours


    #Blockage detection loop
    while(1):
        #Read original frame.
        ret, frame = cap.read()
        if not ret:
            workbook.close()
            break
   
        #Nathan's function - Normalize the frame (Reduce the noise).
        cvimg = normRGB(frame)

        #Applying background subtraction.
        bsFrame = backgroundSub.apply(cvimg)

        grayimg = cv2.cvtColor(cvimg, cv2.COLOR_BGR2GRAY)


        canny = cv2.Canny(grayimg, 200,20)
        ret, thresh1 = cv2.threshold(canny,0,255,cv2.THRESH_BINARY)
        dat = cv2.distanceTransform(thresh1, cv2.DIST_L2 ,3);

        #Creating circle mask to the middle of the frame to block all noise.
        size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        radius = size[1]//4
        center = [int(size[0]/2), int(size[1]/2)]
        mask= create_circular_mask(size[0], size[1], center = center, radius = radius)
        mask_area = np.pi*radius**2
        masked_img = bsFrame.copy()
        masked_img[~mask] = 0
    
        seconds = int(cap.get(cv2.CAP_PROP_POS_FRAMES)/cap.get(cv2.CAP_PROP_FPS));
        videotime = secs_to_HMS(seconds)
        circles = cv2.HoughCircles(masked_img,cv2.HOUGH_GRADIENT,1,20, param1=200,param2=20,minRadius= int(radius/2), maxRadius=int(radius))
        #print(type(masked_img))
        if circles is not None and applyDetection:
            #print(circles)
            #print(type(circles))
            circles = np.uint16(np.around(circles))
            for i in circles[0,:]:
                # draw the outer circle
                cv2.circle(masked_img,(i[0],i[1]),i[2],(0,0,0),20)
                # draw the center of the circle
                arc_denoised_img = detectArcs(dat, masked_img, miniInlierDist, circles)
                contouredImage = highlightContours(arc_denoised_img)
                # cv2.drawContours(frame, contouredImage, -1, (0,255,255), 3)

        elif circles is None and applyDetection:
            contouredImage = highlightContours(masked_img)


            for contour in contouredImage:
                
                [x,y,w,h] = cv2.boundingRect(contour)

                new_blockage_area = w*h
                new_blockage_y = y
                new_blockage_x = x
                new_blockage_h = h
                new_blockage_w = w
                if firstRun:
                    nominated_blockage_area = new_blockage_area
                    nominated_blockage_y = new_blockage_y
                    nominated_blockage_x = new_blockage_x
                    nominated_blockage_h = new_blockage_h
                    nominated_blockage_w = new_blockage_w
                    print("here")
                    firstRun = False

                if new_blockage_area > mask_area or new_blockage_area < 200:
                    continue
                if new_blockage_area > nominated_blockage_area:
                    nominated_blockage_y = new_blockage_y
                    nominated_blockage_x = new_blockage_x
                    nominated_blockage_h = new_blockage_h
                    nominated_blockage_w = new_blockage_w
                    nominated_blockage_area = new_blockage_area
                    nominated_blockage_area_to_mask_area = (nominated_blockage_area / mask_area)*100
                    cv2.rectangle(frame,(nominated_blockage_x,nominated_blockage_y),(nominated_blockage_x+new_blockage_w,nominated_blockage_y+new_blockage_h),(255,0,255),2)
                    cv2.imwrite(str(videodirname+"\\"+"Frame_"+str(blockageCounter-1)+"_"+str(videotime).replace(":","")+".jpg"),frame)
                    continue
                if  recordTime != seconds and applyDetection:
                    worksheet.write('A'+str(blockageCounter), str(blockageCounter-1)) 
                    worksheet.write('B'+str(blockageCounter), str(cap.get(cv2.CAP_PROP_POS_FRAMES))) 
                    worksheet.write('C'+str(blockageCounter), str(videotime).replace(":","")) 
                    worksheet.write('D'+str(blockageCounter), str(nominated_blockage_area))
                    worksheet.write('E'+str(blockageCounter), str("%.2f" % nominated_blockage_area_to_mask_area))
                    worksheet.write('F'+str(blockageCounter), str(nominated_blockage_w))
                    worksheet.write('G'+str(blockageCounter), str(nominated_blockage_h))
                    worksheet.write('H'+str(blockageCounter), str(nominated_blockage_x))
                    worksheet.write('I'+str(blockageCounter), str(nominated_blockage_y))
                    blockageCounter = blockageCounter + 1
                    recordTime = seconds
                    nominated_blockage_area = 0
                    nominated_blockage_y = 0
                    nominated_blockage_x = 0
                    nominated_blockage_h = 0
                    nominated_blockage_w = 0


        n_white_pix = (np.sum(bsFrame == 255))
        n_black_pix = (np.sum(bsFrame == 0))
        noisePercentage = (n_white_pix/n_black_pix)*100
        font = cv2.FONT_HERSHEY_SIMPLEX

        if noisePercentage < max_noise_percentage:
            applyDetection = True
            cv2.putText(frame,'Noise: '+str(("%.2f" % noisePercentage))+'%',(0,size[1]-10), font, 0.5, (0,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame,'Detection: ',(int(size[1]/2-60),size[1]-10), font, 0.5, (0,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame,'ON',(int(size[1]/2+30),size[1]-10), font, 0.5, (0,255,0), 2, cv2.LINE_AA)
            cv2.putText(frame,'Video Time: '+str((videotime)),(int(size[1]/2+270),size[1]-10), font, 0.5, (0,255,255), 2, cv2.LINE_AA)

        else:
            applyDetection = False
            cv2.putText(frame,'Noise: '+str(("%.2f" % noisePercentage)),(0,size[1]-10), font, 0.5, (0,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame,'Detection: ',(int(size[1]/2-60),size[1]-10), font, 0.5, (0,255,255), 2, cv2.LINE_AA)
            cv2.putText(frame,'OFF',(int(size[1]/2+30),size[1]-10), font, 0.5, (0,0,255), 2, cv2.LINE_AA)
            cv2.putText(frame,'Video Time: '+str((videotime)),(int(size[1]/2+270),size[1]-10), font, 0.5, (0,255,255), 2, cv2.LINE_AA)



        # Start time
        ## Time elapsed
        #print ("Time taken : {0} seconds "+format(seconds))



        #Show original frame
        cv2.imshow('Original Frame',frame)

        
        ###Show normalzed frame
        ##cv22.mshow('Normalized Frame',cv22img)

        ##Show background subtraction image
        #cv2.imshow('Background Subtraction',bsFrame)

        ###Show masked image.
        cv2.imshow('Processed Frame',masked_img)

        ###Show circles in the image.
        ##cv22.imshow('Imag with circles detected',circles)

        ##Show masked image.
        cv2.imshow('Canny Frame',canny)

        #cv2.imshow('jgykg', ocr_frame[ocr_frame.shape[0]-100:, ocr_frame.shape[0]-100:])
        ##Show masked image.
        #cv2.imshow('Distance Transform Frame',dat)
        k = cv2.waitKey(30) & 0xff
        if k == 27 or ret:
            workbook.close() 
            break
    cap.release()
    cv2.destroyAllWindows()      
    workbook.close() 