import sys
import csv
import numpy as np 

'''
To do:
-Write Main function
-Figure out how to map inputs to input neurons
-map outputs to output vector
-Test Feedforwar
-Cost Function
-Backpropogation

'''


#Sigmoid function given a vector returns an output vector with sigmoid applied
def sigmoid():
	rows = vector.shape[0]
	ones = np.ones(rows)
	return np.divide(ones, (ones + np.exp(np.negative(vector))))


#Softmax function given a vector returns an output vector with softmax applied
def softmax(vector):
	newvec = np.exp(vector)
	return np.divide(newvec, np.sum(newvec))


#Error calculations for Loss function
def calculate_error():
	pass


#Neural Network Overall Class
class NN(object):
	def __init__(self, layers, orientation, data, labels):
		self.layer_count = layers
		self.orientation = orientation
		self.layers = self.orient()
		self.inputs = data
		self.labels = labels
		self.length = len(data)

	#Creates layers except for input layer and adds to NN
	def orient(self):
		network = [];
		for i in range(1, self.layers):
			network.append(NN_layer(orientation[i]))
		return network

	#Given a sequence number return a tuple of single array input and its labek
	def input(self, current):
		image, label = self.data[current]
		vector = np.reshape(image, 14400)

		#return tuple of input vector and correct label
		return(vector, label)

	#Checks the last layer for highest output and return that
	def output(self):
		return np.argmax(self.layers[-1])


#Neural Network Layer Class
class NN_layer(object):
	def __init__(self, units):
		#uniform distribution from 0 to 1
		self.weights = np.random.uniform(0.0, 1.0, (units, 1))
		self.bias = np.zeros((units, 1))
		self.output = np.zeros((units, 1)) 

	#Given previous layers outputs, can calculate current outputs
	def FeedForward(self, layer, activation):
		self.z = self.weights.dot(layer.output) + self.bias
		if activation == "sigmoid":
			self.output = sigmoid(self.z)
		else:
			self.output = softmax(self.z)


#Initial learning done through feedforward of NN and backpropagation
def Learn(Neural_Network, epochs, learning_rate):

	#Learn for number of epochs
	for i in range(epochs):

		#Loop through all inputs
		for j in range(Neural_Network.length):
			in_layer, label = Neural_Network.input(j)

			#Feedforward with input layer and first layer
			

	

#Once Feeding Forward is complete, backpropogate the error
def SGD():
	pass

#Main function
if __name__ == '__main__':
	#Need to set up initial input layer and add to front of NN object
	input_train = sys.argv[1]
	input_validation = sys.argv[2]
	output_train = sys.argv[3]
	output_validation = sys.argv[4]
