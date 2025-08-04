
import os
import cv2


os.environ['DISPLAY'] = ':0' #required for headless, raspbery connect

stream = cv2.VideoCapture(index=8)
if not stream.isOpened():
    raise ValueError("Failed to open camera")

stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while True:
    result, frame = stream.read()  
    if result is False:
        print("Failed to read frame, no video feed")
        break 
    cv2.imshow("USB Camera Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

if stream is not None:
    stream.release()
    stream = None
else:
    raise ValueError("Failed to open camera")
