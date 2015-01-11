import pdb
import matplotlib.pyplot as plt
import numpy as np


class SoundUtils(object):
    def __init__(self, sample_rate, samples, debug=False):
        self.sample_rate = sample_rate
        self.samples = samples
        self.debug = debug

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

    def find_sudden_amplitude_increases(self, amplitudes, sudden_cutoff=1, sd=1):
        """ given an array of amplitudes (where presumably amplitudes is drawn from amplitude_agg), find any points where
        the amplitude increases suddenly and return those indexes as an array
        :param amplitudes: an array of amplitude values
        :param sudden_cutoff: represents the maximum number of seconds the volume could have shifted in to be considered "sudden"
        :param sd: represents the number of standard deviations which constitute an amplitude increase of noteworthiness
        :return: an array of indexes into amplitudes where the amplitude shifted up suddenly
        """
        increase_indexes = []
        standard_deviation = np.std(amplitudes)

        for amp_i in range(len(amplitudes)):
            comparison_block = amplitudes[amp_i - sudden_cutoff:amp_i]
            potential_chorus_start = amplitudes[amp_i]

            avg_for_block = sum(comparison_block) / len(comparison_block)
            if (avg_for_block + (standard_deviation * sd)) < potential_chorus_start:
                increase_indexes.append(amp_i)

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
        increase_indexes = []
        standard_deviation = np.std(amplitudes)
        for amp_i in range(len(amplitudes)):
            pass
