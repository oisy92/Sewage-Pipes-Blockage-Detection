![alt text1](https://github.com/oisy92/Sewage-Pipes-Blockage-Detection/blob/master/Image/Sample2.jpg?raw=true)

# Sewage Pipes Blockages Detection
Camera based software to autonomosusly detect blockages and defects in sewer pipes. This is a machine learning problem, but I thought it would be interesting to see if it can be solved using OpenCV and simple math. The software manages to detect 90% of blockages in sewage path. 

In addition to detection, the software produces a spreadsheet after each run to record the detected blockages and their related information such as size, width, height, and time of detection.

The software uses variety of OpenCV functions. To name a few, Canny Filter, Background Subtraction, and other manually implemented functions to deliver best performance.

 ## Video Demo (Click on image to be transferred to YouTube)
[![alt text2](https://github.com/oisy92/Sewage-Pipes-Blockage-Detection/blob/master/Image/Sample.jpg?raw=true)](https://www.youtube.com/watch?v=5QffxodpUqE&t=)

 ## Prerequisites
    1. Python3
    1. Sewer pipe insepction video such as https://www.youtube.com/watch?v=AlqL6R-W_E4
 
 ## Packages
    1.opencv-python==4.1.0.25
    2.matplotlib==3.1.2
    3.numpy==1.17.4,
    4.Pillow==6.2.1, 
    5.xlsxwriter==1.2.6,
 
 ## How To Run
    1. Run Main.py
