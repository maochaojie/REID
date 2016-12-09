from math import *
import glob
import random
import sys
import os

from multiprocessing import Pool 
from experiments_py.common_tools.base_input_layer import videoRead
from experiments_py.common_tools.ProgressBar import *
# def progresslog(s,i):
#     sys.stdout.write(s+':{0:3}/{1:3}:'.format(i, 100)+'#'*i+'->'+'\r')
def processList(filelistname,frames_l,balance,height,width,list_num):
    video_dict = {}
    videokey = int(filelistname.split(' ')[0])
    video_dict[videokey] = {}
    video_dict[videokey]['frames'] = []
    video_dict[videokey]['frames_p'] = []

    filename = filelistname.split(' ')[1]
    filepre = filename.split('/')[-1]
    fileser = filename.split('/')[-3]+'/'+filename.split('/')[-2]
    fileTem = filename[:-8]+'%04d'+filename[-4:]
    # print fileTem
    startID = int(filename[-8:-4])
    if frames_l>1 :
        if balance == True:
            # file_list = glob.glob(fileser)
            # file_list.sort()
            file_num = list_num[fileser]
            endID = startID+ frames_l
            if endID > file_num:
                startID = file_num - frames_l
            index = 0
            count = 0
            while(count < frames_l):
                filerename = fileTem%(startID+index)
                if os.path.isfile(filerename):
                    video_dict[videokey]['frames'].append(filerename)  # should verify
                    count += 1
                index += 1  
        else:
            for i in range(frames_l):
                video_dict[videokey]['frames'].append(filename)
    else:
         video_dict[videokey]['frames'].append(filelistname.split(' ')[1])

    filename = filelistname.split(' ')[2]
    filepre = filename.split('/')[-1]
    fileser = filename.split('/')[-3]+'/'+filename.split('/')[-2]
    fileTem = filename[:-8]+'%04d'+filename[-4:]
    startID = int(filename[-8:-4])
    if frames_l>1:
        file_num = list_num[fileser]
        endID = startID+ frames_l
        if endID > file_num:
            startID = file_num - frames_l
        index = 0
        count = 0
        while(count < frames_l):
            filerename = fileTem%(startID+index)
            if os.path.isfile(filerename):
                video_dict[videokey]['frames_p'].append(filerename)  # should verify
                count += 1
            index += 1 
    else:
         video_dict[videokey]['frames_p'].append(filelistname.split(' ')[2])  # should verify

    video_dict[videokey]['reshape'] = (height, width)
    video_dict[videokey]['crop'] = (height, width)

    video_dict[videokey]['label'] = []
    video_dict[videokey]['label'].append(int(filelistname.split(' ')[3]))

    return video_dict


class listprocessor(object):
    def __init__(self, frames_l,balance,height,width,list_num):
        self.frames_l = frames_l
        self.balance = balance
        self.height = height
        self.width = width
        self.list_num = list_num

    def __call__(self, filename):
        return processList(filename, self.frames_l, self.balance , self.height, self.width, self.list_num)

def readlistFromFile(video_list,num_list,frames_l,balance,height,width):

    f = open(video_list, 'r')
    f_lines = f.readlines()
    # print f_lines
    f.close()
    f = open(num_list, 'r')
    f_list = f.readlines()
    # print f_lines
    f.close()
    num_dict = {}
    for line in f_list:
        key = '%s/person_%04d'%(line.split(' ')[0],int(line.split(' ')[1]))
        num_dict[key] = int(line.split(' ')[2])
    
    pool_size = 24
    pool = Pool(processes=pool_size)
    processor = listprocessor(frames_l,balance,height,width,num_dict)
    
    video_dict = {}
    video_dicList = []
    new_lines = []
    video_order = []
    c = 0
    total = len(f_lines)
    point = total/100
    for ix, line in enumerate(f_lines):
        newline = str(ix)+' '+line 
        new_lines.append(newline)
        if ix%point == 0 and ix > 0:
            # print len(new_lines)
            video_dict_buffer = pool.map(processor,new_lines)
            video_dicList.extend(video_dict_buffer)
            
            new_lines = []
            progresslog('data list is loading',ix/point)
    video_dict_buffer = pool.map(processor,new_lines)
    video_dicList.extend(video_dict_buffer)
    # video_order.extend(video_order)
    pool.close()
    pool.join()
    for entity in video_dicList:
        key = entity.keys()[0] 
        video_dict[key] = entity[entity.keys()[0]]
    # video_dict = video_dicList
    video_order = video_dict.keys()
    # print video_order
    print 'video_list:%s'%(video_list)
    print 'list example:'
    print random.choice(video_dict)
    return [video_dict,video_order]




