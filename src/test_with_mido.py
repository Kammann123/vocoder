# Custom Libraries
import vocoder

# Third-Party Libraries
from scipy import signal
import pyaudio
import numpy as np
import mido

# Native-Python Libraries
debug = np.array([], dtype=np.float32)

def output_callback(in_data, frame_count, time_info, status):
    global excitation_frame, excitation_consumed, debug
    while excitation_consumed == True:
        pass
    excitation_consumed = True
    #debug = np.append(debug, excitation_frame[:FRAME_SIZE])
    return (excitation_frame[:FRAME_SIZE].astype(np.float32).tobytes(), pyaudio.paContinue)

# Parameters needed to configure the streams
SAMPLE_RATE = 48000
CHANNELS = 1
SAMPLE_WIDTH_IN_BYTES = 4
ORDER = 48
FRAME_TIME = 40e-3
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
    stream_callback=output_callback
)

# Using the MIDO library we can get what MIDI inputs are connected to the
# system and use any of them to open a MIDI connection.
# TODO Instead of choosing the default input (the first one) let the user choose
input_devices = mido.get_input_names()
input_port = mido.open_input()
excitation_frame = np.zeros((FRAME_SIZE * 3), dtype=np.float32)
STEP_SIZE = int(0.5 * FRAME_SIZE)
amplitude = 0
frequency = 0
i = 0
excitation_consumed = True

print(STEP_SIZE)

#input_stream.start_stream()
output_stream.start_stream()

# TODO Create a better user interface (not necessarily graphical)
# TODO Is it necessary to have a GUI?
while True:
    try:
        for message in input_port.iter_pending():
            if message.type == 'note_on':
                note = message.note
                amplitude = 1
                frequency = 440 * (2**((note - 69) / 12))
                count = 0
                print(f'Start note of {frequency} Hz')
            elif message.type == 'note_off':
                print(f'Stop note of {frequency} Hz')
                amplitude = 0
                frequency = 0
                count = 0

        if excitation_consumed == True:
            excitation_frame = np.roll(excitation_frame, -FRAME_SIZE)
            
            excitation_frame[FRAME_SIZE*2:] = np.zeros(FRAME_SIZE, dtype=np.float32)

            excitation_time = np.arange(FRAME_SIZE) / SAMPLE_RATE + i * STEP_SIZE / SAMPLE_RATE
            i = i + 1
            excitation_frame[FRAME_SIZE // 2 + FRAME_SIZE : FRAME_SIZE // 2 + FRAME_SIZE * 2] += amplitude * signal.square(2 * np.pi * frequency * excitation_time) * signal.windows.hann(FRAME_SIZE)

            excitation_time = np.arange(FRAME_SIZE) / SAMPLE_RATE + i * STEP_SIZE / SAMPLE_RATE
            i = i + 1
            excitation_frame[FRAME_SIZE * 2:] += amplitude * signal.square(2 * np.pi * frequency * excitation_time) * signal.windows.hann(FRAME_SIZE)

            excitation_consumed = False
    except KeyboardInterrupt:
        break

import soundfile as sf

sf.write('test.wav', debug, SAMPLE_RATE, subtype='FLOAT')
# Close MIDI ports
input_port.close()

# Close streams
output_stream.stop_stream()
output_stream.close()

# Clean up the resources taken from the system by PyAudio
p.terminate()