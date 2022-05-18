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
        self.step_index = 0

        # Buffer instantiation
        self.frames = np.zeros((frame_size * 3), dtype=np.float32)

        self.notes_playing = dict()
    
    def note_on(self, amplitude: float, frequency: float):
        """ Adds a new note to the dictionary of currently playing notes
            :param amplitude: Amplitude of the waveform
            :param frequency: Fundamental frequency of the waveform
        """
        if amplitude < 0.0:
            raise ValueError('The amplitude has to be a positive number')
        if frequency < 0.0:
            raise ValueError('Invalid negative frequency value')
        frequency = round(frequency, 3)     # Round float to get reliable comparisons
        self.notes_playing[frequency] = amplitude
    
    def note_off(self, frequency: float) -> bool:
        """ Removes note from the dictionary of currently playing notes
            :param frequency: Fundamental frequency of the waveform
            :return: True if value was succesfully removed, False otherwise
        """
        if frequency < 0.0:
            raise ValueError('Invalid negative frequency value')
        frequency = round(frequency, 3)     # Round float to get reliable comparisons
        result = self.notes_playing.pop(frequency, None)
        return result != None

    def SincM(self, x, M):
        """ SincM function from: https://ccrma.stanford.edu/~stilti/papers/blit.pdf
            :param x: Array of x values
            :param M: Number of harmonics to preserve
            :return: Array containing the resulting waveform
        """
        return np.sin(np.pi*x) / (M * np.sin(np.pi*x / M))

    def generate_waveform(self, time: np.array) -> np.array:
        """ Generates a waveform from the currently playing notes at the specified times
            :param time: Array of time samples
            :return: Array containing the resulting waveform
        """
        waveform = np.zeros_like(time)
        for freq, amp in self.notes_playing.items():
            #waveform += amp * signal.square(2 * np.pi * freq * time)

            P = self.sample_rate / freq
            M = 2 * P//2 + 1
            waveform += amp * (M/P)*self.SincM((M/P) * time / self.sample_rate)
        return waveform
    
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
        self.frames[self.frame_size // 2 + self.frame_size : self.frame_size // 2 + self.frame_size * 2] += self.generate_waveform(t) * signal.windows.hann(self.frame_size)

        # Generates the non-overlapping samples of the new frame
        t = self._get_next_frame_time()
        self.frames[self.frame_size * 2:] += self.generate_waveform(t) * signal.windows.hann(self.frame_size)

        # Return the generated frame
        return generated_frame
    
    def _get_next_frame_time(self):
        """ Get the time interval for the next frame to be generated
        """
        excitation_time = np.arange(self.frame_size) / self.sample_rate + self.step_index * self.step_size / self.sample_rate
        self.step_index = self.step_index + 1
        return excitation_time
