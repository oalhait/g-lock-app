from flask import Flask, flash, redirect, render_template, request, session, abort
import grpc
import os

import lock_pb2
import lock_pb2_grpc

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



class VideoCamera(object):
    def __init__(self):
        self.vs = PiVideoStream().start()
        time.sleep(2.0)

    def __del__(self):
        self.vs.stop()

    def get_frame(self):
        frame = self.flip_if_needed(self.vs.read())
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()

video_camera = VideoCamera(flip=True) # creates a camera object, flip vertically

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(video_camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(host='0.0.0.0', debug=True, use_reloader=True)





#login from https://pythonspot.com/login-authentication-with-flask/