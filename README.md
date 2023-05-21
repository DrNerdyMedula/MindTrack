## Inspiration
Our team sought to develop an innovation aimed at alleviating the stress experienced by college students and enhancing their information retention capabilities. This venture was spurred on by a series of discussions I (Vraj) had with medical students at UC Davis Medical School and other institutions, who expressed a shared frustration: despite investing over six hours daily into their studies, they struggled to retain the information. This suggested a pervasive issue of diminishing focus over time, a problem potentially linked to a myriad of factors including sleep deprivation, which could lead to diminished concentration, delayed reaction times, and a reduced attention span. Other potential obstacles include an abundance of distractions within the study environment, detracting attention away from study materials.

To address this, we engineered a classifier which incorporates an openBCI Cyton board and an Arduino system, designed to send an audio signal to alert the user when their focus is waning. As we delved further into the development process, it became clear that this was not the endpoint, but rather a starting point. During our hardware testing, we discovered the potential of utilizing focus as a functional input for various applications.

Due to time constraints, we could only demonstrate this concept through the operation of a single motor as a functional representation. However, we firmly believed that if one motor could function in this capacity, so could multiple motors. This belief formed the foundation of our additional concept: a drone controlled through focus, alongside other elements like a gyroscope.

## What it does
The OpenBCI Cyton board sends the signal to a program that we built using python. The program has high-pass and low-pass filters to remove excess noise from the signal it gets, it then sorts the data value from each thread and uses an algorithm to calculate a singular value of frequency it works with. The frequency can be used to classify different states of the user's brain. This classifer then sends commands directly to the arduino, which triggers the arduino code to run. This all happens live-time. 

## How we built it
We used Virtual Studio Code to program a python classifier, the code has a library that communicates with the OpenBCI Cyton board, and translate the information in numberical values, and sends the code to arduino. The string output that arduino recieves then responds to it depending on what it is. The arduino code has 2 possible outcomes, whether a user is focused or un-focused. The arduino is connected to two breadboards, one of them has an LCD screen and an active buzzer that vibrates when the user is not focused. We added a delay in the code of about 110ms so there is a buffer period for the user to get back in focus after a brief interaction that might signal them unfocused. 

## Challenges we ran into
Hardware mostly, it was hard to connect arduino into two different breadboards that connect and run simultaneously. We ended up spending the whole night on it, and just bypassing the ground plug-in issue by inserting two leads in the same place on the breadboard. 

## Accomplishments that we're proud of
It works, the program and classifier is just perfect when it comes to analyzing focus vs un-focus. Incorporation of different material last minute, which was unplanned but that functioning as expected too. 

## What we learned
How to deal with issues in python, arduino, and hardware connection with arduino. How to better prepare for Hack-a-thons since it was our first one ever.

## What's next for MindTrack
Incorporation of the drone idea. We will also look at other applications of using focus as an input where it can advance medicine. Our focus would be on combining the knowledge of neuroscience and engineering. 
