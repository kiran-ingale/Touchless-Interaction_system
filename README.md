🖐️ Touchless Interaction System

A real-time computer vision system that enables users to control their computer using hand gestures without physical contact.
This project uses advanced hand tracking to provide a natural and intuitive interaction experience for both general computer control and presentations.

🚀 Features

🎯 Cursor control using hand movement

🖱️ Left click functionality

✍️ Drag and text selection

🔍 Zoom in / Zoom out

📊 Presentation control using gestures

🖐️ Fully touchless and real-time interaction

🧠 Technologies Used

Python

OpenCV – Video processing

MediaPipe – Hand tracking and landmark detection

PyAutoGUI – System control automation

🏗️ System Architecture

Video Capture – Webcam captures live frames

Hand Detection – MediaPipe detects hand landmarks

Feature Extraction – Fingertip coordinates are extracted

Gesture Recognition – Finger states and distances are analyzed

Action Execution – Commands executed using PyAutoGUI

🖐️ Gesture Controls
🎯 Cursor Control

Index Finger Up → Move Cursor

🖱️ Mouse Actions

Thumb + Index Pinch → Left Click

Hold Thumb + Index Pinch → Drag / Select Text

🔍 Zoom Controls

Pinch In (Thumb + Index Close) → Zoom Out

Spread Thumb + Index → Zoom In

⚙️ System Control

Closed Fist → Exit Application

📊 Presentation Controls

Swipe Right → Next Slide

Swipe Left → Previous Slide

Open Palm → Start / Pause Presentation

⚡ Key Design Decisions

Avoided gesture conflicts for smooth interaction

Maintained index finger for stable cursor control

Used simple and intuitive gestures

Focused on real-time responsiveness

💻 Installation
1. Clone the repository
git clone https://github.com/your-username/touchless-interaction-system.git
cd touchless-interaction-system
2. Create virtual environment (recommended)
3. Install dependencies
pip install opencv-python mediapipe pyautogui
▶️ How to Run
python controller.py

Ensure webcam is connected

Perform gestures in front of the camera

Keep hand clearly visible

🧪 Tips for Best Performance

Use good lighting

Avoid cluttered background

Keep hand within camera frame

Move smoothly for better accuracy

📌 Applications

Smart classrooms

Business presentations

Accessibility systems

Human-Computer Interaction research

Touchless environments

🔮 Future Enhancements / In Progress

🖱️ Right Click Gesture Implementation

🖱️ Double Click Gesture Optimization

🤖 Improve gesture accuracy using deep learning

🗣️ Voice + gesture integration

👥 Multi-user support

🕶️ AR/VR interaction

👩‍💻 Author

Developed by Kiran
