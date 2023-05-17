#!/usr/bin/env python
# coding: utf-8

# In[7]:

import yt_dlp
import cv2
import re
import os
from time import sleep
import shutil
import numpy as np
from PIL import Image
import argparse as arg
import json
import warnings

# In[8]:

def CreateArguments() -> arg.ArgumentParser.parse_args:
    
    '''
    This function creates the arguments of the command line
    
    Returns
    -------
    
    argparse: argparse object created by ArgumentParser.parse_args
    
    '''
    
    args = arg.ArgumentParser(description="Face recognition script to read from the camera or youtube video")
    args.add_argument("--source", dest="source", 
                    type=str, choices=["camera","youtube"],
                    default="camera",
                    help="Choose if face recognition will be done on a youtube video or it'll be using the camera. Default is 'camera'")
    args.add_argument("--url", dest="url",
                    type=str, 
                    help="Url of the youtube video. Ignore if --source 'camera'")
    args.add_argument("--quality", dest="quality",
                    type=str, default="best",
                    help="If --source 'youtube', do face recognition on the youtube video with the quality specified e.g '360p'")    
    args.add_argument("--add_person", const=True, default=False, nargs="?",
                    help="Add a new person to the database. Combined with --source 'camera', the camera will turned on to add a new person, no value is expected. Combined with --source 'youtube', a path to load images to process is expected")
    
    argspa = args.parse_args()

    return argspa
    
def ShowArguments(arguments:arg) -> None:
    
    # This functions shows the arguments
    
    print("##### ARGUMENTS #####\n")
    for args in vars(arguments):
        print("--" + args + ":", getattr(arguments, args))
    print("\n")

def LoadSettings() -> dict:

    # This function loads the json file with the setting of output files and input files

    with open("settings.json", "r") as input_json:
        settings = json.load(input_json)

    return settings

class Users:

    '''
    This class provides some basic methods to handle users such as create
    and load user info (user names and user images)
    '''

    def CreateUser(self, storing_path:str) -> "(str, str)":

        # This method creates the folder to storage a new user info

        # Id to save info of the person
        person_id = input('id to save user (format expected "username_id"): ')

        path = os.path.join(storing_path, person_id)
        print(f"Creating user folder in: {path}")

        if os.path.exists(path):

            while True: 

                option = input("User already exists, continue? [Y][n]: ")

                if option == "Y":
            
                    shutil.rmtree(path)
                    os.makedirs(path)
                    break

                elif option == "n":
            
                    print("Ending script")
                    exit()
            
                else:
                    print("option not recognized")

        else:
            os.makedirs(path)

        print("Done")

        return path, person_id
    
    def LoadUsers(self, storing_path:str) -> dict:

        # This method loads the user name and user ids from the folder name in the database

        # Filtering the path to get only the user folder and retrieving name and id
        all_folder_users = os.listdir(storing_path)

        user_map = {}

        for full_user in all_folder_users:

            user_full_id = full_user.split("_")

            # Fisrt element is the name and second one is the number id
            user_map[int(user_full_id[1])] = str(user_full_id[0])

        return user_map
    
    def LoadImageUsers(self, user_path_database:str) -> "(list, np.array)":

        # This method loads the images of the users
        
        user_full_names = os.listdir(user_path_database)
        user_images = []
        user_ids = []

        for user in user_full_names:
            
            full_path = os.path.join(user_path_database, user)
            images_path = os.listdir(full_path)
            images_path = [os.path.join(full_path, image) for image in images_path]
            ids = int(user.split("_")[1])

            for image in images_path:
                matrix_image = np.array(Image.open(image))
                user_images.append(matrix_image)
                user_ids.append(ids)

        return user_images, np.array(user_ids).reshape(-1,)

class CaptureModel:

    '''
    This class provides methods to create, load and verify the models of face recognition and
    face detection. In addition, this class allows to create the capture or source of information
    where the face recognition task will be done
    '''

    def CreateCapture(self, source:int|str) -> cv2.VideoCapture:
        
        self.capture = cv2.VideoCapture(source)
        
        if not self.capture.isOpened():
            raise Exception("Can't be possible to open the video/camera")

    def CreateModels(self, settings:dict) -> "(cv2.CascadeClassifier, cv2.face.LBPHFaceRecognizer_create)":

        print("Loading models")

        self.face_detection = cv2.CascadeClassifier(settings["models"]["training"]["cascade"])
        self.face_recognition = cv2.face.LBPHFaceRecognizer_create()

        if os.path.isfile(settings["models"]["training"]["lbph"]):
            print("\tLoading pre-trained model")
            self.face_recognition.read(settings["models"]["training"]["lbph"])
        else:
            print("Pre-trained model was not found")
        
        print("Done")
    
    def FaceRecognition(self, capture:cv2.VideoCapture, face_detection:cv2.CascadeClassifier,
                        face_recognition:cv2.face.LBPHFaceRecognizer, title:str, user_maps:dict) -> None:
        
        font = cv2.FONT_HERSHEY_DUPLEX

        while True:
            ret, frame = capture.read()
    
            if not ret:
                print("Video has ended")
                break
        
            # Gray scale converting
            gray_scale_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
            # Face detection front and profile
            location_face_frontal = face_detection.detectMultiScale(gray_scale_frame, 1.2, 5)        
        
            for (x, y, w, h) in location_face_frontal:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                user_id, confidence = face_recognition.predict(gray_scale_frame[y:y+h, x:x+w])

                if confidence < 90:
                    user = user_maps[user_id]
                    confidence = f" {int(100 - confidence)}"
                else:
                    user = "Unknown"
                    confidence = f" {int(100 - confidence)}"

                cv2.putText(frame, str(user), (x+5, y-5), font, 1, (255,255,255), 2)
                cv2.putText(frame, str(confidence), (x+5, y+h-5), font, 1, (255,255,0), 1) 

            cv2.imshow(title, frame)

            if cv2.waitKey(30) & 0xFF == ord('q'):
                break
    
        capture.release()
        cv2.destroyAllWindows()

