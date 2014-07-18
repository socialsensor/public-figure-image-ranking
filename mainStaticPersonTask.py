#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:
# Purpose:       This .py file is the main Framework file
#                It ranks images of a specific person of interest in a static manner
#
# Required libs: python-dateutil, numpy,matplotlib,pyparsing
# Author:        konkonst
#
# Created:       20/08/2013
# Copyright:     (c) ITI (CERTH) 2013
# Licence:       <apache licence 2.0>
#-------------------------------------------------------------------------------
import time,os,pickle,glob,shutil
from staticCommPersonTask import communitystatic
print('staticCommPersonCentered')
print(time.asctime( time.localtime(time.time()) ))

'''PARAMETERS'''
#Construct the data class from scratch: 1-yes / 2- from the community detection/ else-perform only the ranking
dataextract = 1
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

filename = glob.glob("./data/txt/*.txt")
filename = [x for x in filename if x[11:].startswith('noDups')]
for idx,files in enumerate(filename):
    print(str(idx+1) + '.' + files[11:-4])

selection = int(input('Select a dataset from the above: '))-1

dataset_path_results = "./data/GETTY_"+filename[selection][24:-4]+"/staticPersonCentered_"+commDetectMethod[0]+"/results/"
dataset_path_tmp = "./data/GETTY_"+filename[selection][24:-4]+"/staticPersonCentered_"+commDetectMethod[0]+"/tmp/"

if not os.path.exists(dataset_path_results+"rankedPeople.txt"):
    print('You need to run the personPopularity.py first. Look into that...')
    exit()

if dataextract==1:#Start from scratch
    data = communitystatic.from_txt(filename[selection],dataset_path_results,dataset_path_tmp)
    dataPck = open(dataset_path_tmp + "allPersondata.pck", "wb")
    pickle.dump(data, dataPck , protocol = 2)
    dataPck.close()
    del(data)
    elapsed = time.time() - t
    print('Stage 1: %.2f seconds' % elapsed)
if dataextract==1 or dataextract==2:#If the basic data (authors, mentions, time) has been created
    data = pickle.load(open(dataset_path_tmp + "allPersondata.pck", "rb"))
    captiondict = data.captiondict
    print('static Community detection method selected is :'+commDetectMethod[0])
    dataStatic=data.extraction(commDetectMethod)
    del(data)
    elapsed = time.time() - t
    print('\nStage 2: %.2f seconds' % elapsed)
decisionforAll = input('\nRetrieve the topImages by screening them one by one???(y or n) ')
if dataextract ==1 or dataextract ==2 or dataextract ==3:#Only ranking beyond this point
    data = pickle.load(open(dataset_path_tmp + "allPersondata.pck", "rb"))
    captiondict = data.captiondict
    del(data)
    dataStatic = pickle.load(open(dataset_path_tmp + 'comm_'+commDetectMethod[0]+'.pck','rb'))

#delete folders if you're starting from scratch
if delFolders == 1:
    result_files = glob.glob(dataset_path_results+'/analysis/*.txt')
    if result_files:
        for file in result_files:
            os.remove(file)

if not peopleSet:
    with open(dataset_path_results+'rankedPeople.txt','r') as f:
        for lineId,line in enumerate(f):
            if lineId>topPeople-1:
                break
            line = line.split('\t')
            peopleSet.append(line[0])

for person in peopleSet:
    if decisionforAll != str('n') and not os.path.exists(dataset_path_results+'html/'+person):
        os.makedirs(dataset_path_results+'html/'+person)
    if decisionforAll != str('n'):
        personDecision = input('\nRetrieve images for '+person+'???(y or n) ')
    if decisionforAll == str('n'):
        print("\nRetrieval Commences for "+person)
    if decisionforAll == str('n') or personDecision == str('y'):
        dataStatic.photoRetrieval(topImages, person, captiondict,decisionforAll)
        dataStatic.popularity_coappearence(topImages, person, captiondict)

elapsed = time.time() - t
print('\nStage 3: %.2f seconds' % elapsed)
