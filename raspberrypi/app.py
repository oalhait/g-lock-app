from flask import Flask, flash, redirect, render_template, request, session, abort, Response
import grpc
import os
import cv2
import picamera
import io
from imutils.video.pivideostream import PiVideoStream
from threading import Condition
from threading import Thread, currentThread, Event    # Multi-threading
import imutils
import time
import lock_pb2
import lock_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
output = None
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
        print("Ee")
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



def setup_stream(stop_signal):
    global output

    while not stop_signal.wait(0):
        with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
            # server = StreamingServer(('0.0.0.0', 8000), StreamingHandler)
            # server_thread = Thread(target=server.serve_forever)
            output = StreamingOutput()
            #Uncomment the next line to change your Pi's Camera rotation (in degrees)
            #camera.rotation = 90
            # camera.start_preview()
            camera.start_recording(output, format='mjpeg', splitter_port=1, quality=0)

            count = 0
            while True:
                time.sleep(3)

                # camera.capture('foo' + str(count) +'.jpg', use_video_port=True, splitter_port=2, quality=100)
                count +=1
            time.sleep(_ONE_DAY_IN_SECONDS)
    camera.stop_recording()


    # try:
    #     # server_thread.start()
    #     # count = 0
    #     # while True:
    #     #     time.sleep(10)
    #     #     camera.capture('foo' + str(count) +'.jpg', use_video_port=True, splitter_port=2)
    #     #     count +=1
    # finally :


if __name__ == '__main__':
    try:      

        stop_signal = Event()
        stream_thread = Thread(target=setup_stream, args=(stop_signal,))
        stream_thread.start()
        app.secret_key = os.urandom(12)
        # video_camera = VideoCamera() # creates a camera object, flip vertically

        app.run(host='0.0.0.0', debug=True, use_reloader=False, threaded=True)
    except KeyboardInterrupt:
        stop_signal.set()
        stream_thread.join()
        # video_camera.vs.stop()

#login from https://pythonspot.com/login-authentication-with-flask/

# class StreamingHandler(server.BaseHTTPRequestHandler):
#     def do_GET(self):
#         if self.path == '/':
#             self.send_response(301)
#             self.send_header('Location', '/index.html')
#             self.end_headers()
#         elif self.path == '/index.html':
#             content = PAGE.encode('utf-8')
#             self.send_response(200)
#             self.send_header('Content-Type', 'text/html')
#             self.send_header('Content-Length', len(content))
#             self.end_headers()
#             self.wfile.write(content)
#         elif self.path == '/stream.mjpg':
#             self.send_response(200)
#             self.send_header('Age', 0)
#             self.send_header('Cache-Control', 'no-cache, private')
#             self.send_header('Pragma', 'no-cache')
#             self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
#             self.end_headers()
#             try:
#                 while True:
#                     with output.condition:
#                         output.condition.wait()
#                         frame = output.frame
#                     self.wfile.write(b'--FRAME\r\n')
#                     self.send_header('Content-Type', 'image/jpeg')
#                     self.send_header('Content-Length', len(frame))
#                     self.end_headers()
#                     self.wfile.write(frame)
#                     self.wfile.write(b'\r\n')
#             except Exception as e:
#                 logging.warning(
#                     'Removed streaming client %s: %s',
#                     self.client_address, str(e))
#         else:
#             self.send_error(404)
#             self.end_headers()

# class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
#     allow_reuse_address = True
#     daemon_threads = True


# class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
#     allow_reuse_address = True
#     daemon_threads = True


# class VideoCamera(object):
#     def __init__(self):
#         self.vs = PiVideoStream().start()
#         time.sleep(2.0)

#     def get_frame(self):
#         frame = self.vs.read()
#         ret, jpeg = cv2.imencode('.jpg', frame)
#         return jpeg.tobytes()

#             try:
#                 while True:
#                     with output.condition:
#                         output.condition.wait()
#                         frame = output.frame
#                 yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

#             except Exception as e:
#                 logging.warning(
#                     'Removed streaming client %s: %s',
#                     self.client_address, str(e))
