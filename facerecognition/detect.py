import cv2
import sys
import os
import numpy as np

'''
To Do:
-Given a folder of images, convert all of them into grayscale
numpy arrays and pass through to neural network for training.

-Pass label of who it is by looking at the name of the file.
'''

def detect_face(path=os.curdir):
	data = []

	#Iterate through files in folders 
	for file in os.listdir(path):
		filename = os.fsdecode(file)
		if filename.endswith(".jpeg") or filename.endswith(".jpg"):
			print(filename)
			final = detect_face_file(filename)
		
			#Append to data list
			data.append(final)

	return np.array(data)



def detect_face_file(file):
	cascPath = "haarcascade_frontalface_default.xml"
	# Create the haar cascade
	faceCascade = cv2.CascadeClassifier(cascPath)
	image = cv2.imread(file)
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	# Detect faces in the image
	faces = faceCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5,minSize=(30, 30))
	# Draw a rectangle around the faces
	for (x, y, w, h) in faces:
		print("Found a face!")
		#Resize image to 120 pixels
		cropped = gray[y:y+h, x:x+w]
		final = np.array(cv2.resize(cropped, (120,120)))
	return final




#Main function
if __name__ == '__main__':
	# Get user supplied values
	#imagePath = sys.argv[1]
	finall = detect_face()
	print("Faces found: ", len(finall))
	cv2.imshow("Image", finall[0])
	cv2.waitKey(0)
	