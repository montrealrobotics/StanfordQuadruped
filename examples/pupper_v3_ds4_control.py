from pupper_controller.src.pupperv3 import pupper, ros_joystick_interface
import time
import argparse
# from StanfordQuadruped.examples.playback_joint_angles import playback_joint_angles
#from examples.playback_joint_angles import playback_joint_angles
from rclpy.node import Node
import os
import random
import pyaudio
import wave
import numpy as np
import sys

sys.path.insert(0, '/home/pi/StanfordQuadruped/examples')

from playback_joint_angles import playback_joint_angles

DEFAULT_X_SHIFT = -0.0095#-0.035
DEFAULT_TROT_HEIGHT = -0.12

def run_example(half_robot=False):
    joystick = ros_joystick_interface.Joystick()

    pup = pupper.Pupper(half_robot=half_robot)
    pup.reset()

    print("starting...")
    # pup.slow_stand(min_height=-0.08, duration=1.0, do_sleep=True)
    last_control = pup.time()
    com_x_shift = DEFAULT_X_SHIFT
    height = DEFAULT_TROT_HEIGHT
    filtered_control_rate = 200.0 # 100.0
    alpha = 0.95
    cur_angley = 0

    try:
        while True:
            # Busy-wait until it's time to run the control loop again
            while pup.time() - last_control < pup.config.dt:
                # Reduce sleep time if your sim runs > 10x realtime
                time.sleep(0.0001)
            filtered_control_rate = alpha * filtered_control_rate + \
                (1-alpha) / (pup.time() - last_control)
            last_control = pup.time()
            print("Ticks: ", pup.state.ticks, "Update Rate: ", filtered_control_rate)

            # Run the control loop
            observation = pup.get_observation()
            joystick_vals = joystick.joystick_values()
            
            # ALL CONTROLS
            if joystick_vals["triangle"] > 0: # BARK
                sound_idx = random.randint(1, 4)
                play_sound(f"/home/pi/StanfordQuadruped/examples/sounds/dog_sounds_{sound_idx}.wav")     
            elif joystick_vals["L2"] < 0: # WALK
                behavior_state_override = "trot"
            elif joystick_vals["circle"] > 0: # RIGHT WAVE
                playback_joint_angles("/home/pi/StanfordQuadruped/right_wave.json")
            elif joystick_vals["square"] > 0: # LEFT WAVE
                playback_joint_angles("/home/pi/StanfordQuadruped/left_wave.json")
            elif joystick_vals["x"] > 0: # STAND UP
                playback_joint_angles("/home/pi/StanfordQuadruped/standup3.json")
            # elif joystick_vals["R2"] > 0: # LISTEN
            #     print("Pupper is listening")
            #     for i in range(10000000000):
            #         print(i)
            else:
                behavior_state_override = "rest" # DO NOTHING
            
            com_x_shift += -1.0 * joystick_vals["d_pad_y"] * pup.config.dt / 100.0
            com_x_shift = min(max(com_x_shift, -0.05), 0.05)
            com_x_shift = DEFAULT_X_SHIFT

            # CHANGE HEIGHT
            height += (
                (-joystick_vals["L1"] + joystick_vals["R1"]
                 ) * pup.config.dt / 25.0
            )
            height = min(max(height, -0.25), -0.05)

            print("stepping...")

            pup.step(
                action={
                    "x_velocity": joystick_vals["left_y"] / 2.0,#1.5,
                    "y_velocity": -joystick_vals["left_x"] / 4.0,#1.5,
                    "yaw_rate": joystick_vals["right_x"] * -3.0,#-4,
                    "pitch": joystick_vals["right_y"] * 0.5,
                    "height": height,
                    "com_x_shift": com_x_shift,
                },
                behavior_state_override=behavior_state_override,
            )
            # print("Foot coordinates: \n", pup.state.final_foot_locations)

    finally:
        pup.shutdown()

def play_sound(file_path, volume=2.0, output_device_index=None):
    if not os.path.exists(file_path):
        print(f"Error: The file {file_path} does not exist.")
        return

    # Open the sound file
    wf = wave.open(file_path, 'rb')
    
    # Create an audio stream
    p = pyaudio.PyAudio()
    
    print("Opening audio stream...")
    player_stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                           channels=wf.getnchannels(),
                           rate=48000,
                           output=True,
                           output_device_index=2)

    print(f"Playing {file_path} with volume {volume}...")

    # Read data in chunks
    data = wf.readframes(1024)

    # Play the sound by writing the audio data to the stream
    while data:
        # Convert byte data to numpy array
        audio_data = np.frombuffer(data, dtype=np.int16)

        # Amplify audio data
        audio_data = np.int16(audio_data * volume)

        # Convert back to byte data
        data = audio_data.tobytes()

        player_stream.write(data)
        data = wf.readframes(1024)

    # Stop and close the stream
    player_stream.stop_stream()
    player_stream.close()
    
    # Close PyAudio
    p.terminate()
    print("Finished playing.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--half", action="store_true", help="Enable flag half")
    args = parser.parse_args()
    run_example(half_robot=args.half)
