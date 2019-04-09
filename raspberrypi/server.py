import time
import RPi.GPIO as GPIO 

from concurrent import futures
from threading import Thread, currentThread, Event    # Multi-threading
import shlex, subprocess
import grpc
import KEYPAD as keypad
import LED as led
import lock_pb2
import lock_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


#GPIO SETUP
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(25,GPIO.OUT) # LED pin

 
class Glock(object):
    def __init__(self,code):
        self.code = code
        self.keypad = None
        self.killed = False 
        self.stream_process = None

    def Unlock(self):
        pass

    def KeypadHandler(self):
        while True:
            if (self.killed): 
                print("handler exit")
                return #exit handler on glock kill 
                
            print("jeee")
            result = keypad.keypad_verify(self.code, self.keypad)
            print(result)
            if result == True:
                led.LED_on() #replace with swtich Unlock
        return

    def run(self):
        self.stream_serve()

        self.keypad = keypad.keypad_setup()
        print("running2")

        self.KeypadHandler()
        print("running3")



    def stream_serve(self):
        p0 = subprocess.call(['sudo', 'pkill', 'uv4l']) #exit any hanging uv4l processes

        command = "sudo uv4l -nopreview --auto-video_nr --driver raspicam --encoding mjpeg --width 640 --height 480 --framerate 20 --server-option '--port=9090' --server-option '--max-queued-connections=30' --server-option '--max-streams=25' --server-option '--max-threads=29'"
        args = shlex.split(command)
        p1 = subprocess.Popen(args) #start streaming server 


    def kill(self):
        self.killed = True
        #kill streaming server process
        print("Killing Stream Process")
        
        subprocess.call(['sudo', 'pkill', 'uv4l']) #exit any uv4l processes




class GlockServer(lock_pb2_grpc.GLOCKServicer):
    def Unlock(self, request, context):
        print("RPC Server Received Unlock")
        led.LED_on() #switch unlock 

        return lock_pb2.GlockResponse(message='Server Unlocked Strike')

def serve(stop_signal):
    # s = currentThread()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    lock_pb2_grpc.add_GLOCKServicer_to_server(GlockServer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("RPC Server Started")


    while not stop_signal.wait(0):
        continue
    print("rpcserver stop")
    server.stop(0) 

       # try:
    # while getattr(s, "server_alive", True):
    #     print("rpc working")
    #     time.sleep(_ONE_DAY_IN_SECONDS)
    # print("server stop")
    # server.stop(0)
    # except:
    #     print("rpcserve exception")
    #     server.stop(0)

    # try:
    #     while True:
    #         time.sleep(_ONE_DAY_IN_SECONDS)


if __name__ == '__main__':
    try:          
        stop_signal = Event()
        rpc_thread = Thread(target=serve, args=(stop_signal,))
        rpc_thread.start()
        glock = Glock("1234")
        glock.run()
        print("running1")
    except KeyboardInterrupt:
        print("main key KeyboardInterrupt")
        stop_signal.set()
        # rpc_thread.server_alive = False
        rpc_thread.join()
        print("joined")
        glock.kill()

