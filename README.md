# Stanford Quadruped

## Overview
This repository hosts the code for Stanford Pupper and Stanford Woofer, Raspberry Pi-based quadruped robots that can trot, walk, and jump. 

![pupper-hero](https://github.com/user-attachments/assets/9fb4e451-7c53-4799-b0da-cb8f90fd1488)


Video of pupper in action: https://youtu.be/NIjodHA78UE

Project page: https://stanfordstudentrobotics.org/pupper

Documentation & build guide: https://pupper-independent-study.readthedocs.io/en/latest/index.html

## How it works
![Overview diagram](imgs/diagram1.jpg)
The main program is ```run_djipupper.py``` which is located in this directory. The robot code is run as a loop, with a joystick interface, a controller, and a hardware interface orchestrating the behavior. 

The joystick interface is responsible for reading joystick inputs and converting them into a generic robot ```command``` type. The controller does the bulk of the work, switching between states (trot, walk, rest, etc) and generating servo position targets. A detailed model of the controller is shown below. The third component of the code, the hardware interface, generates messages that are sent to the Teensy board, these can be either control commands or updates to configuration.
![Controller diagram](imgs/diagram2.jpg)
This diagram shows a breakdown of the robot controller. Inside, you can see four primary components: a gait scheduler (also called gait controller), a stance controller, a swing controller, and an inverse kinematics model. 

The gait scheduler is responsible for planning which feet should be on the ground (stance) and which should be moving forward to the next step (swing) at any given time. In a trot for example, the diagonal pairs of legs move in sync and take turns between stance and swing. As shown in the diagram, the gait scheduler can be thought of as a conductor for each leg, switching it between stance and swing as time progresses. 

The stance controller controls the feet on the ground, and is actually quite simple. It looks at the desired robot velocity, and then generates a body-relative target velocity for these stance feet that is in the opposite direction as the desired velocity. It also incorporates turning, in which case it rotates the feet relative to the body in the opposite direction as the desired body rotation. 

The swing controller picks up the feet that just finished their stance phase, and brings them to their next touchdown location. The touchdown locations are selected so that the foot moves the same distance forward in swing as it does backwards in stance. For example, if in stance phase the feet move backwards at -0.4m/s (to achieve a body velocity of +0.4m/s) and the stance phase is 0.5 seconds long, then we know the feet will have moved backwards -0.20m. The swing controller will then move the feet forwards 0.20m to put the foot back in its starting place. You can imagine that if the swing controller only put the leg forward 0.15m, then every step the foot would lag more and more behind the body by -0.05m. 

Both the stance and swing controllers generate target positions for the feet in cartesian coordinates relative the body center of mass. It's convenient to work in cartesian coordinates for the stance and swing planning, but we now need to convert them to motor angles. This is done by using an inverse kinematics model, which maps between cartesian body coordinates and motor angles. These motor angles, also called joint angles, are then populated into the ```state``` variable and returned by the model. 


## How to Build Pupper
Main documentation: https://pupper-independent-study.readthedocs.io/en/latest/index.html

You can find the bill of materials, pre-made kit purchasing options, assembly instructions, software installation, etc at this website.


## Help
- Feel free to raise an issue (https://github.com/stanfordroboticsclub/StanfordQuadruped/issues/new/choose) or email me at nathankau [at] stanford [dot] edu
- We also have a Google group set up here: https://groups.google.com/forum/#!forum/stanford-quadrupeds


## Using DJI Pupper
### Connecting to Pupper
The first time that you use pupper, if it has not previously been connected to your wifi network, you can connect to pupper using the USB C port on it's back.

* Go to your network settings
* Click the cog next to the wired connection
* Go to IPV4 tab
* Select link-local only
* Apply
* Then toggle the connection OFF then ON
* you should now be able to ssh to the raspberry pi with ssh pi@raspberrypi.local, password 'raspberry'.
* You can then connect the pupper to wifi if you don't want to have the USB tether to the robot.

### Connect pupper to wifi
* sudo raspi-config
* System options
* S1 Wireless LAN
* Enter SSID and password for you wifi network
  
### Set up
* Clone this repo and checkout this branch ("current_hw_version")

### First Time Setup
* Plug the Teensy into your computer and figure out which tty device it is.
  * It shows up on my computer as "/dev/ttyACM0" but it can vary
  * Run `ls /dev | grep ttyACM
  * Update `SERIAL_PORT` in `djipupper/IndividualConfig.py` with the specific port name

### Homing Pupper
Before powering on Pupper, it should be placed into its zero position.
* The zero position is shown in the images below.
* The hip joints should be square to the body, the feet and the knees should be pressed into the ground.
* Powering up pupper will start the homing routine, the initial joint state is saved and each joint' zero position is calculated based on this starting state. The legs will then slowly move up into their 'ready' pose. Hip abduction should be 45 degrees out, and the thigh links should be horizontal.
* From this point you can start to send commands to pupper.
* This process should be repeated before powering on Pupper, every time.

![IMG_6059](https://github.com/user-attachments/assets/8f40d252-f12a-4b13-aba9-aa9ade0dfecf)
![IMG_6060](https://github.com/user-attachments/assets/5ace4df8-d6d7-4cf0-b1c3-3c248a9fb421)

### Using DJI Pupper
* Place the robot into it's zero position
* Press the power button
* The robot will record it's zero position and slowly move into a 'ready' pose
* Power on the BetaFPV Lite 3 joystick by holding the central button, it should light up and play a small jingle. If the light is red, move the joystick levers until it turns blue.
* The controller launches on startup of the Pupper, with command:
  ```
  python3 run_djipupper.py
  ```
* The legs will twitch slightly, this signals that the controller is running on the raspberry pi and is ready to receive commands
* The joystick should be in startup position, this means that rocker buttons should be centered, SA and SD should be released, joystick analog levers should be centered. No commands will be sent to the robot until this start condition is met.
* Press 'SA' to activate the robot, it will move into a standing position
* Press 'SD' to switch to walking move
* Pressing rocker button 'SC' towards you will switch pupper to 'trot' mode
* Pressing 'SA' at any time will deactivate the robot and cause it to collapse

### Tuning
* You can mess with the cartesian PD control gains by changing values in `djipupper/HardwareConfig.py`
  * `MAX_CURRENT`: it's interesting to put it a little lower, like 4A, to test squishiness.
  * 'MAX_VELOCITY': Sets the fault velocity, if any actuator is found to be moving at or above this velocity, it will be send a 0 current command.
  * `CART_POSITION_KPS`: Stiffness in the x, y, z directions. I've found 400 - 4000 to be interesting values. 400 is quite loose while 4000-6000 is very stiff. Much higher (>6000) and you risk uncontrolled oscillations even with higher damping.
  * `CART_POSITION_KDS`: Damping in the x, y, z directions. 100 to 500 seems to be a good range. Use higher values when you're using higher stiffnesses to avoid oscillations, which totally does happen when you use, for example, kp=4000 and kd=1500.
  * 'LIMITED_CART_POSITION_KPS': This value is set when the robot switches from DEACTIVATED to STANDiNG state, as the joint angle change is large, leaving the default values can cause the robot to move very quickly. This value is reverted to the non limited value after standing state has been reached.
  * 'LIMITED_CART_POSITION_KDS': Same as the value above.
  * `POSITION_KP` and `POSITION_KD` unused for cartesian pd control.
* You can also mess with the usual values like x and y velocity, z_clearance (stepping height), etc in `djipupper/Config.py`

### Debug
To view the messages that the controller is sending to the robot, a script is provided to emulate a serial port.
ssh to the pupper, either connect via the USB C port on the pupper's back or if the pupper is powered on, you can connect over wifi,
On the Pupper:

```
cd StanfordQuadruped
sudo python3 serial_emulator.py

```
