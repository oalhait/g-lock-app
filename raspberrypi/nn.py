import sys
import csv
import numpy as np 
import tensorflow as tf
from tensorflow import keras
from detect import detect_face_frame
import tensor

'''
To do:
-Write Main function
-Figure out how to map inputs to input neurons
-map outputs to output vector
-Test Feedforwar
-Cost Function
-Backpropogation

-Call into detect script eventually

'''


# #Sigmoid function given a vector returns an output vector with sigmoid applied
# def sigmoid(vector):
# 	rows = vector.shape[0]
# 	ones = np.ones(rows)
# 	return np.divide(ones, (ones + np.exp(np.negative(vector))))


# #Softmax function given a vector returns an output vector with softmax applied
# def softmax(vector):
# 	newvec = np.exp(vector)
# 	return np.divide(newvec, np.sum(newvec))


# #Error calculations for Loss function
# def calculate_error():
# 	pass


# #Neural Network Overall Class
# class NN(object):
# 	def __init__(self, layers, orientation, data):
# 		self.layer_count = layers
# 		self.orientation = orientation
# 		self.layers = self.orient()
# 		self.inputs = data
# 		self.length = len(data)

# 	#Creates layers except for input layer and adds to NN
# 	def orient(self):
# 		network = [];
# 		for i in range(1, self.layers):
# 			network.append(NN_layer(self.orientation[i]))
# 		return network

# 	#Given a sequence number return a tuple of single array input and its labek
# 	def input(self, current):
# 		image, label = self.data[current]
# 		vector = np.reshape(image, (self.orientation[0], 1))

# 		#return tuple of input vector and correct label
# 		return(vector, label)

# 	#Checks the last layer for highest output and return that
# 	def output(self):
# 		return np.argmax(self.layers[-1])


# #Neural Network Layer Class
# class NN_layer(object):
# 	def __init__(self, units):
# 		#uniform distribution from 0 to 1
# 		self.weights = np.random.uniform(0.0, 1.0, (units, 1))
# 		self.bias = np.zeros((units, 1))
# 		self.output = np.zeros((units, 1)) 

# 	#Given previous layers outputs, can calculate current outputs
# 	def FeedForward(self, layer, activation):
# 		self.z = self.weights.dot(layer.output) + self.bias
# 		if activation == "sigmoid":
# 			self.output = sigmoid(self.z)
# 		else:
# 			self.output = softmax(self.z)


# #Initial learning done through feedforward of NN and backpropagation
# def Learn(Neural_Network, epochs, learning_rate):

# 	#Learn for number of epochs
# 	for i in range(epochs):

# 		#Loop through all inputs
# 		for j in range(Neural_Network.length):
# 			in_layer, label = Neural_Network.input(j)

# 			#Set inputs to output of input layer
# 			Neural_Network.layers[0].output = in_layer
# 			layers = Neural_Network.layer_count

# 			#Feedforward the 3 next layers.
# 			else:
# 				for k in range(1,layers):
# 					prev = Neural_Network.layers[k-1]

# 					#If last layer we have an activation of softmax
# 					if k == layers:
# 						Neural_Network.layers[k].FeedForward(prev, "softmax")
# 					else:
# 						Neural_Network.layers[k].FeedForward(prev, "sigmoid")

# 			#Based on feedforward determine the error with input
# 			guess = Neural_Network.output()
# 			err = calculate_error(guess, label)

# 			#Compute backpropogation to update network weights
# 			#Blah backprop

# 	#Return trained Neural Network
# 	return Neural_Network
	

# #Main function
# if __name__ == '__main__':
# 	#Grab inputs from commandline
# 	input_layer = sys.argv[1]
# 	first_hidden = sys.argv[2]
# 	second_hidden = sys.argv[3]
# 	output_layer = sys.argv[4]
# 	input_location = sys.argv[5]
# 	epoch = sys.argv[6]
# 	rate = sys.argv[7]

# 	#Call detect script to parse input data
# 	#detect blah

# 	#Create the Neural Network Object and pass it in to Function
# 	NeuralN = NN(4, [input_layer, first_hidden, second_hidden, output_layer], inputdata)

# 	#Learn with NN
# 	NewNN = Learn(NN, epoch, rate)


def find_face(img):
	face = detect_face_frame(img)
	#If no face found
	if face == []:
		return 0
	N = tensor.Neuron_Network(14400, 3000, 100, 6)
	N.model = tf.keras.models.load_model("14400,3000,100,6")
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
	layer = model_file[:-3]
	l = layer.split(",")
	NN = tensor.Neuron_Network(int(l[0]), int(l[1]), int(l[2]), int(l[3]))

	#Load model after it being trained
	NN.model = tf.keras.models.load_model(model_file)

	#Print result from traiaing
	prediction = NN.predict(test_file)
	print("Prediction = ", prediction)


