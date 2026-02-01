import shutil
from pathlib import Path
import os

def main():
    curr_dir = Path.cwd() # current directory
    
    # iterate through all the items in the current directory
    # to find the folders using is_dir()
    folders = [item for item in curr_dir.iterdir() if item.is_dir()]

    for folder in folders:
        # now copy all the files in the folders to the current directory
        # in case of a name conflict rename the file
        # to get the name of the file using path.name
        # to get only the name use path.suffix
        # to get only the name without suffix using path.stem
        for item in folder.iterdir():
            # here the assumption is that each item is just a file and not a folder
            if item.is_file():
                new_item_name = item.name
                idx = 0
                while (curr_dir / new_item_name).exists():
                    idx += 1 
                    new_item_name = f"{item.stem}_{idx}.{item.suffix}"
                shutil.copy(item, curr_dir / new_item_name)
            else:
                # if not a file then copy the entire folder along with all the files to the curr_directory
                shutil.copytree(item, curr_dir)
if __name__ == "__main__":
    main()

    # three suggestion to map the videos

    # picture in picture like zoom - small box in right corner
    # ffmpeg -i presentation.mp4 -i teacher.mp4 -filter_complex "[0:v][1:v]overlay=W-w-10:10[v]" -map "[v]" -map 1:a -c:v libx264 -c:a aac output.mp4
    breakpoint()
    # ffmpeg -i presentation.mp4 -i teacher.mp4 -filter_complex "[0:v][1:v]hstack=inputs=2[v]" -map "[v]" -map 1:a -c:v libx264 -c:a aac output.mp4
    # ffmpeg -i presentation.mp4 -i teacher.mp4 -filter_complex "[0:v]scale=1280:720[v0];[1:v]scale=1280:720[v1];[v0][v1]hstack=inputs=2[v]" -map "[v]" -map 1:a -c:v libx264 -c:a aac output.mp4