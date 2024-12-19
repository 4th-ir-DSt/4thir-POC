from fastapi import FastAPI, UploadFile, File
import cv2
import numpy as np
from PIL import Image
import io

app = FastAPI()

# Load models
faceProto = r"models/opencv_face_detector.pbtxt"
faceModel = r"models/opencv_face_detector_uint8.pb"
ageProto = r"models/age_deploy.prototxt"
ageModel = r"models/age_net.caffemodel"

MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']

# Load networks
faceNet = cv2.dnn.readNet(faceModel, faceProto)
ageNet = cv2.dnn.readNet(ageModel, ageProto)

def highlightFace(net, frame, conf_threshold=0.7):
    frameOpencvDnn = frame.copy()
    frameHeight = frameOpencvDnn.shape[0]
    frameWidth = frameOpencvDnn.shape[1]
    blob = cv2.dnn.blobFromImage(frameOpencvDnn, 1.0, (300, 300), [104, 117, 123], True, False)

    net.setInput(blob)
    detections = net.forward()
    faceBoxes = []
    
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            x1 = int(detections[0, 0, i, 3] * frameWidth)
            y1 = int(detections[0, 0, i, 4] * frameHeight)
            x2 = int(detections[0, 0, i, 5] * frameWidth)
            y2 = int(detections[0, 0, i, 6] * frameHeight)
            faceBoxes.append([x1, y1, x2, y2])
            
    return faceBoxes

def detect_age(image):
    # Ensure image is in RGB format
    if image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
    elif len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    
    padding = 20
    faceBoxes = highlightFace(faceNet, image)
    
    if not faceBoxes:
        return None
    
    # Process only the first face found
    faceBox = faceBoxes[0]
    face = image[max(0, faceBox[1]-padding):
                 min(faceBox[3]+padding, image.shape[0]-1),
                 max(0, faceBox[0]-padding):
                 min(faceBox[2]+padding, image.shape[1]-1)]

    blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
    
    ageNet.setInput(blob)
    agePreds = ageNet.forward()
    age = ageList[agePreds[0].argmax()]
    
    return age


