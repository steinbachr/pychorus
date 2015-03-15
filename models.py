from sound_utils import SoundUtils
import math
import numpy as np
import time
import pdb


class Frame(object):
    """ a frame is an abstraction for a group of samples and can be thought of as a link in a doubly linked list """
    def __init__(self, samples=None, sample_rate=None, next_frame=None, prev_frame=None, index=0):
        """
        :param samples: ``array`` of samples read from the sound file
        :param sample_rate: ``int``
        :param next_frame: ``Frame`` the next frame in the DLL
        :param prev_frame: ``Frame`` the previous frame in the DLL
        :param amplitude_score: ``float`` value between 0 and 1 which represents how loud the song is at this point relative
        to the rest of the song (a value above .5 means the volume is above average at this point)
        :param index: ``int`` primarily for debugging purpose, this frames index in the song's list of frames
        """
        self.samples = samples
        self.sample_rate = sample_rate
        self.next_frame = next_frame
        self.prev_frame = prev_frame
        self.index = index

        self.value = self._value()

        # should be set after all initialization has occurred (including setting prev and next pointers as appropriate)
        self.is_crescendo = None
        # value between 0 and 1 which represents a measure of the frequency dispersion / density of this frame
        self.frequency_score = None

    def _value(self):
        """ for self.samples, get the average amplitude
        :return: ``int`` the average amplitude of the samples for this Frame
        """
        return sum([abs(n) for n in self.samples]) / len(self.samples)

    def _is_crescendo(self):
        """ check whether this Frame represents a step in a crescendo
        :return: ``bool`` True if this Frame is part of a crescendo, False otherwise
        """
        return self.prev_frame is not None and self.prev_frame.value < self.value

    def _frequency_score(self):
        """ this frames frequency score is a function of the dispersion of the frequency (i.e. the number of populated
        buckets), the amplitude in those buckets, and extra weight is given to frequencies in the human vocals bucket
        :return: ``float`` value between 0 and 1 representing this frame's (unweighted relative to the entire song)
        frequency score
        """
        frequency_buckets = SoundUtils.fourier_transform(self.samples, self.sample_rate)

        print "frequency buckets are {}\n\n".format(frequency_buckets)



    #####-----< Public >-----#####
    def get_num_seconds(self):
        """ calculate the number of seconds in the frame, using the length of the given samples and the sample_rate
        :return: the number of seconds in the song
        """
        return len(self.samples) / self.sample_rate

    def get_frames_between(self, other_frame):
        """ get the number of frames between self and other_frame
        :return: ``list`` of ``Frame`` between this frame and other frame, inclusive on both ends
        """
        frames_between = [self]

        next_frame = self.next_frame
        while next_frame and next_frame != other_frame:
            frames_between.append(next_frame)
            next_frame = next_frame.next_frame

        frames_between.append(other_frame)

        return frames_between

    def get_crescendo_length(self):
        """ find how long the crescendo leading up to this Frame is
        :return: ``int`` the number of frames the crescendo occupies up to self or - if self is not part of
        a crescendo - 0
        """
        if not self.is_crescendo or not self.prev_frame:
            return 0
        else:
            return 1 + self.prev_frame.get_crescendo_length()


    #####-----< Setters >-----#####
    def set_is_crescendo(self):
        self.is_crescendo = self._is_crescendo()

    def set_frequency_score(self):
        self.frequency_score = self._frequency_score()

    def __repr__(self):
        return "{val} {cresc}".format(val=self.value, cresc="inc" if self.is_crescendo else "dec")


