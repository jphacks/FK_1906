import sys

import numpy as np
from pydub import AudioSegment
from scipy.fftpack import fft, fftfreq


def analyze_sound(video_source, display=False):
    sound = AudioSegment.from_file(video_source, format="mp4")
    sound_data = np.array(sound.get_array_of_samples())
    sound_data = sound_data[10:-10]
    amplitudes = np.abs(sound_data)
    

    amplitudes_mean = np.mean(amplitudes)
    amplitudes_var  = np.var(amplitudes)
    print("amplitudes_mean: ", amplitudes_mean)
    print("amplitudes_var: ", amplitudes_var)

    num_samples = sound_data.shape[0]
    fps = 30
    dt = 1.0 / fps
    t = np.arange(0, num_samples*dt, dt)
    f_data = fft(sound_data)
    freq = np.linspace(0, fps, num_samples)

    
    F = np.fft.fft(f_data)
    Amp = np.abs(F) / 10e7 /2
    fleurie_mean = np.mean(Amp)
    fleurie_var = np.var(Amp)
    print("fleurie_mean: ", fleurie_mean)
    print("fleurie_var: ", fleurie_var)

    if display:
        import matplotlib.pyplot as plt

        plt.figure()
        plt.subplot(121)
        plt.plot(t, f_data, label='f(n)')
        plt.xlabel("Time", fontsize=20)
        plt.ylabel("Signal", fontsize=20)
        plt.grid()
        leg = plt.legend(loc=1, fontsize=25)
        leg.get_frame().set_alpha(1)
        plt.subplot(122)
        plt.plot(freq, Amp, label='|F(k)|')
        plt.xlabel('Frequency', fontsize=20)
        plt.ylabel('Amplitude', fontsize=20)
        plt.grid()
        leg = plt.legend(loc=1, fontsize=25)
        leg.get_frame().set_alpha(1)
        plt.show()

    return {
        'amplitudes': {'mean': amplitudes_mean, 'var': amplitudes_var},
        'fleurie':    {'mean': fleurie_mean,    'var': fleurie_var}
    }

if __name__ == '__main__':
    source = sys.argv[1]
    analyze_sound(source, display=True)
