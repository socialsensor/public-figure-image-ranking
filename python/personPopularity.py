# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:
# Purpose:       This .py file extracts popularity of people (frequency of appearance)
#
# Required libs: python-dateutil, matplotlib
# Author:        konkonst
#
# Created:       30/03/2014
# Copyright:     (c) ITI (CERTH) 2014
# Licence:       <apache licence 2.0>
#-------------------------------------------------------------------------------
import glob, codecs, os, time, dateutil.parser, collections, pickle

def popPerson(filename, dataset_path_results, dataset_path_tmp, commDetectMethod,timeLimit = 0):

    print('personpopularity')
    t = time.time()
    #Nodes that will be removed
    try:
        stopNodes = open('./data/txt/stopNodes.txt').readlines()
        stopNodes = [x.strip().lower() for x in stopNodes]
        stopNodes = [x.replace(' - ','_').replace(' ','_') for x in stopNodes if x]
    except:
        stopNodes = []

    '''Parse the txt files into authors/mentions/alltime lists'''
    emptyvalues = 0
    print(filename)
    personContainer, totPics = [], 0
    with codecs.open(filename, "r", 'utf-8',errors='ignore') as f:
        for line in f:
            read_line = line.strip().encode('utf-8')
            read_line = read_line.decode('utf-8')
            # try:
            splitLine = read_line.split("\t")
            dt = dateutil.parser.parse(splitLine[0])
            mytime = int(time.mktime(dt.timetuple()))
            # numFaces = int(splitLine[5])
            if mytime > timeLimit:
                peopleLine = splitLine[3].strip(', \n').strip('\n').replace('.','').replace('?','-').replace(', ',',').replace(', ,','').lower().split(",")
                peopleLine = [x.replace(' - ','_').replace(' ','_') for x in peopleLine if x]
                peopleLine = [x for x in peopleLine if x not in stopNodes]
                numofpeople = len(peopleLine)
                if numofpeople > 1:
                    totPics+=1
                    for person in peopleLine:
                        if person:
                            personContainer.append(person)

    print('Total Pics are:'+str(totPics))
    popularity = {}
    countPeople = collections.Counter(personContainer)
    popularity['countPeople'] = countPeople
    sortedPeople = sorted(countPeople, key = countPeople.get, reverse = True)
    popularity['sortedPeople'] = sortedPeople
    allPeople = list(countPeople.keys())
    allPeople.sort()
    print('Num of unique people: '+str(len(sortedPeople)))

    peoplePopularity = open(dataset_path_tmp+"peoplePopularity.pck", "wb")
    pickle.dump(popularity, peoplePopularity , protocol = 2)
    peoplePopularity.close()

    personfile1 = codecs.open(dataset_path_results+"rankedPeople.txt",'w','utf-8')
    for key in sortedPeople:
            personfile1.write(key+'\t'+str(countPeople[key])+'\n')
    personfile1.close()

    elapsed = time.time() - t
    print('Time elapsed: %.2f seconds' % elapsed)
