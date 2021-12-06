#!/usr/bin/env python
from cv_bridge.core import CvBridgeError
from rosgraph.names import anonymous_name
import rospy
import cv2
import numpy as np
from sensor_msgs.msg import Image
from cv_bridge import CvBridge,CvBridgeError

lowerBound = np.array([30, 160, 160]) # Red # np.array([65, 30, 30])  # Green np.array([120-10, 30, 30]) # Blue
upperBound = np.array([330, 255, 255]) # Red # np.array([130, 100, 100])  # Green np.array([120+10, 255, 255]) # Blue
# HSV color boundary. you can change the value as you wish

list_location = []
history_locations = []
isDraw = True

def __init__():
    rospy.init_node("webcam_pub", anonymous=True)

def draw(img_color, locations):
    for i in range(len(locations) - 1):
        if locations[0] is None or locations[1] is None:
            continue
        cv2.line(img_color, tuple(locations[i]), tuple(locations[i + 1]), (0, 255, 255), 3)
    
    return img_color


def image_publish():
    image_color_pub = rospy.Publisher("image_color_pub", Image, queue_size=1)
    image_mask_pub = rospy.Publisher("image_mask_pub", Image, queue_size=1)
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    bridge = CvBridge()
    rospy.loginfo("Openning WebCam...")
    while not rospy.is_shutdown():
        # Capture frame-by-frame
        ret_cap, cv_image = cap.read()
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV) # RGB to HSV color change
        color_mask = cv2.inRange(hsv, lowerBound, upperBound) # image mask to detect the color in range

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        image_mask = cv2.morphologyEx(color_mask, cv2.MORPH_DILATE, kernel, iterations=3)
        nlabels, labels, stats, centroids = cv2.connectedComponentsWithStats(image_mask)

        max = -1
        max_index = -1

        ret_thr, thr =cv2.threshold(color_mask, 127, 255, 0) # binary encoding to find contour
        _, contours, _ = cv2.findContours(thr, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) # find contour, '_' is not used variable
        
        for j in range(nlabels):
            if j<1:
                continue

            area = stats[j, cv2.CC_STAT_AREA]

            if area > max:
                max = area
                max_index = j
        
        if max_index != -1:
            center_x = int(centroids[max_index, 0])
            center_y = int(centroids[max_index, 1])
            left = stats[max_index, cv2.CC_STAT_LEFT]
            top = stats[max_index, cv2.CC_STAT_TOP]
            width = stats[max_index, cv2.CC_STAT_WIDTH]
            height = stats[max_index, cv2.CC_STAT_HEIGHT]
        
            cv2.rectangle(cv_image, (left, top), (left+width, top+height), (0,0,255), 5)
            cv2.circle(cv_image, (center_x, center_y), 10, (0,255,0), -1)
            
            if isDraw:
                list_location.append((center_x, center_y))
            else:
                history_locations.append(list_location.copy())
                list_location.claer()
        cv_image = draw(cv_image, list_location)

        for locations in history_locations:
            cv_image = draw(cv_image, locations)

        # if (len(contours) > 0):
        #     for i in range(len(contours)):
        #         area = cv2.contourArea(contours[i]) # find the area of contour
        #         if area > 100: # for object which have the area more than 100
        #             rect = cv2.minAreaRect(contours[i]) # make rectangle using coutour
        #             box = cv2.boxPoints(rect) # find rectangle and return 4 points
        #             box = np.int0(box)
        #             cv_image_cont = cv2.drawContours(cv_image, contours=[box], contourIdx=0, color=(0, 0, 255), thickness=2) # draw the rectangle in image
        # # Display the resulting frame
        # # cv2.imshow('frame',cv_image)
        # # cv2.imshow('mask', image_mask)
        # # cv2.waitKey(3)
        # # image_color_pub.publish(bridge.cv2_to_imgmsg(color_mask))
        image_color_pub.publish(bridge.cv2_to_imgmsg(cv_image, 'bgr8'))
        image_mask_pub.publish(bridge.cv2_to_imgmsg(image_mask))

    # When everything is done, release the capture
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    __init__()
    try:
        image_publish()
    except rospy.ROSInterruptException:
        pass