class YoutubeRecognition(CaptureModel, Users):
    
    '''
    This class allows to do the task of face recognition on youtube videos and add users to the database
    based on a serie of images
    '''

    def __init__(self, arguments:arg, settings:dict) -> None:

        # Initializing youtube video object
        ydl = yt_dlp.YoutubeDL({})
        self.settings = settings

        # Loading youtube video data
        self.url = arguments.url
        info_dict = ydl.extract_info(arguments.url, download=False)
        video_title = info_dict["title"]
        video_title = self.__RemoveSpecialChar(video_title)

        # Get video formats available
        formats = info_dict.get('formats', None)

        # Check if the video resolution is available
        is_present_res = self.__CheckResolution(formats, arguments.quality)

        if not is_present_res:
            raise Exception("Resolution not available")

        # Several formats ara avilable with the same resolution, returns the last format found with -1
        last_format = self.__GetMetaVideo(formats, is_present_res, -1)
    
        self.video_title, self.last_format = video_title, last_format

        # Creating capture to read video and loading models (face detection and face recognition)
        super().CreateCapture(self.last_format["url"])
        super().CreateModels(self.settings)

    def __CheckResolution(self, formats:"yt_dlp.YoutubeDL.extract_info.get('formats')",
                    resolution:str = "best") -> list[dict]:
    
        '''

        Check if the resolution supplied is avilable, otherwise return False

        Parameters
        ----------

        formats:list[dict]
            list of diccionaries obtained from yt_dlp.YoutubeDL.extract_info.get('formats')

        resolution:str, default "best"
            string indicating to check the resolution, e.g "144p", "360p", "1080p60", etc 


        Returns
            str|bool: str indicating resolution if available, otherwise returns bool False

        '''

        if resolution != "best":

            matches = [resolution for f in formats if f.get("format_note", None) == resolution]
            matches_len = len(matches)

            return resolution if matches_len else False

        max_resolution_available = {"res": "0p"}

        for f in formats:
    
            current_res = f.get("format_note", "0p")
        
            # Only retrieving if metadata is describing some numeric value
            if bool(re.match("^\d+", current_res)):
                current_pixels = re.split("[A-Za-z]", current_res)[0]
                current_pixels = int(current_pixels)
            
                before_pixels = re.split("[A-Za-z]", max_resolution_available["res"])[0]
                before_pixels = int(before_pixels)
            
                max_res = current_res if current_pixels > before_pixels else max_resolution_available["res"] 
                max_resolution_available["res"] = max_res 
            
        return max_resolution_available["res"]

    def __GetMetaVideo(self, formats:"yt_dlp.YoutubeDL.extract_info.get('formats')",
                    resolution:str, which:int=-1) -> dict:

        # This method returns the format (video) with the resolution asked
        url_options = [f for f in formats if f.get("format_note") == resolution]
        return url_options[which]

    def __RemoveSpecialChar(self, string:str) -> str:
        # This method returns a string with only ascii characters
        return re.sub(r'[^\x00-\x7F]+',' ', string)
    
    def __CreateTrainData(self, path_images:str, storage_path:str, user_name:str) -> "(list, np.array)":
        
        '''
        This function creates the training data used to do the task of face recognition. This
        training data will be the same used to storage in the database of users

        Parameters
        ----------

        path_images: str
            Path where the images of the new user is storaged
        
        storage_parh: str
            Path where the processed images of the new user will be saved. A database

        user_name: str
            Full id/name of the new user that will be added in format username_numericid
        
        Returns
        -------
            (images=list, ids=np.array): List of numpy arrays containing the images of the new user
                and one dimentional numpy array containing the full id/name of the new user

        '''

        images_path = os.listdir(path_images)
        images_array = [Image.open(os.path.join(path_images, image)) for image in images_path]
        images_array = [np.array(image) for image in images_array]
        train_images = []
        ids = []

        count_positive_images = 0
        for file_name, image in zip(images_path, images_array):

            print(f"Processing image: {file_name}")
            print(f"Image shape: {image.shape}")

            try:

                gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                face_location = self.face_detection.detectMultiScale(gray_image, 1.2, 5)

                # Only one face is expected by image
                if len(face_location) == 1:

                    for (x, y, w, h) in face_location:
                        
                        face_filtered = gray_image[y:y+h, x:x+w]
                        train_images.append(face_filtered)
                        ids.append(int(user_name))

                        new_file_name = user_name + "_" + str(count_positive_images) + ".png"
                        full_path_new_image = os.path.join(storage_path, new_file_name)
                        Image.fromarray(face_filtered).save(full_path_new_image)

                        count_positive_images += 1
            except:
                warnings.warn("Image shape not supported. Skipping image")

        if count_positive_images < 10:
            warnings.warn("Less than 10 images were succesfully processed. Training face recognition could fail")

        return train_images, np.array(ids).reshape(-1,)
    
    def AddUser(self, path_new_data:str):

        # This method create the folder of the new user, process the new user data and train the
        # face recognition algorithm with the new data 

        path_storage_new_user, person_id = self.CreateUser(self.settings["data_base"]["users"])

        user_number = person_id.split("_")[1]

        # Open the images found in path supplied
        # and transform the images using a gray scale and filter the faces
        _, _ = self.__CreateTrainData(path_new_data, path_storage_new_user, user_number)

        # Retraining with all the users, unknown behavior using train(), does it forget the old training?
        train_images, ids = self.LoadImageUsers(self.settings["data_base"]["users"])

        # Re-Train and save new weights
        self.face_recognition.train(train_images, ids)
        self.face_recognition.save(self.settings["models"]["training"]["lbph"])

    def RunRecognition(self):

        # Run the recognition task

        # Load the dict to map the numeric id with the name of the user
        self.user_maps = self.LoadUsers(self.settings["data_base"]["users"])
        print(self.user_maps)

        # Launch face recognition
        super().FaceRecognition(self.capture, self.face_detection,
                                self.face_recognition, self.video_title, self.user_maps)

