from time import sleep, time, strftime
from flask import Flask, flash, redirect, render_template, request, session, abort, Response, g
import grpc
from os import urandom
import lock_pb2
import lock_pb2_grpc
import RPi.GPIO as GPIO 
import numpy as np
import board
from neopixel import GRB, NeoPixel
from concurrent import futures
from twilio.rest import Client
from threading import Thread, currentThread, Event    # Multi-threading
# import shlex, subprocess
import KEYPAD as keypad
import LED as led
# import STRIP as strip
import ULTRASONIC as sonic
import lock_pb2
import lock_pb2_grpc
import UTILS as utils
from imutils.video import VideoStream
from imutils.video import FPS
from imutils.video.pivideostream import PiVideoStream
from picamera.array import PiRGBArray
from picamera import PiCamera
from nn import load_model
import tensorflow as tf
from tensorflow import keras
import cv2 as opencv
from io import BytesIO
from socketserver import ThreadingMixIn
from http import server
from threading import Condition
import logging
# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
output = None
model = None

#logging
log_handler = logging.StreamHandler()
log_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(log_handler)
GLOBAL_LOG = ""

class Glock(object):
    def __init__(self):
        self.code = utils.get_code()
        print("CURRENT KP CODE:", self.code)

        self.result_count = 0
        self.last = -1
        self.names = ["Joel", "Obed", "Malcolm", "Omar", "Matt", "Chris", "Chinny"]

        #thread variables
        self.kp_thread = None
        self.camera_thread = None
        self.stream_thread = None
        self.main_thread = None
        self.idle_thread = None

        #thread event signals
        self.kp_stop_signal = None
        self.camera_stop_signal = None
        self.stream_stop_signal = None
        self.main_stop_signal = None
        self.idle_stop_signal = None
        self.idle_blue_signal = Event()

        #system variables
        self.camera = None
        self.system_active_idle = False
        self.ran_validation = False
        self.keypad = None
        self.killed = False 
        self.stream_process = None
        self.stream = None
        self.result_count = None
        self.init_done = False
        self.bytes = None
        self.key = None
        self.fps = None
        self.kp_active = False
        self.result_count = None
        self.frame_counter = 0
        self.verification_frame_count = 0


        # NeoPixel Setup
        self.pixel_pin = board.D21
        self.num_pixels = 60
        self.ORDER = GRB
        self.pixels = NeoPixel(self.pixel_pin, self.num_pixels, brightness=0.2, auto_write=False,
                                   pixel_order=self.ORDER)

        #setup GPIO pins
        self.GPIO_TRIGGER = 13 
        self.GPIO_ECHO = 19
        self.GPIO_STRIKE = 20
        self.LED_PIN = 25
           
        #set GPIO direction (IN / OUT)
        #GPIO SETUP
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.GPIO_TRIGGER, GPIO.OUT)
        GPIO.setup(self.GPIO_ECHO, GPIO.IN)
        GPIO.setup(self.GPIO_STRIKE, GPIO.OUT)
        GPIO.setup(self.LED_PIN,GPIO.OUT) # LED pin

    def detect_face_frame(self, image):
        final = []
        cascPath = "haarcascade_frontalface_default.xml"
        # Create the haar cascade
        faceCascade = opencv.CascadeClassifier(cascPath)
        gray = opencv.cvtColor(image, opencv.COLOR_BGR2GRAY)

        print("frame processing...")
        # cv2.destroyAllWindows()
        # Detect faces in the image
        faces = faceCascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        #If no faces were found tweak parameters
        if len(faces) == 0:
            faces = faceCascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
        if len(faces) == 0:
            faces = faceCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            
        # Draw a rectangle around the faces
        for (x, y, w, h) in faces[::-1]:
            print("Found a face!")
            #Resize image to 120 pixels
            cropped = gray[y-20:y+h+20, x:x+w]
            final = np.array(opencv.resize(cropped, (100,100)))

            opencv.imshow("Display WIndow" , final)
            opencv.waitKey(0)  
            opencv.destroyAllWindows()
        return final

    def find_face(self, img):
        global model_sigmoid
        global model_softmax
        global sig_input_details
        global soft_input_details
        global sig_output_details
        global soft_output_details
        
        face = self.detect_face_frame(img)
        #If no face found
        if face == []:
            return 0, -1
        
        #Sigmoid output
        sig_input_data = np.reshape(np.array(face, dtype=np.float32), sig_input_details[0]['shape'])
        model_sigmoid.set_tensor(sig_input_details[0]['index'], sig_input_data)
        model_sigmoid.invoke()
        sig_output = model_sigmoid.get_tensor(sig_output_details[0]['index'])
        
        #Softmax Output
        soft_input_data = np.divide(np.reshape(np.array(face, dtype=np.float32), soft_input_details[0]['shape']), 255.0)
        model_softmax.set_tensor(soft_input_details[0]['index'], soft_input_data)
        model_softmax.invoke()
        soft_output = model_softmax.get_tensor(soft_output_details[0]['index'])
        
        sig = np.argmax(sig_output)
        soft = np.argmax(soft_output)
        print("Sig Raw Value: ", sig_output)
        print("Soft Raw Value: ", soft_output)
        print("Person: ", self.names[sig])
        #If 2 differnt people
        if sig != soft:
            return -1, -1
        #If not above threshold
        #elif
        else:
            return 1, sig

    def distance(self):
        #set Trigger to HIGH
        GPIO.output(self.GPIO_TRIGGER, True)
                    
        # set Trigger after 0.01ms to LOW
        sleep(0.00001)
        GPIO.output(self.GPIO_TRIGGER, False)
                       
        StartTime = time()
        StopTime = time()
                                           
        # save StartTime
        while GPIO.input(self.GPIO_ECHO) == 0:
            StartTime = time()
                                                   
        # save time of arrival
        while GPIO.input(self.GPIO_ECHO) == 1:
            StopTime = time()
                                                                                    
        # time difference between start and arrival
        TimeElapsed = StopTime - StartTime
        # multiply with the sonic speed (34300 cm/s)
        # and divide by 2, because there and back
        distance = (TimeElapsed * 34300) / 2                                                                                       
        return distance


    def led_unlock_success(self):
        #stop idle led to allow for GREEN light
        if self.idle_stop_signal!=None:
            self.idle_stop_signal.set()
            self.idle_thread.join()

        #start with green flash and then pulse     
        self.pixels.fill((0, 225, 0))
        for i in range(60):
            self.pixels[i] = (0, 125, 0)
            self.pixels.show()
            sleep(.01)

        for i in range(60):
            self.pixels[60-i-1] = (0, 50, 0)
            self.pixels.show()
            sleep(.01)


    def led_unlock_fail(self):
        #stop idle led to allow for RED light
        if self.idle_stop_signal!=None:
            self.idle_stop_signal.set()
            self.idle_thread.join()
        #pluse in red
        for eek in range(3):
            for i in range(20):
                self.pixels.fill((225-i, 0, 0))
                self.pixels.show()
                sleep(.0005)
        sleep(.5)


    def restart_idle(self):
        #Function to restart IDLE LED Thread
        sleep(1)

        self.idle_stop_signal = Event()
        self.idle_blue_signal.clear()
        self.idle_thread = Thread(target=self.idle) 

        self.idle_thread.start()


    def idle(self):
        print("starting IDLE LED thread")
        #Process to  pulse either white or blue
        #will plulse in blue if signal is sent by keypad handler 
        while not self.idle_stop_signal.wait(0):
            if self.idle_blue_signal.isSet():
                for i in range(60):
                    self.pixels[i] = (0, 0, 125)
                    self.pixels.show()
                    sleep(.01)

                for i in range(60):
                    self.pixels[60-i-1] = (0, 0, 50)
                    self.pixels.show()
                    sleep(.01)
            else:
                for i in range(60):
                    self.pixels[i] = (125, 125, 125)
                    self.pixels.show()
                    sleep(.01)

                for i in range(60):
                    self.pixels[60-i-1] = (50, 50, 50)
                    self.pixels.show()
                    sleep(.01)


    def Validated(self):
        #add mutex on gpio ops?
        #activate strike for 10 sec
        GPIO.output(self.GPIO_STRIKE,GPIO.HIGH)
        print("GLOCK STRIKE ACTIVATED")
        sendText(True)

        self.led_unlock_success() #unlock strike and wait 
        sleep(16) 
        GPIO.output(self.GPIO_STRIKE,GPIO.LOW)
        self.ran_validation=True #send signal to restaart idle thread

        

    def Invalidated(self):
        #add mutex on gpips?
        print("GLOCK INVALID")
        sendText(False)
        self.led_unlock_fail()
        self.ran_validation = True
        


    def setup_stream(self):
        global output
        #loop to send cameera feed to streaming output class 
        while not self.stream_stop_signal.wait(0):
            with PiCamera(resolution='1024x768', framerate=24) as self.camera:
                output = StreamingOutput()
                self.camera.start_recording(output, format='mjpeg', splitter_port=1, quality=0)
                sleep(_ONE_DAY_IN_SECONDS)
        self.camera.stop_recording()


    def CameraHandler(self):
        #Load models
        global model_sigmoid
        global model_softmax
        global sig_input_details
        global soft_input_details
        global sig_output_details
        global soft_output_details
        
        model_sigmoid = tf.lite.Interpreter(model_path="sigmoid.tflite")
        model_sigmoid.allocate_tensors()
        sig_input_details = model_sigmoid.get_input_details()
        sig_output_details = model_sigmoid.get_output_details()
        
        model_softmax = tf.lite.Interpreter(model_path="softmax.tflite")
        model_softmax.allocate_tensors()
        soft_input_details = model_softmax.get_input_details()
        soft_output_details = model_softmax.get_output_details()
        
        self.init_done = True
        print("Enter CameraHandler...")
        log_handler.emit("Enter CameraHandler...")
        self.result_count = 0

        while not self.camera_stop_signal.wait(0):
            #if no one infrom of door or keypad currently in use then skip processing frame
            if self.system_active_idle == False or self.kp_active:
                # print("loop until motion")
                continue
            #grab every third frame from the camera to verfiy face
            if (self.verification_frame_count % 3 == 0):
                #capture image in array and send to ML suite
                rawCapture = PiRGBArray(self.camera, size=(1024,768))
                sleep(0.1)
                self.camera.capture(rawCapture, format="bgr", use_video_port=True, splitter_port=2)
                image = rawCapture.array
   
                result, person = self.find_face(image)

                rawCapture.truncate(0)
                if result == 0: #no face found in image
                    print("NO FACE FOUND")
                    log_handler.emit("NO FACE FOUND")
                    continue
                elif (result == 1 and self.last == -1) or (result == 1 and self.last == person): #corect face found
                    self.result_count += 1
                    last = person
                    print("RESIDENT FACE FOUND")    
                    log_handler.emit("RESIDENT FACE FOUND")    
                else: #face found but incorrect
                    self.result_count -= 1
                    print("INCORRECT FACE FOUND")
                    log_handler.emit("INCORRECT FACE FOUND")    
                    
                #need to see the same face twice in order to verify resident   
                if (self.result_count == 2): 
                    self.Validated()
                    self.result_count = 0 #reset "correct score"
                    self.last = -1
                #same logic..if two wrong faces then signal invalid    
                elif (self.result_count == -2):
                    self.Invalidated()
                    self.result_count = 0
                    self.last = -1
                else:
                    continue
            self.verification_frame_count += 1
            # count +=1
            # #call verification on captured image


    def KeypadHandler(self):
        print("Enter KeypadHandler")
        log_handler.emit("Enter KeypadHandler")

        code_as_list = list(self.code)
        print("code as list: ", code_as_list)
        log_handler.emit("code as list: ", code_as_list)
        #create empty buffer for entered code
        entered_code = list()
        new_code_list = list()
        code_active = False # flag for signaling when input seq ready 
        reset_active = False
        self.kp_active = False
        looking_new_code = False

        while not self.kp_stop_signal.wait(0):
            keys = self.keypad.pressed_keys #grab key pressed
            if len(keys) != 1:
                #eliminate multi press for keypad
                continue 
        
            if keys ==["#"] and looking_new_code:
                #clear newcode being entered while in "enter code state"
                new_code_list = list()

            elif keys == ['*']: #input is reset and now look for code
                entered_code = list()
                new_code_list = list()

                code_active = True 
                reset_active = False
                self.kp_active = True
                looking_new_code = False

                self.idle_blue_signal.clear()
            #reset master key code (usual '#' case)
            elif keys == ['#']:
                self.idle_blue_signal.set()

                entered_code = list()
                new_code_list = list()
                code_active = False
                reset_active = True
                self.kp_active = True
                looking_new_code = False


            elif reset_active:
                #regualar number is pressed while setting new key code ]
                #or to verifty old code for kp code change
                new_code_list += keys
                if looking_new_code: #if case will short to here if alrady entered old code to change to new
                    if len(code_as_list) == len(new_code_list): #get new code 
                        print("new_code",new_code_list)
                        log_handler.emit("new_code",new_code_list)

                        as_string = [str(elem) for elem in new_code_list]   
                        as_string = ''.join(as_string)  

                        #update code variavles 
                        self.code = as_string
                        utils.change_code(as_string) 
                        code_as_list = new_code_list

                        #flash blue
                        new_code_list = list()
                        entered_code = list()
                        looking_new_code = False
                        reset_active = False

                        self.idle_blue_signal.clear()
                        self.kp_active=False

                elif len(code_as_list) == len(new_code_list): #submit old code for verification
                    verification_res = (new_code_list == [int(i) for i in code_as_list]) #verify list
                    print("old_code", new_code_list, "verified:", str(verification_res))
                    log_handler.emit("old_code", new_code_list, "verified:", str(verification_res))
                    
                    if verification_res:
                        #flash blue
                        # time.sleep(1)
                        # time.sleep(1)
                        looking_new_code = True

                        self.led_unlock_success()

                    else:
                        #flash red
                        reset_active = False
                        self.kp_active = False
                        self.Invalidated()
                    
                    new_code_list = list()
                    entered_code = list()



            elif code_active:
                    entered_code += keys #add key to code
                    if len(code_as_list) == len(entered_code): #submit code for verification
                        code_active = False
                        self.kp_active=False

                        print("code", entered_code)
                        log_handler.emit("code", entered_code)
                        verification_res = (entered_code == [int(i) for i in code_as_list]) #verify list
                        if verification_res == True:
                            print("Validated")
                            log_handler.emit("Validated")
                            self.Validated()
                        else:
                            print("Invalidated")
                            log_handler.emit("Invalidated")
                            self.Invalidated()

            else:
                continue
     
            print("code", entered_code)
            print("reset_code", new_code_list)

            sleep(0.3)


    def MainHandler(self):
        print("Enter Main MainHandler...")
        # distances = [1000,1000,1000] #track last three disances 

        #create queue of seen distances
        distances = [0,0,0]
        d_count = 0 
        d_max = 0 
        while not self.init_done:
            continue
        while not self.main_stop_signal.wait(0):
            sleep(0.5)
            distance = self.distance()
            distances[d_count%3] = distance
            d_count += 1
            print ("Measured Distance = %.1f cm" % distance)
            # print(self.system_active_idle)
            # print(self.ran_validation)
            if(max(distances) < 90 and self.system_active_idle==False): #start process for camera and LED
                print("idlewake")

                self.system_active_idle=True

                self.restart_idle()

                self.kp_stop_signal = Event()
                self.kp_thread = Thread(target=self.KeypadHandler)
                self.kp_thread.start()


            elif(self.ran_validation==True):
                print("ran validation, restarting idle")
                log_handler.emit("ran validation, restarting idle")



                #clear pixels
                self.pixels.fill((0, 0, 0))
                self.pixels.show()

                #restart the killed idle thread if person in front of sensor
                if max(distances)<90:
                    self.restart_idle()
                    self.system_active_idle= True
                else:
                
                    self.system_active_idle= False
                self.ran_validation = False
            elif(min(distances) > 90 and self.system_active_idle==True): #close ML and turn off LED
                print("no motion detected...close idle")
                log_handler.emit("no motion detected...close idle")
                self.system_active_idle=False

                self.idle_blue_signal.clear()
                self.idle_stop_signal.set()
                self.kp_stop_signal.set()

                self.idle_thread.join()


                self.kp_thread.join()
                print("kp joined")

                self.pixels.fill((0, 0, 0))
                self.pixels.show()

                self.ran_validation = False
        try:
            self.camera_stop_signal.set()
            self.camera_thread.join()
            print("camera joined")
            self.idle_stop_signal.set() #stop self.idle_thread when main function exits
            self.idle_thread.join()
        except:
            return

            
    def run(self):

        #clear pixels
        self.pixels.fill((0, 0, 0))
        self.pixels.show()


        self.stream_stop_signal = Event()
        self.stream_thread = Thread(target=self.setup_stream)
        self.stream_thread.start()

        self.keypad = keypad.keypad_setup()

        self.camera_stop_signal = Event()
        self.camera_thread = Thread(target=self.CameraHandler)
        self.camera_thread.start()

        self.main_stop_signal = Event()
        self.main_thread = Thread(target=self.MainHandler)
        self.main_thread.start()



        print("G_LOCK HAS BEEN STARTED")
        log_handler.emit("G_LOCK HAS BEEN STARTED")


    # def stream_serve(self):
    #     p0 = subprocess.call(['sudo', 'pkill', 'uv4l']) #exit any hanging uv4l processes

    #     command = "sudo uv4l -nopreview --auto-video_nr --driver raspicam --encoding mjpeg --width 640 --height 480 --framerate 20 --server-option '--port=2020' --server-option '--max-queued-connections=30' --server-option '--max-streams=25' --server-option '--max-threads=29'"
    #     args = shlex.split(command)
    #     p1 = subprocess.Popen(args) #start streaming server 

    #     print("BEGIN UV4L STREAMING")


    def kill(self):
        self.killed = True

        print("GLOCK KILL: Stopping threads")

        self.main_stop_signal.set()
        self.stream_stop_signal.set()

        self.stream_thread.join()
        self.main_thread.join()

        #clear pixels
        self.pixels.fill((0, 0, 0))
        self.pixels.show()


