# Third-Party Libraries
import numpy as np
from scipy import signal
from statsmodels.tsa import stattools
import librosa

class Vocoder:

    def __init__(self, frame_size: int, order: int, alpha: float):
        """ Initializes the Vocoder instance.
            :param frame_size: Size of the frames
            :param order: Order of the articulatory filter whose parameters will be estimated
            :param alpha: Pre-emphasis filter coefficient
        """
        # Save the parameters of the vocoder
        self.frame_size = frame_size
        self.order = order
        self.alpha = alpha
        # Stores the previous input window and has space to insert the new window 
        # to simplify how the math is taken during the processing (when the overlapped
        # window is needed)
        self.x = np.zeros((frame_size * 2), dtype=np.float32)
        # Stores the data being fed to the output and data being written by 
        # the processing algorithm with the new input data
        self.y = np.zeros((frame_size * 2), dtype=np.float32)
        # Store the excitation samples
        self.excitation = np.zeros((frame_size * 2), dtype=np.float32)

    def process_frame(self, voice_frame: np.array, excitation_frame: np.array) -> np.array:
        """ Process a new voice frame.
            :param voice_frame: Contains the voice samples
            :param excitation_frame: Contains the frame_samples
            :return: Output samples ready to be reproduced
        """
        # In self.x we have an array with space for two frames -> [ FRAME_SIZE | FRAME_SIZE ]
        # and its status to this point is [ x(n-2) | x(n-1) ]. So, first the data is shifted to
        # the left and replaced with the new data. Finally, we have [ x(n-1) | x(n) ]. The time
        # isn't the sampling time, it's the framing time.
        # Why do we need this? When we use 50% overlap, each incoming data window has to be used 
        # (at least part of its data) three times. You'll process a segment which overlaps with 
        # the previous window, a segment which has no overlap (uses only this window) and a segment
        # which overlaps with the future window.
        self.x = np.roll(self.x, -self.frame_size)
        self.x[self.frame_size:] = voice_frame
        self.excitation = np.roll(self.excitation, -self.frame_size)
        self.excitation[self.frame_size:] = excitation_frame
        
        # In self.y we have an array with space for two frames -> [ FRAME_SIZE | FRAME_SIZE ]
        # and its status to this point is [ y(n-1) : y(n) ]. In this processing cycle we start
        # working on y(n) which won't be ready until the next cycle (always one cycle of delay
        # due to real-time limitations).
        self.y = np.roll(self.y, -self.frame_size)
        self.y[self.frame_size:] = np.zeros((self.frame_size))

        # Process the overlapped segment using the previous window
        self.y[self.frame_size // 2:self.frame_size // 2 + self.frame_size] += self.vocode_frame(
            self.x[self.frame_size // 2:self.frame_size // 2 + self.frame_size],
            self.excitation[self.frame_size // 2:self.frame_size // 2 + self.frame_size],
            self.order,
            self.alpha
        )

        # Process the current window
        self.y[self.frame_size:] += self.vocode_frame(
            self.x[self.frame_size:],
            self.excitation[self.frame_size:],
            self.order,
            self.alpha
        )

        # Return the frame that is ready after this processing cycle
        # and the external user may decide when to use it (to synchronize or not)
        return self.y[:self.frame_size]

    @staticmethod
    def vocode_frame(
        voice_frame: np.array, 
        excitation_frame: np.array, 
        order: int,
        alpha: float = 0.97,
        apply_filter: bool = True, 
        apply_window: bool = True,
        normalize_correlation: bool = True
    ) -> np.array:
        """ Applies the vocoder processing algorithm to one frame or window, extracting the model parameters from the voice sequence
            and replacing the voice's generator with the given artificial excitation.
            :param voice_frame: Voice samples
            :param excitation_frame: Excitation samples
            :param order: Order of the articulatory model whose parameters are to be estimated
            :param alpha: Pre-emphasis high-pass filter coefficient
            :param apply_filter: If false, the output will be directly the excitation frame (without filtering).
            :param apply_window: If false, the output will not have the window applied.
            :param normalize_correlation: If true, the correlation is normalized
            :return: The vocoded frame
        """
        # Verify if both the voice and the excitation frames have the same length
        if len(voice_frame) != len(excitation_frame):
            raise ValueError('Voice and excitation frames must have the same length')
        
        # Get the frame size
        frame_size = len(voice_frame)

        # Apply a pre-emphasis filter to the voice signal to remove
        # the effect of the glotal pulses produces by the vocal chords
        voice_frame = librosa.effects.preemphasis(voice_frame, coef=alpha)
        #signal.lfilter([1.0, -alpha], [1.0], voice_frame)

        # Estimate the short-time autocorrelation of the given data
        # TODO Use different sizes for each window in the autocorrelation to mitigate bias
        rxx = signal.correlate(voice_frame, voice_frame, method='fft')

        # Extract only the needed lags
        rxx = rxx[len(rxx) // 2 : len(rxx) // 2 + order + 1]
        if normalize_correlation == True:
            rxx /= rxx[0]

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