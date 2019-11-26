import cv2

def highlightContours(masked_img):
    ret,thresh = cv2.threshold(masked_img,127,255,0)
    contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    return contours