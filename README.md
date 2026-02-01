look at this data. I am trying to determine which videos are actually a pair, meaning that they are two sides of the same coin based on the information that I have about their duration. The list is already sorted by the duration. But as I was thinking about a way to make pairs while at the same time having no baked in assumption, I thought that it is not possible to resolve some ambiguous cases by knowing only the duration of the videos. Consider the case that there are somewhere 4 videos 1, 2, 3, 4 . In reality 1-2 and 3-4 are pairs but the distance between 1 to 2 is greater than distance between 2 to 3 and also less that distance between 3 to 4. Now the method that I was considering was comparing triples given that the array is already sorted and then to decide which one is the pair I will select those that have the smallest distance between themselves but then according to the case that I gave distance alone cannot resolve that case.

Which means that I need to assume that the first two videos that have a distance less than say 2 sec are the pairs. 

okay then here is the assumption that I am going to make, the first pair that occurs will be consider pairs. the condition to make the pair is just that the distance should be less that 2 sec, which I choose arbitrarily by looking at the data.

so if something gets pair then I will advance by 2 and if it does not then I will advance by 1

Through experimentation I figured that keeping the aspect ratio of presentation is important
Also it is better to keep the video where teacher is talking to the left rather than to the right