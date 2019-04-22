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

if __name__ == '__main__':
	app.secret_key = os.urandom(12)
	app.run(host='0.0.0.0', debug=True, use_reloader=True)




#login from https://pythonspot.com/login-authentication-with-flask/