class Song(object):
    # standard deviations for what defines a loud / quiet portion of a song
    SD_FOR_QUIET = .5
    SD_FOR_LOUD = .5

    def __init__(self, samples=None, sample_rate=None, debug=False):
        self.frames = self._create_frames(samples, sample_rate)
        self.debug = debug

    #####-----< Init Helpers >-----#####
    def _create_frames(self, samples, sample_rate):
        """ group the given samples into windows which we can more easily work with
        :param samples: ``array`` of raw samples read from a .wav file
        :param sample_rate: ``int`` the sampling rate of the .wav audio
        """
        # group the samples into second-intervals (so each Frame represents a second of audio)
        frames = []

        for i in range(0, len(samples) - sample_rate, sample_rate):
            cur_frame = Frame(samples=samples[i:i + sample_rate], sample_rate=sample_rate, index=(i / sample_rate))

            if len(frames) > 0:
                # we pop the last frame off the stack in order to set pointers appropriately, then we add it back to
                # the top of the stack after pointers have been set
                prev_frame = frames.pop()
                prev_frame.next_frame = cur_frame
                frames.append(prev_frame)

                cur_frame.prev_frame = prev_frame
                cur_frame.set_is_crescendo()

            frames.append(cur_frame)

        return frames


    #####-----< Internals >-----#####
    def __iter__(self):
        for i in self.frames:
            yield i

    def __repr__(self):
        uni = ""

        for f in self:
            uni += "{} -> ".format(f.value)

        return uni


    #####-----< Properties >-----#####
    @property
    def length(self):
        """ get the length of this song in seconds """
        return sum([f.get_num_seconds() for f in self])

    @property
    def min_chorus_length(self):
        """
        :return: a lower bound on the length of the chorus (in frames)
        """
        NUM_CHORUSES = 3
        CHORUSES_OVERALL_PERCENTAGE_OF_SONG = .10
        CHORUS_SONG_PERCENTAGE = CHORUSES_OVERALL_PERCENTAGE_OF_SONG / NUM_CHORUSES

        min_length = int(len(self.frames) * CHORUS_SONG_PERCENTAGE)
        print "using min chorus length ", min_length
        return min_length

    @property
    def max_chorus_length(self):
        """
        :return: an upper bound on the length of the chorus (in frames)
        """
        NUM_CHORUSES = 3
        CHORUSES_OVERALL_PERCENTAGE_OF_SONG = .40
        CHORUS_SONG_PERCENTAGE = CHORUSES_OVERALL_PERCENTAGE_OF_SONG / NUM_CHORUSES

        max_length = int(len(self.frames) * CHORUS_SONG_PERCENTAGE)
        print "using max chorus length ", max_length
        return max_length

    @property
    def amplitudes(self):
        return [f.value for f in self]

    @property
    def avg_amplitude(self):
        return np.average(self.amplitudes)

    @property
    def std_amplitude(self):
        return np.std(self.amplitudes)

    @property
    def quiet_threshold(self):
        """ defines the amplitude threshold for what is considered "quiet" (everything below the returned value) """
        return self.avg_amplitude - (self.std_amplitude * self.SD_FOR_QUIET)

    @property
    def loud_threshold(self):
        """ defines the amplitude threshold for what is considered "loud" (everything above the returned value) """
        return self.avg_amplitude + (self.std_amplitude * self.SD_FOR_LOUD)


    #####-----< Helpers >-----#####
    def print_data_in_time(self):
        """ print one Frame of this Song every second
        """
        for el in self:
            time.sleep(1)
            print el

    def _get_temporal_boundaries(self, frames):
        """ find the temporal boundaries for the given frames. For instance, the given frames might be the frames referenced
        by the following indexes into self.frames: [16, 17, 18, 19, 20, 40, 41, 42, 43, 44, 45, 46, 60, 61, 62]. This
        method should then return the indexes 4 (20) and 11 (46) as these represent the boundaries of the temporal blocks
        of ``frames``
        :param frames: ``list`` of ``Frame`` instances (would make the most sense if they are given as sequenctial values
        as in example above)
        :return: ``list`` of ``int`` indexes into the ``frames`` which indicate temporal boundaries into ``frames``.
        """
        boundaries = []
        for i in range(0, len(frames) - 2):
            frame = frames[i]
            if frame.next_frame != frames[i + 1]:
                boundaries.append(i)

        return boundaries


    #####-----< Find the Chorus >-----#####
    def _find_sudden_amplitude_increases(self):
        """ find points in this Song where the amplitude increases suddenly
        :return: ``list`` of Frame where the amplitude shifts up suddenly
        """
        print "finding points where amplitudes suddenly increase.."

        result = []
        crescendo_frames = [f for f in self if f.is_crescendo is True]
        loud_threshold = self.loud_threshold

        for frame in crescendo_frames:
            prev_frame = frame.prev_frame
            if frame.value >= loud_threshold and prev_frame <= self.avg_amplitude:
                print "sudden increase from {a} to {p}".format(a=frame, p=prev_frame)
                result.append(frame)

        print "found {} points where amplitude increases suddenly".format(len(result))
        return result

    def _find_sustained_amplitude_increases(self):
        """ find points in this Song where the amplitude is sustained for an extended period of time (a more naive
        indicator of a chorus)
        """
        print "finding points with sustained amplitude increase.."

        result = []

        # the number of sequential frames which are allowed to have a dip in amplitude without triggering a break from
        # the inner loop
        INCONGRUITY_CUSHION = 2
        # the minimum number of frames which must have am amp increase in order to be considered sustained
        MINIMUM_LENGTH = 10

        loud_threshold = self.loud_threshold

        for frame in self.frames:
            num_loud_frames = 0

            if frame.value >= loud_threshold:
                num_loud_frames += 1

                num_incongruities = 0
                seq_frame = frame.next_frame
                while seq_frame and num_incongruities <= INCONGRUITY_CUSHION:
                    if seq_frame.value >= loud_threshold:
                        num_loud_frames += 1
                    else:
                        num_incongruities += 1

                    seq_frame = seq_frame.next_frame

                if num_loud_frames >= MINIMUM_LENGTH:
                    result += frame.get_frames_between(seq_frame)

        print "found {} points where amplitude was increased for sustained period".format(len(result))
        print "points were ", result
        return result

    def _find_saturated_points(self):
        """ search self.samples for points where the frequency spectrum is heavily saturated (as it's likely that these
        are the chorus, since the chorus tends to have many instruments in it).
        :return: an array of two-tuples which represent points where the frequencies are heavily saturated, relative to
        most of the song
        """
        pass

    def _find_bridge_end(self):
        """ if we're able to successfully identify the bridge, we know the chorus is sure to come next. We identify
        the bridge as having both low amplitude, a point where the amplitude quickly increases (when the chorus starts)
        low frequency dispersion, and being towards the end of the song.

        :return: Frame representing the end of the bridge (and the start of the chorus) if we feel confident we've found
        the bridge, otherwise None
        """
        bridge_end = None

        # the maximum amount of the song the bridge might occupy
        MAX_BRIDGE_LENGTH = .2
        # the minimum length of a crescendo which could be considered a build up to a chorus
        BUILDING_BRIDGE_THRESHOLD = 3

        # indicators of chorus
        sudden_amplitude_increase_points = self._find_sudden_amplitude_increases()
        saturated_frequency_points = self._find_saturated_points()
        quiet_threshold = self.quiet_threshold
        loud_threshold = self.loud_threshold

        # the earliest point in the song where the bridge might start (20% from the end plus the length of a chorus)
        earliest_bridge_start = (MAX_BRIDGE_LENGTH * len(self.frames)) + self.max_chorus_length
        current_frame_i = len(self.frames) - 1

        # we take the end of the bridge to be when the current frame is loud / dense and the previous few frames are
        # not
        while bridge_end is None and current_frame_i >= earliest_bridge_start:
            current_frame = self.frames[current_frame_i]
            prev_frame = self.frames[current_frame_i - 1]

            # the more important indicator is amplitude. The type of bridges seem to either be a slow build to a loud chorus
            # or a sudden "drop"
            if current_frame in sudden_amplitude_increase_points and prev_frame <= quiet_threshold:
                print "identified the end of the bridge using `sudden amplitude shift` method"
                bridge_end = current_frame
            elif current_frame.get_crescendo_length() >= BUILDING_BRIDGE_THRESHOLD and not prev_frame >= loud_threshold:
                # we check not prev_frame >= loud_threshold to make sure we're not identifying the middle of the chorus as the bridge end
                print "identified the end of the bridge using `building bridge` method"
                bridge_end = current_frame

            current_frame_i -= 1

        return bridge_end

    def find_chorus(self):
        """ use amplitude and frequency analysis to guess the location of the chorus start/end.
        :return: two-tuple containing two Frames, the guessed start and end of the chorus for this Song
        """
        print "finding chorus using stats:\nAvg:{avg}\nSTD:{std}\nLow:{low}\nHigh:{high}".format(avg=self.avg_amplitude,
                                                                                                 std=self.std_amplitude,
                                                                                                 low=self.quiet_threshold,
                                                                                                 high=self.loud_threshold)
        chorus_start = chorus_end = None
        bridge_end = self._find_bridge_end()

        if bridge_end:
            chorus_start = cur_frame = bridge_end

            std_dev = self.std_amplitude
            avg_amp = self.avg_amplitude
            # the amplitude threshold is 1 standard deviation below the average
            amp_threshold = avg_amp - std_dev

            # we say that the chorus continues until the frames drop to 1 standard deviation below the norm
            while cur_frame is not None and cur_frame.value > amp_threshold:
                cur_frame = cur_frame.next_frame

            chorus_end = cur_frame
            print "found chorus using `bridge reference` measure"
        else:
            # if we weren't able to find the bridge, then attempt to locate the chorus by simply looking for blocks of the
            # song that have a sustained amplitude
            increased_amplitude_frames = self._find_sustained_amplitude_increases()

            # since the increased amplitude frames should now - ideally - contain multiple chorus blocks, break the blocks
            # up by temporal locality (to isolate a single chorus block)
            if len(increased_amplitude_frames) > 0:
                frame_boundaries = self._get_temporal_boundaries(increased_amplitude_frames)
                print "the frame boundaries are ", frame_boundaries

                chorus_start = increased_amplitude_frames[0]
                chorus_end = increased_amplitude_frames[frame_boundaries[0]]

                print "found chorus using `increased amplitude` measure"

        if chorus_start:
            print "the number of frames between the calculated frames is ", len(chorus_start.get_frames_between(chorus_end))
        else:
            print "chorus unable to be found"

        return chorus_start, chorus_end


