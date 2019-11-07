#!/usr/bin/env python3
# -*- coding: utf-8 -*-

### Gaze Estimation API Client ################################################
__author__  = "Yoshi Kajiki <y-kajiki@ah.jp.nec.com>"
__version__ = "0.9"
__date__    = "Oct 18, 2019"

import os
import sys
import time
import math
import cv2
import json
import base64
import requests
import numpy
import threading
import queue

import numpy as np

from models.models import Progress
from models.database import db_session
## Settings ###################################################################

endPoint = 'http://a8b88762ef01211e9950f0eacce6e863-2021028779.ap-northeast-1.elb.amazonaws.com'       # for JPHACKS 2019

proxies = []
#proxies = ['http':'http://proxygate2.nic.nec.co.jp:8080', 'https':'http://proxygate2.nic.nec.co.jp:8080']

# displayFlag = True
displayFlag = False

def is_looking_forward(gaze, yaw_min=-60, yaw_max=60, pich_min=-60, pich_max=20):
    yaw, pich = gaze[0], gaze[1]
    return yaw_min < yaw < yaw_max and pich_min < pich < pich_max

###############################################################################
# Send Request
def sendRequest(image, width, height):
    global resultQueue
    global proxies

    # Extrace RAW image
    imgGray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    imgRawArray = numpy.reshape(imgGray, (-1))
    imgRaw = imgRawArray.tobytes()

    # Set URL
    url = endPoint + "/v1/query/gaze_byRAW"

    # Set request parameter
    reqPara = {
        'width' : width,
        'height' : height,
        'raw_b64' : base64.b64encode(imgRaw).decode('utf-8')
    }
    params = {
        'smooth' : 'yes',
    }

    # Send the request
    headers = {'Content-Type' : 'application/json'}
    data = json.dumps(reqPara).encode('utf-8')
    try:
        res = requests.post(url, params=params, data=data, headers=headers, proxies=proxies, timeout=10)
    except:
        print('Error! Can not connect to the API.')
        return ["NONE"]
        #  sys.exit(1)

    # Get response
    if res.status_code == 200:
        # print(json.dumps(res.json(), indent=4))
        #resultQueue.put(res.json())
        return res.json()
    else:
        print('## Error! ##')
        print(res.text)
        return [[],[]]

###############################################################################
def videoReader(videoSource):

    # Open the Video
    try:
        video = cv2.VideoCapture(videoSource)
    except:
        print('Error!  Can not open the video [%s].' % videoSource)
        sys.exit(1)
    if not video.isOpened():
        print('Error!  Can not open the video [%s].' % videoSource)
        sys.exit(1)

    # Read Parameters of the Video
    width = video.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
    num_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video.get(cv2.CAP_PROP_FPS)
    print("fps", fps)
    interval = 1. / fps
    results = []
    eyesColor = (255, 0, 0)
    gaze = None
    gazeLen = width / 5
    gaze_colors = ((0, 0, 255), (0, 102, 255), (0, 204, 255), (0, 255, 204), (0, 255, 0))
    line_color_pattern = len(gaze_colors)
    gaze_line_params = []

    # Create video writer
    #  fourcc = cv2.VideoWriter_fourcc('M', 'P', '4', 'V')
    fourcc = cv2.VideoWriter_fourcc(*'XVID')

    writer = cv2.VideoWriter('uploads/edited.avi', fourcc, fps, (int(width), int(height)))

    gaze_duration = 0
    gaze_list = []

    # Read the Video Stream
    for i in range(num_frames):
    #  for i in range(100):
        start_time = time.time()

        success, image = video.read()
        for j, line_param in enumerate(gaze_line_params[:-1]):
            cv2.arrowedLine(image, *line_param, gaze_colors[j % line_color_pattern], thickness=2)

        # Read a frame
        if i % int(fps/2) != 0:
            writer.write(image)
            continue

        stTime = time.time()
        while not success:
            print("Not success")
            video.release()
            cv2.destroyAllWindows()
            writer.release()
            return gaze_list
        frameNo = video.get(cv2.CAP_PROP_POS_FRAMES)

        # call API with frameRateAPI
        results = ["NONE"]
        while results == ["NONE"]:
            print("count: {}/{}".format(i, num_frames))
            print("Connecting...")

            progress = Progress.query.first()
            if progress is None:
                progress = Progress(movie_frames=num_frames, movie_progress=i)
            else :
                progress.movie_frames = num_frames
                progress.movie_progress = i

            db_session.add(progress)
            db_session.commit()
            results = sendRequest(image, width, height)
            time.sleep(0.1)

        gaze_duration += time.time() - start_time

        #######################################################################
        # Edit for your application
        #######################################################################
        for result in results:
            reye = result['reye']
            leye = result['leye']
            gaze = result['gaze']

            if not gaze is None:
                print("yaw: {}, pich: {}".format(*gaze))
                print(is_looking_forward(gaze))
                gaze_list.append(gaze)


            cv2.circle(image, (int(reye[0]), int(reye[1])), 15, eyesColor, thickness=2)
            cv2.circle(image, (int(leye[0]), int(leye[1])), 15, eyesColor, thickness=2)
            center = ((reye[0]+leye[0])/2, (reye[1]+leye[1])/2)
            gazeTop = (center[0] + gazeLen * math.sin(math.radians(gaze[0])), center[1] + gazeLen * math.sin(math.radians(gaze[1])))
            gaze_line_params.append(((int(center[0]), int(center[1])), (int(gazeTop[0]), int(gazeTop[1]))))
            if len(gaze_line_params) > 5:
                gaze_line_params.pop(0)

        # Show the video
        if displayFlag:
            cv2.imshow('video', image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                video.release()
                cv2.destroyAllWindows()
                return gaze_list
        else:
            if len(results) > 0:
                print('    ', gaze)

        print(gaze_duration)
        writer.write(image)
   
    video.release()
    return gaze_list

### Main ######################################################################
if __name__ == "__main__":

    argvs = sys.argv
    argc = len(argvs)
    if argc < 2:
        print('Usage: python3 %s videoSource' % argvs[0])
        sys.exit(1)
    videoSource = argvs[1]

    # start video
    videoReader(videoSource)
