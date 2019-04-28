import sys
import csv
import numpy as np 
import tensorflow as tf
from tensorflow import keras
from detect import detect_face_frame
import tensor

def load_model(filename):
	layer = filename[:-5]
	l = layer.split(",")
	NN = tensor.Neuron_Network(int(l[0]), int(l[1]), int(l[2]), int(l[3]))

	#Load model after it being trained
	NN.model = tf.keras.models.load_model(filename)
	return NN

# def find_face(img):
# 	face = detect_face_frame(img)
# 	#If no face found
# 	if face == []:
# 		return 0
# 	N = tensor.Neuron_Network(14400, 1000, 100, 6)
# 	N.model = tf.keras.models.load_model("14400,1000,100,6,30si")
# 	image = (np.expand_dims(face,0))
# 	prediction = M.model.predict(image)
# 	print(prediction[0])
# 	guess = np.argmax(prediction[0])
# 	if prediction[0][guess] < .05:
# 		return -1
# 	else:
# 		return 1



# #Main function
if __name__ == '__main__':
	#Grab inputs from commandline
	model_file = sys.argv[1]
	test_file = sys.argv[2]
	# test2 = sys.argv[3]
	# test3 = sys.argv[4]

	#Set NeuralNetwork Class
	layer = model_file[:-5]
	l = layer.split(",")
	NN = tensor.Neuron_Network(int(l[0]), int(l[1]), int(l[2]), int(l[3]))

	#Load model after it being trained
	NN.model = tf.keras.models.load_model(model_file)

	#Print result from traiaing
	prediction = NN.predict(test_file)
	print("Prediction1 = ", prediction)
	# prediction = NN.predict(test2)
	# print("Prediction2 = ", prediction)
	# prediction = NN.predict(test3)
	# print("Prediction3 = ", prediction)


