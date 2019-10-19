import sys

import numpy as np
from pydub import AudioSegment

def analyze_sound(video_source):
    sound = AudioSegment.from_file(video_source, format="mp4")
    print(sound)
    sound_data = np.array(sound.get_array_of_samples())
    print(sound_data)
    print(sound_data.shape)
    amplitudes = np.abs(sound_data)
    
    mean = np.mean(amplitudes)
    var  = np.var(amplitudes)
    print(mean, var)

if __name__ == '__main__':
    source = sys.argv[1]
    print(source)
    analyze_sound(source)
