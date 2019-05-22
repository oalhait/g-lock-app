# Download the helper library from https://www.twilio.com/docs/python/install
from twilio.rest import Client
# import boto
# import boto.s3
# import sys
# from boto.s3.connection import S3Connection
# from boto.s3.key import Key

# Your Account Sid and Auth Token from twilio.com/console
# DANGER! This is insecure. See http://twil.io/secure
# AWS_ACCESS_KEY_ID = 'ACb951bc7639f942010d564c7b73e328ba'
# AWS_SECRET_ACCESS_KEY = '175fde8e1e3aef96d715bda163df83ff'

# bucket_name = 'glock-photos'
# REGION_HOST = 's3.us-east-2.amazonaws.com'
# conn = boto.connect_s3(AWS_ACCESS_KEY_ID,
#         AWS_SECRET_ACCESS_KEY, host=REGION_HOST)


# # bucket = conn.create_bucket(bucket_name,
#     # location=boto.s3.connection.Location.DEFAULT)
# bucket = conn.get_bucket(bucket_name, validate=False)

# testfile = "/Users/oalhait/Desktop/Spring 19/Capstone/g-lock-app/facerecognition/dataset/omar/0.jpg"
# print('Uploading %s to Amazon S3 bucket %s' % \
#    (testfile, bucket_name))

# def percent_cb(complete, total):
#     sys.stdout.write('.')
#     sys.stdout.flush()


# k = Key(bucket)
# k.key = 'my test file'
# k.set_contents_from_filename(testfile,
#     cb=percent_cb, num_cb=10, )



numbers_to_message = ['+14088886246', '+14158141829', '+15017122661']
for number in numbers_to_message:
    client.messages.create(
        body = 'Failed recognition at your front door! Click to see: http://g-lock.com/stream',
        from_ = '+18054161977',
        to = 'number'
    )


