import pyaudio
import time
import soundfile as sf
from scipy.io import wavfile
from scipy import signal
from statsmodels.tsa import stattools
import numpy as np
import librosa

def vocoder_frame(voice_frame: np.array, excitation_frame:np.array, order: int, apply_window: bool = False):
    # Verify if both the voice and the excitation frames have the same length
    if len(voice_frame) != len(excitation_frame):
        raise ValueError('Voice and excitation frames must have the same length')
    
    # Get the frame size
    frame_size = len(voice_frame)

    # Estimate the short-time autocorrelation of the given data
    rxx = signal.correlate(voice_frame, voice_frame, method='fft')

    # Extract only the needed lags
    rxx = rxx[len(rxx) // 2 : len(rxx) // 2 + order + 1] #/ rxx[0]

    # Use the Levinson-Durbin algorithm to find the error filter coefficients
    _, ao, _, J, _ = stattools.levinson_durbin(rxx, nlags=len(rxx)-1, isacov=True)
    predictor_coeff = -ao
    error_coeff = np.concatenate(([1.0], predictor_coeff))

    # Filter
    y = signal.lfilter([1], error_coeff, excitation_frame)
    if apply_window == True:
        y = y * signal.windows.hann(frame_size)
    return y

def stream_callback(in_data, frame_count, time_info, status):
    global excitation, x, y, frame_index
    # Convert the byte buffer to a float representation
    parsed_data = np.frombuffer(in_data, dtype=np.float32)
    # x = np.append(x, parsed_data)
    y_frame = vocoder_frame(
        parsed_data,
        excitation[frame_index * FRAME_SIZE:frame_index * FRAME_SIZE + FRAME_SIZE],
        ORDER
    )
    frame_index = frame_index + 1
    #y = np.append(y, excitation[frame_index * FRAME_SIZE:frame_index * FRAME_SIZE + FRAME_SIZE])
    y = np.append(y, y_frame)
    return (in_data, pyaudio.paContinue)

# Parameters needed to configure the streams
SAMPLE_RATE = 48000
CHANNELS = 1
SAMPLE_WIDTH_IN_BYTES = 4
ORDER = 48
FRAME_TIME = 10e-3
FRAME_SIZE = int(FRAME_TIME * SAMPLE_RATE)

# Load the the excitation
# TODO
excitation, _ = librosa.load('assets/excitation.wav', sr=48000)

# Initializations
p = pyaudio.PyAudio()               # PyAudio Instance
x = np.array([], dtype=np.float32)  # Array to store input data
y = np.array([], dtype=np.float32)  # Array to store output data
frame_index = 0

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
stream = p.open(
    rate=SAMPLE_RATE,
    channels=CHANNELS,
    format=p.get_format_from_width(SAMPLE_WIDTH_IN_BYTES),
    input=True,
    output=False,
    frames_per_buffer=FRAME_SIZE,
    input_device_index=default_input_device['index'],
    stream_callback=stream_callback
)
stream.start_stream()

# TODO
time.sleep(10)
stream.stop_stream()
stream.close()
sf.write('sound.wav', y, SAMPLE_RATE)

# Clean up the resources taken from the system by PyAudio
p.terminate()