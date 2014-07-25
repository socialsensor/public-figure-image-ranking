#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:
# Purpose:       This .py file is the class file that does all the work
#                It ranks images of a specific person of interest in a dynamic manner
#
# Required libs: python-dateutil, numpy,matplotlib,pyparsing
# Author:        konkonst
#
# Created:       30/03/2014
# Copyright:     (c) ITI (CERTH) 2014
# Licence:       <apache licence 2.0>
#-------------------------------------------------------------------------------
import json, codecs, os, glob, time, dateutil.parser, collections, datetime, pickle, re, math
import urllib.request, webbrowser
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt


class communitydynamic:

    @classmethod
    def from_txt(cls,timeSeg,filename,dataset_path_results,dataset_path_tmp,timeLimit = 0):

        if not os.path.exists(dataset_path_results):
            os.makedirs(dataset_path_results)
            os.makedirs(dataset_path_tmp)

        #Nodes that will be removed
        try:
            stopNodes = open('./data/txt/stopNodes.txt').readlines()
            stopNodes = [x.strip().lower() for x in stopNodes]
            stopNodes = [x.replace(' - ','_').replace(' ','_') for x in stopNodes if x]
        except:
            stopNodes = []

        '''Parse the txt files into authors/mentions/alltime lists'''
        authors, mentions, alltime, photoIds= [], [], [], []
        totPics,totPeople = 0,0
        photodict={}
        captiondict = {}
        print(filename)
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
                    peopleLine.sort()
                    numofpeople = len(peopleLine)
                    if numofpeople > 1:#numFaces>=numofpeople and
                        photodict[totPics]={}
                        photodict[totPics]['nodes'] = peopleLine
                        photodict[totPics]['url'] = splitLine[2]
                        photodict[totPics]['date'] = mytime
                        captiondict[totPics] = splitLine[-2]
                        totPeople+=numofpeople
                        for idx,tmpAuth in enumerate(peopleLine[:-1]):
                            theRest=peopleLine[idx+1:]
                            for tmpMent in theRest:
                                authors.append(tmpAuth)
                                mentions.append(tmpMent)
                                alltime.append(mytime)
                                photoIds.append(totPics)
                        totPics+=1
                # except:
                #     pass
        f.close()

        statsfile = open(dataset_path_results+"basicstats.txt",'w')
        statement = ('Total # of Pics= ' + str(totPics)+
            "\nTotal # of People in Pics: "+str(totPeople)+'\n')
        print(statement)
        statsfile.write(statement)
        statsfile.close()

        zippedall=zip(alltime,authors,mentions,photoIds)
        zippedall=sorted(zippedall)
        alltime, authors, mentions, photoIds=zip(*zippedall)
        alltime,authors,mentions,photoIds=list(alltime),list(authors),list(mentions),list(photoIds)

        return cls(authors, mentions, alltime, photoIds, timeSeg, photodict, captiondict, dataset_path_results, dataset_path_tmp)

    def __init__(self, authors, mentions, alltime, photoIds, timeSeg, photodict, captiondict, dataset_path_results, dataset_path_tmp):
        self.authors = authors
        self.mentions = mentions
        self.alltime = alltime
        self.photoIds = photoIds
        self.timeSeg = timeSeg
        self.uniqueUsers = {}
        self.userPgRnkBag = {}
        self.photodict = photodict
        self.captiondict = captiondict
        self.commStrBag = {}
        self.userdict = {}
        self.overlNodes = {}
        self.dataset_path_results = dataset_path_results
        self.dataset_path_tmp = dataset_path_tmp
        self.partitionLouv = {}

    def extraction(self, commDetectMethod, timeSelection):
        '''Extract adjacency lists,mats,user and community centrality and communities bags'''
        import community,link_clustering_din
        import Demon as D

        '''Extract unique users globally and construct dictionary'''
        usrs = self.authors.copy()
        usrs.extend(self.mentions)
        usrs = list(set(usrs))
        usrs.sort()
        uniqueUsers, counter1 = {}, 0
        for tmpusrs in usrs:
            uniqueUsers[tmpusrs] = counter1
            counter1 += 1
        self.uniqueUsers = uniqueUsers

        statement = "Total # of unique users: "+ str(len(uniqueUsers)) + '\n'
        statsfile = open(self.dataset_path_results+"basicstats.txt",'a')
        print(statement)
        statsfile.write(statement)
        statsfile.close()

        #Compute the point of timeslot separation
        mentionLimit = self.timeslotselection(self.alltime, timeSelection)

        #Split time according to the first derivative of the users' activity#
        sesStart, timeslot, timeLimit,commCount,commCountLouv = 0, 0, [], 0, 0
        self.userEvolPagerank, ranklist = {}, {}#evolutionary reciprocal pagerank rank per timeslot
        mymodularity = []
        print("Forming timeslots and extracting graph structure...")
        for tmplim in mentionLimit:
            #make timeslot timelimit array
            try:
                timeLimit.append(self.alltime[int(tmplim)])
            except:
                timeLimit.append(self.alltime[-1])
                pass
            fileNum = '{0}'.format(str(timeslot).zfill(2))
            # print("Forming Timeslot Data "+str(timeslot)+" at point "+str(tmplim))
            sesEnd = int(tmplim)

            '''Make userlist per timeslot'''
            tmpphotoIds = self.photoIds[sesStart:sesEnd]
            tmpphotoIds = list(set(tmpphotoIds))
            for photo in tmpphotoIds:
                for node in self.photodict[photo]['nodes']:
                    if node in self.userdict:
                        if timeslot in self.userdict[node]:
                            self.userdict[node][timeslot].append(photo)
                        else:
                            self.userdict[node][timeslot] = [photo]
                    else:
                        self.userdict[node]={}
                        self.userdict[node][timeslot] = [photo]

            '''Make pairs of users with weights'''
            usersPair = list(zip(self.authors[sesStart:sesEnd], self.mentions[sesStart:sesEnd]))
            #Create weighted adjacency list
            weighted = collections.Counter(usersPair)
            weighted = list(weighted.items())
            adjusrs, weights = zip(*weighted)
            adjauthors, adjments = zip(*adjusrs)
            adjList = list(zip(adjauthors, adjments, weights))
            '''Make pairs of users(their uniqueUsers Ids) with weights for Copra'''
            authorsNum,mentionsNum = [], []
            for idx,auth in enumerate(adjauthors):
                authorsNum.append(uniqueUsers[auth])
                mentionsNum.append(uniqueUsers[adjments[idx]])
            adjListNum = list(zip(authorsNum, mentionsNum, weights))
            del(adjusrs,adjauthors,adjments,weights,weighted,usersPair, authorsNum, mentionsNum)

            # '''Write pairs of users to txt file for Gephi'''
            #Make temp folder if non existant
            # if not os.path.exists(self.dataset_path_tmp[:-4]+"forGephi/"+self.fileTitle):
            #     os.makedirs(self.dataset_path_tmp[:-4]+"forGephi/"+self.fileTitle)
            # try:
            #     my_txt = codecs.open(self.dataset_path_tmp[:-4]+"forGephi/" + self.fileTitle + '/partition_' + fileNum + '_' + datetime.datetime.fromtimestamp(int(self.alltime[int(tmplim)])).strftime('%b_%d_%y') + ".txt", "w", "utf-8")
            # except:
            #     my_txt = codecs.open(self.dataset_path_tmp[:-4]+"forGephi/" + self.fileTitle + '/partition_' + fileNum + '_' + datetime.datetime.fromtimestamp(int(self.alltime[-1])).strftime('%b_%d_%y') + ".txt", "w", "utf-8")
            #     pass
            # my_txt.write("Source,Target,Weight,Type" + "\n")
            # for line in adjList:
            #     line = list(line)
            #     line.append('Undirected')
            #     my_txt.write(",".join(str(x) for x in line) + "\n")
            # my_txt.close()

            '''Write pairs of users to txt file for COPRA and invert the uniqueUsers dictionary'''
            if commDetectMethod[0] == 'Copra':
                my_txt = open(self.dataset_path_tmp+"forCopra.txt", "w")
                for line in adjListNum:
                    my_txt.write(" ".join(str(x) for x in line) + "\n")
                my_txt.close()
                uniqueUsersInv = {v:k for k, v in uniqueUsers.items()}

            '''Construct networkX graph'''
            tempGraph = nx.Graph()
            tempGraph.add_weighted_edges_from(adjList)
            tempGraph.remove_edges_from(tempGraph.selfloop_edges())

            '''Extract the centrality of each user using the PageRank algorithm'''
            tempUserPgRnk = nx.pagerank(tempGraph, alpha=0.85, max_iter=100, tol=0.001)
            minPGR=min((pgr for k,(pgr) in tempUserPgRnk.items()))
            for k in tempUserPgRnk.items():
                tempUserPgRnk[k[0]]/=minPGR
            self.userPgRnkBag[timeslot] = tempUserPgRnk

            '''Extract dynamic centrality of each user by calculating the reciprocal rank fusion
            measure based on static centrality rank on a temporal basis'''
            usrCentrSorted = sorted(tempUserPgRnk, key = tempUserPgRnk.get, reverse = True)#rank pageranks
            self.userEvolPagerank[timeslot] = {}
            for idx,user in enumerate(usrCentrSorted):
                if user in ranklist:
                    ranklist[user].append(idx)
                else:
                    ranklist[user] = [idx]
                self.userEvolPagerank[timeslot][user] = recRankFusEvol(ranklist[user])


            '''Detect Communities using the louvain algorithm'''
            partitionLouv = community.best_partition(tempGraph)
            mymodularity.append(community.modularity(partitionLouv,tempGraph))

            inv_partitionLouv = {}
            for k, v in partitionLouv.items():
                inv_partitionLouv[v] = inv_partitionLouv.get(v, [])
                inv_partitionLouv[v].append(k)
                inv_partitionLouv[v].sort()
            strCommsLouv = [inv_partitionLouv[x] for x in inv_partitionLouv]
            strCommsLouv.sort(key=len, reverse=True)
            commCountLouv+=len(strCommsLouv)
            if commDetectMethod[0] == 'Ahn':
                '''Detect Communities using the Ahn algorithm'''
                inv_partition = link_clustering_din.ahnsmethod(adjList, threshold=commDetectMethod[1])
                strComms = [inv_partition[x] for x in inv_partition]
                strComms.sort(key=len, reverse=True)
                commCount+=len(strComms)
            elif commDetectMethod[0] == 'Demon':
                DemObj = D.Demon()
                strComms = DemObj.execute(tempGraph, weighted=True, min_community_size=1)
                strComms.sort(key=len, reverse=True)
                commCount+=len(strComms)
                inv_partition=0
            elif commDetectMethod[0] == 'Copra':
                '''Detect Communities using the Copra algorithm'''
                os.system("java -cp ./copra.jar COPRA " + self.dataset_path_tmp + "forCopra.txt -w -extrasimplify -v 10 -mo -repeat 3")
                if os.path.exists(self.dataset_path_tmp+'best-clusters-forCopra.txt'):
                    os.remove(self.dataset_path_tmp+'best-clusters-forCopra.txt')
                try:
                    os.rename('./best-clusters-forCopra.txt',self.dataset_path_tmp + 'best-clusters-forCopra.txt')
                except:
                    os.rename('./clusters-forCopra.txt',self.dataset_path_tmp + 'best-clusters-forCopra.txt')
                flag = False
                strComms = []
                while flag == False:
                    try:
                        with open(self.dataset_path_tmp+'best-clusters-forCopra.txt', "r") as f:
                            for line in f:
                                read_line = line.strip()
                                numComm = [uniqueUsersInv[int(x)] for x in read_line.split(' ')]
                                strComms.append(numComm)
                        strComms.sort()
                        flag = True
                    except:
                        time.sleep(3)
                        pass
                commCount+=len(strComms)
                inv_partition=0
                if os.path.exists(self.dataset_path_tmp+'best-clusters-forCopra.txt'):
                    os.remove(self.dataset_path_tmp+'best-clusters-forCopra.txt')
                    os.remove(self.dataset_path_tmp+'forCopra.txt')
                for filename in  glob.glob("./clusters*.txt"):#delete txt files
                    os.remove(filename)
            else:
                print('No such method as:'+commDetectMethod[0])
            del(adjList,inv_partition)

            #Check for overlapping nodes in between communities
            tmpoverlNodes = {}
            for node in self.uniqueUsers.keys():
                nodeComms = []
                for idx, comms in enumerate(strComms):
                    if node in comms:
                        nodeComms.append(idx)
                if len(nodeComms) > 1:
                    tmpoverlNodes[node]=nodeComms

            '''Construct Community Dictionary'''
            # self.commStrBag[timeslot] = strComms
            self.overlNodes[timeslot] = tmpoverlNodes
            self.partitionLouv[timeslot] = partitionLouv

            sesStart = sesEnd
            timeslot += 1

        self.commDetectMethod = commDetectMethod[0]
        self.day_month = [datetime.datetime.fromtimestamp(int(x)).strftime('%m/%y') for x in timeLimit]
        self.timeLimit = [datetime.datetime.fromtimestamp(int(x)).strftime('%b %d %y') for x in timeLimit]

        xLablNum = 20 #how many tick labels to display
        font = {'size': 12}
        plt.rc('font', **font)
        fig3, ax3 = plt.subplots()
        pertick=math.ceil(len(mymodularity)/xLablNum)
        ax3.plot(mymodularity, 'b-')
        ax3.set_xticks(np.arange(0,len(mymodularity),pertick), minor=False)
        ax3.set_xticklabels(self.day_month[0: :pertick], minor=False, fontsize=12, rotation = 30)
        for tick in ax3.yaxis.get_major_ticks():
            tick.label.set_fontsize(12)
        # xmin, xmax = plt.xlim()
        # plt.xlim( 1, xmax+1 )
        plt.ylabel("Modularity Value")
        plt.xlabel('Timeslots')
        plt.tight_layout()
        fig3 = plt.gcf()
        plt.show()
        fig3.savefig(self.dataset_path_results+self.fileTitle+"/modularityEvol"+'_'+str(self.fileTitle)+".pdf",bbox_inches='tight', format='pdf')
        plt.close()
        del(fig3)

        if not os.path.exists(self.dataset_path_results+self.fileTitle+"/"):
            os.makedirs(self.dataset_path_results+self.fileTitle+"/")
        statement = '\nTotal # of Demon communities is '+str(commCount) + '\n' + 'Total # of Louvain communities is '+str(commCountLouv) + '\n'

        statsfile = open(self.dataset_path_results+self.fileTitle+"/"+str(self.commDetectMethod)+'_'+str(self.fileTitle)+'_stats.txt','w')
        print(statement)
        statsfile.write(statement)
        statsfile.close()

        del(self.authors,self.mentions,self.alltime,self.captiondict)

        dataCommPck = open(self.dataset_path_tmp+'comm_'+self.commDetectMethod+'_'+str(self.fileTitle)+'.pck','wb')
        pickle.dump(self, dataCommPck , protocol = 2)
        dataCommPck.close()
        return self


    def timeslotselection(self, alltime, seg):

        xLablNum = 24 #how many tick labels to display

        #Find time distance between posts#
        time2 = np.append(alltime[0], alltime)
        time2 = time2[0:len(time2) - 1]
        timeDif = alltime - time2
        lT = len(alltime)

        timeSegInput = seg
        del(self.timeSeg)
        if timeSegInput >= 86400 and timeSegInput < 604800:
            timeNum = timeSegInput / 86400
            timeTitle = "per" + str(int(timeNum)) + "days"
            timeTitle2 = " days"
            labelstr = '%d/%b'
        elif timeSegInput>= 604800 and timeSegInput < 2592000:
            timeNum = timeSegInput / 604800
            timeTitle = "per" + str(int(timeNum)) + "weeks"
            timeTitle2 = " weeks"
            labelstr = '%b/%y'
        else:
            timeNum = timeSegInput / 2592000
            timeTitle = "per" + str(int(timeNum)) + "months"
            timeTitle2 = " months"
            labelstr = '%b/%y'

        '''Extract the time limits'''
        plotcount = 0
        curTime, bin, freqStat, mentionLimit, timeLabels = 0, 0, [0], [], []
        for i,tD in enumerate(timeDif):
            curTime += tD
            if curTime <= seg:
                freqStat[bin] += 1
            else:
                curTime = 0
                mentionLimit = np.append(mentionLimit, i)
                timeLabels = np.append(timeLabels, datetime.datetime.fromtimestamp(alltime[i]).strftime(labelstr))
                bin += 1
                freqStat = np.append(freqStat, 0)
        mentionLimit = np.append(mentionLimit, i+1)
        timeLabels = np.append(timeLabels, datetime.datetime.fromtimestamp(alltime[-1]).strftime(labelstr))

        font = {'size': 12}
        plt.rc('font', **font)
        fig = plt.figure()
        ax = fig.add_subplot(111)
        plt.grid(axis='x')
        plt.plot(freqStat, 'b-')
        plt.ylabel("Photo frequency")
        plt.xlabel("Init. time: " + datetime.datetime.fromtimestamp(int(self.alltime[0])).strftime('%d/%m/%y')+ ", Last point:"+ datetime.datetime.fromtimestamp(int(self.alltime[-1])).strftime('%d/%m/%y') + " (Ts:" + str(round(timeNum)) + timeTitle2 + ")")
        pertick=math.ceil(len(freqStat)/xLablNum)
        plt.xlim(xmax=(len(freqStat)))
        ax.set_xticks(list(range(0, len(freqStat), pertick)), minor=False)#, minor=False)
        ax.set_xticklabels(timeLabels[0: :pertick], minor=False, fontsize = 12, rotation = 35)
        xmin, xmax = plt.xlim()
        plt.xlim( 0, xmax-1 )
        # interactive(True)
        fig = plt.gcf()
        plt.show()
        fig.savefig(self.dataset_path_tmp + "photo_frequency_"+timeTitle+".pdf", bbox_inches='tight', format='pdf')#
        plt.close()

        self.fileTitle = timeTitle
        self.labelstr = labelstr
        return mentionLimit

    def photoRetrieval(self, topImages, person, captiondict, decisionforAll):

        decisionforAll = str(decisionforAll).lower()
        self.decisionforAll = decisionforAll

        POItimeslots = list(self.userdict[person].keys()) #timeslots that contain the POI
        POItimeslots.sort()
        personPopularity,personPool = {}, {}
        personTotPhotos, combinationDict = 0, {}
        personPR = {}
        Tmsl = {}
        for slot in POItimeslots:
            combinationDict[slot] = {}
            personPool[slot] = self.userdict[person][slot]#Create persons own pool of images
            personPopularity[slot] = len(self.userdict[person][slot])
            personPR[slot] = self.userPgRnkBag[slot][person]
            maxPGR=max((pgr for k,(pgr) in self.userPgRnkBag[slot].items()))
            for k in self.userPgRnkBag[slot].items():
                self.userPgRnkBag[slot][k[0]]/=maxPGR
            personTotPhotos += len(self.userdict[person][slot])
            for image in self.userdict[person][slot]:
                Tmsl[image] = slot
                if ','.join(self.photodict[image]['nodes']) in combinationDict[slot]:
                    combinationDict[slot][','.join(self.photodict[image]['nodes'])].append(image)
                    combinationDict[slot][','.join(self.photodict[image]['nodes'])].sort()
                else:
                    combinationDict[slot][','.join(self.photodict[image]['nodes'])] = [image]

        if decisionforAll == str('y') or decisionforAll == str(3):
            if not os.path.exists(self.dataset_path_results+self.fileTitle+'/userStats/'):
                os.makedirs(self.dataset_path_results+self.fileTitle+'/userStats/')
            personPRarray = []
            personFreqArray = []
            for idx,date in enumerate(self.day_month):
                try:
                    personPRarray.append(personPR[idx])
                    personFreqArray.append(personPopularity[idx])
                except:
                    personPRarray.append(0)
                    personFreqArray.append(0)
                    pass
            # personFreqArray = [x/max(personFreqArray) for x in personFreqArray]
            # personPRarray = [x/max(personPRarray) for x in personPRarray]
            dateArray = range(len(self.day_month))
            font = {'size': 12}
            plt.rc('font', **font)
            fig = plt.figure()
            ax = fig.add_subplot(111)
            # plt.ylabel('Centrality measure')            
            plt.ylabel('Photo Frequency')
            plt.xlabel('Timeslot')
            # plt.plot(dateArray,personPRarray, 'ro', label = 'PageRank')
            plt.plot(dateArray,personFreqArray, 'b-s', label = 'Frequency')
            pertick = math.ceil(len(dateArray)/24)
            ax.set_xticks(list(range(0, len(dateArray), pertick)))#, minor=False)
            ax.set_xticklabels(self.day_month[0: :pertick], fontsize = 12, rotation = 35)# minor=False,
            # ax.legend(loc='upper left', numpoints = 1)
            # mng = plt.get_current_fig_manager()
            # mng.resize(*mng.window.maxsize())
            plt.show()
            fig.savefig(self.dataset_path_results+self.fileTitle+'/userStats/'+person+"_frequencyFlux.pdf",bbox_inches='tight', format='pdf')
            plt.close()

            personFreqArray = [x/max(personFreqArray) for x in personFreqArray]
            personPRarray = [x/max(personPRarray) for x in personPRarray]
            dateArray = range(len(self.day_month))
            font = {'size': 12}
            plt.rc('font', **font)
            fig = plt.figure()
            ax = fig.add_subplot(111)
            plt.ylabel('Centrality Vs Frequency')            
            # plt.ylabel('Photo Frequency')
            plt.xlabel('Timeslot')
            plt.plot(dateArray,personPRarray, 'ro', label = 'PageRank')
            plt.plot(dateArray,personFreqArray, 'b-s', label = 'Frequency')
            pertick = math.ceil(len(dateArray)/24)
            ax.set_xticks(list(range(0, len(dateArray), pertick)))#, minor=False)
            ax.set_xticklabels(self.day_month[0: :pertick], fontsize = 12, rotation = 35)# minor=False,
            ax.legend(loc='upper left', numpoints = 1)
            # mng = plt.get_current_fig_manager()
            # mng.resize(*mng.window.maxsize())
            plt.show()
            fig.savefig(self.dataset_path_results+self.fileTitle+'/userStats/'+person+"_freqVsPR.pdf",bbox_inches='tight', format='pdf')
            plt.close()

        '''combinationDict is used to retrieve images if the presented one is incorrect'''
        self.combinationDict = combinationDict
        self.personPool = personPool
        self.Tmsl = Tmsl

        poiRankedTimeslots = sorted(personPopularity, key = personPopularity.get, reverse = True) #rank timeslots according to POI's PR

        self.poiRankedTimeslots = poiRankedTimeslots

        if decisionforAll == str('y') or decisionforAll == str(3):
            doItCoappOverl = str(input('\nRetrieve photos with most common overlappers???(y or n):'))
            doItOverlRank = str(input('\nRetrieve photos according to the overlappers\' ranking???(y or n):'))
            doItRecipr = str(input('\nRank images by reciprocal of ranks of the contained nodes???(y or n):'))
            doItReciprEvol = str(input('\nRank images by evolutionary reciprocal of ranks of the contained nodes???(y or n):'))
            personTotPhotos = 1
        else:
            doItCoappOverl = str('y')
            doItOverlRank = str('y')
            doItRecipr = str('y')
            doItReciprEvol = str('y')

        rankedPhotosCoappOverl, rankedPhotosRankedOverl,rankedPhotosReciprocal, rankedPhotosReciprocalEvol = [], [], [], []
        coappOverlMeasureDict, rankedOverlMeasureDict, reciprocalMeasureDict, reciprocalEvolMeasureDict = {},{},{},{}
        CoappOverlPrevLength,RankedOverlPrevLength,ReciprocalPrevLength,ReciprocalEvolPrevLength = 0,0,0,0
        rpco, rpro, rpr, rpre = False, False, False, False
        coappOverlDict, rankedOverlDict, PRstaticDict, PRevolDict = {}, {}, {}, {}
        if len(poiRankedTimeslots) > 1:
            while len(rankedPhotosCoappOverl)<personTotPhotos or len(rankedPhotosRankedOverl)<personTotPhotos or len(rankedPhotosReciprocal)<personTotPhotos or len(rankedPhotosReciprocalEvol)<personTotPhotos:
                for rankedslot in poiRankedTimeslots:
                    #reduce global temporal variables to slot variables
                    userPgRnkBaglocal = self.userPgRnkBag[rankedslot]
                    overlNodeslocal = self.overlNodes[rankedslot]
                    personPoollocal = personPool[rankedslot]
                    userEvolpageranklocal = self.userEvolPagerank[rankedslot]
                    '''Rank users in accordance to their centrality'''
                    usrCentrSorted = sorted(userPgRnkBaglocal, key = userPgRnkBaglocal.get, reverse = True)
                    '''Rank users in accordance to their evolving centrality'''
                    usrEvolCentrSorted = sorted(userEvolpageranklocal, key = userEvolpageranklocal.get, reverse = True)
                    '''Retrieve images in respect to their overlapping of communities'''
                    rankedOverlNodes = sorted(overlNodeslocal, key=lambda k: len(overlNodeslocal[k])+userPgRnkBaglocal[k], reverse=True)
                    try:
                        personIdx = rankedOverlNodes.index(person)
                        del(rankedOverlNodes[personIdx])
                    except:
                        pass
                    if rankedslot in coappOverlDict:
                        mostcomm = coappOverlDict[rankedslot]
                        rankedPhotos = rankedOverlDict[rankedslot]
                    else:
                        poolIntersex = {}
                        nodePool = []
                        for image in personPoollocal:#Retrieve photos with most common overlappers##############
                            commonNodes = list(set(self.photodict[image]['nodes']) & set(rankedOverlNodes))
                            imageOverlapperPopularity = len(commonNodes)
                            nodePool.extend(self.photodict[image]['nodes'])
                            if imageOverlapperPopularity:
                                # poolIntersex[image] = imageOverlapperPopularity
                                poolIntersex[image] = sum([len(overlNodeslocal[k]) for k in commonNodes])
                        nodePool = list(set(nodePool))
                        nodePool.sort()
                        if len(poolIntersex) > 0:
                            '''Retrieve photos with most common overlappers'''
                            sortedPoolIntersex = sorted(poolIntersex, key = poolIntersex.get, reverse = True)
                            mostcomm=[]
                            for image in sortedPoolIntersex:
                                entropyList =  [self.partitionLouv[rankedslot][x] for x in self.photodict[image]['nodes']]
                                entropy = myentropy(entropyList)
                                tmp = [usrCentrSorted.index(x) for x in self.photodict[image]['nodes']]
                                mostcomm.append([image,poolIntersex[image], entropy, recRankCustom(tmp)])
                                coappOverlMeasureDict[image] = poolIntersex[image]*(1+entropy)
                            mostcomm.sort(key=lambda k: (k[1]*(1+k[2]),k[3]), reverse = True)
                            mostcomm = [x[0] for x in mostcomm]
                            coappOverlDict[rankedslot] = mostcomm

                            '''Retrieve photos according to the overlappers' ranking'''
                            plainRanking = {}
                            photokeys = poolIntersex.keys()
                            maxPlain = 0
                            rankedtmpnodes = []
                            for node in rankedOverlNodes:
                                if node in nodePool:
                                    tmpRank = {}
                                    plainRanking[node] = []
                                    for photoId in photokeys:
                                        if node in self.photodict[photoId]['nodes'] and photoId not in rankedOverlMeasureDict:
                                            tmp = [usrCentrSorted.index(x) for x in self.photodict[photoId]['nodes']]
                                            tmpRank[photoId] = recRankCustom(tmp)
                                            rankedOverlMeasureDict[photoId] = tmpRank[photoId]
                                            if node not in rankedtmpnodes:
                                                rankedtmpnodes.append(node)
                                    plainRanking[node] = sorted(tmpRank, key = tmpRank.get, reverse = True)
                                    maxPlain = max(maxPlain,len(tmpRank))
                            rankedPhotos = []
                            cnt = 0
                            while cnt < maxPlain:
                                for node in rankedtmpnodes:
                                    try:
                                        rankedPhotos.append(plainRanking[node][cnt])
                                    except:
                                        pass
                                        continue
                                cnt+=1
                            rankedOverlDict[rankedslot] = rankedPhotos
                        else:
                            mostcomm = []
                            coappOverlDict[rankedslot] = mostcomm
                            rankedPhotos = []
                            rankedOverlDict[rankedslot] = rankedPhotos

                    '''Retrieve photos with most common overlappers'''
                    if not rpco:
                        for photo in mostcomm:
                            if photo and photo not in rankedPhotosCoappOverl:
                                rankedPhotosCoappOverl.append(photo)
                                break

                    '''Retrieve photos according to the overlappers' ranking'''
                    if not rpro:
                        for photo in rankedPhotos:
                            if photo and photo not in rankedPhotosRankedOverl:
                                rankedPhotosRankedOverl.append(photo)
                                break

                    '''Rank images by creating measuring value for each photo using reciprocal of centrality ranks of the contained nodes
                    and  using reciprocal of evolutionary centrality ranks'''
                    if rankedslot in PRstaticDict:
                        photoRank = PRstaticDict[rankedslot]
                        photoRankEvol = PRevolDict[rankedslot]
                    else:
                        photoRank = {}
                        photoRankEvol = {}
                        for photoId in personPoollocal:
                            tmp = [usrCentrSorted.index(x) for x in self.photodict[photoId]['nodes']]
                            tmpEvol = [usrEvolCentrSorted.index(x) for x in self.photodict[photoId]['nodes']]
                            photoRank[photoId] = recRankCustom(tmp)
                            photoRankEvol[photoId] = recRankCustom(tmpEvol)
                            reciprocalMeasureDict[photoId] = photoRank[photoId]
                            reciprocalEvolMeasureDict[photoId] = photoRankEvol[photoId]
                        PRstaticDict[rankedslot] = sorted(photoRank, key = photoRank.get, reverse = True)
                        PRevolDict[rankedslot] = sorted(photoRankEvol, key = photoRankEvol.get, reverse = True)

                    if not rpr:
                        for photo in PRstaticDict[rankedslot]:
                            if photo not in rankedPhotosReciprocal:
                                rankedPhotosReciprocal.append(photo)
                                break
                    if not rpre:
                        for photo in PRevolDict[rankedslot]:
                            if photo not in rankedPhotosReciprocalEvol:
                                rankedPhotosReciprocalEvol.append(photo)
                                break
                rpco = len(rankedPhotosCoappOverl) == CoappOverlPrevLength
                rpro = len(rankedPhotosRankedOverl) == RankedOverlPrevLength
                rpr = len(rankedPhotosReciprocal) == ReciprocalPrevLength
                rpre = len(rankedPhotosReciprocalEvol) == ReciprocalEvolPrevLength
                if rpco and rpro and rpr and rpre:
                    break
                CoappOverlPrevLength,RankedOverlPrevLength,ReciprocalPrevLength,ReciprocalEvolPrevLength = len(rankedPhotosCoappOverl),len(rankedPhotosRankedOverl),len(rankedPhotosReciprocal),len(rankedPhotosReciprocalEvol)
        else:
            print('Refer to static results for person: '+ person)

        #Save results
        if str(doItCoappOverl).lower() == str('y') or str(doItCoappOverl).lower() == str(3):
            methodName = 'Coappearing_Overlappers'
            print('\n'+methodName)
            if decisionforAll == str('y') or decisionforAll == str(3):
                resultsSaver(poiRankedTimeslots,methodName,topImages,person,coappOverlDict,coappOverlMeasureDict,self.photodict,self.dataset_path_results,captiondict,combinationDict,Tmsl,self.fileTitle)
            else:
                resultsSaverAll(methodName,topImages,person,rankedPhotosCoappOverl,coappOverlMeasureDict,self.photodict,self.dataset_path_results,captiondict,combinationDict,Tmsl,self.fileTitle)

        #Save results
        if str(doItOverlRank).lower() == str('y') or str(doItOverlRank).lower() == str(3):
            methodName = 'Ranked_Overlappers'
            print('\n'+methodName)
            if decisionforAll == str('y') or decisionforAll == str(3):
                resultsSaver(poiRankedTimeslots,methodName,topImages,person,rankedOverlDict,rankedOverlMeasureDict,self.photodict,self.dataset_path_results,captiondict,combinationDict,Tmsl,self.fileTitle)
            else:
                resultsSaverAll(methodName,topImages,person,rankedPhotosRankedOverl,rankedOverlMeasureDict,self.photodict,self.dataset_path_results,captiondict,combinationDict,Tmsl,self.fileTitle)

        #Save results
        if str(doItRecipr).lower() == str('y') or str(doItRecipr).lower() == str(3):
            methodName = 'ReciprocalRanks'
            print('\n'+methodName)
            if decisionforAll == str('y') or decisionforAll == str(3):
                resultsSaver(poiRankedTimeslots,methodName,topImages,person,PRstaticDict,reciprocalMeasureDict,self.photodict,self.dataset_path_results,captiondict,combinationDict,Tmsl,self.fileTitle)
            else:
                resultsSaverAll(methodName,topImages,person,rankedPhotosReciprocal,reciprocalMeasureDict,self.photodict,self.dataset_path_results,captiondict,combinationDict,Tmsl,self.fileTitle)

        #Save results
        if str(doItReciprEvol).lower() == str('y') or str(doItReciprEvol).lower() == str(3):
            methodName = 'ReciprocalRanksEvol'
            print('\n'+methodName)
            if decisionforAll == str('y') or decisionforAll == str(3):
                resultsSaver(poiRankedTimeslots,methodName,topImages,person,PRevolDict,reciprocalEvolMeasureDict,self.photodict,self.dataset_path_results,captiondict,combinationDict,Tmsl,self.fileTitle)
            else:
                resultsSaverAll(methodName,topImages,person,rankedPhotosReciprocalEvol,reciprocalEvolMeasureDict,self.photodict,self.dataset_path_results,captiondict,combinationDict,Tmsl,self.fileTitle)


    '''Create baseline solutions'''
    def popularity_coappearence(self, topImages, person, captiondict):

        decisionforAll = self.decisionforAll

        POItimeslots = self.userdict[person].keys() #timeslots that contain the POI
        personPool = self.personPool
        combinationDict = self.combinationDict
        Tmsl = self.Tmsl

        peoplePopularity, personPopularity, personTotPhotos = {}, {}, 0
        # combinationDict, Tmsl = {}, {}
        for slot in POItimeslots:
            # combinationDict[slot] = {}
            personTotPhotos += len(self.userdict[person][slot])
            peoplePopularity[slot] = {}
            personPopularity[slot] = len(self.userdict[person][slot])
            for people in self.userPgRnkBag[slot].keys():#create global popularity dictionary for all nodes in coapp slots
                peoplePopularity[slot][people] = len(self.userdict[people][slot])
            # for image in self.userdict[person][slot]:
            #     Tmsl[image] = slot
            #     if ','.join(self.photodict[image]['nodes']) in combinationDict[slot]:
            #         combinationDict[slot][','.join(self.photodict[image]['nodes'])].append(image)
            #     else:
            #         combinationDict[slot][','.join(self.photodict[image]['nodes'])] = [image]

        # poiRankedTimeslots = sorted(personPopularity, key = personPopularity.get, reverse = True) #rank timeslots according to POI's popularity
        poiRankedTimeslots = self.poiRankedTimeslots

        if decisionforAll == str('y') or decisionforAll == str(3):
            doItPop = input('\nRank images by node popularity (frequency)???(y or n):')
            doItCoapp = input('\nRank images by Coappearence frequency???(y or n):')
            personTotPhotos = 1
        else:
            doItPop = str('y')
            doItCoapp = str('y')

        rankedPhotosPopularityRRF, rankedPhotosPopularitySum = [], []
        photoRankCoapp, plainRankingCoapp,photoCoappearence, nodePool = {}, {},{}, {}
        popularityRRFMeasure,popularitySumMeasure = {}, {}
        popularityRRFDict, popularitySumDict = {}, {}
        PopularityRRFPrevLength,PopularitySumPrevLength,CoappPrevLength = 0,0,0
        maxPlain2 = 0
        while len(rankedPhotosPopularityRRF)<personTotPhotos or len(rankedPhotosPopularitySum)<personTotPhotos or len(photoRankCoapp)<personTotPhotos:
            for rankedslot in poiRankedTimeslots:
                peoplePopPerSlot = peoplePopularity[rankedslot]
                photoPool = personPool[rankedslot]
                sortedPeople = sorted(peoplePopPerSlot, key = peoplePopPerSlot.get, reverse = True)
                if rankedslot in popularityRRFDict:
                    plainRanking = popularityRRFDict[rankedslot]
                    plainRankingSum = popularitySumDict[rankedslot]
                else:
                    '''popularity dict builder'''
                    photoRankRRF, photoRankSum = {}, {}
                    nodePool[rankedslot] = []
                    for photo in photoPool:
                        tmpPop = [sortedPeople.index(x) for x in self.photodict[photo]['nodes']]
                        photoRankRRF[photo] = recRankCustom(tmpPop)
                        popularityRRFMeasure[photo] = photoRankRRF[photo]
                        tmpPopSum = [peoplePopPerSlot[x] for x in self.photodict[photo]['nodes']]
                        photoRankSum[photo] = sum(tmpPopSum)
                        popularitySumMeasure[photo] = photoRankSum[photo]
                        nodePool[rankedslot].append(self.photodict[photo]['nodes'])
                        plainRanking = sorted(photoRankRRF, key = photoRankRRF.get, reverse = True)
                        plainRankingSum = sorted(photoRankSum, key = photoRankSum.get, reverse = True)
                        popularityRRFDict[rankedslot] = plainRanking
                        popularitySumDict[rankedslot] = plainRankingSum
                    '''Coapp dict builder'''
                    if str(doItCoapp).lower() == str('y') or str(doItCoapp).lower() == str(3):
                        photoCoappearence[rankedslot] = {}
                        for idx,nodes in enumerate(nodePool[rankedslot]):
                            for idx2,poolnodes in enumerate(nodePool[rankedslot][idx:]):
                                commonNodes = list(set(nodes) & set(poolnodes))
                                commonNodes.sort()
                                if len(commonNodes) > 1:
                                    nodestr = ','.join(commonNodes)
                                    if nodestr not in photoCoappearence[rankedslot]:
                                        photoCoappearence[rankedslot][nodestr] = [photoPool[idx]]
                                        if photoPool[idx2+idx] not in photoCoappearence[rankedslot][nodestr]:
                                            photoCoappearence[rankedslot][nodestr].append(photoPool[idx2+idx])
                                    else:
                                        if photoPool[idx2+idx] not in photoCoappearence[rankedslot][nodestr]:
                                            photoCoappearence[rankedslot][nodestr].append(photoPool[idx2+idx])
                                        if photoPool[idx] not in photoCoappearence[rankedslot][nodestr]:
                                            photoCoappearence[rankedslot][nodestr].append(photoPool[idx])
                        photoCoappearence[rankedslot] = {k: v for k, v in photoCoappearence[rankedslot].items() if len(v)>1}
                        plainRankingCoapp[rankedslot] = sorted(photoCoappearence[rankedslot], key=lambda k: len(photoCoappearence[rankedslot][k])*len(k.split(',')), reverse = True)
                        photoRankCoapp[rankedslot] = []
                        for plain in plainRankingCoapp[rankedslot]:
                            photoCoappearence[rankedslot][plain].sort()
                            photoRankCoapp[rankedslot].append(photoCoappearence[rankedslot][plain])
                            maxPlain2 = max(maxPlain2,len(photoCoappearence[rankedslot][plain]))

                for photo in plainRanking:
                    if photo not in rankedPhotosPopularityRRF:
                        rankedPhotosPopularityRRF.append(photo)
                        break
                for photo in plainRankingSum:
                    if photo not in rankedPhotosPopularitySum:
                        rankedPhotosPopularitySum.append(photo)
                        break

            if (len(rankedPhotosPopularityRRF) == PopularityRRFPrevLength) and (len(rankedPhotosPopularitySum)==PopularitySumPrevLength) and (len(photoRankCoapp) == len(poiRankedTimeslots)):
                break
            PopularityRRFPrevLength,PopularitySumPrevLength = len(rankedPhotosPopularityRRF), len(rankedPhotosPopularitySum)

        if str(doItPop).lower() == str('y') or str(doItPop).lower() == str(3):
            #Save results
            methodName = 'basePopularityRRF'
            print('\n'+methodName)
            if decisionforAll == str('y') or decisionforAll == str(3):
                resultsSaver(poiRankedTimeslots,methodName,topImages,person,popularityRRFDict,popularityRRFMeasure,self.photodict,self.dataset_path_results,captiondict,combinationDict,Tmsl,self.fileTitle)
            else:
                resultsSaverAll(methodName,topImages,person,rankedPhotosPopularityRRF,popularityRRFMeasure,self.photodict,self.dataset_path_results,captiondict,combinationDict,Tmsl,self.fileTitle)

            #Save results
            methodName = 'basePopularitySum'
            print('\n'+methodName)
            if decisionforAll == str('y') or decisionforAll == str(3):
                resultsSaver(poiRankedTimeslots,methodName,topImages,person,popularitySumDict,popularitySumMeasure,self.photodict,self.dataset_path_results,captiondict,combinationDict,Tmsl,self.fileTitle)
            else:
                resultsSaverAll(methodName,topImages,person,rankedPhotosPopularitySum,popularitySumMeasure,self.photodict,self.dataset_path_results,captiondict,combinationDict,Tmsl,self.fileTitle)

        #Coapp saving results for html
        methodName = 'baseCoappearence'
        print('\n'+methodName)
        if decisionforAll == str('y') or decisionforAll == str(3):
            cnt = 0
            finPhotoPool, measurementCoapp, Coapps = {}, {}, {}
            cnt,nodeChckPool = 0,[]
            while len(finPhotoPool) < topImages:
                for slot in poiRankedTimeslots:
                    if len(finPhotoPool)>=topImages:
                        break
                    for k,coappPhotos in enumerate(photoRankCoapp[slot]):
                        try:
                            cnt2 = cnt
                            while self.photodict[coappPhotos[cnt2]]['nodes'] in nodeChckPool or plainRankingCoapp[slot][k] in nodeChckPool:
                                cnt2+=1
                            webbrowser.open(self.photodict[coappPhotos[cnt2]]['url'])
                            print('\n'+'\n'.join(plainRankingCoapp[slot][k].split(',')))
                            print(str(len(photoCoappearence[slot][plainRankingCoapp[slot][k]])*len(plainRankingCoapp[slot][k].split(','))))
                            decision = input('\nIs the url ok? Press Enter for Yes or 3|n for No?: ')
                            cnt3=cnt2
                            if decision == 'move':
                                continue
                            while str(decision).lower == 'n' or decision == str(3):
                                cnt3+=1
                                if self.photodict[coappPhotos[cnt3]]['nodes'] not in nodeChckPool:
                                    webbrowser.open(self.photodict[coappPhotos[cnt3]]['url'])
                                    decision = input('\nIs this duplicate ok?: ')
                                cnt2 = cnt3
                            else:
                                finPhotoPool[coappPhotos[cnt2]] = self.photodict[coappPhotos[cnt2]]['date']
                                nodeChckPool.append(plainRankingCoapp[slot][k])
                                nodeChckPool.append(self.photodict[coappPhotos[cnt2]]['nodes'])
                                measurementCoapp[coappPhotos[cnt2]] = str(len(photoCoappearence[slot][plainRankingCoapp[slot][k]])*len(plainRankingCoapp[slot][k].split(',')))
                                Coapps[coappPhotos[cnt2]] = plainRankingCoapp[slot][k]
                                break
                        except:
                            pass
                            continue
                cnt+=1
                if cnt > maxPlain2*len(photoRankCoapp):
                    break

            #save coappearence results
            finPhotos = sorted(finPhotoPool, key = finPhotoPool.get)
            finfile = codecs.open(self.dataset_path_results+self.fileTitle+'/html/'+person+"/"+methodName+".txt",'w','utf-8')
            for rP in finPhotos:
                finfile.write(person + '\t' + self.photodict[rP]['url'] + '\t' +str(Tmsl[rP])+'_'+ datetime.datetime.fromtimestamp(self.photodict[rP]['date']).strftime('%d/%m/%y')
                        + '\t' + str(rP) + '\t' + captiondict[rP] + '\t'+ ' '.join(Coapps[rP].split(',')) + '\t'+str(measurementCoapp[rP]) + '\n')
            finfile.close()
        else:#saving results for numeric analysis
            Coapps = {}
            cnt = 0
            finfile = codecs.open(self.dataset_path_results+self.fileTitle+'/analysis/'+methodName+".txt",'a','utf-8')
            while cnt < maxPlain2*len(photoRankCoapp):
                for slot in poiRankedTimeslots:
                    for k,coappPhotos in enumerate(photoRankCoapp[slot]):
                        try:
                            finfile.write(person + '\t' + self.photodict[coappPhotos[cnt]]['url'] + '\t' +str(Tmsl[coappPhotos[cnt]])+'_'+ datetime.datetime.fromtimestamp(self.photodict[coappPhotos[cnt]]['date']).strftime('%d/%m/%y')
                                + '\t' + str(coappPhotos[cnt]) + '\t' + captiondict[coappPhotos[cnt]] + '\t'+ ' '.join(plainRankingCoapp[slot][k].split(',')) + '\t'+str(len(photoCoappearence[slot][plainRankingCoapp[slot][k]])*len(plainRankingCoapp[slot][k].split(','))) + '\n')
                            break
                        except:
                            pass
                            continue
                cnt+=1
                if cnt > maxPlain2*len(photoRankCoapp):
                    break
            finfile.close()

