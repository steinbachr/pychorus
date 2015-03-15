from numpy.fft import fft
import pdb
import numpy as np
import math


class SoundUtils(object):
    @staticmethod
    def fourier_transform(samples, sample_rate):
        """ create a Fourier Transform to analyze the data in the frequency domain
        (borrowed heavily from http://samcarcagno.altervista.org/blog/basic-sound-processing-python/)
        :param samples: an array of samples to create an FFT over
        :return: an array of two-tuple where each two tuple represents a frequency bin and it's associated power level
        """
        print "creating fourier transform over samples"
        n = len(samples)
        n_unique_pts = math.ceil((n + 1) / 2.0)

        transform = fft(samples)
        transform = transform[0:n_unique_pts]
        transform = abs(transform)
        transform = transform / float(n)
        transform = transform ** 2

        if n % 2 > 0:
            # we've got odd number of points fft
            transform[1:len(transform)] = transform[1:len(transform)] * 2
        else:
            # we've got even number of points fft
            transform[1:len(transform) - 1] = transform[1:len(transform) - 1] * 2

        # the frequency bins (in kiloherz)
        frequencies = (np.arange(0, n_unique_pts, 1.0) * (sample_rate / n)) / 1000
        # the values of the frequencies (in db)
        powers = 10 * np.log10(transform)

        return zip(frequencies, powers)