Train_batch_size = 12
Test_batch_size = 12
Train_frames_l = 3 #SEQUENCE LENGTH
Test_frames_l = 3
chnnels = 3
height = 160
width = 80
path_root = './'

TrainVideolist ='dataset/Prid2011/split/img_seq/MultiShot_set01_train.txt'
TestVideolist ='dataset/Prid2011/split/img_seq/MultiShot_set01_test.txt'
TrainVideolistFlow =''
TestVideolistFlow =''
affine = True
multylabel = False
balance = True #if True then seq-seq;else then img-seq
Numlist = 'dataset/Prid2011/split/totalNumListDict.txt'





class videoReadTrain_flow(videoRead):

  def initialize(self):
    self.train_or_test = 'train'
    self.flow = True
    self.buffer_size = Train_batch_size  #num videos processed per batch
    self.frames = Train_frames_l   #length of processed clip
    self.N = self.buffer_size*self.frames
    self.idx = 0
    self.channels = chnnels
    self.height = height
    self.width = width
    self.path_to_images = path_root  # the pre path to the datasets
    video_dict = readlistFromFile(TrainVideolistFlow,Numlist,self.frames,balance,self.height,self.width)
    self.video_dict = video_dict[0]
    self.video_order = video_dict[1]
    self.num_videos = len(self.video_dict)
    self.multylabel = multylabel
    self.affine = affine

class videoReadTest_flow(videoRead):

  def initialize(self):
    self.train_or_test = 'train'
    self.flow = True
    self.buffer_size = Test_batch_size  #num videos processed per batch
    self.frames = Test_frames_l   #length of processed clip
    self.N = self.buffer_size*self.frames
    self.idx = 0
    self.channels = chnnels
    self.height = height
    self.width = width
    self.path_to_images = path_root  # the pre path to the datasets
    video_dict = readlistFromFile(TestVideolistFlow,Numlist,self.frames,balance,self.height,self.width)
    self.video_dict = video_dict[0]
    self.video_order = video_dict[1]
    self.num_videos = len(self.video_dict)
    self.multylabel = multylabel
    self.affine = affine

class videoReadTrain(videoRead):

  def initialize(self):
    self.train_or_test = 'train'
    self.flow = False
    self.buffer_size = Train_batch_size  #num videos processed per batch
    self.frames = Train_frames_l   #length of processed clip
    self.N = self.buffer_size*self.frames
    self.idx = 0
    self.channels = chnnels
    self.height = height
    self.width = width
    self.path_to_images = path_root  # the pre path to the datasets
    video_dict = readlistFromFile(TrainVideolist,Numlist,self.frames,balance,self.height,self.width)
    self.video_dict = video_dict[0]
    self.video_order = video_dict[1]
    self.num_videos = len(self.video_dict)
    self.multylabel = multylabel
    self.affine = affine

class videoReadTest(videoRead):

  def initialize(self):
    self.train_or_test = 'train'
    self.flow = False
    self.buffer_size = Test_batch_size  #num videos processed per batch
    self.frames = Test_frames_l  #length of processed clip
    self.N = self.buffer_size*self.frames
    self.idx = 0
    self.channels = chnnels
    self.height = height
    self.width = width
    self.path_to_images = path_root  # the pre path to the datasets
    video_dict = readlistFromFile(TestVideolist,Numlist,self.frames,balance,self.height,self.width)
    self.video_dict = video_dict[0]
    self.video_order = video_dict[1]
    self.num_videos = len(self.video_dict)
    self.multylabel = multylabel
    self.affine = affine