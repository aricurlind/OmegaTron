
# Omega‑Tron – Autonomous Robot Vehicle  



Omega‑Tron is an autonomous robot vehicle developed as part of the M4000 project at Munich University of Applied Sciences.  
The system integrates **lane detection**, **obstacle avoidance**, **object detection**, **robot‑arm control**, **navigation**, and **inductive charging** into one modular platform powered by a Raspberry Pi 4B and Arduino Nano.

![Omega Tron Logo](doc\vids_pics\Logo1.png) ![Omega Tron](doc\vids_pics\OmegaTron.jpg)

---

## Project Overview  
Omega‑Tron demonstrates how modern autonomous‑driving concepts can be implemented in a compact robotic system.  
The robot can:

- Detect and follow lanes  
- Avoid obstacles using 5 ultrasonic sensors  
- Identify objects (4 types of waste) using YOLOv3  
- Pick up objects with a 4‑DOF robot arm  
- Navigate using ROS odometry  
- Automatically dock to a charging station using a QR‑code marker  

![Modules](doc\vids_pics\Modules.png)
---

## System Architecture  
The project is divided into several functional modules:

- **Lane Detection**  
- **Obstacle Avoidance**  
- **Object Detection**  
- **Robot Arm Control**  
- **Navigation & ROS**  
- **Inductive Charging**  

---

## Hardware Components  
- Raspberry Pi 4B (Master)  
- Arduino Nano (Slave for ultrasonic sensors)  
- 5× HC‑SR04 ultrasonic sensors  
- JOY‑IT DC gear motors  
- Arduino Motor Shield L293D  
- PCA9685 servo driver  
- MG996R / MG905 servos  
- Raspberry Pi Camera  
- Inductive charging coil + QR‑code marker  

---

## Software Stack  
- Python (OpenCV, NumPy, Pytorch, Pygame, Serial)  
- YOLOv3 for object detection  
- PyTorch for CNN and lane detection 
- TorchVision (image transforms & datasets)
- ROS (Odometry + Mapping)  
- Arduino C++ for sensor control  
- AMSpi library for motor control  

---

## Repository Structure  
```plaintext
Omega-Tron/
│
├── motor_control/        # AMSpi + motor driver scripts
├── obstacle_avoidance/   # USS master + Arduino slave
├── lane_detection/       # Classical + CNN lane detection
├── object_detection/     # YOLOv3 integration
├── robot_arm/            # PCA9685 + servo control
├── navigation/           # ROS odometry + mapping
└── docs/                 # Project report, diagrams, images
```

---

## Lane Detection  
### Classical Approach  

![LaneDetection1](doc\vids_pics\LaneDetection1.png)

- Canny edge detection  
- Bird’s‑eye transformation  
- Histogram‑based lane center estimation  
- Hough transform for line detection  

![LaneDetection1_Video](doc\vids_pics\Media1.mp4)

### Deep Learning Approach  
- Data collection during driving  
- CNN training on lane images  
- Output: steering angle prediction  

![LaneDetection2](doc\vids_pics\LaneDetection2.png) ![LaneDetection3](doc\vids_pics\LaneDetection3.png)

![LaneDetection4](doc\vids_pics\LaneDetection4.png)
![LaneDetection5](doc\vids_pics\LaneDetection5.png)

![LaneDetection2_Video](doc\vids_pics\Media2.mp4)
![LaneDetection3_Video](doc\vids_pics\Media3.mp4)

---

## Obstacle Avoidance  

![DistanceSensors2](doc\vids_pics\DistanceSensors2.png) 

- 5 ultrasonic sensors controlled by Arduino Nano  
- Encoded distance values sent to Raspberry Pi  
- Python master interprets sensor data  
- Motor control decisions via AMSpi  


---

## Object Detection  

![WasteDetection](doc\vids_pics\WasteDetection.png) 

YOLOv3 identifies trash objects and provides bounding boxes.  
Detected coordinates are forwarded to the robot arm module.

---

## Robot Arm  

![RobotArm](doc\vids_pics\Arm1.png) 


- 4 degrees of freedom  
- MG996R / MG905 servos  
- PCA9685 for precise PWM control  
- Automated grasping based on object position  

![RobotArm_Video](doc\vids_pics\Media4.mp4) 

---

## Inductive Charging  
- Battery monitoring via GPIO  
- ROS navigation to charging station  
- Final alignment using QR‑code detection  

---

## 👥 Authors  
- Arlind Çurumi       - Team and SW Lead
- Christoph Häußler   - HW Integration Lead
- Jiang Qi Qiu  
- Ismail Güney  
- Munich University of Applied Sciences – Faculty of Mechanical Engineering - Mechatronics Laboratory
