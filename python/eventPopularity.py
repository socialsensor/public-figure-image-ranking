#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:
# Purpose:       This .py file extracts popularity of events (frequency of images in events)
#
# Required libs: python-dateutil, matplotlib
# Author:        konkonst
#
# Created:       30/03/2014
# Copyright:     (c) ITI (CERTH) 2014
# Licence:       <apache licence 2.0>
#-------------------------------------------------------------------------------
import glob, codecs, os, time, dateutil.parser, collections, pickle
import matplotlib.pyplot as plt

def popEvent(filename, dataset_path_results, dataset_path_tmp, commDetectMethod,timeLimit = 0):
    print('eventpopularity.py')
    t = time.time()
    #Nodes that will be removed
    try:
        stopNodes = open('./data/txt/stopNodes.txt').readlines()
        stopNodes = [x.strip().lower() for x in stopNodes]
        stopNodes = [x.replace(' - ','_').replace(' ','_') for x in stopNodes if x]
    except:
        stopNodes = []

    alltime = []
    totPics,totPeople = 0,0
    emptyvalues = 0
    eventContainer = []
    with codecs.open(filename, "r", 'utf-8',errors='ignore') as f:
        for line in f:
            read_line = line.strip().encode('utf-8')
            read_line = read_line.decode('utf-8')
            # try:
            splitLine = read_line.split("\t")
            dt = dateutil.parser.parse(splitLine[0])
            mytime = int(time.mktime(dt.timetuple()))
            numFaces = int(splitLine[5])
            if mytime > timeLimit:
                peopleLine = splitLine[3].strip(', \n').strip('\n').replace('.','').replace('?','-').replace(', ',',').replace(', ,','').lower().split(",")
                peopleLine = [x.replace(' - ','_').replace(' ','_') for x in peopleLine if x]
                peopleLine = [x for x in peopleLine if x not in stopNodes]
                numofpeople = len(peopleLine)
                eventIds = splitLine[1].replace(' ','').split(',')
                if not eventIds:
                    emptyvalues+=1
                else:
                    if numofpeople > 1:
                        for eventId in eventIds:
                            if eventId:
                                totPics+=1
                                totPeople+=numofpeople
                                eventContainer.append(eventId)

    countEvents = collections.Counter(eventContainer)
    sortedEvents = sorted(countEvents, key = countEvents.get, reverse = True)

    statsfile = open(dataset_path_tmp+"basicstats_eventBased.txt",'w')
    statement = ('Total # of event assigned pics= ' + str(totPics)+
        "\nTotal # of People in event assigned pics: "+str(totPeople)+
        "\nTotal # of eventIds: "+str(len(eventContainer))+
        "\nTotal # of unique events: "+str(len(countEvents))+
        "\nTotal empty eventIds: "+str(emptyvalues))
    print(statement)
    statsfile.write(statement)
    statsfile.close()
    eventfile = open(dataset_path_results+"rankedEvents.txt",'w')
    forplot = []
    for key in sortedEvents:
        eventfile.write(key+'\t'+str(countEvents[key])+'\n')
        if countEvents[key]>10:
            forplot.append(countEvents[key])
    eventfile.close()

    fig=plt.figure()
    plt.ylabel('Number of images')
    plt.xlabel('Events')
    plt.loglog(forplot)
    plt.draw()
    fig.savefig(dataset_path_tmp+"eventDistributionLog.pdf",bbox_inches='tight', format='pdf')
    plt.close()

    elapsed = time.time() - t
    print('Time elapsed: %.2f seconds' % elapsed)
