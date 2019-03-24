import cv2
import sys

# Get user supplied values
imagePath = sys.argv[1]
cascPath = "haarcascade_frontalface_default.xml"

# Create the haar cascade
faceCascade = cv2.CascadeClassifier(cascPath)

# Read the image
image = cv2.imread(imagePath)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Detect faces in the image
faces = faceCascade.detectMultiScale(
    gray,
    scaleFactor=1.1,
    minNeighbors=5,
    minSize=(30, 30)
    #flags = cv2.CV_HAAR_SCALE_IMAGE
)

print("Found {0} faces!".format(len(faces)))

#Resize image to 120 pixels

# Draw a rectangle around the faces
for (x, y, w, h) in faces:
	# extraw = (120 - w)//2
	# extrah = (120 - h)//2
	# newy = y - extrah
	# newx = x - extraw
	# cropped = gray[newy:newy+h+(2*extrah), newx:newx+w+(2*extraw)]
	cropped = gray[y:y+h, x:x+w]
	final = cv2.resize(cropped, (120,120))
	# cv2.rectangle(gray, (x, y), (x+w, y+h), (0, 255, 0), 2)

print(final)
cv2.imshow("Faces found", final)
cv2.waitKey(0)