class GlockServer(lock_pb2_grpc.GLOCKServicer):
    def Unlock(self, request, context):
        # led.LED_on() #switch unlock 
        glock.Validated()
        # self.ran_validation = True/
        #     #clear pixels
        glock.pixels.fill((0, 0, 0))
        glock.pixels.show()
        return lock_pb2.GlockResponse(message='Server Unlocked Strike')

def serve(stop_signal):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    lock_pb2_grpc.add_GLOCKServicer_to_server(GlockServer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("RPC Server Started")

    while not stop_signal.isSet():
        sleep(_ONE_DAY_IN_SECONDS)
        continue
    print("rpcserver stop")
    server.stop(0) 

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = BytesIO()
        self.condition = Condition()

    def write(self, buf):

        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingServer(ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

app = Flask(__name__)

@app.route('/')
def homepage():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('index.html')

@app.route('/login', methods=['POST'])
def do_admin_login():
    if request.form['password'] == 'password' and request.form['username'] == 'glock':
        session['logged_in'] = True
        return render_template('index.html')
    else:
        flash('wrong password!')
        return render_template('login.html')

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return render_template('login.html')

@app.route("/unlock_request")
def unlock_request():
    channel = grpc.insecure_channel('172.20.10.6:50051')
    stub = lock_pb2_grpc.GLOCKStub(channel)
    response = stub.Unlock(lock_pb2.GlockRequest())
    # print('Client received: {}'.format(response.message))
    return "OK"

def gen():
    global output
    while True:
        frame = output.frame
        # frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.before_request
def set_up_logging():
    global log_handler
    g.log_handler = log_handler

@app.route('/video_feed')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def sendText(unlock):
    body = ""
    time = strftime("%m/%d/%Y %H:%M")
    if(unlock):
        body = 'SUCCESS: ' + time + 'Front door unlocked!'
    else:
        body = 'FAILED: ' + time + 'Unsuccessful recognition attempted.'

    numbers_to_message = ['+14088886246', '+17086993770', '+13107384780']
    for number in numbers_to_message:
        Client.messages.create(
            body = body,
            from_ = '+18054161977',
            to = number
        )


if __name__ == '__main__':
    try:
	
	#system setup logic
        rpc_stop_signal = Event()
        rpc_thread = Thread(target=serve, args=(rpc_stop_signal,))
        rpc_thread.start()
        glock = Glock()
        #Neural Network
        glock.run()
        
        app.secret_key = urandom(12)
        # video_camera = VideoCamera() # creates a camera object, flip vertically
        app.run(host='0.0.0.0', debug=True, use_reloader=False, threaded=True)
        print("running1")
    except KeyboardInterrupt:
        print("main key KeyboardInterrupt")
        rpc_stop_signal.set()
        # rpc_thread.server_alive = False
        rpc_thread.join()
        print("joined")
        glock.kill()
