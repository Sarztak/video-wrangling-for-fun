import shutil
import csv
import json
import subprocess
from pathlib import Path
from helper import capture_frame, detect_text_from_img, run_cmd
from rich.traceback import install; install()

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
    n = int(n) # make integer
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

    # Build ffmpeg command
    ffmpeg_cmd = [
        'ffmpeg',
        '-y', # overwrite the file without asking
        '-i', video0,
        '-i', video1,
        '-filter_complex', f"[1:v]scale={new_v1_w}:{new_v1_h}[v1];[0:v]scale={new_v0_w}:{new_v0_h}[v0_scaled];[v0_scaled]pad={new_v0_w}:{pad_height}:0:{y_offset}:black[v0];[v0][v1]hstack[v]",
        '-map', '[v]',
        '-map', '0:a:0',
        '-c:v', 'libx265',
        '-c:a', 'aac',
        'output_4.mp4'
    ]

    run_cmd(ffmpeg_cmd)

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

def video_over_video(
        base_video_path, overlay_video_path, output_path, width_overlay=320, padding=10, position='top-left', ow_by_bw=0.25,
    ):
    """
    This function will overlay one video over the another. The aspect ratio of the overlay video will be preserved. The overlay video will be resized according to the width_overlay parameter. Additionally, some padding will be added. The position parameter can be top-left, top-right, bottom-left and bottom-right.

    The video to be overlayed has a origin system at the top left corner. To the right is positive in x direction; down is positive y direction. The same is true of the background video, it too has an origin system at top left corner. 
    
    So,
    overlay=0:0 -> overlay's top left aligns with background's top left
    overlay=W-w:0 -> overlay in the top right corner
    overlay=W-w:H-h -> overlay in the bottom right corner
    overlay=10:10 -> overlay 10px to the right and 10px down

    The padding is in pixels; default 10 px
    """
    x, y = 0, 0
    match position:
        case 'top-left':
            x, y = f"{padding}", f"{padding}"
        case 'top-right':
            x, y = f"W-w-{padding}", f"{padding}"
        case 'bottom-right':
            x, y = f"W-w-{padding}", f"H-h-{padding}"
        case 'bottom-left':
            x, y = f"{padding}", f"H-h-{padding}"

    base_video_path = str(base_video_path) 
    overlay_video_path = str(overlay_video_path)
    output_path = str(output_path)

    # scale2ref is not reliable, therefore I will get the true sizes of the videos
    bv_w, bv_h = get_video_dimensions(base_video_path)
    
    # now the math to calcuate the relative width of the ov
    new_ov_w = bv_w * ow_by_bw # I will also keep the relative size the same while scaling
    new_ov_w =_make_even(new_ov_w)
    # build the filter graph
    filter_graph = f'[1:v]scale={new_ov_w}:-1[v1_scaled];[0:v][v1_scaled]overlay={x}:{y}[v]'

    # Build ffmpeg command
    ffmpeg_cmd = [
        'ffmpeg',
        '-y', # overwrite the file without asking
        '-i', base_video_path,
        '-i', overlay_video_path,
        '-filter_complex', filter_graph,
        '-map', '[v]',
        '-map', '1:a',
        '-c:v', 'libx265',
        '-c:a', 'aac',
        output_path
    ]

    run_cmd(ffmpeg_cmd)

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
    return paired, unpaired

if __name__ == "__main__":
    # remove_duplicate_videos()
    # write_video_duration()
    paired, unpaired = make_pairs()
    
    # paired is a list of tuples; each tuple is a pair of two and each member is the name of file and the duration, so I need to unrap it to get the names of the videos
    paired_videos = [(v0[0], v1[0]) for v0, v1 in paired]
    cwd = Path.cwd()
    output_dir = Path('./output')
    images_dir= Path('./images')
    output_dir.mkdir(exist_ok=True, parents=True)
    images_dir.mkdir(exist_ok=True, parents=True)
    _counter = 0
    for (v0, v1) in paired_videos:
        # first I need to determine which one is the base video and which one is the overlay. For that I am going to see which one has text in them. This is a simple observation each background video starts with some text, and if the OCR can detect it then it is background video
        v0_path = cwd / v0
        v1_path = cwd / v1
        v0_img_path = images_dir / f"{v0_path.stem}.png"
        v1_img_path = images_dir / f"{v1_path.stem}.png"
        capture_frame(v0_path, v0_img_path)
        capture_frame(v1_path, v1_img_path)
        v0_text = detect_text_from_img(v0_img_path)
        v1_text = detect_text_from_img(v1_img_path)

        bg_video, overlay_video = None, None
        # there are 4 cases but only two are valid v0 can be either background or overlay and v1 must be different from v0
        if v0_text and not v1_text:
            bg_video = v0_path
            overlay_video = v1_path
        elif not v0_text and v1_text:
            bg_video = v1_path
            overlay_video = v0_path

 
        if bg_video and overlay_video:
            output_path = output_dir / f"overlayed_video_{_counter}.mp4"
            _counter += 1
            video_over_video(bg_video, overlay_video, output_path, width_overlay=240, padding=15, position='bottom-right', ow_by_bw=0.2)

    # concat_video_horizontally('fragmented.mp4', 'fragmented_2.mp4', 0.3)
    # video_over_video('fragmented_2.mp4', 'fragmented.mp4', width_overlay=240, position='bottom-right')