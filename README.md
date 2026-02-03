I woke up on Sunday morning and didn't know what to do when I opened my Downloads folder and then opened another folder where these video files were stored 
['fragmented_2.mp4', 'fragmented_4.mp4', 'fragmented_5.mp4', 'index (448p)_10.mp4', 'index (448p)_11.mp4', 'index (448p)_12.mp4', 'index (448p)_13.mp4', 'index (448p)_3.mp4', 'index (448p)_5.mp4', 'index (448p)_7.mp4', 'index (480p_aac)_10.mp4', 'index (480p_aac)_11.mp4', 'index (480p_aac)_12.mp4', 'index (480p_aac)_13.mp4', 'index (480p_aac)_14.mp4', 'index (480p_aac)_2.mp4', 'index (480p_aac)_3.mp4', 'index (480p_aac)_5.mp4', 'index (480p_aac)_6.mp4', 'index (480p_aac)_7.mp4', 'index (480p_aac)_8.mp4', 'index (480p_aac)_9.mp4', 'index (896p).mp4', 'index (896p)_2.mp4', 'index (896p)_3.mp4','index (448p_aac).mp4', 'index (448p_aac)_2.mp4', 'index (448p_aac)_3.mp4', 'index (448p_aac)_4.mp4', 'index (448p_aac)_5.mp4', 'index (480p_aac).mp4', 'index (634p_aac).mp4', 'index (634p_aac)_2.mp4', 'index (896p_aac).mp4', 'index (896p_aac)_2.mp4', 'index (896p_aac)_3.mp4', 'index (896p_aac)_4.mp4' ]

Looking at these files it was not clear what I was supposed to do, and that exactly was the task perfect for a Sunday. You see these files had a pattern, so of them were just recording of presentation - a powerpoint presentation or just something written on an Apple Ipad and then there was the video of my teacher with his voice. So somehow I ended up downloading two split files one containing just the recording of his screen and then another one which has his self recording with his voice in it. But these two were linked because they were recorded at the same time. 

But not all files were in pair, some of them were solo as well that didn't require a partner. Here again after looking at them, I saw a pattern.

And yet another thing was clear that I had also downloaded duplicate files with different resolution or quality. 

Hence this was the iternary of tasks
1. Detect and delect the duplicate files
2. Merge the split files
3. Separate the files that didn't require merging

Luckily there were some patterns or some hints that could be harness to do so. 

For this task the main tools were python, pytessaract with Tessaract for windows, ffmpeg, pillow for reading image. 

### What were the patterns in this data ? 

1. Videos of different qualities still had the same length or duration therefore I could read them using ffmpeg and then output their durations or write them somewhere. Then I decided to keep the one with the highest quality which was simply determined by measuring the size of the file. Here I __assumed that size is proportional to quality__. The size was measured using pathlib library which also is the only library that I use to handle paths before which my life was miserable and working with paths was no fun. I send all the vidoes that I didn't need to delete folder 

2. The videos that didn't need merging had the first frame containing the name and logo of my university - **THE UNIVERSITY OF CHICAGO**. What I did was again use ffmpeg to get the frame at 1 sec and then used `tesseract` to exctract the text from the images. And then if I was able to detect the name of my university then bingo, I send those files to a badly named folder called transfer. 

3. Now how do I find the pairs of file ? One easy was to look at their duration. So I again used ffmpeg to get their duration in seconds and dumped a data to a `.csv` file like a true data scientist. 

**This was my internal monologue at that point**

    looking at this data. I am trying to determine which videos are actually a pair, meaning that they are two sides of the same coin based on the information that I have about their duration. The list is already sorted by the duration. But as I was thinking about a way to make pairs while at the same time having no baked in assumption, I thought that it is not possible to resolve some ambiguous cases by knowing only the duration of the videos. Consider the case that there are somewhere 4 videos 1, 2, 3, 4 . In reality 1-2 and 3-4 are pairs but the distance between 1 to 2 is greater than distance between 2 to 3 and also less that distance between 3 to 4. Now the method that I was considering was comparing triples given that the array is already sorted and then to decide which one is the pair I will select those that have the smallest distance between themselves but then according to the case that I gave distance alone cannot resolve that case.

    Which means that I need to assume that the first two videos that have a distance less than say 2 sec are the pairs. 

    okay then here is the assumption that I am going to make, the first pair that occurs will be consider pairs. the condition to make the pair is just that the distance should be less that 2 sec, which I choose arbitrarily by looking at the data.

    so if something gets pair then I will advance by 2 and if it does not then I will advance by 1

    Through experimentation I figured that keeping the aspect ratio of presentation is important
    Also it is better to keep the video where teacher is talking to the left rather than to the right

The gist is I made some assumptions to find the answer because just using the duration of videos was insufficient information. But in this case it was cheap to try out and so I did. 

Now the most fun and frustrating part. How do I want to merge the videos. There were two options
1. I could lay them side by side
2. I could overlay the speaker video over the presentation

After experimentation I decided that overlay was better, but then I couldn't decide where should I place the speaker video - in the right corner, or in the left corner, in the top or at the bottom. Every thing seemed weird, but finally I decided that okay I don't care I will place it at the bottom right corner. 

The again I used ffmpeg to overlay one video over the top of another in 11/13 cases this was successful. 

In one case I discovered that I was not able to delete a duplicate video so I deleted it

In one last case the assumption of paired videos differing by just 2 sec or less didn't hold. But the two videos that were different by 10 sec turned out to be pairs so I merged them using their names. 

And that is how I spend my Sunday. 

I learned a lot about handling paths, how versatile ffmpeg is, how I can actually think about solving problems based on patterns. And the most important I finally watched the videos that  **I was supposed to watch before that class**. But now I am watching them after graduation. It doesn't matter though because learning never stops. 

