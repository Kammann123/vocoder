# Custom Libraries
import vocoder
import synthesizer
import gui

# Third-Party Libraries
import pyaudio
import numpy as np
import mido

# Native-Python Libraries
import queue

def on_output_frame(in_data, frame_count, time_info, status):
    global output_queue
    if output_queue.empty() == True:
        buffer = np.zeros((FRAME_SIZE), dtype=np.float32)
    else:
        buffer = output_queue.get()
    return (buffer.astype(np.float32).tobytes(), pyaudio.paContinue)

def on_input_frame(in_data, frame_count, time_info, status):
    voice_queue.put(np.frombuffer(in_data, dtype=np.float32))
    return (in_data, pyaudio.paContinue)



def start_vocoder(input_device, output_device, midi_device):
    global input_stream, output_stream, input_port, output_queue, s, vocoder_running

    # Choose a specific input device and create a stream to start reading
    # audio samples from it, using the non-blocking method (callback)
    selected_input_device = list(filter(lambda device: device['name'] == input_device, devices_info))[0]
    input_stream = p.open(
        rate=SAMPLE_RATE,
        channels=CHANNELS,
        format=p.get_format_from_width(SAMPLE_WIDTH_IN_BYTES),
        input=True,
        output=False,
        frames_per_buffer=FRAME_SIZE,
        input_device_index=selected_input_device['index'],
        stream_callback=on_input_frame
    )

    # Choose a specific output device and create a stream to start sending
    # audio samples to it, using the non-blocking method (callback)
    selected_output_device = list(filter(lambda device: device['name'] == output_device, devices_info))[0]
    output_stream = p.open(
        rate=SAMPLE_RATE,
        channels=CHANNELS,
        format=pyaudio.paFloat32,
        input=False,
        output=True,
        frames_per_buffer=FRAME_SIZE,
        #output_device_index=virtual_mic['index'],
        output_device_index=selected_output_device['index'],
        stream_callback=on_output_frame
    )
    
    input_port = mido.open_input(midi_device)

    # Initialize the output queue
    output_queue.put(np.zeros((FRAME_SIZE), dtype=np.float32))

    # Start the streams
    input_stream.start_stream()
    output_stream.start_stream()

    vocoder_running = True


def stop_vocoder():
    global input_stream, output_stream, input_port, output_queue, vocoder_running

    # Close streams
    input_stream.stop_stream()
    input_stream.close()
    output_stream.stop_stream()
    output_stream.close()

    vocoder_running = False


# Parameters needed to configure the streams
SAMPLE_RATE = 48000
CHANNELS = 1
SAMPLE_WIDTH_IN_BYTES = 4
ORDER = 48
FRAME_TIME = 60e-3                              # Audio Buffer Duration
FRAME_SIZE = int(FRAME_TIME * SAMPLE_RATE)
WINDOW_TIME = 20e-3                              # Vocoder Processing Duration
WINDOW_SIZE = int(WINDOW_TIME * SAMPLE_RATE)
PRE_EMPHASIS = 0.97
VOICE_THRESHOLD_dB = -40

# Initializations
p = pyaudio.PyAudio()                                               # PyAudio Instance
v = vocoder.Vocoder(WINDOW_SIZE, ORDER, PRE_EMPHASIS)               # Vocoder Instance
s = synthesizer.Synthesizer(FRAME_SIZE, SAMPLE_RATE)                # Synthesizer Instance
vocoder_running = False
input_stream = None
output_stream = None

# Create the needed queues
voice_queue = queue.Queue()
output_queue = queue.Queue()
excitation_queue = queue.Queue()

# Fetch devices' information and parameters from the PyAudio API, we can select
# to use the default input/output devices or allow the user to choose some of the 
# other available devices
devices_count = p.get_device_count()
devices_info = [p.get_device_info_by_index(i) for i in range(devices_count)]
virtual_mic = list(filter(lambda device: device['name'] == "CABLE Input (VB-Audio Virtual C", devices_info))[0]
default_input_device = p.get_default_input_device_info()
default_output_device = p.get_default_output_device_info()


# Using the MIDO library we can get what MIDI inputs are connected to the
# system and use any of them to open a MIDI connection.
midi_devices = mido.get_input_names()

input_list = [ device['name'] for device in filter(lambda device: device['maxInputChannels'] > 0, devices_info) ]
output_list = [ device['name'] for device in filter(lambda device: device['maxOutputChannels'] > 0, devices_info) ]

threshold_queue = queue.Queue()
volume_queue = queue.Queue()
application = gui.App(  start_vocoder, stop_vocoder, volume_queue, threshold_queue,
                        input_list, output_list, midi_devices, input_list,
                        default_input_device['name'], default_output_device['name']
                        )
application.start()

while True:
    while vocoder_running == True:
        try:
            if not threshold_queue.empty():
                VOICE_THRESHOLD_dB = float(threshold_queue.get())
            if voice_queue.empty() == False and excitation_queue.empty() == False:
                voice_frame = voice_queue.get()
                excitation = excitation_queue.get()
                output_frame = np.zeros(voice_frame.shape, dtype=np.float32)
                voice_windows = np.split(voice_frame, FRAME_SIZE // WINDOW_SIZE)
                excitation_windows = np.split(excitation, FRAME_SIZE // WINDOW_SIZE)
                for index, voice_window in enumerate(voice_windows):
                    voice_level = voice_window.std()
                    voice_level_dB = 20 * np.log10(voice_level)
                    excitation_window = excitation_windows[index] if voice_level_dB > VOICE_THRESHOLD_dB else np.zeros(WINDOW_SIZE)
                    output_window = v.process_frame(
                        voice_window,
                        #np.random.normal(0, 0.03, size=WINDOW_SIZE),
                        excitation_window,
                    )
                    output_frame[index * WINDOW_SIZE:(index + 1) * WINDOW_SIZE] = output_window
                    volume_queue.put(voice_level_dB)

                output_queue.put(output_frame)
            elif excitation_queue.empty() == True:
                generated_frame = s.generate_frame()
                excitation_queue.put(generated_frame)
                
            for message in input_port.iter_pending():
                if message.type == 'note_on':
                    s.note_on(0.008, 440 * (2**((message.note - 69) / 12)))
                elif message.type == 'note_off':
                    s.note_off(440 * (2**((message.note - 69) / 12)))
                    
        except KeyboardInterrupt:
            break
    
# Clean up the resources taken from the system by PyAudio
p.terminate()