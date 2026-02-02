import subprocess
import shutil
from pathlib import Path
import pytesseract
from PIL import Image
import re

def detect_text_from_img(input_path):
    image = Image.open(input_path)
    text = pytesseract.image_to_string(image)
    return text

def detect_uchicago(text):
    pattern = re.compile(r"""THE UNIVERSITY OF""")
    match = re.findall(pattern, text)
    return len(match) > 0

def run_cmd(cmd):
    # run the command 
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # check the output
    if result.returncode != 0:
        raise Exception(f"Error : {result.stderr}")


def capture_frame(input_path, output_path, time=1):
    # time is in seconds
    input_path = str(input_path)
    output_path = str(output_path) # convert path to string

    # Build ffmpeg command
    ffmpeg_cmd = [
        'ffmpeg',
        '-ss', str(time),           # Start time
        '-i', input_path,     # Input file
        '-frames:v', '1',     # Number of frames to output
        '-y',                  # Overwrite output files without asking
        output_path           # Output file
    ]    
    run_cmd(ffmpeg_cmd)

if __name__ == "__main__":
    breakpoint()
    image_dir = Path('./images')
    image_dir.mkdir(exist_ok=True, parents=True)
    transfer_dir = Path('./transfer')
    transfer_dir.mkdir(exist_ok=True, parents=True)
    video_dir = Path.cwd()
    video_path_generator = video_dir.glob("*.mp4")
    for video_path in video_path_generator:
        # filename without extension using path.stem
        video_name = video_path.stem
        img_path = image_dir / f"{video_name}.png"
        capture_frame(video_path, img_path, time=0) # capture frame at 0 sec
        text = detect_text_from_img(img_path) # get text from img
        if detect_uchicago(text): # if the image contains THE UNIVERSITY OF then I remove those videos to a separate folder
            new_video_path = transfer_dir / f"{video_name}.mp4"
            shutil.move(video_path, new_video_path)
            breakpoint()