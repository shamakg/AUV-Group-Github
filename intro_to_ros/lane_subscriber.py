#!/usr/bin/env python

#ros2 launch /home/kenayosh/auvc_ws/src/AUV-Group-Github/launch/_.yaml

# import necessary libraries
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from std_msgs.msg import Int16
import numpy as np
import cv2
import matplotlib.pyplot as plt

# create image subscriber class
class ImageSubscriber(Node):
    def __init__(self):
        super().__init__("image_subscriber")

        # initialize interface between ROS and OpenCV
        self.cvb = CvBridge()

        # subscribe to receive camera frames
        self.subscription = self.create_subscription(
            Image, "bluerov2/camera", self.image_callback, 10
        )

        # subscribe to heading topic to get current heading
        self.heading_subscriber = self.create_subscription(
            Int16,
            'bluerov2/heading',
            self.heading_callback,
            10
        )

        # subscribe to desired_heading topic which will be based on AUV's angle to april tag(s)
        self.desired_heading_publisher = self.create_publisher(
            Int16,
            'bluerov2/desired_heading',
            10
        )
        self.heading = 0
    def heading_callback(self, msg):
        """This method logs and stores int16 heading from subscriber"""
        self.heading = msg.data


    def detect_lines(self,img, threshold1=100, threshold2=200, apertureSize=5, minLineLength= 400, maxLineGap= 50):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, threshold1, threshold2, apertureSize=apertureSize)
        plt.imshow(edges)
        lines = cv2.HoughLinesP(
                    edges,
                    10,
                    np.pi/180,
                    100,
                    minLineLength=minLineLength,
                    maxLineGap=maxLineGap,
            ) # detect lines
        return lines
    def line_reduct_v2(self,lines):
        """
        This method sorts the slopes and deletes all duplicate lines detected by the Probabilistic Hough Transform
        """
        margin = 0.05
        slopes = self.get_slopes_intercepts(lines)[0]
        line_dict = dict()
        for i in range(len(lines)):
            line_dict.update({slopes[i]:lines[i]})

        myKeys = list(line_dict.keys())
        myKeys.sort()
        sorted_dict = {i: line_dict[i] for i in myKeys}

        last_slope = -1000
        final_lines = []
        for key in myKeys:
            if(abs(key-last_slope) > margin and abs(key) > 0.3):
                final_lines.append(sorted_dict[key])
            last_slope = key
        return final_lines
        
    def draw_lines(self, img, lines, color=(0, 255, 0)):
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(img, (x1, y1), (x2, y2), color, 2)
        return img

    def get_slopes_intercepts(self,lines):
        slopes = []
        intercepts = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 != 0:  # Avoid division by zero
                slope = (y2 - y1) / (x2 - x1)
                intercept = y1 - slope * x1
            else:
                slope = None  # Vertical line case
                intercept = None
            slopes.append(slope)
            intercepts.append(intercept)
        return slopes, intercepts

    def detect_lanes(self, lines, slope_threshold=0.3, intercept_threshold=1):
        slopes, intercepts = self.get_slopes_intercepts(lines)
        lanes = []
        used_lines = set()  # Keep track of lines that have been assigned to a lane

        for i in range(len(lines)):
            if i in used_lines:
                continue  # Skip lines that have already been assigned to a lane

            best_pair = None
            best_intercept_diff = float('inf')

            for j in range(i + 1, len(lines)):
                if j in used_lines:
                    continue  # Skip lines that have already been assigned to a lane

                if slopes[i] is not None and slopes[j] is not None:
                    slope_diff = abs(slopes[i] - slopes[j])
                    intercept_diff = abs(intercepts[i] - intercepts[j])

                    if slope_diff < slope_threshold and intercept_diff > intercept_threshold:
                        if intercept_diff < best_intercept_diff:
                            best_intercept_diff = intercept_diff
                            best_pair = j

            if best_pair is not None:
                lanes.append([lines[i], lines[best_pair]])
                used_lines.add(i)
                used_lines.add(best_pair)

        return lanes

    def draw_lanes(self, img, lanes):
        colors = [[0, 255, 0],[255,0,0], [0,0,255], [255,255,255], [0,0,0]]
        for i, lane in enumerate(lanes):
            color = colors[i%5]
            for line in lane:
                x1, y1, x2, y2 = line[0]
                cv2.line(img, (x1, y1), (x2, y2), color, 2)
        return img



    def get_lane_center(self, lanes, img_width, img_height):
        if not lanes:
            return None, None
        
        # Initialize the closest lane variables
        closest_distance = float('inf')
        closest_intercept = None
        closest_slope = None

        # Image center
        img_center_x = img_width // 2

        # Compute center of each lane and find the closest
        for lane in lanes:
            for line in lane:
                slopes, intercepts = self.get_slopes_intercepts([line])
                bottom_intercepts = (img_height - intercepts[0]) / slopes
                distance = abs(img_center_x - bottom_intercepts)
                
                if distance < closest_distance:
                    closest_distance = distance
                    closest_slope = slopes[0]
                    closest_intercept =bottom_intercepts

        return  closest_slope, closest_intercept

    def recommend_direction(self, center_intercept, slope, img_width):
        FOV_HOR = 80
        if center_intercept is None or slope is None:
            return "unknown"
        if center_intercept is not None:
            x = center_intercept
            return FOV_HOR*(x-img_width/2)/img_width
    def draw_lines(self, img, lines, color=(0, 255, 0)):
        for line in lines:
            x1, y1, x2, y2 = line
            cv2.line(img, (x1, y1), (x2, y2), color, 2)
        return img 
        

    def image_callback(self, msg: Image):
        """
        Callback function for the image subscriber.
        It receives an image message and saves it.

        Args:
            msg (Image): The image message
        """
        # Convert Image message to OpenCV image
        image = self.cvb.imgmsg_to_cv2(msg)
        
        imgwidth = np.shape(image)[1]
        imgheight = np.shape(image)[0]
        lines = self.detect_lines(image)
        image = self.draw_lines(image, lines)
        lines = self.line_reduct_v2(lines)
        #plt.imsave("/home/kenayosh/auvc_ws/src/AUV-Group-Github/intro_to_ros/Camera_feed.png", image)
        lanes = self.detect_lanes(lines)
        self.get_logger().info(str(len(lanes)))
        closeintercept, closeslope = self.get_lane_center(lanes, imgwidth, imgheight)
        correction = self.recommend_direction(closeintercept, closeslope, imgwidth)
        self.get_logger().info(correction)
        #self.desired_heading_publisher.publish(correction + self.heading)
        
        
        # Save the image
        cv2.imwrite("image.png", image)


def main(args=None):
    rclpy.init(args=args)
    image_subscriber = ImageSubscriber()

    try:
        rclpy.spin(image_subscriber)
    except KeyboardInterrupt:
        pass
    finally:
        image_subscriber.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()





"""
def draw_lines(img, lines, color=(0, 255, 0)):
    for line in lines:
        x1, y1, x2, y2 = line
        cv2.line(img, (x1, y1), (x2, y2), color, 2)
    return img
"""