class CameraRecognition(CaptureModel, Users):

    '''
    This class allows to do the task of face recognition using the camera integrated
    in the current device and add users to the database based on images that will be
    captured using the camera
    '''

    def __init__(self, settings:dict) -> None:

        self.settings = settings
        
        # Creating capture to read video and models
        super().CreateCapture(0)
        super().CreateModels(settings)
    
    def CaptureUser(self, capture:cv2.VideoCapture, user_id:str, path:str,
                    face_detection:cv2.CascadeClassifier) -> None:

        '''
        This method launch the camera to capture a new user. 30 pictures will be taken

        Parameters
        ----------
        
        capture:cv2.VideoCapture
            cv2.VideoCapture() object to launch the camera of the current device
        
        user_id:str
            Full user name/id of the new user

        path:str
            Path where the new user information (images) will be saved. A database

        face_detection:cv2.CascadeClassifier
            cv2.CascadeClassifier() object to do the face recognition task and filter face from the images
            taken by the camera

        '''

        for i in range(5, 0,-1):
            print(f"Capturing user. Launching camera in {i} secs", end="\r")
            sleep(1)
        print("")

        count_frame = 0

        while(count_frame < 30):

            _, frame = capture.read()

            gray_scale_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            location_face_frontal = face_detection.detectMultiScale(gray_scale_frame, 1.2, 5)

            for (x,y,w,h) in location_face_frontal:

                cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,0), 2)     

                # Save current positive frame into data/users
                file_name = str(user_id) + "_" + str(count_frame) + ".jpg"
                full_path = os.path.join(path, file_name)

                cv2.imwrite(full_path, gray_scale_frame[y:y+h,x:x+w])

                cv2.imshow('Frame Capturing', frame)

                count_frame += 1

                sleep(0.25)

            if cv2.waitKey(30) & 0xFF == ord('q'):
                break

        cv2.destroyAllWindows()

    def AddUser(self, launch):
        
        # This method creates the folder of the new user, take and process the new user data
        #  and train the face recognition algorithm with the new data 

        #######
        ### Argument launch is not actually used in this class, but it is used with the youtube class
        #######

        # Creating user folder
        path_storage_new_user, person_id = self.CreateUser(self.settings["data_base"]["users"])
        
        # Launching camera and taking photos
        self.CaptureUser(self.capture, person_id, path_storage_new_user, self.face_detection)

        # Loading all users in database and retraining
        train_images, ids = self.LoadImageUsers(self.settings["data_base"]["users"])
        self.face_recognition.train(train_images, ids)

        # Saving new weights
        self.face_recognition.save(self.settings["models"]["training"]["lbph"])

    def RunRecognition(self):

        # Run the recognition task

        # Load the dict to map the numeric id with the name of the user
        self.user_maps = self.LoadUsers(self.settings["data_base"]["users"])
        print(self.user_maps)

        super().FaceRecognition(self.capture, self.face_detection,
                                self.face_recognition, "Camera", self.user_maps)



# In[ ]:


if __name__ == "__main__":
    
    settings = LoadSettings()

    args = CreateArguments()
    ShowArguments(args)
    
    if args.source == "youtube":
        face_recognition = YoutubeRecognition(args, settings)
    else:
        face_recognition = CameraRecognition(settings)

    if args.add_person:
        face_recognition.AddUser(args.add_person)

    face_recognition.RunRecognition()
    