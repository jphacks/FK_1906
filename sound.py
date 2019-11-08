import numpy as np
import audiosegment
from matplotlib import pyplot as plt
import time
from pydub import AudioSegment

plt.ion()
    
def analyze_sound(video_source):
    volume_mean, volume_var = analyze_volume(video_source)
    tone_var = analyze_tone(video_source, display=False)
    return {'volume_mean': volume_mean, 'volume_var': volume_var, 'tone_var': tone_var}


def analyze_volume(video_source):
    sound = AudioSegment.from_file(video_source, format="mp4")
    sound = np.array(sound.get_array_of_samples())
    sound = np.abs(sound)
    mean = sound.mean()
    var  = sound.var()
    return mean, var


def analyze_tone(video_source, display=False):
    sound = audiosegment.from_file(video_source).resample(sample_rate_Hz=24000, sample_width=2, channels=1)
    hist_bins, hist_vals = sound.fft()
    hist_vals_real_normed = np.abs(hist_vals) / len(hist_vals)
    mean = np.mean(hist_vals_real_normed)
    
    max_hz, min_hz = 1200, 400
    num_samples = len(sound)
    offset = 1000
    total_data = np.zeros(max_hz-min_hz)
    for i in range(0, num_samples-offset, offset):
        hist_bins, hist_vals = sound[i:i+offset].fft()
        hist_bins, hist_vals = hist_bins[min_hz:max_hz], hist_vals[min_hz:max_hz]
        hist_vals = np.abs(hist_vals) / len(hist_vals)
        hist_vals = np.where(hist_vals >= 500, hist_vals / mean, 0)
        total_data += hist_vals

        if display:
            plt.plot(hist_bins, hist_vals)
            plt.xlabel("Hz")
            plt.ylabel("dB")
            plt.draw()
            plt.pause(1)

    mean = np.mean(total_data)
    #  total_data /= mean
    distribution = np.array([], dtype="int32")
    for i, num_samples in enumerate(total_data):
        hz = i + min_hz
        hz_array = np.full(int(num_samples), hz)
        distribution = np.append(distribution, hz_array)

    return np.var(distribution)

if __name__ == '__main__':
    import sys

    video_source = sys.argv[1]
    print("tone var: ", analyze_tone(video_source, True))
    volume_result = analyze_volume(video_source)
    print("volume:", volume_result)
    time.sleep(10)
