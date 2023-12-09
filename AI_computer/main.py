import mediapipe as mp
import cv2
import numpy as np
import uuid
import os
from matplotlib import pyplot as plt
from gtts import gTTS
import pygame
import time
import socket
import threading

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    END = '\033[0m'

HOST = '10.244.84.105'  # 서버에 출력되는 IP를 입력하세요
PORT = 7672

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client_socket.connect((HOST, PORT))
except ConnectionError as e:
    print(f"{Colors.YELLOW}[Socket]{Colors.END}{Colors.RED}[Error] {e}{Colors.END}")
    exit()

def recv_data(client_socket):
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            print(f"{Colors.YELLOW}[Socket] {Colors.END}{Colors.BLUE}Received: {Colors.END}{Colors.WHITE}{repr(data.decode())}{Colors.END}")
        except ConnectionError as e:
            print(f"{Colors.YELLOW}[Socket]{Colors.END}{Colors.RED}[Error: receiving data]: {e}{Colors.END}")
            break

recv_thread = threading.Thread(target=recv_data, args=(client_socket,))
recv_thread.start()
print(f'{Colors.YELLOW}[Socket] {Colors.END}{Colors.BLUE}Connected to the Server{Colors.END}')

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands
cap = cv2.VideoCapture(0)
hand_way="None"
mode="normal"
send_angle=[]
temp_arr=[]
joint_list = [[1,5,6],[0,9,10],[0,13,14],[0,17,18],[7,6,5],[11,10,9],[15,14,13],[19,18,17]]# [[4,3,2],[3,2,1],[2,1,0],[1,0,5],[8,7,6],[7,6,5],[6,5,0],[12,11,10],[11,10,9],[10,9,0],[16,15,14],[15,14,13],[14,13,0],[20,19,18],[19,18,17],[18,17,0]]          [1,5,6],[0,9,10],[0,13,14],[0,17,18]

def draw_finger_angles(image, results, joint_list):
    cnt=0
    # Loop through hands
    for hand in results.multi_hand_landmarks:
        global send_angle,temp_arr
        temp_arr=[]
        #Loop through joint sets
        for joint in joint_list:
            a = np.array([hand.landmark[joint[0]].x, hand.landmark[joint[0]].y]) # First coord
            b = np.array([hand.landmark[joint[1]].x, hand.landmark[joint[1]].y]) # Second coord
            c = np.array([hand.landmark[joint[2]].x, hand.landmark[joint[2]].y]) # Third coord

            radians = np.arctan2(c[1] - b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
            angle = np.abs(radians*180.0/np.pi)

            if angle > 180.0:
                angle = 360-angle
            if cnt<4:
                angle=180-angle
            if cnt>=4:
                if angle>80:
                    angle=((180-angle)/100)*90
                elif angle<80:
                    angle=90
                angle=90-angle
                if angle<10:
                    angle=10
            angle=str(round(angle, 2))
            temp_arr.append(angle)
            cv2.putText(image, angle, tuple(np.multiply(b, [640, 480]).astype(int)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1 ,cv2.LINE_AA)
            cnt+=1
        send_angle=temp_arr
        message=f"action:{send_angle[0]}:{send_angle[1]}:{send_angle[2]}:{send_angle[3]}:{send_angle[4]}:{send_angle[5]}:{send_angle[6]}:{send_angle[7]}:0:0:0"
        client_socket.send(message.encode())
        print(f"{Colors.CYAN}[Detected the Hand]{Colors.END} {Colors.WHITE}angle: {send_angle}{Colors.END}")
    return image

with mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.5,max_num_hands=1) as hands: 
    while cap.isOpened():
        ret, frame = cap.read()
        
        # BGR 2 RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Flip on horizontal
        image = cv2.flip(image, 1)
        
        # Set flag
        image.flags.writeable = False
        # Detections
        results = hands.process(image)
        
        # Set flag to true
        image.flags.writeable = True
        
        # RGB 2 BGR
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Detections

        handway_result=results.multi_handedness
        if type(handway_result) is list:
            if "Right" in str(handway_result):
                hand_way="Right"
                # Rendering results
                if results.multi_hand_landmarks:
                    for num, hand in enumerate(results.multi_hand_landmarks):
                        mp_drawing.draw_landmarks(image, hand, mp_hands.HAND_CONNECTIONS, mp_drawing_styles.get_default_hand_landmarks_style(),mp_drawing_styles.get_default_hand_connections_style())
                    draw_finger_angles(image, results, joint_list)
            elif "Left" in str(handway_result):
                hand_way="Left"
        text = "DiSRHiT"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        font_color = (0,0,0)
        thickness = 2
        cv2.putText(image,"DiSRHiT", (540, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        text = "Mode: {}".format(mode)
        cv2.putText(image,text,(540,50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)
        if hand_way=="Right":
            text = "Hand: Right"
            font_color=(255,0,0)
        elif hand_way=="Left":
            text="Hand: Left"
            font_color=(0,0,255)
        else:
            text="Hand: None"
            font_color=(255,255,255)
        hand_way="None"
        cv2.putText(image,text,(540,65), cv2.FONT_HERSHEY_SIMPLEX, 0.4, font_color, 1)
        cv2.imshow("DiSRHiT", image)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
client_socket.close()