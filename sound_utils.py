import pdb
import matplotlib.pyplot as plt
import numpy as np
import math
from scipy.fftpack import fft


class SoundUtils(object):
    def __init__(self, sample_rate, samples, debug=False):
        self.sample_rate = sample_rate
        self.samples = samples
        self.debug = debug


    #####-----< Helpers >-----#####
    def get_num_seconds(self):
        """ calculate the number of seconds in the song, using the song's length of samples and sampling rate
        :return: the number of seconds in the song
        """
        return len(self.samples) / self.sample_rate

    def amplitude_agg(self):
        """ for self.samples, use self.sample_rate to aggregate the samples into their average amplitude for a second of audio
        :returns an array of average amplitudes for the samples where each value represents a second of audio's average
        amplitude
        """
        amp_agg = []
        for sample_i in range(0, len(self.samples), self.sample_rate):
            agg_samples = self.samples[sample_i:sample_i + self.sample_rate]
            avg_sample_amp = sum([abs(n) for n in agg_samples]) / len(agg_samples)
            amp_agg.append(avg_sample_amp)

        if self.debug:
            plt.plot(amp_agg)
            plt.title("amplitude vs. time")

            fig, ax = plt.subplots()
            start, end = ax.get_xlim()
            ax.xaxis.set_ticks(np.arange(start, end, 10))

            plt.show()

        return amp_agg

    def fourier_transform(self, samples):
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
        frequencies = (np.arange(0, n_unique_pts, 1.0) * (self.sample_rate / n)) / 1000
        # the values of the frequencies (in db)
        powers = 10 * np.log10(transform)

        return zip(frequencies, powers)


    #####-----< Amplitude Analysis >-----#####
    def find_sudden_amplitude_increases(self, amplitudes, sudden_cutoff=1, sd=1):
        """ given an array of amplitudes (where presumably amplitudes is drawn from amplitude_agg), find any points where
        the amplitude increases suddenly and return those indexes as an array
        :param amplitudes: an array of amplitude values
        :param sudden_cutoff: represents the maximum number of seconds the volume could have shifted in to be considered "sudden"
        :param sd: represents the number of standard deviations which constitute an amplitude increase of noteworthiness
        :return: an array of indexes into amplitudes where the amplitude shifted up suddenly
        """
        print "finding points where amplitudes suddenly increase.."

        increase_indexes = []
        standard_deviation = np.std(amplitudes)
        average_amplitude = np.average(amplitudes)
        deviation_threshold = average_amplitude + (standard_deviation * sd)

        for amp_i in range(1, len(amplitudes)):
            audio_block = amplitudes[amp_i - sudden_cutoff:amp_i]
            potential_chorus_start = amplitudes[amp_i]
            avg_for_block = np.average(audio_block)

            if avg_for_block <= average_amplitude and potential_chorus_start >= deviation_threshold:
                print "sudden increase from {a} to {p}".format(a=avg_for_block, p=potential_chorus_start)
                increase_indexes.append(amp_i)

        print "found points where amplitude increases suddenly: ", increase_indexes
        return increase_indexes

    def find_sustained_increased_amplitudes(self, amplitudes, min_seconds=5, max_seconds=20, sd=1):
        """ discover indexes into amplitudes where the amplitude level is sustained above average for more than min_seconds
        and less than max_seconds
        :param amplitudes: an array of amplitude values
        :param min_seconds: the minimum number of seconds the amplitude must be high to be considered sustained
        :param max_seconds: the maximum number of seconds to record as sustained
        :param sd: represents the number of standard deviations which constitute an amplitude increase of noteworthiness
        :return: an array of two-tuples which represent indexes into amplitudes where the amplitude was sustained above average (each
        tuple represents the point where the sustain started/ended)
        """
        print "finding points where amplitudes are high.."

        increased_indexes = []
        standard_deviation = np.std(amplitudes)
        average_amplitude = np.average(amplitudes)
        deviation_threshold = average_amplitude + (standard_deviation * sd)

        print "sustained amplititude processing stats -- avg amp: {avg}, deviation: {dev}, threshold: {t}".format(avg=average_amplitude, dev=standard_deviation, t=deviation_threshold)

        i = 0
        j = min_seconds
        while i < len(amplitudes):
            audio_block_fn = lambda j: amplitudes[i:j]
            audio_block_avg = np.average(audio_block_fn(j))

            if audio_block_avg > deviation_threshold:
                while audio_block_avg > deviation_threshold and j < len(amplitudes):
                    j += 1
                    audio_block_avg = np.average(audio_block_fn(j))

                increased_indexes.append((i, j))
                i = j
            else:
                i += 1

        print "sustained amplitude increases found: ", increased_indexes
        return increased_indexes


    #####-----< Frequency Analysis >-----#####
    def find_saturated_points(self):
        """ search self.samples for points where the frequency spectrum is heavily saturated (as it's likely that these
        are the chorus, since the chorus tends to have many instruments in it).
        :return: an array of two-tuples which represent points where the frequencies are heavily saturated, relative to
        most of the song
        """
        pass

    def find_similar_points(self):
        pass