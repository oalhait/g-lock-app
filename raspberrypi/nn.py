import sys
import csv
import numpy as np 
import tensorflow as tf
from tensorflow import keras
from detect import detect_face_file
import tensor



def find_face(img):
	face = detect_face_file(img)
	#If no face found
	if face == []:
		return 0
	N = tensor.Neuron_Network(14400, 3000, 100, 6)
	N.model = tf.keras.models.load_model("14400,3000,100,6,30si")
	image = (np.expand_dims(face,0))
	prediction = M.model.predict(image)
	print(prediction[0])
	guess = np.argmax(prediction[0])
	if prediction[0][guess] < .05:
		return -1
	else:
		return 1



# #Main function
if __name__ == '__main__':
	#Grab inputs from commandline
	model_file = sys.argv[1]
	test_file = sys.argv[2]

	#Set NeuralNetwork Class
	layer = model_file[:-5]
	l = layer.split(",")
	NN = tensor.Neuron_Network(int(l[0]), int(l[1]), int(l[2]), int(l[3]))

	#Load model after it being trained
	NN.model = tf.keras.models.load_model(model_file)

	#Print result from traiaing
	prediction = NN.predict(test_file)
	print("Prediction = ", prediction)


