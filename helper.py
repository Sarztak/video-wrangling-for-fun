import shutil
from pathlib import Path
import pytesseract
from PIL import Image
import re
import ffmpeg

def detect_text_from_img(input_path):
    image = Image.open(input_path)
    text = pytesseract.image_to_string(image)
    return text

def detect_uchicago(text):
    pattern = re.compile(r"""THE UNIVERSITY OF""")
    match = re.findall(pattern, text)
    return len(match) > 0

def capture_frame(input_path, output_path, time=1):
    # time is in seconds
    output_path = str(output_path) # convert path to string
    ffmpeg.input(input_path, ss=time).output(output_path, frames=1).overwrite_output().run()

if __name__ == "__main__":
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