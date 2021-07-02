# ---------------------------------------------------------------------------
# Copyright 2017-2018  OMRON Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ---------------------------------------------------------------------------

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import math
import mycroft.client.enclosure.tama.hvc.p2def as p2def
from mycroft.client.enclosure.tama.hvc.serial_connector import SerialConnector
from mycroft.client.enclosure.tama.hvc.hvc_p2_api import HVCP2Api
from mycroft.client.enclosure.tama.hvc.hvc_tracking_result import HVCTrackingResult
from mycroft.client.enclosure.tama.hvc.grayscale_image import GrayscaleImage
from mycroft.util.log import LOG


###############################################################################
#  User Config. Please edit here if you need.                                 #
###############################################################################
# Output image file name.
img_fname = 'img.jpg'

# Read timeout value in seconds for serial communication.
# If you use UART slow baudrate, please edit here.
timeout = 30

#-------------------------
# B5T-007001 settings
#-------------------------
# Execute functions
exec_func = p2def.EX_FACE\
          | p2def.EX_DIRECTION\
          | p2def.EX_GAZE\
          | p2def.EX_BLINK\

#exec_func = p2def.EX_NONE  # Please use this to get just the image.

# Output image type
output_img_type = p2def.OUT_IMG_TYPE_NONE
                      # OUT_IMG_TYPE_QQVGA
                      # OUT_IMG_TYPE_QVGA

# HVC camera angle setting
hvc_camera_angle = p2def.HVC_CAM_ANGLE_0
                       # HVC_CAM_ANGLE_90
                       # HVC_CAM_ANGLE_180
                       # HVC_CAM_ANGLE_270

# Threshold value settings
body_thresh = 500         # Threshold for Human body detection [1 to 1000]
hand_thresh = 500         # Threshold for Hand detection       [1 to 1000]
face_thresh = 500         # Threshold for Face detection       [1 to 1000]
recognition_thresh = 500  # Threshold for Recognition          [0 to 1000]

# Detection size setings
min_body_size = 30      # Mininum human body detection size [20 to 8192]
max_body_size = 8192    # Maximum human body detection size [20 to 8192]
min_hand_size = 40      # Mininum hand detection size       [20 to 8192]
max_hand_size = 8192    # Maximum hand detection size       [20 to 8192]
min_face_size = 64      # Mininum face detection size       [20 to 8192]
max_face_size = 8192    # Maximum face detection size       [20 to 8192]

# Detection face angle settings
face_angle_yaw  = p2def.HVC_FACE_ANGLE_YAW_30
                      # HVC_FACE_ANGLE_YAW_60
                      # HVC_FACE_ANGLE_YAW_90
face_angle_roll = p2def.HVC_FACE_ANGLE_ROLL_45
                      # HVC_FACE_ANGLE_ROLL_15

#-------------------------
# STB library settings
#-------------------------
# Tracking parameters
max_retry_count = 2         # Maximum tracking retry count            [0 to 30]
steadiness_param_pos = 30   # Rectangle position steadiness parameter [0 to 100]
steadiness_param_size = 30  # Rectangle size steadiness parameter     [0 to 100]

# Steadiness parameters for Gender/Age estimation
pe_threshold_use = 300  # Estimation result stabilizing threshold value
                        #                                          [0 to 1000]
pe_min_UD_angle = -15   # Minimum up-down angel threshold value    [-90 to 90]
pe_max_UD_angle = 20    # Maxmum up-down angel threshold value     [-90 to 90]
pe_min_LR_angle = -30   # Minimum left-right angel threshold value [-90 to 90]
pe_max_LR_angle = 30    # Maxmum left-right angel threshold value  [-90 to 90]
pe_complete_frame_count = 5
                        # The number of previous frames applying to fix
                        # stabilization.                           [1 to 20]

# Steadiness parameters for Recognition
fr_threshold_use = 300  # Recognition result stabilizing threshold value
                        #                                          [0 to 1000]
fr_min_UD_angle = -15   # Minimum up-down angel threshold value    [-90 to 90]
fr_max_UD_angle = 20    # Maxmum up-down angel threshold value     [-90 to 90]
fr_min_LR_angle = -30   # Minimum left-right angel threshold value [-90 to 90]
fr_max_LR_angle = 30    # Maxmum left-right angel threshold value  [-90 to 90]
fr_complete_frame_count = 5
                        # The number of previous frames applying to fix
                        # stabilization.                           [1 to 20]
fr_min_ratio = 60       # Minimum account ratio in complete frame count.
                        #                                           [0 to 100]

###############################################################################

def getdeg(x,y):
    x -= 800
    y -= 600
    x_=1
    y_=1
    x_pos = (math.atan(x * math.tan(27 * math.pi / 180) / 800)) * 180 / math.pi #HVC spec X: -27deg to 27deg
    y_pos = 15-(math.atan(y * math.tan(20.5 * math.pi / 180) / 600)) * 180 / math.pi #HVC spec Y:-20.5deg to 20.5deg
    if (x<0): 
        x_=-1
    if (y<0): 
        y_=-1
    return (x_,round(x_pos), y_, round(y_pos))



