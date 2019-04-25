import time
from flask import Flask, flash, redirect, render_template, request, session, abort, Response
import grpc
import os
import lock_pb2
import lock_pb2_grpc
import RPi.GPIO as GPIO 
import numpy as np
import board
import neopixel
from concurrent import futures
from threading import Thread, currentThread, Event    # Multi-threading
import shlex, subprocess
import KEYPAD as keypad
import LED as led
# import STRIP as strip
import ULTRASONIC as sonic
import grpc
import lock_pb2
import lock_pb2_grpc
import UTILS as utils
from imutils.video import VideoStream
from imutils.video import FPS
from nn import find_face
import imutils
import cv2 as opencv
import urllib.request
import io
import picamera
import logging
import socketserver
from http import server
from imutils.video.pivideostream import PiVideoStream
from threading import Condition

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
output = None


 
class Glock(object):
    def __init__(self):
        self.code = utils.get_code()
        print("CURRENT CODE:", self.code)

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
        self.bytes = None
        self.key = None
        self.fps = None
        self.result_count = None
        self.frame_counter = 0
        self.verification_frame_count = 0


        # NeoPixel Setup
        self.pixel_pin = board.D21
        self.num_pixels = 60
        self.ORDER = neopixel.GRB
        self.pixels = neopixel.NeoPixel(self.pixel_pin, self.num_pixels, brightness=0.2, auto_write=False,
                                   pixel_order=self.ORDER)

        #setup GPIO pins
        self.GPIO_TRIGGER = 5 
        self.GPIO_ECHO = 6
        self.GPIO_STRIKE = 26
        self.LED_PIN = 25
           
        #set GPIO direction (IN / OUT)
        #GPIO SETUP
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.GPIO_TRIGGER, GPIO.OUT)
        GPIO.setup(self.GPIO_ECHO, GPIO.IN)
        GPIO.setup(self.GPIO_STRIKE, GPIO.OUT)
        GPIO.setup(self.LED_PIN,GPIO.OUT) # LED pin


    def distance(self):
        #set Trigger to HIGH
        GPIO.output(self.GPIO_TRIGGER, True)
                    
        # set Trigger after 0.01ms to LOW
        time.sleep(0.00001)
        GPIO.output(self.GPIO_TRIGGER, False)
                       
        StartTime = time.time()
        StopTime = time.time()
                                           
        # save StartTime
        while GPIO.input(self.GPIO_ECHO) == 0:
            StartTime = time.time()
                                                   
        # save time of arrival
        while GPIO.input(self.GPIO_ECHO) == 1:
            StopTime = time.time()
                                                                                    
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


        self.pixels.fill((0, 225, 0))
        for i in range(60):
            self.pixels[i] = (0, 125, 0)
            self.pixels.show()
            time.sleep(.01)

        for i in range(60):
            self.pixels[60-i-1] = (0, 50, 0)
            self.pixels.show()
            time.sleep(.01)


    def led_unlock_fail(self):
        #stop idle led to allow for RED light
        if self.idle_stop_signal!=None:
            self.idle_stop_signal.set()
            self.idle_thread.join()

        for eek in range(3):
            for i in range(20):
                self.pixels.fill((225-i, 0, 0))
                self.pixels.show()
                time.sleep(.0005)
        time.sleep(.5)


    def restart_idle(self):
        #Function to restart IDLE LED Thread
        time.sleep(1)

        self.idle_stop_signal = Event()
        self.idle_blue_signal.clear()
        self.idle_thread = Thread(target=self.idle)

        self.idle_thread.start()


    def idle(self):
        print("starting IDLE LED thread")
        #Process to  pulse either white or blue 
        while not self.idle_stop_signal.wait(0):
            if self.idle_blue_signal.isSet():
                for i in range(60):
                    self.pixels[i] = (0, 0, 125)
                    self.pixels.show()
                    time.sleep(.01)

                for i in range(60):
                    self.pixels[60-i-1] = (0, 0, 50)
                    self.pixels.show()
                    time.sleep(.01)
            else:
                for i in range(60):
                    self.pixels[i] = (125, 125, 125)
                    self.pixels.show()
                    time.sleep(.01)

                for i in range(60):
                    self.pixels[60-i-1] = (50, 50, 50)
                    self.pixels.show()
                    time.sleep(.01)


    def Validated(self):
        #add mutex on gpio ops?
        #activate strike for 10 sec
        GPIO.output(self.GPIO_STRIKE,GPIO.HIGH)
        self.led_unlock_success() #light LEDs

        time.sleep(16)
        GPIO.output(self.GPIO_STRIKE,GPIO.LOW)
        print("GLOCK STRIKE ACTIVATED")
        

    def Invalidated(self):
        #add mutex on gpips?
        self.led_unlock_fail()



    def setup_stream(self):
        global output

        while not self.stream_stop_signal.wait(0):
            with picamera.PiCamera(resolution='640x480', framerate=24) as self.camera:
                # server = StreamingServer(('0.0.0.0', 8000), StreamingHandler)
                # server_thread = Thread(target=server.serve_forever)
                output = StreamingOutput()
                #Uncomment the next line to change your Pi's Camera rotation (in degrees)
                #camera.rotation = 90
                # camera.start_preview()
                self.camera.start_recording(output, format='mjpeg', splitter_port=1, quality=0)
                time.sleep(_ONE_DAY_IN_SECONDS)
        self.camera.stop_recording()


    def CameraHandler(self):
        print("Starting CameraHandler...")
        while not self.camera_stop_signal.wait(0):
            if (self.verification_frame_count % 3 == 0):
                self.camera.capture("test_image.jpg", format='jpeg', use_video_port=True, splitter_port=2, quality=100)
                # camera.capture('foo' + str(count) +'.jpg', use_video_port=True, splitter_port=2, quality=100)
                # print(image[1])
                # print(np.shape(image))
                # print(self.camera.resolution)
                # temp_image = opencv.imread("test_image.jpg")
                # opencv.imshow("Frame", temp_image)
                # # time.sleep(2)
                # opencv.waitKey(1) & 0xFF
                # opencv.destroyAllWindows()
                result = find_face("test_image.jpg")
                if result == 0:
                    print("NO FACE FOUND")
                    continue
                elif result == -1:
                    print("INCORRECT FACE FOUND")

                elif result == 1:

                    print("RESIDENT FACE FOUND")
                self.result_count += 1
                if (self.result_count == 2): 
                    self.Validated()
                    self.ran_validation = True
                    return

                elif (self.result_count == -2):
                    self.Invalidated()
                    self.ran_validation = True
                    return

                else:
                    continue
            self.verification_frame_count += 1
            # count +=1
            # #call verification on captured image

           




    def KeypadHandler(self):
        print("Enter KeypadHandler")

        code_as_list = list(self.code)
        #create empty buffer for entered code
        entered_code = list()
        new_code_list = list()
        code_active = False # flag for signaling when input seq ready 
        reset_active = False
        looking_new_code = False

        while not self.kp_stop_signal.wait(0):
            keys = self.keypad.pressed_keys
            if len(keys) != 1: continue #eliminate multi press

            if looking_new_code and keys == ['#']:
                new_code_list = list()

            elif keys == ['*']: #input is reset and now look for code
                entered_code = list()
                new_code_list = list()

                code_active = True 
                reset_active = False
                looking_new_code = False

                self.idle_blue_signal.clear()
            #reset master key code
            elif keys == ['#']:
                self.idle_blue_signal.set()

                entered_code = list()
                new_code_list = list()
                code_active = False
                reset_active = True
                looking_new_code = False


            elif reset_active:
                new_code_list += keys
                if looking_new_code:
                    if len(code_as_list) == len(new_code_list): #get new code 
                        print("new_code",new_code_list)

                        as_string = [str(elem) for elem in new_code_list]   
                        print(as_string)
                        as_string = ''.join(as_string)  

                        #update code variavles 
                        self.code = as_string
                        utils.change_code(as_string) 
                        code_as_list = new_code_list
                        print(self.code) 

                        #flash blue


                        new_code_list = list()
                        looking_new_code = False
                        reset_active = False

                        self.idle_blue_signal.clear()

                elif len(code_as_list) == len(new_code_list): #submit old code for verification
                    verification_res = (new_code_list == [int(i) for i in code_as_list]) #verify list
                    print("old_code", new_code_list, "verified", str(verification_res))
                    
                    if verification_res:
                        looking_new_code = True
                        #flash blue
                        # time.sleep(1)
                        # time.sleep(1)
                        self.Validated()
                    else:
                        #flash red
                        self.Invalidated()
                    
                    self.ran_validation = True

                    new_code_list = list()


            elif code_active:
                    entered_code += keys #add key to code
                    if len(code_as_list) == len(entered_code): #submit code for verification
                        code_active = False
                        print("code", entered_code)
                        verification_res = (entered_code == [int(i) for i in code_as_list]) #verify list
                        if verification_res == True:
                            print("Validated")
                            self.Validated()
                        else:
                            print("Invalidated")
                            self.Invalidated()


                        self.ran_validation = True
            else:
                continue
     
            print("code", entered_code)
            print("reset_code", new_code_list)

            time.sleep(0.2)


    def MainHandler(self):
        print("Enter Main")
        # distances = [1000,1000,1000] #track last three disances 

        #create queue of seen distances
        distances = [0,0]
        d_count = 0 
        d_max = 0 
        while not self.main_stop_signal.wait(0):
            print('loop')
            time.sleep(1)
            distance = self.distance()
            distances[d_count%2] = distance
            d_count += 1
            print ("Measured Distance = %.1f cm" % distance)
            print(self.system_active_idle)
            print(self.ran_validation)
            if(max(distances) < 60 and self.system_active_idle==False): #start process for camera and LED
                self.system_active_idle=True

                self.restart_idle()

                self.kp_stop_signal = Event()
                self.kp_thread = Thread(target=self.KeypadHandler)
                self.kp_thread.start()

                self.camera_stop_signal = Event()
                self.camera_thread = Thread(target=self.CameraHandler)
                self.camera_thread.start()


                print("idlewake")
            elif(max(distances)<60 and self.ran_validation==True):

                #clear pixels
                self.pixels.fill((0, 0, 0))
                self.pixels.show()

                #restart the killed idle thread

                self.restart_idle()

                self.ran_validation = False

            elif(max(distances) > 60 and self.system_active_idle==True): #close ML and turn off LED
                self.system_active_idle=False

                self.idle_blue_signal.clear()
                self.idle_stop_signal.set()
                self.kp_stop_signal.set()
                self.camera_stop_signal.set()

                self.idle_thread.join()


                self.kp_thread.join()
                print("kp joined")

                self.camera_thread.join()
                print("camera joined")

                self.pixels.fill((0, 0, 0))
                self.pixels.show()
        try:
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
        print("22222222222222222222222222222")

        self.keypad = keypad.keypad_setup()
        self.GPIO_TRIGGER, self.GPIO_ECHO = sonic.sonic_setup()


        print("33333333333333333333333333333333")


        # self.camera_stop_signal = Event()
        # self.camera_thread = Thread(target=self.CameraHandler)
        # self.camera_thread.start()

        print("44444444444444444444444444444444")


        self.main_stop_signal = Event()
        self.main_thread = Thread(target=self.MainHandler)
        self.main_thread.start()

        print("5555555555555555555555555")




    def stream_serve(self):
        p0 = subprocess.call(['sudo', 'pkill', 'uv4l']) #exit any hanging uv4l processes

        command = "sudo uv4l -nopreview --auto-video_nr --driver raspicam --encoding mjpeg --width 640 --height 480 --framerate 20 --server-option '--port=2020' --server-option '--max-queued-connections=30' --server-option '--max-streams=25' --server-option '--max-threads=29'"
        args = shlex.split(command)
        p1 = subprocess.Popen(args) #start streaming server 

        print("BEGIN UV4L STREAMING")


    def kill(self):
        self.killed = True

        print("stopping threads")
        # self.camera_stop_signal.set()


        self.main_stop_signal.set()

        # self.camera_thread.join()

        self.main_thread.join()


        #kill streaming server process
        print("Killing Stream Process")
        subprocess.call(['sudo', 'pkill', 'uv4l']) #exit any uv4l processes

        #clear pixels
        self.pixels.fill((0, 0, 0))
        self.pixels.show()


