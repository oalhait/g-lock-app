#Important imports
import sys
import os

#Import Tensorflow and keras
import tensorflow as tf
from tensorflow import keras

#Import numpy and pyplot
import numpy as np

#Import detect.py for opencv
from detect import detect_face
from detect import detect_face_file

class Neuron_Network(object):
	def __init__(self, in_neuron, neuron1, neuron2, out_neuron):
		self.in_neurons = in_neuron
		self.neurons1 = neuron1
		self.neurons2 = neuron2
		self.out_neurons = out_neuron
		self.square_root = int(self.in_neurons**.5)
		self.model = self.initialize_nn()

	#Function that returns a 3-layered NN model based on number of neurons
	def initialize_nn(self):
		return tf.keras.Sequential([
			#Input Layer
			keras.layers.Flatten(input_shape=(self.square_root, self.square_root)),
			#First hidden Layer
			keras.layers.Dense(self.neurons1, activation="sigmoid"),
			#Second Hidden Layer
			keras.layers.Dense(self.neurons2, activation="sigmoid"),
			#Output Layer
			keras.layers.Dense(self.out_neurons, activation="softmax")])

	def predict(self, imagepath):
		img = detect_face_file(imagepath)
		image = (np.expand_dims(img,0))
		prediction = self.model.predict(image)
		print(prediction[0])
		guess = np.argmax(prediction[0])
		return guess



#Main function
if __name__ == '__main__':
	#Grab inputs from commandline
	input_layer = int(sys.argv[1])
	first_hidden = int(sys.argv[2])
	second_hidden = int(sys.argv[3])
	output_layer = int(sys.argv[4])
	epoch = int(sys.argv[5])
	# path = sys.argv[6]

	#Get input data from files
	# with np.load("/training/data.npy") as data:
	# 	in_data = data

	# with np.load("/training/labels.npy") as labels:
	# 	in_labels = labels

	# #Make sure labels and data are same length
	# assert in_data.shape[0] == in_labels.shape[0]

	# #Create a placeholder for current input instead of copying in all training data
	# input_current = tf.placeholder(in_data.dtype, in_data.shape)
	# labels_current = tf.placeholder(in_labels.dtype, in_labels.shape)
	# dataset = tf.data.Dataset.from_tensor_slices((input_current, labels_current))
	# iterator = dataset.make_initializable_iterator()

	in_data, labels = detect_face()

	#Initialize model based on architecture we desire
	NN = Neuron_Network(input_layer, first_hidden, second_hidden, output_layer)

	#Compile model by setting all correct parameters
	NN.model.compile(optimizer="sgd", 
						loss='sparse_categorical_crossentropy', 
						metrics=['accuracy'])
	
	NN.model.fit(x=in_data, y=labels, epochs=epoch)

	file_name = str(input_layer)+","+str(first_hidden)+","+str(second_hidden)+","+str(output_layer)+","+str(epoch)

	NN.model.save(file_name)

	#Call method Fit in order to begin training.
	# NN.model.fit(iterator, epochs=epoch, 
	# 	steps_per_epoch=in_data.shape[0], 
	# 	validations_split=0.2)


	#Simple test prediction
	# print("Prediction = ", NN.predict(path))


