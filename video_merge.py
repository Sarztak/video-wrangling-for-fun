import shutil
import csv
import json
import subprocess
from pathlib import Path

def get_video_dimensions(video_file_path):
    path = str(video_file_path)
    command = [
        'ffprobe',
        '-i', f"{path}",
        '-v', 'error', # set verbosity level to error
        '-select_streams', 'v:0', # select the video stream from 1st input
        '-show_entries', 'stream=width,height', # get widht and height information
        '-of', 'json', # get output in json format
    ]

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        raise Exception(f"Error getting the video dimensions: {result.stderr}")
    
    video_info_json = result.stdout # the text=True ensure that stdout is a string
    video_info = json.loads(video_info_json) # use json.loads because input is string

    if 'streams' not in video_info or len(video_info['streams']) == 0:
        raise Exception(f"Error getting the video dimensions: {result.stderr}")

    wh_dict = video_info['streams'][0] # the streams is the key and value is a list
    width = wh_dict['width']
    height = wh_dict['height']

    return width, height

def get_video_duration(video_file_path):
    path = str(video_file_path)
    command = [
        'ffprobe',
        '-i', f"{path}",
        '-v', 'error', # set verbosity level to error
        '-show_entries', 'format=duration', # get the duration of the videos
        '-of', 'json', # get output in json format
    ]

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        raise Exception(f"Error getting the video duration: {result.stderr}")
    
    video_info_json = result.stdout # the text=True ensure that stdout is a string
    video_info = json.loads(video_info_json) # use json.loads because input is string

    if 'format' not in video_info:
        raise Exception(f"Error getting the video duration: {result.stderr}")

    duration = float(video_info['format']['duration']) # this is a string which needs to be converted to float; the duration is also in seconds

    return duration

def _make_even(n):
    return n if n % 2 == 0 else n - 1

def concat_video_horizontally(video0, video1, v0_v1_width_ratio=0.3):
    """
    constraints : 
    1. video 0 and video 1 will have the same height
    2. the width will be fixed and divided between them as needed
    """
    # most of the video compression methods require height and widths are divisible by 2
    v0_w, v0_h = get_video_dimensions(video0)
    v1_w, v1_h = get_video_dimensions(video1)

    new_v1_w = int(v1_w * (1 - v0_v1_width_ratio))
    new_v1_w = _make_even(new_v1_w)

    new_v1_h = int(v1_h * (1 - v0_v1_width_ratio)) # preserve the aspect ratio of v1
    new_v1_h = _make_even(new_v1_h)

    # new width of video 1 will be 30% of old video 2
    new_v0_w = int(v1_w * v0_v1_width_ratio)
    new_v0_w = _make_even(new_v0_w)
    v0_aspect_ratio = v0_w / v0_h 
    new_v0_h = int(new_v0_w / v0_aspect_ratio)
    new_v0_h = _make_even(new_v0_h)

    # the height of new video 1 should match the new height of video 2 so it will be padded. Here I am assuming that video 2 is bigger 
    pad_height = new_v1_h
    y_offset = int((pad_height - new_v0_h) / 2)
    breakpoint()
    # Build ffmpeg command
    ffmpeg_cmd = [
        'ffmpeg',
        '-y', # overwrite the file without asking
        '-i', video0,
        '-i', video1,
        '-filter_complex', f"[1:v]scale={new_v1_w}:{new_v1_h}[v1];[0:v]scale={new_v0_w}:{new_v0_h}[v0_scaled];[v0_scaled]pad={new_v0_w}:{pad_height}:0:{y_offset}:black[v0];[v0][v1]hstack[v]",
        '-map', '[v]',
        '-map', '0:a:0',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        'output_4.mp4'
    ]

    # run the command 
    result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # check the output
    if result.returncode != 0:
        raise Exception(f"Error : {result.stderr}")


def write_video_duration():
    cwd = Path.cwd()
    video_duration = [
        (video.name, get_video_duration(video)) for video in cwd.glob('*.mp4')
    ]

    # arrange by duration
    video_duration = sorted(video_duration, key=lambda x: x[1])
    with open('video_durations.csv', 'w', encoding='utf8') as w:
        w.write(f'name,duration\n')
        for name, duration in video_duration:
            w.write(f"{name},{duration}\n")

def remove_duplicate_videos():
    write_video_duration()
    _collector = []
    with open('video_durations.csv', 'r', encoding='utf8') as r:
        csv_reader = csv.reader(r)
        _ = next(csv_reader) # skip the header
        rows = [(name, float(duration)) for name, duration in csv_reader]
        rows = sorted(rows, key=lambda x: x[1]) # sort by duration

        _temp = []
        prev, curr = 0, 0
        while curr < len(rows):
            if rows[prev][1] == rows[curr][1]:
                _temp.append(rows[curr])
            else:
                _collector.append(_temp)
                _temp = [rows[curr]]
            prev, curr = curr, curr + 1
        _collector.append(_temp) # the last list won't be appended if last element is not equal to last be one hence a new _temp will be created

    # now go over each collection and decide by size of the video which one to keep
    # those with the biggest size will be kept
    del_dir = Path('./delete')
    del_dir.mkdir(exist_ok=True, parents=True)
    cwd = Path.cwd()
    for item in _collector:
        _temp = []
        for name, duration in item:
            path = cwd / name
            size = path.stat().st_size
            _temp.append((path, size))
        _temp = sorted(_temp, key=lambda x: x[1])    

        # keep the one with max size and send other to delete folder
        for i in range(len(_temp) - 1): # the largest one is at the end of _temp
            path, size = _temp[i]
            filename = path.name
            shutil.move(path, del_dir / filename)

def make_pairs():
    paired, unpaired = [], []
    tol = 2 # arbitary 2 sec duration
    with open('video_durations.csv', 'r', encoding='utf8') as r:
        csv_reader = csv.reader(r)
        _ = next(csv_reader) # skip the header
        rows = [(name, float(duration)) for name, duration in csv_reader]
        rows = sorted(rows, key=lambda x: x[1]) # sort by duration

        prev, curr = 0, 1
        while curr < len(rows):
            if abs(rows[prev][1] - rows[curr][1]) < tol:
                paired.append((rows[prev], rows[curr]))
                prev = curr + 1
                curr = prev + 1
            else:
                unpaired.append(rows[prev])
                prev = curr
                curr = prev + 1

if __name__ == "__main__":
    concat_video_horizontally('fragmented.mp4', 'fragmented_2.mp4', 0.4)