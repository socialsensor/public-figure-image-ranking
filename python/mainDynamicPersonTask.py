#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:
# Purpose:       This .py file is the main Framework file
#                It ranks images of a specific person of interest in a dynamic manner
#
# Required libs: python-dateutil, numpy,matplotlib,pyparsing
# Author:        konkonst
#
# Created:       30/03/2014
# Copyright:     (c) ITI (CERTH) 2014
# Licence:       <apache licence 2.0>
#-------------------------------------------------------------------------------
import time,os,pickle,glob,codecs
from dynamicCommPersonTask import communitydynamic
print('dynamicCommPersonCentered')
print(time.asctime( time.localtime(time.time()) ))

'''PARAMETERS'''
#Construct the data class from scratch: 1-yes / 2- from the community detection/ else-perform only the ranking
dataextract = 1
#User sets desired time intervals in seconds
timeSeg=[86400*30,86400*365]#[86400*365]#
#Provide a time Limit (unix timestamp) about when the dataset begins in case you only want part of the dataset. If it is set to 0 the whole dataset is considered.
timeLimit = 0 #1071561600 
#Community detection method. 'Ahn','Demon' and 'Copra' for overlapping and 'Louvain' for non. Ahn carries a threshold.
commDetectMethod = ['Demon', 0.66]
#User sets desired number of displayed top images
topImages = 8
#User sets desired number of most frequent people to retrieve
topPeople = 200
#Provide people set or leave empty to retrieve images for the number of topPeople as set above
peopleSet = ['justin_timberlake','oprah_winfrey','lady_gaga','justin_bieber','michael_schumacher','miley_cyrus','jk_rowling','zinedine_zidane','barack_obama','prince_william','brad_pitt_actor','leonardo_dicaprio','natalie_portman']
peopleSet.sort()
##peopleSet = [] #Uncomment this to activate the use of the rankedPeople.txt pool of users
#Delete all previous folders containing results? (Does not apply to the html files)
delFolders = 0
#If there are any nodes that should not be considered, please place them in './data/txt/stopNodes.txt'

'''Functions'''
t = time.time()

filename = [f for f in os.listdir("./data/txt/")]
for idx,files in enumerate(filename):
    print(str(idx+1) + '.' + files)

selection = int(input('Select a dataset from the above: '))-1

dataset_path_results = "./data/"+filename[selection][:-4]+"/dynamicPersonCentered_"+commDetectMethod[0]+"/results/"
dataset_path_tmp = "./data/"+filename[selection][:-4]+"/dynamicPersonCentered_"+commDetectMethod[0]+"/tmp/"
datasetFilename = './data/txt/'+filename[selection]

if not os.path.exists(dataset_path_results):
    os.makedirs(dataset_path_results)
    os.makedirs(dataset_path_tmp)

if dataextract==1:#Start from scratch
    data = communitydynamic.from_txt(timeSeg,datasetFilename,dataset_path_results,dataset_path_tmp,timeLimit=timeLimit)
    dataPck = open(dataset_path_tmp+"allPersondata.pck", "wb")
    pickle.dump(data, dataPck , protocol = 2)
    dataPck.close()
    elapsed = time.time() - t
    print('Stage 1: %.2f seconds' % elapsed)

fileTitleChoices = []
for seg in timeSeg:
    if seg >= 86400 and seg < 604800:
        timeNum = seg / 86400
        timeTitle = "per" + str(int(timeNum)) + "days"
    elif seg>= 604800 and seg < 2592000:
        timeNum = seg / 604800
        timeTitle = "per" + str(int(timeNum)) + "weeks"
    else:
        timeNum = seg / 2592000
        timeTitle = "per" + str(int(timeNum)) + "months"
    fileTitleChoices.append(timeTitle)

timeSelectionChoices = range(len(fileTitleChoices))#
if dataextract==1 or dataextract==2:#If the basic data (authors, mentions, time) has been created
    for timeSelection in timeSelectionChoices:
        data = pickle.load(open(dataset_path_tmp+"allPersondata.pck", "rb"))
        captiondict = data.captiondict
        fileTitle = fileTitleChoices[timeSelection]
        if not os.path.exists(dataset_path_results+fileTitle+'/'):
            os.makedirs(dataset_path_results+fileTitle+'/')
        print('dynamic Community detection method selected is :'+commDetectMethod[0])
        datadynamic=data.extraction(commDetectMethod, timeSeg[timeSelection])
        del(data)
        elapsed = time.time() - t
        print('\nStage 2: %.2f seconds' % elapsed)
decisionforAll = input('\nRetrieve the topImages by screening them one by one???(y or n) ')
if dataextract==1 or dataextract==2 or dataextract==3:
    for timeSelection in timeSelectionChoices:
        fileTitle = fileTitleChoices[timeSelection]
        data = pickle.load(open(dataset_path_tmp+"allPersondata.pck", "rb"))
        captiondict = data.captiondict
        del(data)
        datadynamic = pickle.load(open(dataset_path_tmp+"comm_"+commDetectMethod[0]+'_'+fileTitle+'.pck','rb'))

        #delete folders if you're starting from scratch
        if delFolders == 1:
            result_files = glob.glob(dataset_path_results+fileTitle+'/analysis/*.txt')
            if result_files:
                for file in result_files:
                    os.remove(file)

        if not peopleSet:
            if not os.path.exists(dataset_path_results+"rankedPeople.txt"):
                print('You need to run the personPopularity.py first. Look into that...')
                exit()
            with codecs.open(dataset_path_results+'rankedPeople.txt','r','utf-8') as f:
                for lineId,line in enumerate(f):
                    if lineId > topPeople-1:
                        break
                    line = line.split('\t')
                    peopleSet.append(line[0])

        for person in peopleSet:
            if decisionforAll.lower() != str('n') and not os.path.exists(dataset_path_results+fileTitle+'/html/'+person):
                os.makedirs(dataset_path_results+fileTitle+'/html/'+person)
            if decisionforAll.lower() != str('n'):
                personDecision = 'y'#input('\nRetrieve images for '+person+'???(y or n) ')
            if decisionforAll.lower() == str('n'):
                print("\nRetrieval Commences for "+person)
            if decisionforAll.lower() == str('n') or personDecision.lower() == str('y'):
                datadynamic.photoRetrieval(topImages, person, captiondict,decisionforAll)
                datadynamic.popularity_coappearence(topImages, person, captiondict)

elapsed = time.time() - t
print('\nStage 3: %.2f seconds' % elapsed)
