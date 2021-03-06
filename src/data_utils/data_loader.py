
import numpy as np
import cv2
import glob
import itertools
import os
from tqdm import tqdm
from .augmentation import augment_seg
import random
random.seed(0)
class_colors = [  ( random.randint(0,255),random.randint(0,255),random.randint(0,255)   ) for _ in range(5000)  ]

IMAGE_ORDERING = 'channels_last'

def get_pairs_from_paths( images_path , segs_path ):
		images = glob.glob( os.path.join(images_path,"*.jpg")  ) + glob.glob( os.path.join(images_path,"*.png")  ) +  glob.glob( os.path.join(images_path,"*.jpeg")  )
		segmentations  =  glob.glob( os.path.join(segs_path,"*.png")  ) 

		segmentations_d = dict( zip(segmentations,segmentations ))

		ret = []

		for im in images:
			seg_bnme = os.path.basename(im).replace(".jpg" , ".png").replace(".jpeg" , ".png")
			seg = os.path.join( segs_path , seg_bnme  )
			assert ( seg in segmentations_d ),  (im + " is present in "+images_path +" but "+seg_bnme+" is not found in "+segs_path + " . Make sure annotation image are in .png"  )
			ret.append((im , seg) )

		return ret


def get_image_arr( path , width , height , imgNorm="sub_mean" , ordering='channels_last' ):

	if type( path ) is np.ndarray:
		img = path
	else:
		img = cv2.imread(path, 1)

	if imgNorm == "sub_and_divide":
		img = np.float32(cv2.resize(img, ( width , height ))) / 127.5 - 1
	elif imgNorm == "sub_mean":
		img = cv2.resize(img, ( width , height ))
		img = img.astype(np.float32)
		img[:,:,0] -= 103.939
		img[:,:,1] -= 116.779
		img[:,:,2] -= 123.68
		img = img[ : , : , ::-1 ]
	elif imgNorm == "divide":
		img = cv2.resize(img, ( width , height ))
		img = img.astype(np.float32)
		img = img/255.0

	if ordering == 'channels_first':
		img = np.rollaxis(img, 2, 0)
	return img


def get_segmentation_arr( path , n_classes ,  width , height , no_reshape=False ):

	seg_labels = np.zeros((  height , width  , n_classes ))
		
	if type( path ) is np.ndarray:
		img = path
	else:
		img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

	img = cv2.resize(img, ( width , height ) , interpolation=cv2.INTER_NEAREST )

	if n_classes == 2: # Binary
		img[img > 0] = 1

	for c in range(n_classes):
		seg_labels[: , : , c ] = (img == c).astype(int)

	if no_reshape:
		return seg_labels

	seg_labels = np.reshape(seg_labels, ( height, width, n_classes ))
	return seg_labels

def verify_segmentation_dataset( images_path , segs_path , n_classes ):
	
	img_seg_pairs = get_pairs_from_paths( images_path , segs_path )

	assert len(img_seg_pairs)>0 , "Dataset looks empty or path is wrong "
	
	for im_fn , seg_fn in tqdm(img_seg_pairs) :
		img = cv2.imread( im_fn )
		seg = cv2.imread( seg_fn )

		assert ( img.shape[0]==seg.shape[0] and img.shape[1]==seg.shape[1] ) , "The size of image and the annotation does not match or they are corrupt "+ im_fn + " " + seg_fn
		assert ( np.max(seg[:,:,0]) < n_classes) , "The pixel values of seg image should be from 0 to "+str(n_classes-1) + " . Found pixel value "+str(np.max(seg[:,:,0]))

	print("Dataset verified! ")



	