#! /usr/bin/env python

"""
Lane Detection

    Usage: python3 run.py  --conf=./config.json

"""

import cv2
import tensorflow as tf
for gpu in tf.config.experimental.list_physical_devices('GPU'):
    tf.compat.v2.config.experimental.set_memory_growth(gpu, True)
import numpy as np
import argparse
import json
import os

# gpus = tf.config.experimental.list_physical_devices('GPU')
# if gpus:
#     tf.config.experimental.set_virtual_device_configuration(gpus[0], [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=7700)])


# define command line arguments
argparser = argparse.ArgumentParser(
    description='Run Road Segmentation Model on a video')

argparser.add_argument(
    '-c',
    '--conf', default="config.json",
    help='path to configuration file')

argparser.add_argument(
    '-m',
    '--model', default="UNET_trained.h5",
    help='path to model file')

argparser.add_argument(
    '-v',
    '--video', default="video.mp4",
    help='path to video file')

argparser.add_argument(
    '-o',
    '--out_video',
    help='path to output video file')

argparser.add_argument(
    '-oi',
    '--out_images',
    help='path to output image folder')

def _main_(args):
    """
    :param args: command line argument
    """

    # parse command line argument
    config_path = args.conf

    # open and load the config json
    with open(config_path) as config_buffer:
        config = json.loads(config_buffer.read())

    # Load best model
    model = tf.keras.models.load_model(args.model)

    input_size = (config["model"]["im_width"], config["model"]["im_height"])

    # Create a VideoCapture object and read from input file
    # If the input is the camera, pass 0 instead of the video file name
    cap = cv2.VideoCapture(args.video)

    # Init out video writer
    if args.out_video is not None:
        out_vid = out = cv2.VideoWriter(args.out_video,cv2.VideoWriter_fourcc('M','J','P','G'), cap.get(cv2.CAP_PROP_FPS), (config["model"]["out_width"], config["model"]["out_height"]))
    
    # Check if camera opened successfully
    if (cap.isOpened()== False): 
        print("Error opening video stream or file")
        return
        
    count = 0
    # Read until video is completed
    while(cap.isOpened()):
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            break

        raw = cv2.resize(frame, (input_size[0], input_size[1]))

        # Sub mean
        # Because we use it with the training samples, I put it here
        # See in ./src/data/data_utils/data_loader
        img = raw.astype(np.float32)
        img[:,:,0] -= 103.939
        img[:,:,1] -= 116.779
        img[:,:,2] -= 123.68
        img = img[ : , : , ::-1 ]

        net_input = np.expand_dims(img, axis=0)
        preds = model.predict(net_input, verbose=1)
        pred_1 = preds[:,:,:,1].reshape((input_size[1], input_size[0]))
        pred_2 = preds[:,:,:,2].reshape((input_size[1], input_size[0]))
        pred_3 = preds[:,:,:,3].reshape((input_size[1], input_size[0]))
        # pred_1[pred_1 < 0.2] = 0
        # print(pred_1)

        pred_out = 255 * pred_1 + 100 * pred_2 + 50 * pred_3 # Now scale by 255
        out_img = pred_out.astype(np.uint8)

        # Write output
        if args.out_video is not None:
            # Write the frame into the output
            out_vid.write(out_img)

        if args.out_images is not None:
            cv2.imwrite(os.path.join(args.out_images, str(count) + ".png"), out_img)

        count += 1
        cv2.imshow("Raw", raw)
        cv2.waitKey(1)
        cv2.imshow("out_img", out_img)
        cv2.waitKey(1)
            
    cap.release()
    if args.out_video is not None:
        out_vid.release()


if __name__ == '__main__':
    # parse the arguments
    args = argparser.parse_args()
    _main_(args)
