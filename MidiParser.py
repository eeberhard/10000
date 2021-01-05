import numpy as np
import mido


class MidiParser:
    """
    MidiParser reads the individual notes from a midi file,
    gives them a timestamp in seconds and returns them in a list.
    :param filename: The path to the midi file.
    :type filename: str
    """
    def __init__(self, filename: str):
        self.mid = mido.MidiFile(filename)
        self.tempo = 500000  # default tempo 120bpm
        self._tick_time = 0

    @staticmethod
    def note_to_text(note):
        """
        Convert a note pitch value into a note text value (e.g. 60 -> C 4).
        :param note: The midi note pitch value.
        :type note: int
        :return: The 3 character text representation of the note pitch
        """
        letters = ['C ', 'C#', 'D ', 'D#', 'E ', 'F ', 'F#', 'G ', 'G#', 'A ', 'A#', 'B ']
        octave = int(note / 12) - 1
        return f'{letters[note % 12]}{octave}'

    @staticmethod
    def get_note_range(note_list):
        """
        Get the pitch range across a note list.
        :param note_list: The note list returned by MidiParser.extract_notes()
        :type note_list: list
        :return: The minimum and maximum pitch values in the list
        :rtype: list
        """
        notes = [n['note'] for n in note_list]
        return [np.min(notes), np.max(notes)]

    @staticmethod
    def get_velocity_range(note_list):
        """
        Get the velocity range across a note list.
        :param note_list: The note list returned by MidiParser.extract_notes()
        :type note_list: list
        :return: The minimum and maximum velocity values in the list
        :rtype: list
        """
        velocities = [n['velocity'] for n in note_list]
        return [np.min(velocities), np.max(velocities)]

    def tick2second(self):
        """
        Convert a midi tick time to a time in seconds.
        :return: The converted time in seconds
        """
        return mido.tick2second(self._tick_time, ticks_per_beat=self.mid.ticks_per_beat, tempo=self.tempo)

    def extract_notes(self, track=0):
        """
        Extract and timestamp the notes of a midi file track into a Python list.
        :param track: The track number of the midi file to analyse (default to first track)
        :type track: int
        :return: A list of notes, where each note is a dictionary containing
            the time, note (pitch), note_text (e.g. A4), and velocity
        :rtype: list
        """
        self._tick_time = 0
        note_list = []

        for msg in self.mid.tracks[track]:
            if msg.is_meta:
                if msg.type == 'set_tempo':
                    # update tick time to represent the current time in the new tempo
                    self._tick_time = self._tick_time * msg.tempo / self.tempo
                    self.tempo = msg.tempo
                continue

            # keep track of the elapsed time in ticks
            self._tick_time = self._tick_time + msg.time

            # append note start events to the note list
            # (note_on with velocity 0 is equivalent to a note_off)
            if msg.type == 'note_on' and msg.velocity > 0:
                note_list.append({'time': self.tick2second(),
                                  'note_text': self.note_to_text(msg.note),
                                  'note': msg.note,
                                  'velocity': msg.velocity})

        return note_list


if __name__ == "__main__":
    notes = MidiParser('resources/10000.mid').extract_notes()
    print(f'Note count: {len(notes)}')
    print(f'Pitch range: {MidiParser.get_note_range(notes)}')
    print(f'Velocity range: {MidiParser.get_velocity_range(notes)}')
    print(f'Total time: {notes[-1]["time"]}')
