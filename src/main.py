# Custom Libraries
import vocoder

# Third-Party Libraries
import pyaudio
import numpy as np

# Native-Python Libraries
import time

def stream_callback(in_data, frame_count, time_info, status):
    global v, output_stream
    # TODO Estimate the processing time to ensure there is no extra latency

    # TODO The excitation is limited to white gaussian noise
    # TODO We could select different types of inputs, such as MIDI
    out_data = v.process_frame(
        np.frombuffer(in_data, dtype=np.float32),
        np.random.normal(0, 0.01, size=FRAME_SIZE)
    )
    # TODO The user could be asked to record the output and save it as a WAV
    # TODO The user may want to send the output to a virtual microphone
    output_stream.write(out_data.astype(np.float32).tobytes())
    return (in_data, pyaudio.paContinue)

# Parameters needed to configure the streams
SAMPLE_RATE = 48000
CHANNELS = 1
SAMPLE_WIDTH_IN_BYTES = 4
ORDER = 48
FRAME_TIME = 10e-3
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
    stream_callback=stream_callback
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
    output_device_index=default_output_device['index']
)
output_stream.start_stream()

# TODO Create a better user interface (not necessarily graphical)
# TODO Is it necessary to have a GUI?
time.sleep(10)
input_stream.stop_stream()
input_stream.close()
output_stream.stop_stream()
output_stream.close()

# Clean up the resources taken from the system by PyAudio
p.terminate()