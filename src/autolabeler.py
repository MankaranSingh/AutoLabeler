import tkinter
import cv2
import PIL.Image, PIL.ImageTk
import time
import glob
import os
import pandas as pd
from time import time
import sys, getopt

argv = sys.argv[1:]

WIDTH = 640
HEIGHT = 420
datafile = ''
basedir = './'
savefile = './output.csv'
labels = ['disable', 'undefined', 'stay_in_lane', 'change_lane_left',
          'change_lane_right', 'turn_left',
          'turn_right']


try:
    opts, args = getopt.getopt(argv,"b:d:h:w:s:",["basedir=","datafile=", "height=", "width=", "savefile="])
except getopt.GetoptError:
    print('following arguements are supported:\n -b <basedir> -d <datafile> -h <height> -w <width> -s <savefile>')
    sys.exit(2)
    
    
for opt, arg in opts:
    if opt in ('-b', '--basedir'):
        basedir = arg
    if opt in ("-d", "--datafile"):
        datafile = arg
    if opt in ("-h", "--height"):
        HEIGHT = int(arg)
    if opt in ("-w", "--width"):
        WIDTH = int(arg)
    if opt in ("-s", "--savefile"):
        savefile = arg


if not datafile:
    print('No datafile provided.. Exiting..')
    sys.exit(2)

data = pd.read_csv(datafile)

if 'filename' in data.columns:
    filenames = data['filename']
else:
    print("No 'filename' column found in datafile.. exiting")
    sys.exit(2)

if 'action' in data.columns:
    actions = data['action']
else:
    print("WARNING: 'action' column not found in datafile. initializing to undefined actions..")
    actions = pd.Series(['undefined']*len(filenames))


class App:
    def __init__(self, window, window_title, video_source=[], labels=[], actions=[], basedir='./', columns=20, savefile='./output.csv'):
        self.window = window
        self.window.resizable(0, 0)
        self.window.title(window_title)
        self.video_source = video_source
        self.basedir = basedir
        self.labels = labels
        self.actions = actions
        self.savefile = savefile
        self.current_label = tkinter.StringVar(self.window)
        self.current_label.set(self.labels[0])
        self.playing = False
        self.vid = VideoCapture(self.video_source)

        # Create a canvas that can fit the above video source size
        self.canvas = tkinter.Canvas(window, width=WIDTH, height=HEIGHT)
        self.canvas.grid(row=0, columnspan=columns)

        self.slider = tkinter.Scale(window, from_=0, to=len(video_source),
                                    length=WIDTH, sliderrelief='flat',
                                    orient="horizontal", highlightthickness=0, background='#454545',
                                    fg='grey', troughcolor='#1a1a1a',
                                    activebackground='#1065BF', command=self.seek)
        self.slider.grid(row=1, columnspan=columns)

        self.btn_play=tkinter.Button(window, text=u"\u25B6", command=self.play, activebackground='#1a1a1a')
        self.btn_play.grid(row=3, column=columns//2 - 2, sticky='NEWS')
        
        self.btn_pause=tkinter.Button(window, text=u"| |", command=self.pause, activebackground='#1a1a1a')
        self.btn_pause.grid(row=3, column=columns//2-1, sticky='NEWS')

        self.drop_down = tkinter.OptionMenu(window, self.current_label, *self.labels)
        self.drop_down.grid(row=3, column=columns-1, sticky='NEWS')

        self.display_label = tkinter.Label(self.window)
        self.display_label.grid(row=3, column=0, sticky='NEWS')

        self.btn_faster=tkinter.Button(window, text=">>", command=self.faster, activebackground='#1a1a1a')
        self.btn_faster.grid(row=3, column=columns//2 , sticky='NEWS')

        self.btn_slower=tkinter.Button(window, text="<<", command=self.slower, activebackground='#1a1a1a')
        self.btn_slower.grid(row=3, column=columns//2-3 , sticky='NEWS')
        
        # After it is called once, the update method will be automatically called every delay milliseconds
        self.delay = 64
        self.index = 0
        self.update()
        self.window.configure(bg='#e0e0e0')
        self.window.mainloop()
        

    def pause(self):
        self.playing = False

    def play(self):
        self.playing = True

    def faster(self):
        self.delay -= 10
    
    def slower(self):
        self.delay += 10

    def speed_buttons_controller(self):
        if self.delay <= 104:
            self.btn_slower["state"] = "normal"
        else:
            self.btn_slower["state"] = "disabled"

        if self.delay >= 24: 
            self.btn_faster["state"] = "normal"
        else:
            self.btn_faster["state"] = "disabled"
         
    def update(self):

        if self.index >= len(self.video_source) - 1:
            self.index = 0
            self.pause()

        # Get a frame from the video source
        ret, frame = self.vid.get_frame(self.basedir, self.index)

        if ret:
            self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
            self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)

        self.window.after(self.delay, self.update)

        self.display_label.configure(text='Current Action: ' + self.actions[self.index])
        
        if self.playing:
            if self.current_label.get() != 'disable':
                self.actions[self.index] = self.current_label.get() 
            self.index += 1
            self.slider.set(self.index)

        self.speed_buttons_controller()
        

    def seek(self, index):
        self.index = int(index)
        self.slider.set(self.index)

    def __del__(self):
        df = pd.DataFrame({'filename':self.video_source, 'action':self.actions})
        df.to_csv(self.savefile, index=False)


class VideoCapture:
    def __init__(self, video_source=[]):
        
        self.frames = video_source
        self.width = WIDTH
        self.height = HEIGHT

    def get_frame(self, basedir, index):
        try:
            frame = cv2.imread(os.path.join(basedir, self.frames[index]))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return (True, cv2.resize(frame, (WIDTH, HEIGHT)))
        
        except Exception as e:
            print(e)
            return (False, None)
        
App(tkinter.Tk(), 'AutoLabeler', video_source=filenames, labels=labels, actions=actions, savefile=savefile, basedir=basedir)
