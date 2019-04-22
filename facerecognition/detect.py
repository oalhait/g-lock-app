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
#joel-0, obed-1, mal-2, omar-3, matt-4, chris-5, chin-6
def who(s):
	if s.startswith("joel"):
		return 0
	elif s.startswith("obed"):
		return 1
	elif s.startswith("mal"):
		return 2
	elif s.startswith("omar"):
		return 3
	elif s.startswith("matt"):
		return 4
	elif s.startswith("chris"):
		return 5
	elif s.startswith("chin"):
		return 6


def detect_face(path=os.curdir):
	data = []
	labels = []

	#Iterate through files in folders 
	for root, dirs, files in os.walk(os.curdir, topdown=False):
		for filename in files:
			if filename.endswith(".jpeg") or filename.endswith(".jpg"):
				print(filename)
				final = detect_face_file(os.path.join(root,filename))

				#If no face is found dont add anything
				if final != []:
					#Figure out who it is and and to label
					labels.append(who(filename))
				
					#Append to data list
					data.append(final)

	return (np.array(data), np.array(labels))



def detect_face_file(file):
	final = []
	cascPath = "haarcascade_frontalface_default.xml"
	# Create the haar cascade
	faceCascade = cv2.CascadeClassifier(cascPath)
	image = cv2.imread(file)
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	# Detect faces in the image
	faces = faceCascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
	# Draw a rectangle around the faces
	for (x, y, w, h) in faces[::-1]:
		print("Found a face!")
		#Resize image to 120 pixels
		cropped = gray[y:y+h, x:x+w]
		final = np.array(cv2.resize(cropped, (120,120)))
	return final




#Main function
if __name__ == '__main__':
	# Get user supplied values
	#imagePath = sys.argv[1]
	print()
	finall, labelss = detect_face()
	print("Faces found: ", len(finall))
	for imagee in finall:
		cv2.imshow( "Display WIndow" , imagee)
		cv2.waitKey(0)
	cv2.destroyAllWindows()
	
	