class GlockServer(lock_pb2_grpc.GLOCKServicer):
    def Unlock(self, request, context):
        print("RPC Server Received Unlock")
        # led.LED_on() #switch unlock 
        glock.Validated()
        glock.ran_validation = True
        # self.ran_validation = True/
        time.sleep(3)
        #     #clear pixels
        glock.pixels.fill((0, 0, 0))
        glock.pixels.show()
        return lock_pb2.GlockResponse(message='Server Unlocked Strike')

def serve(stop_signal):
    # s = currentThread()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    lock_pb2_grpc.add_GLOCKServicer_to_server(GlockServer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("RPC Server Started")

    while not stop_signal.isSet():
        print("not")

        time.sleep(_ONE_DAY_IN_SECONDS)
        continue
    print("rpcserver stop")
    server.stop(0) 


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
    channel = grpc.insecure_channel('192.168.1.56:50051')
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

@app.route('/video_feed')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')



class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
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


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True





if __name__ == '__main__':
    try:          
        rpc_stop_signal = Event()
        rpc_thread = Thread(target=serve, args=(rpc_stop_signal,))
        rpc_thread.start()
        glock = Glock()
        glock.run()
        
        app.secret_key = os.urandom(12)
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


    # try:
    #     # server_thread.start()
    #     # count = 0
    #     # while True:
    #     #     time.sleep(10)
    #     #     camera.capture('foo' + str(count) +'.jpg', use_video_port=True, splitter_port=2)
    #     #     count +=1
    # finally :

    # def CameraHandler(self):
    #     # initialize the video stream and allow the camera sensor to warm up
    #     print("Starting CameraHandler...")
    #     # vs = VideoStream(usePiCamera=True).start()
    #     # vs=cv2.VideoCapture('http://192.168.1.56:2020/video.mjpeg')

    #     self.stream = urllib.request.urlopen('http://192.168.1.56:2020/stream/video.mjpeg')

    #     # stream=open("192.168.1.56:2020/stream/video.mjpeg")

    #     self.bytes=b''
    #     time.sleep(2.0)
         
    #     # start the FPS counter
    #     self.fps = FPS().start()
    #     self.frame_counter += 1

    #     self.result_count = 0 #dont verfiy until three frames are in agreement
    #     while not self.camera_stop_signal.wait(0):
    #         # ret, frame = vs.read()
    #         # display the image to our screen
    #         # to read mjpeg frame -
    #         self.bytes+=self.stream.read(1024)
    #         a = self.bytes.find(b'\xff\xd8')
    #         b = self.bytes.find(b'\xff\xd9')
    #         if a!=-1 and b!=-1:
    #             jpg = self.bytes[a:b+2]
    #             self.bytes= self.bytes[b+2:]
    #             self.frame = opencv.imdecode(np.fromstring(jpg, dtype=np.uint8),opencv.IMREAD_COLOR)
    #             # we now have frame stored in frame.
    #             print(self.frame)
    #             window_name = "Frame" + str(self.frame_counter)
    #             opencv.imshow(window_name , self.frame)
    #             print("EEEEEEEEEEEEEEEEEE")

    #             self.key = opencv.waitKey(1) & 0xFF
    #             self.fps.update()
    #             opencv.destroyAllWindows()



    #         # update the FPS counter
    #         # result_count += find_face(frame)

    #         if (self.result_count == 3): 
    #             self.Validated()
    #             self.ran_validation = True
    #             return


    #         elif (self.result_count == -3):
    #             self.Invalidated()
    #             self.ran_validation = True
    #             return

    #         else:
    #             continue



    #     # stop the timer and display FPS information
    #     self.fps.stop()
    #     print("[INFO] elasped time: {:.2f}".format(self.fps.elapsed()))
    #     print("[INFO] approx. FPS: {:.2f}".format(self.fps.fps()))
         
    #     # do a bit of cleanup
    #     self.frame = None
    #     self.stream.close()

    # try:
    #     server_thread.start()

    #     while True:
    #         time.sleep(1)
    #         camera.capture(image, use_video_port=True, splitter_port=2)

    # finally :
    #     camera.stop_recording()
