#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:
# Purpose:       This .py file is the main Framework file
#                It ranks images in specific events
#
# Required libs: python-dateutil, numpy,matplotlib,pyparsing
# Author:        konkonst
#
# Created:       30/03/2014
# Copyright:     (c) ITI (CERTH) 2014
# Licence:       <apache licence 2.0>
#-------------------------------------------------------------------------------
import time,os,pickle, glob, eventPopularity
from staticCommEventTask import communitystatic
print('staticCommEventCentered')
print(time.asctime( time.localtime(time.time()) ))

'''PARAMETERS'''
#Construct the data class from scratch: 1-yes / 2- perform community detection / else- perform just the ranking process
dataextract = 1
#Provide a time Limit (unix timestamp) about when the dataset begins in case you only want part of the dataset. If it is set to 0 the whole dataset is considered.
timeLimit = 0 #1071561600 
#Community detection method. 'Ahn','Demon' and 'Copra' for overlapping and 'Louvain' for non. Ahn carries a threshold.
commDetectMethod = ['Demon', 0.66]
#User sets desired number of displayed top images
topImages = 8
#User sets the number of events is requested in population order as extracted from the rankedEvents.txt file.
topEvents = 100
#Delete all previous folders containing results? (Does not apply to the html files)
delFolders = 0
#If there are any nodes that should not be considered, please place them in './data/txt/stopNodes.txt'


filename = [f for f in os.listdir("./data/txt/")]
for idx,files in enumerate(filename):
    print(str(idx+1) + '.' + files)

selection = int(input('Select a dataset from the above: '))-1

dataset_path_results = "./data/"+filename[selection][:-4]+"/staticEventCentered_"+commDetectMethod[0]+"/results/"
dataset_path_tmp = "./data/"+filename[selection][:-4]+"/staticEventCentered_"+commDetectMethod[0]+"/tmp/"
datasetFilename = './data/txt/'+filename[selection]

if not os.path.exists(dataset_path_results):
    os.makedirs(dataset_path_results)
    os.makedirs(dataset_path_tmp)

if not os.path.exists(dataset_path_results+"rankedEvents.txt"):
    eventPopularity.popEvent(datasetFilename, dataset_path_results, dataset_path_tmp, commDetectMethod,timeLimit=timeLimit)

'''Functions'''
t = time.time()

if dataextract==1:
    data = communitystatic.from_txt(datasetFilename,dataset_path_results,dataset_path_tmp,timeLimit=timeLimit)
    dataPck = open(dataset_path_tmp + "allEventdata.pck", "wb")
    pickle.dump(data, dataPck , protocol = 2)
    dataPck.close()
    elapsed = time.time() - t
    print('Stage 1: %.2f seconds' % elapsed)

if dataextract == 1 or dataextract == 2:#If the basic data (authors, mentions, time) has been created
    with open(dataset_path_results+'rankedEvents.txt','r') as f:
        for lineId,line in enumerate(f):
            if lineId >= topEvents:
                break
            line = line.split('\t')
            eventIdInput = line[0]
            print('\nCreating data files for event: '+str(eventIdInput))
            data = pickle.load(open(dataset_path_tmp + "allEventdata.pck", "rb"))
            print('Static Community detection method selected is :'+commDetectMethod[0])
            dataStatic=data.extraction(commDetectMethod,eventIdInput)
            del(data)
            elapsed = time.time() - t
            print('Stage 2: %.2f seconds' % elapsed)

#Only ranking beyond this point
try:
    captiondict = data.captiondict[eventIdInput]
except:
    data = pickle.load(open(dataset_path_tmp + "allEventdata.pck", "rb"))
    pass
#delete folders if you're starting from scratch
if delFolders == 1:
    result_files = glob.glob(dataset_path_results+'/analysis/*.txt')
    if result_files:
        for file in result_files:
            os.remove(file)
counter = 0
decisionforAll = input('\nRetrieve the topImages by screening them one by one???(y or n) ')
with open(dataset_path_results+'rankedEvents.txt','r') as f:
    for line in f:
        if counter >= topEvents:
            break
        line = line.split('\t')
        eventIdInput = line[0]
        if decisionforAll == str('y'):
            decision = str(input('\nWould you like to retrieve images for event: ' + str(eventIdInput) + '?'))
        else:
            decision = str('y')
        if decision == str('y'):
            captiondict = data.captiondict[eventIdInput]
            dataStatic = pickle.load(open(dataset_path_tmp + 'comm_'+commDetectMethod[0]+'Ev_'+str(eventIdInput)+'.pck','rb'))
            print("\nRetrieval Commences for event: " + str(eventIdInput))
            dataStatic.photoRetrieval(topImages,captiondict,decisionforAll)
            dataStatic.popularity_coapperence(topImages,captiondict)
            elapsed = time.time() - t
            print('Stage 3: %.2f seconds' % elapsed)
            counter+=1
