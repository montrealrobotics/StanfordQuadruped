# from pupper_controller.src.pupperv2 import pupper
from pupper_controller.src.pupperv3 import ros_interface
import math
import time
from absl import app
import json
import numpy as np
import time

def playback_joint_angles(filename):
    joint_angles = dict()

    interface = ros_interface.Interface(
            0, 0
        )

    with open(filename, "r") as f:
        joint_angles = json.load(f)

    prev = 0.
    
    cur_angles = None
    while True:
        interface.read_incoming_data()
        cur_angles = interface.robot_state.joint_angles
        # breakpoint()
        print(cur_angles)
        if isinstance(cur_angles, np.ndarray):
            if not np.any(cur_angles == None):
                break
        time.sleep(0.1)

    print("angs after waiting", cur_angles)

    t1 = time.time()

    for timestamp, angles in joint_angles.items(): 
        interpolation_steps = 50
        sleep_time = 5 * (float(timestamp)-prev) / interpolation_steps

        angles = np.array(angles)
        step_angles = (angles - cur_angles) / interpolation_steps

        last_time = time.time()
    
        for i in range(interpolation_steps):
            # print(f"Setting joint angles to {angles}")

            # flip the 0 and 1 columns of the angles
            
            # angles_flip = [[angles[:,3]], [angles[:,2]], [angles[:,1]], [angles[:,0]]]
            cur_angles = cur_angles + step_angles
            interface.set_joint_angles(cur_angles)
            # convert timestamp (a string) to a float
            # time.sleep(float(timestamp)-prev)
            while time.time() - last_time < sleep_time:
                continue
            last_time = time.time()
            # time.sleep(sleep_time)
            
        prev = float(timestamp)

    t2 = time.time()
    print("time to completion: ",t2 - t1)


# playback_joint_angles()

