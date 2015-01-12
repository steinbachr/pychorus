from file_utils import FileUtils
from sound_utils import SoundUtils
import matplotlib.pyplot as plt
import time
import pdb
import math


class PyChorus(object):
    def __init__(self, path, debug=False):
        self.file = FileUtils(path)
        self.debug = debug

        rate, data = self.file.get_file_data()
        self.sound_utils = SoundUtils(rate, data, debug=self.debug)

    @property
    def min_chorus_length(self):
        """
        :return: a lower bound on the length of the chorus
        """
        NUM_CHORUSES = 3
        CHORUSES_OVERALL_PERCENTAGE_OF_SONG = .10
        CHORUS_SONG_PERCENTAGE = CHORUSES_OVERALL_PERCENTAGE_OF_SONG / NUM_CHORUSES

        min_length = int(self.sound_utils.get_num_seconds() * CHORUS_SONG_PERCENTAGE)
        print "using min chorus length ", min_length
        return min_length

    @property
    def max_chorus_length(self):
        """
        :return: an upper bound on the length of the chorus
        """
        NUM_CHORUSES = 3
        CHORUSES_OVERALL_PERCENTAGE_OF_SONG = .40
        CHORUS_SONG_PERCENTAGE = CHORUSES_OVERALL_PERCENTAGE_OF_SONG / NUM_CHORUSES

        max_length = int(self.sound_utils.get_num_seconds() * CHORUS_SONG_PERCENTAGE)
        print "using max chorus length ", max_length
        return max_length

    def _print_data_in_time(self, data):
        """given an array of data, print one element of the array every second
        :param data an array of anything
        """
        for el in data:
            time.sleep(1)
            print el

    def _choose_best_point(self, points):
        """ find the point in points which is most inclusive, that is it either contains the most other points inside the
        points list and/or it spans the greatest distance
        :param points: an array of song points (start, end)
        :return: a point (start, end) which is most inclusive
        """
        most_inclusive = (None, 0)
        for i in range(0, len(points)):
            start, end = points[i]
            contains_points = 0

            for j in range(0, len(points)):
                if i != j:
                    other_start, other_end = points[j]
                    if start <= other_start and end >= other_end:
                        contains_points += 1

            if contains_points > most_inclusive[1]:
                most_inclusive = (points[i], contains_points)

        # there must be no overlap in discovered points, so just choose the point spanning the greatest range
        most_inclusive = most_inclusive[0] or max(points, key=lambda point: point[1] - point[0])
        return most_inclusive


    def _guess_chorus_using_amplitudes(self):
        """ one possible indicator of the chorus is that it is louder relative to the surrounding verses. This method
        uses this hypotheses to try and guess the chorus and returns a two-tuple of the guesses chorus start/end and
        a score representing how confident in the guess it is
        :return: guessed chorus start/end, or just start if start_only=True
        """
        INCREASE_STANDARD_DEVIATION = 1

        average_amps = self.sound_utils.amplitude_agg()
        min_chorus_length = self.min_chorus_length
        max_chorus_length = self.max_chorus_length
        print "avg amps ", average_amps

        sudden_amp_increases = self.sound_utils.find_sudden_amplitude_increases(average_amps, sd=INCREASE_STANDARD_DEVIATION)
        sustained_amp_increases = self.sound_utils.find_sustained_increased_amplitudes(average_amps, min_seconds=min_chorus_length,
                                                                                       max_seconds=max_chorus_length, sd=INCREASE_STANDARD_DEVIATION)

        best_locations = None
        alternate_locations = sustained_amp_increases
        if sustained_amp_increases:
            BUFFER = 2
            for chorus_start, chorus_end in sustained_amp_increases:
                for sudden_increase in sudden_amp_increases:
                    overlap = sudden_increase == chorus_start
                    overlap = overlap or (chorus_start < sudden_increase < chorus_end)
                    # it's possible that the sudden increase occurs just before the sustained increase, in this case attempt
                    # to buffer the sudden increase
                    overlap = overlap or ((sudden_increase < chorus_start) and (sudden_increase - BUFFER > chorus_start))

                    if overlap:
                        best_locations.append((sudden_increase, chorus_end))
        else:
            alternate_locations = [(increase, increase + max_chorus_length) for increase in sudden_amp_increases]

        if best_locations:
            return best_locations
        else:
            return alternate_locations

    def _guess_chorus_using_frequencies(self):
        min_chorus_length = self.min_chorus_length
        max_chorus_length = self.max_chorus_length

        saturated_points = self.sound_utils.find_saturated_points()
        similar_points = self.sound_utils.find_similar_points()

        best_locations = saturated_points if saturated_points else similar_points
        if saturated_points and not similar_points:
            best_locations = saturated_points
        elif similar_points and not saturated_points:
            best_locations = similar_points
        else:
            pass

        return best_locations

    def _choose_chorus_candidate(self, amp_locations, freq_locations):
        """ using a combination of the results from amplitude and frequency based analysis, pick the most likely candidate
        for the chorus
        :param amp_locations: list of two-tuples containing calculated chorus locations based on amplitude analysis
        :param freq_locations: list of two-tuples containing calculated chorus locations based on frequency analysis
        :return: a single tuple, the most likeley candidate for the chorus
        """
        # if we're missing results for either the amp or freq analysis, then choose a result from the other set
        # of results
        if not amp_locations and freq_locations:
            best_candidate = freq_locations[int(len(freq_locations) / 2)]
        elif amp_locations and not freq_locations:
            best_candidate = amp_locations[0]
        else:
            best_candidate = self._choose_best_point(amp_locations + freq_locations)

        return best_candidate

    def find_chorus(self):
        # 1: try using amplitudes to guess the location of the chorus
        chorus_by_amps = self._guess_chorus_using_amplitudes()

        # 2: try using frequency analysis to guess the location of the chorus
        chorus_by_freqs = self._guess_chorus_using_frequencies()

        # 3: choose the likeliest chorus location using a combination of the amplitude and frequency analyses
        chorus_location = self._choose_chorus_candidate(chorus_by_amps, chorus_by_freqs)

        return chorus_location

    def write_choruses(self):
        chorus_start, chorus_stop = self.find_chorus()
