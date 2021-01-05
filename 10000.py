from MidiParser import MidiParser
from FrameDrawer import FrameDrawer
from tqdm import tqdm
import numpy as np
import imageio


def normalize_note(note, note_range):
    """
    Remap the pitch of a note to first 240 degrees of the hue spectrum, such that
    the lowest note will be blue, the middle note will be green and the highest will be red.
    :param note: Pitch value.
    :param note_range: List of [min, max] pitch values in the range.
    :return: Normalised value in range 0 - 1.
    """
    n = (note - note_range[0]) / (note_range[1] - note_range[0])
    return 2 * (1 - n) / 3  # return only first 240 degrees of hue spectrum, reversed to be blue - green - red


def normalize_velocity(velocity, velocity_range):
    """
    Remap the velocity of a note to a 0 - 1 range, so that the quietest note is 0 and the loudest note is 1.
    :param velocity: Velocity value.
    :param velocity_range: List of [min, max] velocity values in the range.
    :return: Normalised value in range 0 - 1.
    """
    return (velocity - velocity_range[0]) / (velocity_range[1] - velocity_range[0])


def get_fade_time(note):
    """
    Calculate a fade time in seconds based on the note pitch value.
    Fade time range is about 1 - 5 seconds depending on octave (lowest is longest).
    :param note: Note dict object as member of note_list generated by MidiParser.extract_notes().
    :return: A fade time in seconds.
    """
    #
    return (10 - int(note['note'] / 12))/3 + 1


def generate_10000_video(input_file='resources/10000.mid', output_file='10000.mp4',
                         start_delay=3, end_delay=10, fps=60):
    """
    Generate the 10000 dot video from a MIDI track.
    :param input_file: Path to MIDI file for note timing and values.
    :param output_file: Path to write output video.
    :param start_delay: Seconds to render video before counting MIDI time.
    :param end_delay: Seconds to render video after last MIDI note.
    :param fps: Frame rate of video (default 60fps)
    """
    midi = MidiParser(input_file)
    notes = midi.extract_notes()
    note_range = midi.get_note_range(notes)
    velocity_range = midi.get_velocity_range(notes)

    draw = FrameDrawer()
    base = draw.generate_base()

    text_alpha = 0
    note_index = 0
    notes_left = True
    duration_seconds = start_delay + notes[-1]['time'] + end_delay
    duration_frames = int(np.ceil(duration_seconds * fps))

    with imageio.get_writer(output_file, format='mp4', mode='I', fps=fps) as writer:
        frame = draw.add_centered_text(base, f'00000', text_alpha)
        writer.append_data(np.asarray(frame))

        note = notes.pop(0)
        for f in tqdm(range(duration_frames)):
            time = f / fps - start_delay

            if text_alpha < 255:
                text_alpha = text_alpha + 1

            if notes_left and time >= note['time']:
                base = draw.add_circle(base, note_index)
                draw.add_accent_note(note_index,
                                     normalize_note(note['note'], note_range),
                                     normalize_velocity(note['velocity'], velocity_range),
                                     get_fade_time(note) * fps)
                note_index = note_index + 1
                if len(notes) > 0:
                    note = notes.pop(0)
                else:
                    notes_left = False

            frame = draw.add_centered_text(base, f'{note_index:05}', text_alpha)
            frame = draw.draw_accents(frame)
            writer.append_data(np.asarray(frame))


if __name__ == "__main__":
    generate_10000_video()