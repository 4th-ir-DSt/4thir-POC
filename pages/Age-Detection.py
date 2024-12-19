import streamlit as st
import cv2
import numpy as np
from PIL import Image

def ui():
    st.markdown(
        '<link href="https://cdnjs.cloudflare.com/ajax/libs/mdbootstrap/4.19.1/css/mdb.min.css" rel="stylesheet">',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" '
        'integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" '
        'crossorigin="anonymous">',
        unsafe_allow_html=True,
    )
    
    hide_streamlit_style = """
                <style>
                    header{visibility:hidden;}
                    .main {
                        margin-top: -20px;
                        padding-top:10px;
                    }
                    #MainMenu {visibility: hidden;}
                    footer {visibility: hidden;}
                    .reportview-container {
                        padding-top: 0;
                    }
                    .loan-summary {
                        background-color: white;
                        padding: 20px;
                        color:black;
                        border-radius: 5px;
                        box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    }
                    .loan-summary h1 {
                        color: #4267B2;
                        font-size: 24px;
                        margin-bottom: 20px;
                    }
                    .loan-summary h2 {
                        color: #4267B2;
                        font-size: 18px;
                        margin-top: 15px;
                        margin-bottom: 10px;
                    }
                    .loan-summary hr {
                        margin: 15px 0;
                    }
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    st.markdown(
        """
        <nav class="navbar fixed-top navbar-expand-lg navbar-dark" style="background-color: #4267B2;">
        <a class="navbar-brand" href="#"  target="_blank">Age and Gender Detection</a>  
        </nav>
    """,
        unsafe_allow_html=True,
    )
ui()

# Load models

faceProto = r"api/models/opencv_face_detector.pbtxt"
faceModel = r"api/models/opencv_face_detector_uint8.pb"
ageProto = r"api/models/age_deploy.prototxt"
ageModel = r"api/models/age_net.caffemodel"
genderProto = r"api/models/gender_deploy.prototxt"
genderModel = r"api/models/gender_net.caffemodel"

MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
genderList = ['Male', 'Female']

# Load networks
faceNet = cv2.dnn.readNet(faceModel, faceProto)
ageNet = cv2.dnn.readNet(ageModel, ageProto)
genderNet = cv2.dnn.readNet(genderModel, genderProto)

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
            cv2.rectangle(frameOpencvDnn, (x1, y1), (x2, y2), (0, 255, 0), int(round(frameHeight/150)), 8)
    return frameOpencvDnn, faceBoxes

def detect_age_gender(image):
    # Ensure image is in RGB format
    if image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    elif len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    padding = 20
    resultImg, faceBoxes = highlightFace(faceNet, image)
    
    if not faceBoxes:
        return resultImg, []
    
    results = []
    for faceBox in faceBoxes:
        face = image[max(0, faceBox[1]-padding):
                     min(faceBox[3]+padding, image.shape[0]-1),
                     max(0, faceBox[0]-padding):
                     min(faceBox[2]+padding, image.shape[1]-1)]

        blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
        
        genderNet.setInput(blob)
        genderPreds = genderNet.forward()
        gender = genderList[genderPreds[0].argmax()]
        
        ageNet.setInput(blob)
        agePreds = ageNet.forward()
        age = ageList[agePreds[0].argmax()]
        
        label = f'{age}'
        cv2.putText(resultImg, label, (faceBox[0], faceBox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
        results.append(label)
    
    return resultImg, results

def main():

    col1,col2 = st.columns(2)
    
    option = st.radio("Choose input method:", ("Upload Image", "Capture Image"))

    if option == "Upload Image":
        
        process_uploaded_image()
    elif option == "Capture Image":
        process_captured_image()

    

def process_uploaded_image():
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        img_array = np.array(image)
        process_image(img_array)

def process_captured_image():
    captured_image = st.camera_input("Capture an image")
    if captured_image is not None:
        image = Image.open(captured_image)
        img_array = np.array(image)
        process_image(img_array)

def process_image(img_array):
    result_img, results = detect_age_gender(img_array)
    st.image(result_img, channels="BGR", use_column_width=True,width=10)
    
    if results:
        st.write("Detection Results:")
        for result in results:
            st.markdown(f"""<div class="blockquote note alert-success">{result}</div>""",unsafe_allow_html=True)
    else:
        st.write("No faces detected in the image.")

if __name__ == "__main__":
    main()