def parse_arg(argv):
    argc = len(argv)
    if argc == 3 or argc == 4:
        # Gets port infomation
        portinfo = argv[1]
        # Gets baudrate
        baudrate = int(argv[2])
        if baudrate not in p2def.AVAILABLE_BAUD:
            print("Error: Invalid baudrate.")
            sys.exit()
        # Gets STB flag
        use_stb = p2def.USE_STB_ON # Default setting is ON
        if argc == 4 and argv[3] == "OFF":
            use_stb = p2def.USE_STB_OFF
    else:
        print("Error: Invalid argument.")
        sys.exit()
    return (portinfo, baudrate, use_stb)

def check_connection(hvc_p2_api):
    (res_code, hvc_type, major, minor, release, rev) = hvc_p2_api.get_version()
    if res_code == 0 and hvc_type.startswith(b'B5T-007001'):
        pass
    else:
        raise IOError("Error: connection failure.")

def set_hvc_p2_parameters(hvc_p2_api):
    # Sets camera angle
    res_code = hvc_p2_api.set_camera_angle(hvc_camera_angle)
    if res_code is not p2def.RESPONSE_CODE_NORMAL:
        raise ValueError("Error: Invalid camera angle.")

    # Sets threshold
    res_code = hvc_p2_api.set_threshold(body_thresh, hand_thresh,\
                                        face_thresh, recognition_thresh)
    if res_code is not p2def.RESPONSE_CODE_NORMAL:
        raise ValueError("Error: Invalid threshold.")

    # Sets detection size
    res_code = hvc_p2_api.set_detection_size(min_body_size, max_body_size,\
                                             min_hand_size, max_hand_size,\
                                             min_face_size, max_face_size)
    if res_code is not p2def.RESPONSE_CODE_NORMAL:
        raise ValueError("Error: Invalid detection size.")

    # Sets face angle
    res_code = hvc_p2_api.set_face_angle(face_angle_yaw, face_angle_roll)
    if res_code is not p2def.RESPONSE_CODE_NORMAL:
        raise ValueError("Error: Invalid face angle.")

def set_stb_parameters(hvc_p2_api):
    if hvc_p2_api.use_stb is not True:
        return

    # Sets tracking retry count.
    ret = hvc_p2_api.set_stb_tr_retry_count(max_retry_count)
    if ret != 0:
        raise ValueError("Error: Invalid parameter. set_stb_tr_retry_count().")

    # Sets steadiness parameters
    ret = hvc_p2_api.set_stb_tr_steadiness_param(steadiness_param_pos,
                                                 steadiness_param_size)
    if ret != 0:
        raise ValueError("Error: Invalid parameter. set_stb_tr_steadiness_param().")

    #-- Sets STB parameters for Gender/Age estimation
    # Sets estimation result stabilizing threshold value
    ret = hvc_p2_api.set_stb_pe_threshold_use(pe_threshold_use)
    if ret != 0:
        raise ValueError("Error: Invalid parameter. set_stb_pe_threshold_use().")

    # Sets estimation result stabilizing angle
    ret = hvc_p2_api.set_stb_pe_angle_use(pe_min_UD_angle, pe_max_UD_angle,\
                                          pe_min_LR_angle, pe_max_LR_angle)
    if ret != 0:
        raise ValueError("Error: Invalid parameter. set_stb_pe_angle_use().")

    # Sets age/gender estimation complete frame count
    ret = hvc_p2_api.set_stb_pe_complete_frame_count(pe_complete_frame_count)
    if ret != 0:
        raise ValueError("Error: Invalid parameter. set_stb_pe_complete_frame_count().")

    #-- Sets STB parameters for Recognition
    # Sets recognition stabilizing threshold value
    ret = hvc_p2_api.set_stb_fr_threshold_use(fr_threshold_use)
    if ret != 0:
        raise ValueError("Error: Invalid parameter. set_stb_fr_threshold_use().")

    # Sets recognition stabilizing angle
    ret = hvc_p2_api.set_stb_fr_angle_use(fr_min_UD_angle, fr_max_UD_angle,\
                                          fr_min_LR_angle, fr_max_LR_angle)
    if ret != 0:
        raise ValueError("Error: Invalid parameter. set_stb_fr_angle_use().")

    # Sets recognition stabilizing complete frame count
    ret = hvc_p2_api.set_stb_fr_complete_frame_count(fr_complete_frame_count)
    if ret != 0:
        raise ValueError("Error: Invalid parameter. set_stb_fr_complete_frame_count().")

    # Sets recognition minimum account ratio
    ret = hvc_p2_api.set_stb_fr_min_ratio(fr_min_ratio)
    if ret != 0:
        raise ValueError("Error: Invalid parameter. set_stb_fr_min_ratio().")
