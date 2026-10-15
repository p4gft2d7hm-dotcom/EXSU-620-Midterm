# EXSU-620-Midterm
Hi guys! I've uploaded the code for our EXSU 620 project to GitHub!

Here's the link: https://github.com/p4gft2d7hm-dotcom/EXSU-620-Midterm

I've worked on the software side of our repositioning monitoring patch and created a simulator so we can test the system before building the physical prototype next week.

What the simulator does:

Simulates a patient's movements and detects whether they're lying on their back, left side, right side, or upright.
Distinguishes effective repositioning from small movements that shouldn't count as a proper turn.
Tracks the time since the last effective turn and determines when the patient needs to be repositioned.
Simulates the alert system, including a warning 15 minutes before the repositioning deadline and a critical alert if the patient hasn't been turned.
Displays the monitoring information and recorded events on a dashboard.
The simulator speeds up time so that 2 hours pass in just 2 minutes, allowing us to test the alerts without waiting for the full repositioning interval.

How to try it:

Download the project files from GitHub and open them in VS Code.
Install the dependencies listed in requirements.txt.
Open the terminal and run python server.py --simulate --http 8000.
Open Google Chrome and enter http://127.0.0.1:8000/
This is essentially the software foundation for our prototype. Next week, we'll need to connect the Raspberry Pi and motion sensor, test the readings with actual movements, and integrate the physical LED and speaker alerts.

Feel free to take a look and let me know what you think or if anything needs to be adjusted!
