from file_utils import FileUtils
from sound_utils import SoundUtils
import matplotlib.pyplot as plt
import time
import pdb


class PyChorus(object):
    def __init__(self, path, debug=False):
        self.file = FileUtils(path)
        self.debug = debug

        rate, data = self.file.get_file_data()
        self.sound_utils = SoundUtils(rate, data, debug=self.debug)

    def _print_data_in_time(self, data):
        """given an array of data, print one element of the array every second
        :param data an array of anything
        """
        for el in data:
            time.sleep(1)
            print el

    def _guess_chorus_using_amplitudes(self):
        """ one possible indicator of the chorus is that it is louder relative to the surrounding verses. This method
        uses this hypotheses to try and guess the chorus and returns a two-tuple of the guesses chorus start/end and
        a score representing how confident in the guess it is
        :return: guessed chorus start/end, or just start if start_only=True
        """
        INCREASE_STANDARD_DEVIATION = 1

        average_amps = self.sound_utils.amplitude_agg()
        print "avg amps ", average_amps

        sudden_amp_increases = self.sound_utils.find_sudden_amplitude_increases(average_amps, sd=INCREASE_STANDARD_DEVIATION)
        ##TODO: be more intellingent in setting min_seconds and max_seconds (based on length of song)
        sustained_amp_increases = self.sound_utils.find_sustained_increased_amplitudes(average_amps, sd=INCREASE_STANDARD_DEVIATION)

        #find overlaps in the sudden and sustained amp increases. The reason we choose sustained amp increases to iterate
        # over is that it seems likely that sudden_amp_increases should be a subset of the sustained amp increases
        best_locations = None
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

        if best_locations:
            return best_locations
        else:
            return sustained_amp_increases

    def _find_chorus_end(self, chorus_start):
        """ locate the index of the end of the chorus
        :param chorus_start: the calculated location of the beginning of the chorus
        :return: the calculated second when the chorus ends
        """
        pass

    def _find_chorus_start(self):
        """ locate the index of the beginning of the chorus
        :return: the calculated second when the chorus starts
        """
        # 1: try using amplitudes to guess the start of the chorus

        guessed_chorus = self._guess_chorus_using_amplitudes()
        if not guessed_chorus:
            guessed_chorus = self._guess_chorus_using_amplitudes(start_only=True)


    def find_chorus(self):
        chorus_start = self._find_chorus_start()
        chorus_end = self._find_chorus_end(chorus_start)

        return chorus_start, chorus_end

    def write_choruses(self):
        chorus_start, chorus_stop = self.find_chorus()
