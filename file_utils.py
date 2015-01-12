import subprocess
import wave
import numpy as np
from scipy.io import wavfile
from numpy.fft import fft
import pdb

class UnsupportedFileType(Exception):
    pass


class FileUtils(object):
    MP3, WAV, MP4 = ".mp3", ".wav", ".mp4"

    def __init__(self, path):
        self.path = path

    def _convert_to_wav(self):
        """
        converts the file given by self.path to a wav file
        :return: the path to the new wav file
        """
        file_type = self._get_file_type(self.path)
        if file_type != self.WAV:
            wav_path = "{stripped}.wav".format(stripped=self.path.replace(file_type, ""))
            subprocess.call("ffmpeg -i {path} -ac 1 {wav}".format(path=self.path, wav=wav_path), shell=True)
        else:
            wav_path = self.path

        return wav_path

    def _get_file_type(self, path):
        """return one of of the supported file types depending on the file type for this utils' file"""
        try:
            return [t for t in [self.MP3, self.WAV, self.MP4] if t in path][0]
        except IndexError:
            raise UnsupportedFileType()

    def get_file_data(self):
        """get file data associated with this file, including it's sample rate and raw data"""
        file_type = self._get_file_type(self.path)

        # 1: convert the file if necessary to .wav format
        wav_path = self._convert_to_wav()

        # 2: get the file data
        spf = wave.open(wav_path, 'r')
        signal = spf.readframes(-1)
        signal = np.fromstring(signal, 'Int16')

        sample_rate, wav_data = spf.getframerate(), signal
        return sample_rate, wav_data