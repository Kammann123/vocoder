# Custom Libraries
import vocoder

# Third-Party Libraries
import pyaudio
import numpy as np
import mido

# Native-Python Libraries
import queue
import threading
import time

class RepeatTimer(threading.Timer):  
    def run(self):  
        while not self.finished.wait(self.interval):  
            self.function(*self.args,**self.kwargs)

def on_output_frame(in_data, frame_count, time_info, status):
    global output_queue
    while output_queue.empty() == True:
        pass
    out_frame = output_queue.get()
    return (out_frame.astype(np.float32).tobytes(), pyaudio.paContinue)

def on_input_frame(in_data, frame_count, time_info, status):
    voice_queue.put(np.frombuffer(in_data, dtype=np.float32))
    return (in_data, pyaudio.paContinue)

# Parameters needed to configure the streams
SAMPLE_RATE = 48000
CHANNELS = 1
SAMPLE_WIDTH_IN_BYTES = 4
ORDER = 48
FRAME_TIME = 20e-3
FRAME_SIZE = int(FRAME_TIME * SAMPLE_RATE)

# Initializations
p = pyaudio.PyAudio()                           # PyAudio Instance
v = vocoder.Vocoder(FRAME_SIZE, ORDER)          # Vocoder Instance

# Fetch devices' information and parameters from the PyAudio API, we can select
# to use the default input/output devices or allow the user to choose some of the 
# other available devices
devices_count = p.get_device_count()
devices_info = [p.get_device_info_by_index(i) for i in range(devices_count)]
default_input_device = p.get_default_input_device_info()
default_output_device = p.get_default_output_device_info()

# TODO The user may be asked what input device to use
# Choose a specific input device and create a stream to start reading
# audio samples from it, using the non-blocking method (callback)
selected_input_device = default_input_device
input_stream = p.open(
    rate=SAMPLE_RATE,
    channels=CHANNELS,
    format=p.get_format_from_width(SAMPLE_WIDTH_IN_BYTES),
    input=True,
    output=False,
    frames_per_buffer=FRAME_SIZE,
    input_device_index=default_input_device['index'],
    stream_callback=on_input_frame
)
input_stream.start_stream()

# TODO The user may be asked what output device to use
# Choose a specific output device and create a stream to start sending
# audio samples to it, using the non-blocking method (callback)
selected_output_device = default_output_device
output_stream = p.open(
    rate=SAMPLE_RATE,
    channels=CHANNELS,
    format=pyaudio.paFloat32,
    input=False,
    output=True,
    frames_per_buffer=FRAME_SIZE,
    output_device_index=default_output_device['index'],
    stream_callback=on_output_frame
)
output_stream.start_stream()

# Using the MIDO library we can get what MIDI inputs are connected to the
# system and use any of them to open a MIDI connection.
# TODO Instead of choosing the default input (the first one) let the user choose
input_devices = mido.get_input_names()
input_port = mido.open_input()

# Create the needed queues
voice_queue = queue.Queue()
excitation_queue = queue.Queue()
output_queue = queue.Queue()

def excitation_generator(excitation_queue):
    excitation_queue.put(np.random.normal(0, 0.01, size=FRAME_SIZE))

timer = RepeatTimer(10e-3, excitation_generator, [excitation_queue])
timer.start()

# TODO Create a better user interface (not necessarily graphical)
# TODO Is it necessary to have a GUI?
while True:
    try:
        if voice_queue.empty() == False and excitation_queue.empty() == False:
            voice_frame = voice_queue.get()
            excitation_frame = excitation_queue.get()
            output_frame = v.process_frame(
                voice_frame,
                excitation_frame
            )
            output_queue.put(output_frame)
    except KeyboardInterrupt:
        break
    
timer.cancel()

# Close MIDI ports
input_port.close()

# Close streams
input_stream.stop_stream()
input_stream.close()
output_stream.stop_stream()
output_stream.close()

# Clean up the resources taken from the system by PyAudio
p.terminate()