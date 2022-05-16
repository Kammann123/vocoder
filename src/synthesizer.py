# Third-Party Libraries
from scipy import signal
import numpy as np

# Native-Python Libraries

class Synthesizer:

    def __init__(self, frame_size: int, sample_rate: int):
        """ Initializes the Synthesizer instance
            :param frame_size: Size of the frames
            :param sample_rate: Sampling rate
        """
        # Initialization of internal parameters
        self.frame_size = frame_size
        self.sample_rate = sample_rate
        self.step_size = int(0.5 * frame_size)
        self.amplitude = 0.0
        self.frequency = 0.0
        self.step_index = 0

        # Buffer instantiation
        self.frames = np.zeros((frame_size * 3), dtype=np.float32)
    
    def set_amplitude(self, amplitude: float):
        """ Sets the waveform's amplitude
            :param amplitude: Amplitude of the waveform
        """
        if amplitude < 0.0:
            raise ValueError('The amplitude has to be a positive number')
        self.amplitude = amplitude
    
    def set_frequency(self, frequency: float):
        """ Sets the waveform's fundamental frequency
            :param frequency: Fundamental frequency of the waveform
        """
        if frequency < 0.0:
            raise ValueError('Invalid negative frequency value')
        self.frequency = frequency
    
    def generate_frame(self):
        """ Generates a new frame of the synthesized waveform
        """
        # The internal buffer named self.frames can contain up to three frames
        # [ f(n) | f(n+1) | f(n+2) ]. Each time the generate_frame() method is called
        # the f(n) frame is already ready to be consumed. The f(n+1) preparation is finished
        # for the next generation instant, while the f(n+2) preparation starts.
        generated_frame = np.copy(self.frames[:self.frame_size])

        # After creating a copy for the frame consumed, the buffer is shifted
        # to the left and cleaned to put the next frame to be consumed in place
        self.frames = np.roll(self.frames, -self.frame_size)
        self.frames[self.frame_size * 2:] = np.zeros((self.frame_size), dtype=np.float32)

        # Generates the overlapping samples of the waveform
        t = self._get_next_frame_time()
        self.frames[self.frame_size // 2 + self.frame_size : self.frame_size // 2 + self.frame_size * 2] += self.amplitude * signal.square(2 * np.pi * self.frequency * t) * signal.windows.hann(self.frame_size)

        # Generates the non-overlapping samples of the new frame
        t = self._get_next_frame_time()
        self.frames[self.frame_size * 2:] += self.amplitude * signal.square(2 * np.pi * self.frequency * t) * signal.windows.hann(self.frame_size)

        # Return the generated frame
        return generated_frame
    
    def _get_next_frame_time(self):
        """ Get the time interval for the next frame to be generated
        """
        excitation_time = np.arange(self.frame_size) / self.sample_rate + self.step_index * self.step_size / self.sample_rate
        self.step_index = self.step_index + 1
        return excitation_time