def product(list):
    p = 1
    for i in list:
        p *= i
    return p

def recRankFus(mylist):#Perform the Reciprocal Rank Fusion for a list of rank values
    finscore = []
    mylist=[x+1 for x in mylist]
    for rank in mylist:
        finscore.append(1/(rank))
    return sum(finscore)/len(mylist)

def recRankFusEvol(mylist):
    finscore = []
    mylist=[x+1 for x in mylist]
    for rank in mylist:
        finscore.append(1/(rank))
    return sum(finscore)

def recRankCustom(mylist):
    finscore = []
    mylist=[x+1 for x in mylist]
    mylist.sort()
    for idx, rank in enumerate(mylist):
        if idx > 1:
            proj = 2*mylist[idx-1] - mylist[idx-2]
            if (proj - rank) >= 0:
                finscore.append(1/(rank))
            else:
                value = (1/rank) - (1/proj)
                finscore.append(value)
        else:
            finscore.append(1/(rank))
    return sum(finscore)

def myentropy(data):
    if not data:
        return 0
    entropy = 0
    for x in set(data):
        p_x = float(data.count(x))/len(data)
        if p_x > 0:
            entropy += -p_x*math.log(p_x, 2)
    return entropy

def resultsSaver(poiRankedTimeslots,methodName,topImages,person,mainResults,measurementContainer,photodict,dataset_path_results,captiondict,combinationDict,Tmsl,fileTitle):
    #saving results for html
    nodeChckPool, finPhotoPool, measurement = [], {}, {}
    while len(finPhotoPool) < topImages:
        for rankedslot in poiRankedTimeslots:
            if len(finPhotoPool)>=topImages:
                break
            flag = False
            tmpnodeChckPool = []
            for rP in mainResults[rankedslot]:
                if photodict[rP]['nodes'] in nodeChckPool or photodict[rP]['nodes'] in tmpnodeChckPool:
                    continue
                else:
                    webbrowser.open(photodict[rP]['url'])
                    print('\n'+'\n'.join(photodict[rP]['nodes']))
                    print(str(measurementContainer[rP]))
                    decision = input('\nIs the url ok? Press Enter for Yes or 3|n for No?: ')
                    if decision == 'move':
                        tmpnodeChckPool.append(photodict[rP]['nodes'])
                        continue
                    if str(decision).lower() == 'n' or decision == str(3):
                        for im in combinationDict[rankedslot][','.join(photodict[rP]['nodes'])]:
                            if im!= rP:
                                webbrowser.open(photodict[im]['url'])
                                decision = input('\nIs this duplicate ok?: ')
                                if decision == 'move':
                                    tmpnodeChckPool.append(photodict[im]['nodes'])
                                    break
                                if decision == 'N' or decision == 'n' or decision == str(3):
                                    continue
                                else:
                                    finPhotoPool[im] = photodict[im]['date']
                                    nodeChckPool.append(photodict[im]['nodes'])
                                    measurement[im] = measurementContainer[rP]
                                    flag = True
                                    break
                    else:
                        finPhotoPool[rP] = photodict[rP]['date']
                        nodeChckPool.append(photodict[rP]['nodes'])
                        measurement[rP] = measurementContainer[rP]
                        break
                    if len(finPhotoPool)>=topImages:
                        break
                tmpnodeChckPool.append(photodict[rP]['nodes'])
                if flag == True:
                    break
    finPhotos = sorted(finPhotoPool, key = finPhotoPool.get)
    finfile = codecs.open(dataset_path_results+fileTitle+'/html/'+person+"/"+methodName+".txt",'w','utf-8')
    for rP in finPhotos:
        finfile.write(person + '\t' + photodict[rP]['url'] + '\t' +str(Tmsl[rP])+'_'+ datetime.datetime.fromtimestamp(photodict[rP]['date']).strftime('%d/%m/%y')
            + '\t' + str(rP) + '\t' + captiondict[rP] + '\t'+ ' '.join(photodict[rP]['nodes'])  + '\t'+str(measurement[rP]) + '\n')
    finfile.close()

def resultsSaverAll(methodName,topImages,person,mainResults,measurementContainer,photodict,dataset_path_results,captiondict,combinationDict,Tmsl,fileTitle):
    #saving results for numeric analysis
    if not os.path.exists(dataset_path_results+fileTitle+'/analysis/'):
        os.makedirs(dataset_path_results+fileTitle+'/analysis/')

    finfile = codecs.open(dataset_path_results+fileTitle+'/analysis/'+methodName+".txt",'a','utf-8')
    for rP in mainResults:
        finfile.write(person + '\t' + photodict[rP]['url'] + '\t' +str(Tmsl[rP])+'_'+ datetime.datetime.fromtimestamp(photodict[rP]['date']).strftime('%d/%m/%y')
            + '\t' + str(rP) + '\t' + captiondict[rP] + '\t'+ ' '.join(photodict[rP]['nodes']) + '\t'+str(measurementContainer[rP]) + '\n')
    finfile.close()