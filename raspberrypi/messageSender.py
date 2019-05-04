import requests
from flask import Flask
from flask import request
from flask import send_from_directory
from twilio import twiml

from martianify import martianify

UPLOAD_FOLDER = '/path/to/your/project/'

# App declaration and configuration
app = Flask(__name__)
app.config


# SMS/MMS Request URL
@app.route('/sms', methods=['POST', 'GET'])
def sms():
    response = twiml.Response()

    response.message("Please wait for launch 3, 2, 1...")

    if request.form['NumMedia'] != '0':
        filename = request.form['MessageSid'] + '.jpg'
        f = open(filename, 'wb')
        f.write(requests.get(request.form['MediaUrl0']).content)
        f.close()
        martianify('{}/{}'.format(UPLOAD_FOLDER, filename))

        with response.message() as message:
            message.body = "{0}".format("Welcome to Mars.")
            message.media('http://YourNgrokURL/uploads/{}'.format(filename))
    else:
        response.message("Face forward and text me a selfie!")

    return str(response)


# Martian Media URL
@app.route('/uploads/<filename>', methods=['GET', 'POST'])
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER,
                               filename)

if __name__ == "__main__":
    app.run()