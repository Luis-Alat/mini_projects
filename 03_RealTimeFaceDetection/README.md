# Face recognition

## Getting started

To install the non-standard libraries used here, you can run the folllowing line:

    pip install -r requirements.txt

## Quick tutorial

### Launching face recognition

A script named *RealTimeFaceDetection.py* is provided to run the face detection algorithm. This script offers two methods for face recognition: one based on YouTube videos and the other using your own camera (which is the default behavior).

To run the script using your own camera, you can execute one of the following commands.

    python RealTimeFaceDetection.py --source camera

or

    python RealTimeFaceDetection.py

On the other hand, if the task will be performed on a YouTube video, you will need to specify it and provide a valid URL link to the video as follows:

    python RealTimeFaceDetection.py --source youtube --url my_youtube_video

### Adding user

The script also offers a basic method for adding users to enable recognition of more faces. Similar to performing face recognition on a YouTube video or using the camera, there are two approaches to adding a new user: using preexisting images to load into the model or capturing new pictures with the camera.

If you want to capture pictures with your camera, you'll need to use the arguments **--source** and **--add_person** together in order to do so.

    python --source camera --add_person

Alternatively, if you already have some photos, you'll need to use the following combination

    python --source youtube --url my_youtube_url_video --add_person path_to_folder_with_images

In this case, **--source** should be set to youtube as the value, and **--add_person** should also be set accordingly to specify the path where the images are stored.

### Settings

settings.json is a file that contains the paths to load the trained models and the directory where the user images are stored (referred to as our database). If desired, you can modify this file. However, please be sure that the paths and files exist as per your modifications.
