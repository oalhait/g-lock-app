import time
import RPi.GPIO as GPIO 
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


_ONE_DAY_IN_SECONDS = 60 * 60 * 24


#GPIO SETUP
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

 
class Glock(object):
    def __init__(self):
        self.code = utils.get_code()
        print(self.code)

        self.keypad = None

        self.killed = False 
        self.stream_process = None


        self.kp_thread = None
        self.main_thread = None
        self.idle_thread = None


        self.kp_stop_signal = None
        self.main_stop_signal = None
        self.idle_stop_signal = None
        self.idle_blue_signal = Event()

        self.system_active_idle = False
        self.ran_validation = False


        # Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
        # NeoPixels must be connected to D10, D12, D18 or D21 to work.
        self.pixel_pin = board.D21

        # The number of NeoPixels
        self.num_pixels = 60

        # The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
        # For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
        self.ORDER = neopixel.GRB

        self.pixels = neopixel.NeoPixel(self.pixel_pin, self.num_pixels, brightness=0.2, auto_write=False,
                                   pixel_order=self.ORDER)

        self.GPIO_TRIGGER = 5 
        self.GPIO_ECHO = 6
        self.GPIO_STRIKE = 26
        self.LED_PIN = 25
           
        #set GPIO direction (IN / OUT)
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


    def unlock_success(self):
        print("unlock_success")

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





    def unlock_fail(self):
        #pulse three on fail
        print("unlock_fail")

        if self.idle_stop_signal!=None:
            self.idle_stop_signal.set()
            self.idle_thread.join()

        for eek in range(3):
            for i in range(20):
                self.pixels.fill((225-i, 0, 0))
                self.pixels.show()
                time.sleep(.0005)
        time.sleep(.5)



    def new_code_set(self):
        #pulse three on fail
        print("new code pend")

        for eek in range(3):
            for i in range(20):
                self.pixels.fill((0, 0, 225-i))
                self.pixels.show()
                time.sleep(.0005)
        time.sleep(.5)


    def restart_idle(self):
        time.sleep(1)

        self.idle_stop_signal = Event()
        self.idle_blue_signal.clear()
        self.idle_thread = Thread(target=self.idle)

        self.idle_thread.start()


    def idle(self):
        print("eek9")

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
        self.unlock_success()

        # GPIO.output(self.LED_PIN,GPIO.HIGH)
        # time.sleep(5)
        # GPIO.output(self.LED_PIN,GPIO.LOW)
        # print("Validated End")
        # print("Validated End")
        # if from_rpc:
        #     time.sleep(3)
        #     #clear pixels
        #     self.pixels.fill((0, 0, 0))
        #     self.pixels.show()
        

    def Invalidated(self):
        #add mutex on gpips?
        self.unlock_fail



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
                # self.new_code_set()
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
                        # self.new_code_set()


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
                        # self.new_code_set()
                        # time.sleep(1)
                        # self.new_code_set()
                        # time.sleep(1)
                        # self.new_code_set()
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

                self.idle_thread.join()


                self.kp_thread.join()

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


        self.stream_serve()

        self.keypad = keypad.keypad_setup()
        self.GPIO_TRIGGER, self.GPIO_ECHO = sonic.sonic_setup()

        self.main_stop_signal = Event()
        self.main_thread = Thread(target=self.MainHandler)
        self.main_thread.start()



    def stream_serve(self):
        p0 = subprocess.call(['sudo', 'pkill', 'uv4l']) #exit any hanging uv4l processes

        command = "sudo uv4l -nopreview --auto-video_nr --driver raspicam --encoding mjpeg --width 640 --height 480 --framerate 20 --server-option '--port=9090' --server-option '--max-queued-connections=30' --server-option '--max-streams=25' --server-option '--max-threads=29'"
        args = shlex.split(command)
        p1 = subprocess.Popen(args) #start streaming server 


    def kill(self):
        self.killed = True

        print("stopping threads")
        self.kp_stop_signal.set()
        self.main_stop_signal.set()

        self.kp_thread.join()
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


if __name__ == '__main__':
    try:          
        rpc_stop_signal = Event()
        rpc_thread = Thread(target=serve, args=(rpc_stop_signal,))
        rpc_thread.start()
        glock = Glock()
        glock.run()
        print("running1")
    except KeyboardInterrupt:
        print("main key KeyboardInterrupt")
        rpc_stop_signal.set()
        # rpc_thread.server_alive = False
        rpc_thread.join()
        print("joined")
        glock.kill()

