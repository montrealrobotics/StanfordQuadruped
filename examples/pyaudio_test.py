import pyaudio

def list_output_devices():
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info['maxOutputChannels'] > 0:
            print(f"Device {i}: {device_info['name']}")

    p.terminate()

list_output_devices()