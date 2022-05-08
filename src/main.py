import pyaudio
import time
import soundfile as sf
from scipy.io import wavfile
from scipy import signal
from statsmodels.tsa import stattools
import numpy as np
import librosa

def vocoder_frame(voice_frame: np.array, excitation_frame:np.array, order: int, apply_filter: bool = True, apply_window: bool = True):
    # Verify if both the voice and the excitation frames have the same length
    if len(voice_frame) != len(excitation_frame):
        raise ValueError('Voice and excitation frames must have the same length')
    
    # Get the frame size
    frame_size = len(voice_frame)

    # Estimate the short-time autocorrelation of the given data
    rxx = signal.correlate(voice_frame, voice_frame, method='fft')

    # Extract only the needed lags
    rxx = rxx[len(rxx) // 2 : len(rxx) // 2 + order + 1] / rxx[0]

    # Use the Levinson-Durbin algorithm to find the error filter coefficients
    _, ao, _, J, _ = stattools.levinson_durbin(rxx, nlags=len(rxx)-1, isacov=True)
    predictor_coeff = -ao
    error_coeff = np.concatenate(([1.0], predictor_coeff))

    # Filter
    if apply_filter == True:
        y = signal.lfilter([1.0], error_coeff, excitation_frame)
    else:
        y = excitation_frame
    if apply_window == True:
        y = y * signal.windows.hann(frame_size)
    return y

# TODO Search if we can use the user data to avoid using global variables
# and if not, then create a class with our processing algorithm, and that
# would fix it
def input_processing_callback(in_data, frame_count, time_info, status):
    global excitation, x, y, data, frame_index, output, output_stream

    start_time = time.time()

    # Read data
    # Shift older data to the left and push the new window
    x = np.roll(x, -FRAME_SIZE)
    x[FRAME_SIZE:] = np.frombuffer(in_data, dtype=np.float32)
    
    # Send data to the output, this has to go here to avoid jitter and extra latency
    # in the output signal cause by the algorithm execution time
    data = np.append(data, x[FRAME_SIZE:])
    output = np.append(output, y[:FRAME_SIZE])
    output_stream.write(y[:FRAME_SIZE].astype(np.float32).tostring())
    y = np.roll(y, -FRAME_SIZE)
    y[FRAME_SIZE:] = np.zeros((FRAME_SIZE))

    # Process the overlapped segment using the previous window
    y_frame = vocoder_frame(
        x[FRAME_SIZE // 2:FRAME_SIZE // 2 + FRAME_SIZE],
        excitation[frame_index * (FRAME_SIZE // 2):frame_index * (FRAME_SIZE // 2) + FRAME_SIZE],
        ORDER
    )
    frame_index = frame_index + 1
    y[FRAME_SIZE // 2:FRAME_SIZE // 2 + FRAME_SIZE] += y_frame

    # Process the current window
    y_frame = vocoder_frame(
        x[FRAME_SIZE:],
        excitation[frame_index * (FRAME_SIZE // 2):frame_index * (FRAME_SIZE // 2) + FRAME_SIZE],
        ORDER
    )
    frame_index = frame_index + 1
    y[FRAME_SIZE:] += y_frame

    #y = np.append(y, excitation[frame_index * FRAME_SIZE:frame_index * FRAME_SIZE + FRAME_SIZE])
    #y = np.append(y, y_frame)

    end_time = time.time()
    processing_time = end_time - start_time
    print(f'Took {processing_time}')

    return (in_data, pyaudio.paContinue)

# Parameters needed to configure the streams
SAMPLE_RATE = 48000
CHANNELS = 1
SAMPLE_WIDTH_IN_BYTES = 4
ORDER = 48
FRAME_TIME = 10e-3
FRAME_SIZE = int(FRAME_TIME * SAMPLE_RATE)

# Initializations
p = pyaudio.PyAudio()                            # PyAudio Instance
x = np.zeros((FRAME_SIZE * 2), dtype=np.float32) # Stores the previous input window and has space to insert the new window to simplify
y = np.zeros((FRAME_SIZE * 2), dtype=np.float32) # Stores the data being fed to the output and data being written by the processing
output = np.array([], dtype=np.float32)
data = np.array([], dtype=np.float32)
frame_index = 0
    
# Load the the excitation
# TODO
excitation = np.random.normal(0, 0.01, size=10 * SAMPLE_RATE)

# Fetch devices' information and parameters from the PyAudio API, we can select
# to use the default input/output devices or allow the user to choose some of the 
# other available devices
devices_count = p.get_device_count()
devices_info = [p.get_device_info_by_index(i) for i in range(devices_count)]
default_input_device = p.get_default_input_device_info()
default_output_device = p.get_default_output_device_info()

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
    stream_callback=input_processing_callback
)
input_stream.start_stream()

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

# TODO
time.sleep(5)
input_stream.stop_stream()
input_stream.close()
output_stream.stop_stream()
output_stream.close()
sf.write('output.wav', output, SAMPLE_RATE, subtype='FLOAT')
sf.write('data.wav', data, SAMPLE_RATE, subtype='FLOAT')

# Clean up the resources taken from the system by PyAudio
p.terminate()