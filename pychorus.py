from file_utils import FileUtils
from sound_utils import SoundUtils
from models import Song
import time
import pdb
import math
import sys


class PyChorus(object):
    def __init__(self, path=None, output_path=None, debug=False):
        self.file = FileUtils(path)
        self.output_path = output_path
        self.debug = debug

        rate, data = self.file.get_file_data()
        self.song = Song(samples=data, sample_rate=rate, debug=self.debug)

        print "song is {}".format(str(self.song))

    def find_chorus(self):
        return self.song.find_chorus()

    def write_chorus(self):
        """ write the calculated chorus to self.output_path
        :return: True if the chorus was able to be written False otherwise
        """
        chorus_start, chorus_stop = self.find_chorus()

        print "calculated chorus was {start} to {stop}".format(start=chorus_start, stop=chorus_stop)

        if chorus_start and chorus_stop:
            if self.debug:
                print "chorus timing was {start} to {stop}".format(start=chorus_start.index, stop=chorus_stop.index)
            return True
        else:
            return False


if __name__ == "__main__":
    path = sys.argv[1]

    succeeded = PyChorus(path=path, debug=True).write_chorus()

    if succeeded:
        print "chorus writing succeeded"
    else:
        print "chorus writing failed"