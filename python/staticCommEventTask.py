#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:
# Purpose:       This .py file is the class file that does all the work
#                It ranks images in specific events
#
# Required libs: python-dateutil, numpy,matplotlib,pyparsing
# Author:        konkonst
#
# Created:       30/03/2014
# Copyright:     (c) ITI (CERTH) 2014
# Licence:       <apache licence 2.0>
#-------------------------------------------------------------------------------
import json, codecs, os, glob, time, dateutil.parser, collections, datetime, pickle, re, math
import urllib.request,webbrowser
import networkx as nx


class communitystatic:

    @classmethod
    def from_txt(cls,filename,dataset_path_results,dataset_path_tmp,timeLimit = 0):

        #Nodes that will be removed
        try:
            stopNodes = open('./data/txt/stopNodes.txt').readlines()
            stopNodes = [x.strip().lower() for x in stopNodes]
            stopNodes = [x.replace(' - ','_').replace(' ','_') for x in stopNodes if x]
        except:
            stopNodes = []

        '''Parse the txt files into authors/mentions/alltime lists'''
        authors, mentions =  {}, {}
        totPics,totPeople = 0,0
        photodict={}
        userdict = {}
        captiondict = {}
        emptyvalues = 0
        print(filename)
        with codecs.open(filename, "r", 'utf-8',errors='ignore') as f:
            for line in f:
                read_line = line.strip().encode('utf-8')
                read_line = read_line.decode('utf-8')
                try:
                    splitLine = read_line.split("\t")
                    dt = dateutil.parser.parse(splitLine[0])
                    mytime = int(time.mktime(dt.timetuple()))
                    numFaces = int(splitLine[5])
                    if mytime > timeLimit:
                        eventIds = splitLine[1].replace(' ','').split(',')
                        if not eventIds:
                            emptyvalues+=1
                        else:
                            for eventId in eventIds:
                                if eventId:
                                    peopleLine = splitLine[3].strip(', \n').strip('\n').replace('.','').replace('?','-').replace(', ',',').replace(', ,','').lower().split(",")
                                    peopleLine = [x.replace(' - ','_').replace(' ','_') for x in peopleLine if x]
                                    peopleLine = [x for x in peopleLine if x not in stopNodes]
                                    peopleLine.sort()
                                    numofpeople = len(peopleLine)
                                    if numofpeople > 1:#and numFaces>=numofpeople
                                        if eventId not in photodict:
                                            photodict[eventId] = {}
                                        if eventId not in userdict:
                                            userdict[eventId] = {}
                                        if eventId not in captiondict:
                                            captiondict[eventId] = {}
                                        if eventId not in authors:
                                            authors[eventId] = []
                                        if eventId not in mentions:
                                            mentions[eventId] = []
                                        photodict[eventId][totPics] = {}
                                        photodict[eventId][totPics]['nodes'] = peopleLine
                                        photodict[eventId][totPics]['url'] = splitLine[2]
                                        photodict[eventId][totPics]['date'] = mytime
                                        captiondict[eventId][totPics] = splitLine[-2]
                                        totPeople+=numofpeople
                                        for idx,tmpAuth in enumerate(peopleLine[:-1]):
                                            if tmpAuth in userdict[eventId]:
                                                userdict[eventId][tmpAuth].append(totPics)
                                            else:
                                                userdict[eventId][tmpAuth]=[totPics]
                                            theRest=peopleLine[idx+1:]
                                            for tmpMent in theRest:
                                                authors[eventId].append(tmpAuth)
                                                mentions[eventId].append(tmpMent)
                                        if peopleLine[-1] in userdict[eventId]:
                                                userdict[eventId][peopleLine[-1]].append(totPics)
                                        else:
                                            userdict[eventId][peopleLine[-1]]=[totPics]
                                        totPics+=1

                except:
                    pass
        f.close()

        statsfile = open(dataset_path_results+"basicstats.txt",'w')
        statement = ('Total # of Event Pics= ' + str(totPics)+
            "\nTotal # of People in Event Pics: "+str(totPeople)+
            "\nTotal empty eventIds: "+str(emptyvalues))
        print(statement)
        statsfile.write(statement)
        statsfile.close()

        return cls(authors, mentions, photodict, userdict, captiondict, dataset_path_results, dataset_path_tmp)

    def __init__(self, authors, mentions, photodict, userdict, captiondict, dataset_path_results, dataset_path_tmp):
        self.authors = authors
        self.mentions = mentions
        self.photodict = photodict
        self.userdict = userdict
        self.captiondict = captiondict
        self.uniqueUsers = {}
        self.dataset_path_results = dataset_path_results
        self.dataset_path_tmp = dataset_path_tmp

    def extraction(self,commDetectMethod, eventIdInput):
        self.eventIdInput = eventIdInput
        '''Extract adjacency lists,mats,user and community centrality and communities bags'''
        import community,link_clustering_din
        import Demon as D

        # '''Write all of the captions of the event to a file'''
        # allcaptions = []
        # for pic,(caption) in self.captiondict[eventIdInput].items():
        #     allcaptions.append(caption)
        # allcaptions = set(allcaptions)
        # captionfile = codecs.open(self.dataset_path_results+str(self.eventIdInput)+"/allcaptions.txt", 'w', "utf-8")
        # for caption in allcaptions:
        #     captionfile.write(caption + "\n")
        # captionfile.close()

        self.commPgRnkBag = {}

        '''Extract unique users globally and construct dictionary'''
        usrs = self.authors[eventIdInput].copy()
        usrs.extend(self.mentions[eventIdInput])
        usrs = list(set(usrs))
        usrs.sort()
        uniqueUsers, counter1 = {}, 0
        for tmpusrs in usrs:
            uniqueUsers[tmpusrs] = counter1
            counter1 += 1
        self.uniqueUsers = uniqueUsers

        '''Make pairs of users with weights'''
        usersPair = list(zip(self.authors[eventIdInput], self.mentions[eventIdInput]))
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
        del(adjusrs,adjauthors,adjments,weights,weighted,usersPair, authorsNum, mentionsNum, self.authors,self.mentions, self.captiondict)

        # '''Write pairs of users to txt file for Gephi'''
        # if not os.path.exists(self.dataset_path_results+"forGephi/"):
        #     os.makedirs(self.dataset_path_results+"forGephi/")
        # my_txt = codecs.open(self.dataset_path_results+"forGephi/event_"+str(self.eventIdInput)+".txt", "w", "utf-8")
        # my_txt.write("Source,Target,Weight,Type"+"\n")
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
        self.userPgRnkBag = tempUserPgRnk


        '''Detect Communities using the louvain algorithm'''
        partitionLouv = community.best_partition(tempGraph)
        # inv_partitionLouv = {}
        # for k, v in partitionLouv.items():
        #     inv_partitionLouv[v] = inv_partitionLouv.get(v, [])
        #     inv_partitionLouv[v].append(k)
        #     inv_partitionLouv[v].sort()
        # strCommsLouv = [inv_partitionLouv[x] for x in inv_partitionLouv]
        # strCommsLouv.sort(key=len, reverse=True)
        if commDetectMethod[0] == 'Ahn':
            '''Detect Communities using the Ahn algorithm'''
            inv_partition = link_clustering_din.ahnsmethod(adjList, threshold=commDetectMethod[1])
            strComms = [inv_partition[x] for x in inv_partition]
            strComms.sort(key=len, reverse=True)
        elif commDetectMethod[0] == 'Demon':
            DemObj = D.Demon()
            strComms = DemObj.execute(tempGraph, weighted=True, min_community_size=1)
            strComms.sort(key=len, reverse=True)
            inv_partition=0
        elif commDetectMethod[0] == 'Copra':
            '''Detect Communities using the Copra algorithm'''
            os.system("java -cp ./copra.jar COPRA " + self.dataset_path_tmp + "forCopra.txt -w -extrasimplify -v 10 -mo -repeat 3")
            if os.path.exists(self.dataset_path_tmp+'best-clusters-forCopra.txt'):
                    os.remove(self.dataset_path_tmp+'best-clusters-forCopra.txt')
            os.rename('./best-clusters-forCopra.txt',self.dataset_path_tmp + 'best-clusters-forCopra.txt')
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
                    time.sleep(6)
                    pass
            inv_partition=0
            if os.path.exists(self.dataset_path_tmp+'best-clusters-forCopra.txt'):
                    os.remove(self.dataset_path_tmp+'best-clusters-forCopra.txt')
                    os.remove(self.dataset_path_tmp+'forCopra.txt')
            for filename in  glob.glob("./clusters*.txt"):#delete txt files
                os.remove(filename)
        else:
            print('No such method as:'+commDetectMethod[0])
        del(adjList,inv_partition)

        '''Construct Community Dictionary'''
        self.commStrBag = strComms
        self.partitionLouv = partitionLouv

        self.commDetectMethod = commDetectMethod[0]

        self.photodict = self.photodict[self.eventIdInput]
        self.userdict = self.userdict[self.eventIdInput]

        # statement = 'Total # of communities is '+str(len(strComms))+'\n'
        # statsfile = open(self.dataset_path_results+ str(self.eventIdInput) +"/basicstats.txt",'w')
        # print(statement)
        # statsfile.write(statement)
        # statsfile.close()

        dataCommPck = open(self.dataset_path_tmp+'comm_'+self.commDetectMethod+'Ev_'+str(self.eventIdInput)+'.pck','wb')
        pickle.dump(self, dataCommPck , protocol = 2)
        dataCommPck.close()
        return self

    def photoRetrieval(self, topImages, captiondict,decisionforAll):
        # if not os.path.exists(self.dataset_path_results+str(self.eventIdInput)):
        #     os.makedirs(self.dataset_path_results+str(self.eventIdInput))

        decisionforAll = str(decisionforAll).lower()
        self.decisionforAll = decisionforAll

        '''Rank users in accordance to their centrality'''
        usrCentrSorted = sorted(self.userPgRnkBag, key = self.userPgRnkBag.get, reverse = True)
        maxPGR=max((pgr for k,(pgr) in self.userPgRnkBag.items()))
        for k in self.userPgRnkBag.items():
            self.userPgRnkBag[k[0]]/=maxPGR

        '''Retrieve images in respect to their overlapping of communities'''

        #Check for overlapping nodes in between communities
        overlNodes = {}
        for node in self.uniqueUsers.keys():
            nodeComms = []
            for idx, comms in enumerate(self.commStrBag):
                if node in comms:
                    nodeComms.append(idx)
            if len(nodeComms) > 1:
                overlNodes[node]=nodeComms
        #Retrieve images if any overlapping occurs
        if len(overlNodes) > 0:

            rankedOverlNodes = sorted(overlNodes, key=lambda k: len(overlNodes[k])+self.userPgRnkBag[k], reverse=True)
            '''Retrieve photos with most common overlappers'''
            photoPool, maxPlain  = [], 0
            for node in rankedOverlNodes:
                photoPool.extend(self.userdict[node])
                maxPlain = max(maxPlain,len(self.userdict[node]))
            if decisionforAll == str('y') or decisionforAll == str(3):
                doIt = input('\nRetrieve photos with most common overlappers???(y or n)')
            else:
                doIt = 'y'
            if str(doIt).lower() == 'y' or str(doIt).lower() == str(3):
                commonPhotos = collections.Counter(photoPool)
                commonKeys = list(commonPhotos.keys())
                commonVals = list(commonPhotos.values())
                for keyidx,k in enumerate(commonKeys):
                    if commonVals[keyidx] < 2:
                        del(commonPhotos[k])
                poolIntersex2 = {}
                if len(commonPhotos) > 0:
                    poolIntersex = commonPhotos.most_common()
                    mostcomm, combinationDict = [], {}#combinationDict is used to retrieve images if the presented one is incorrect
                    for vals in poolIntersex:
                        commonNodes = list(set(self.photodict[vals[0]]['nodes']) & set(rankedOverlNodes))
                        poolIntersex2[vals[0]] = sum([len(overlNodes[k]) for k in commonNodes])
                        entropy =  [self.partitionLouv[x] for x in self.photodict[vals[0]]['nodes']]
                        entropy = myentropy(entropy)
                        tmp = [rankedOverlNodes.index(x) for x in self.photodict[vals[0]]['nodes'] if x in rankedOverlNodes]
                        mostcomm.append([vals[0], poolIntersex2[vals[0]], entropy, recRankCustom(tmp)])
                        if ','.join(self.photodict[vals[0]]['nodes']) in combinationDict:
                            combinationDict[','.join(self.photodict[vals[0]]['nodes'])].append(vals[0])
                            combinationDict[','.join(self.photodict[vals[0]]['nodes'])] = list(set(combinationDict[','.join(self.photodict[vals[0]]['nodes'])]))
                            combinationDict[','.join(self.photodict[vals[0]]['nodes'])].sort()
                        else:
                            combinationDict[','.join(self.photodict[vals[0]]['nodes'])] = [vals[0]]
                    mostcomm.sort(key=lambda k: (k[1]*(1+k[2]),k[3]), reverse = True)
                else:
                    mostcomm = []
                    combinationDict = {}

                rankedPhotos, measurementContainer = [], {}
                for comb in mostcomm:
                    rankedPhotos.append(comb[0])
                    measurementContainer[comb[0]] = comb[1]*(1+comb[2])


                #Save results
                methodName = 'Coappearing_Overlappers'
                print('\n'+methodName)
                if decisionforAll == str('y') or decisionforAll == str(3):
                    resultsSaver(methodName,topImages,str(self.eventIdInput),rankedPhotos,measurementContainer,self.photodict,self.dataset_path_results,captiondict,combinationDict)
                else:
                    resultsSaverAll(methodName,topImages,str(self.eventIdInput),rankedPhotos,measurementContainer,self.photodict,self.dataset_path_results,captiondict,combinationDict)
            else:
                combinationDict = {}
            '''Retrieve photos according to the overlappers' ranking'''
            if decisionforAll == str('y') or decisionforAll == str(3):
                doIt = input('\nRetrieve photos according to the overlappers\' ranking???(y or n)')
            else:
                doIt = 'y'
            if str(doIt).lower() == 'y' or str(doIt).lower() == 3:
                rankedPhotos = []
                cnt= 0
                measurementContainer = {}
                while cnt <= maxPlain:
                    for node in rankedOverlNodes:
                        photokeys = self.userdict[node]
                        if cnt <= len(photokeys):
                            photoRank = {}
                            for photoId in photokeys:
                                tmp = [usrCentrSorted.index(x) for x in self.photodict[photoId]['nodes']]
                                photoRank[photoId] = recRankCustom(tmp)
                                measurementContainer[photoId] = photoRank[photoId]
                                if ','.join(self.photodict[photoId]['nodes']) in combinationDict:
                                    combinationDict[','.join(self.photodict[photoId]['nodes'])].append(photoId)
                                    combinationDict[','.join(self.photodict[photoId]['nodes'])] = list(set(combinationDict[','.join(self.photodict[photoId]['nodes'])]))
                                else:
                                    combinationDict[','.join(self.photodict[photoId]['nodes'])] = [photoId]
                            plainRanking = sorted(photoRank, key = photoRank.get, reverse = True)
                            cnt2=0
                            try:
                                while plainRanking[cnt+cnt2] in rankedPhotos:
                                    cnt2+=1
                                rankedPhotos.append(plainRanking[cnt+cnt2])
                            except:
                                pass
                    cnt+=1

                #Save results
                methodName = 'Ranked_Overlappers'
                print('\n'+methodName)
                if decisionforAll == str('y') or decisionforAll == str(3):
                    resultsSaver(methodName,topImages,self.eventIdInput,rankedPhotos,measurementContainer,self.photodict,self.dataset_path_results,captiondict,combinationDict)
                else:
                    resultsSaverAll(methodName,topImages,self.eventIdInput,rankedPhotos,measurementContainer,self.photodict,self.dataset_path_results,captiondict,combinationDict)
        else:
            print('No overlapping occurred')
            combinationDict = {}

        '''Rank images by creating measuring value for each photo using reciprocal of ranks of the contained nodes'''
        if decisionforAll == str('y') or decisionforAll == str(3):
            doIt = input('\nRank images by reciprocal of ranks of the contained nodes???(y or n)')
        else:
            doIt = 'y'
        if str(doIt).lower() == 'y' or str(doIt).lower() == str(3):
            # photoTxt = open(self.dataset_path_results+str(self.eventIdInput)+'/allphotos.txt','w')
            photokeys = self.photodict.keys()
            photoRank = {}
            for photoId in photokeys:
                tmp = [usrCentrSorted.index(x) for x in self.photodict[photoId]['nodes']]
                photoRank[photoId] = recRankCustom(tmp)
                if ','.join(self.photodict[photoId]['nodes']) in combinationDict:
                    combinationDict[','.join(self.photodict[photoId]['nodes'])].append(photoId)
                    combinationDict[','.join(self.photodict[photoId]['nodes'])] = list(set(combinationDict[','.join(self.photodict[photoId]['nodes'])]))
                else:
                    combinationDict[','.join(self.photodict[photoId]['nodes'])] = [photoId]
                #Save all images and all urls for this event
            #     photoTxt.write(self.photodict[photoId]['url']+'\n')
            # photoTxt.close()

            plainRanking = sorted(photoRank, key = photoRank.get, reverse = True)#sort photos by RRF value

            #Save results
            methodName = 'ReciprocalRanks'
            print('\n'+methodName)
            if decisionforAll == str('y') or decisionforAll == str(3):
                resultsSaver(methodName,topImages,self.eventIdInput,plainRanking,photoRank,self.photodict,self.dataset_path_results,captiondict,combinationDict)
            else:
                resultsSaverAll(methodName,topImages,self.eventIdInput,plainRanking,photoRank,self.photodict,self.dataset_path_results,captiondict,combinationDict)

    '''Create baseline solutions'''

    def popularity_coapperence(self, topImages, captiondict):
        decisionforAll = self.decisionforAll
        '''Aggregate node frequency (popularity)'''

        peoplePopularity = {}#compute node popularity in this specific event
        for node in self.userdict.keys():
            peoplePopularity[node] = len(self.userdict[node])
        sortedPeople = sorted(peoplePopularity, key = peoplePopularity.get, reverse = True)

        photoRank, photoRankSum = {}, {} #use node popularity in event to compute photo overall popularity
        nodePool, photoPool, combinationDict = [], [], {}#combinationDict is used to retrieve images if the presented one is incorrect
        for photo in self.photodict:
            photoPool.append(photo)
            tmpPop = [sortedPeople.index(x) for x in self.photodict[photo]['nodes']]
            photoRank[photo] = recRankCustom(tmpPop)
            tmpPopSum = [peoplePopularity[x] for x in self.photodict[photo]['nodes']]
            photoRankSum[photo] = sum(tmpPopSum)
            nodePool.append(self.photodict[photo]['nodes'])#create photopool for coappearence frequency below
            if ','.join(self.photodict[photo]['nodes']) in combinationDict:
                combinationDict[','.join(self.photodict[photo]['nodes'])].append(photo)
                combinationDict[','.join(self.photodict[photo]['nodes'])] = list(set(combinationDict[','.join(self.photodict[photo]['nodes'])]))
            else:
                combinationDict[','.join(self.photodict[photo]['nodes'])] = [photo]

        if decisionforAll == str('y') or decisionforAll == str(3):
            doIt = input('\nRank images by node popularity (frequency)???(y or n)')
        else:
            doIt = 'y'
        if str(doIt).lower() == 'y' or str(doIt).lower() == str(3):
            plainRanking = sorted(photoRank, key = photoRank.get, reverse = True)
            plainRankingSum = sorted(photoRankSum, key = photoRankSum.get, reverse = True)

            #Save results
            methodName = 'basePopularityRRF'
            print('\n'+methodName)
            if decisionforAll == str('y') or decisionforAll == str(3):
                resultsSaver(methodName,topImages,self.eventIdInput,plainRanking,photoRank,self.photodict,self.dataset_path_results,captiondict,combinationDict)
            else:
                resultsSaverAll(methodName,topImages,self.eventIdInput,plainRanking,photoRank,self.photodict,self.dataset_path_results,captiondict,combinationDict)

            #Save results
            methodName = 'basePopularitySum'
            print('\n'+methodName)
            if decisionforAll == str('y') or decisionforAll == str(3):
                resultsSaver(methodName,topImages,self.eventIdInput,plainRankingSum,photoRankSum,self.photodict,self.dataset_path_results,captiondict,combinationDict)
            else:
                resultsSaverAll(methodName,topImages,self.eventIdInput,plainRankingSum,photoRankSum,self.photodict,self.dataset_path_results,captiondict,combinationDict)

        '''Coappearence frequency'''
        if decisionforAll == str('y') or decisionforAll == str(3):
            doIt = input('\nRank images by Coappearence frequency???(y or n)')
        else:
            doIt = 'y'
        if str(doIt).lower() == 'y' or str(doIt).lower() == str(3):
            photoCoappearence = {} #use node coappearence in event to compute photo overall popularity
            coappPop = {}
            for idx,nodes in enumerate(nodePool):
                    for idx2,poolnodes in enumerate(nodePool[idx:]):
                        commonNodes = list(set(nodes) & set(poolnodes))
                        commonNodes.sort()
                        if len(commonNodes) > 1:
                            nodestr = ','.join(commonNodes)
                            if nodestr not in photoCoappearence:                                
                                coappPop[nodestr] = sum([peoplePopularity[x] for x in commonNodes])
                                photoCoappearence[nodestr] = [photoPool[idx]]
                                if photoPool[idx2+idx] not in photoCoappearence[nodestr]:
                                    photoCoappearence[nodestr].append(photoPool[idx2+idx])
                            else:
                                if photoPool[idx2+idx] not in photoCoappearence[nodestr]:
                                    photoCoappearence[nodestr].append(photoPool[idx2+idx])
                                if photoPool[idx] not in photoCoappearence[nodestr]:
                                    photoCoappearence[nodestr].append(photoPool[idx])
            photoCoappearence = {k: v for k, v in photoCoappearence.items() if len(v)>1}
            plainRanking = sorted(photoCoappearence, key=lambda k: (len(photoCoappearence[k])*len(k.split(',')),coappPop[k]), reverse = True)
            photoRank = []
            maxPlain2 = 0
            for plain in plainRanking:
                photoCoappearence[plain].sort()
                photoRank.append(photoCoappearence[plain])
                maxPlain2 = max(maxPlain2,len(photoCoappearence[plain]))

            methodName = 'baseCoappearence'
            if decisionforAll == str('y') or decisionforAll == str(3):
                #save results
                finPhotoPool, measurement, Coapps = {}, {}, {}
                cnt,nodeChckPool = 0, []
                while len(finPhotoPool) < topImages or cnt <= maxPlain2:
                    for k,coappPhotos in enumerate(photoRank):
                        try:
                            if len(finPhotoPool)>=topImages:
                                break
                            cnt2 = cnt
                            while self.photodict[coappPhotos[cnt2]]['nodes'] in nodeChckPool or coappPhotos[cnt2] in finPhotoPool:
                                cnt2+=1
                            webbrowser.open(self.photodict[coappPhotos[cnt2]]['url'])
                            print('\n'+'\n'.join(plainRanking[k].split(',')))
                            print(len(photoCoappearence[plainRanking[k]])*len(plainRanking[k].split(',')))
                            decision = input('\nIs the url ok? Press Enter for Yes or 3|n for No?: ')
                            if decision == 'move':
                                continue
                            cnt3=cnt2
                            while decision == 'N' or decision == 'n' or decision == str(3):
                                cnt3+=1
                                if self.photodict[coappPhotos[cnt3]]['nodes'] not in nodeChckPool and coappPhotos[cnt3] not in finPhotoPool:
                                    webbrowser.open(self.photodict[coappPhotos[cnt3]]['url'])
                                    decision = input('\nIs this duplicate ok?: ')
                                cnt2 = cnt3
                            else:
                                finPhotoPool[coappPhotos[cnt2]] = self.photodict[coappPhotos[cnt2]]['date']
                                measurement[coappPhotos[cnt2]] = len(photoCoappearence[plainRanking[k]])*len(plainRanking[k].split(','))
                                Coapps[coappPhotos[cnt2]] = plainRanking[k]
                        except:
                            pass
                            continue
                    nodeChckPool.append(self.photodict[coappPhotos[cnt2]]['nodes'])
                    cnt+=1
                finPhotos = sorted(finPhotoPool, key = finPhotoPool.get)
                finfile = codecs.open(self.dataset_path_results+'html/'+str(self.eventIdInput)+"/"+methodName+".txt",'w','utf-8')
                for rP in finPhotos:
                    finfile.write(str(self.eventIdInput) + '\t' + self.photodict[rP]['url'] + '\t' + datetime.datetime.fromtimestamp(self.photodict[rP]['date']).strftime('%d/%m/%y')
                        + '\t' + str(rP) + '\t' + captiondict[rP] + '\t'+ ' '.join(Coapps[rP].split(',')) + '\t' + str(measurement[rP]) + '\n')
                finfile.close()
            else:
                #save results                
                print('\n'+methodName)
                cnt = 0
                finfile = codecs.open(self.dataset_path_results+'analysis/'+methodName+".txt",'a','utf-8')
                while cnt <= maxPlain2:
                    for k,coappPhotos in enumerate(photoRank):
                        try:
                            finfile.write(str(self.eventIdInput) + '\t' + self.photodict[coappPhotos[cnt]]['url'] + '\t' + datetime.datetime.fromtimestamp(self.photodict[coappPhotos[cnt]]['date']).strftime('%d/%m/%y')
                                + '\t' + str(coappPhotos[cnt]) + '\t' + captiondict[coappPhotos[cnt]] + '\t'+ ' '.join(plainRanking[k].split(',')) + '\t'+str(len(photoCoappearence[plainRanking[k]])*len(plainRanking[k].split(','))) + '\n')
                        except:
                            pass
                            continue
                    cnt+=1
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
    return sum(finscore)#/len(mylist)

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
            entropy += - p_x*math.log(p_x, 2)
    return entropy

def resultsSaver(methodName,topImages,event,mainResults,measurementContainer,photodict,dataset_path_results,captiondict,combinationDict):
    #Save results
    if not os.path.exists(dataset_path_results+'html/'+str(event)+'/'):
        os.makedirs(dataset_path_results+'html/'+str(event)+'/')
    nodeChckPool, finPhotoPool, measurement = [], {}, {}
    for rP in mainResults:
        if photodict[rP]['nodes'] in nodeChckPool:
            continue
        else:
            webbrowser.open(photodict[rP]['url'])
            print('\n'+'\n'.join(photodict[rP]['nodes']))
            print(str(measurementContainer[rP]))
            decision = input('\nIs the url ok? Press Enter for Yes or 3|n for No?: ')
            if decision == 'move':
                nodeChckPool.append(photodict[rP]['nodes'])
                continue
            if decision == 'N' or decision == 'n' or decision == str(3):
                for im in combinationDict[','.join(photodict[rP]['nodes'])]:
                    if im!= rP:
                        webbrowser.open(photodict[im]['url'])
                        decision = input('\nIs this duplicate ok?: ')
                        if decision == 'N' or decision == 'n' or decision == str(3):
                            continue
                        else:
                            finPhotoPool[im] = photodict[im]['date']
                            nodeChckPool.append(photodict[im]['nodes'])
                            measurement[im] = measurementContainer[rP]
                            break
            else:
                finPhotoPool[rP] = photodict[rP]['date']
                measurement[rP] = measurementContainer[rP]
            if len(finPhotoPool)==topImages:
                break
        nodeChckPool.append(photodict[rP]['nodes'])
    finPhotos = sorted(finPhotoPool, key = finPhotoPool.get)
    finfile = codecs.open(dataset_path_results+'html/'+str(event)+"/"+methodName+".txt",'w','utf-8')
    for rP in finPhotos:
        finfile.write(str(event) + '\t' + photodict[rP]['url'] + '\t' + datetime.datetime.fromtimestamp(photodict[rP]['date']).strftime('%d/%m/%y')
            + '\t' + str(rP) + '\t' + captiondict[rP]  + '\t'+ ' '.join(photodict[rP]['nodes']) + '\t'+str(measurement[rP]) + '\n')
    finfile.close()

def resultsSaverAll(methodName,topImages,event,mainResults,measurementContainer,photodict,dataset_path_results,captiondict,combinationDict):
    #Save results
    if not os.path.exists(dataset_path_results+'analysis/'):
        os.makedirs(dataset_path_results+'analysis/')
    measurement = {}
    finfile = codecs.open(dataset_path_results+'analysis/'+methodName+".txt",'a','utf-8')
    for rP in mainResults:
        finfile.write(str(event) + '\t' + photodict[rP]['url'] + '\t' + datetime.datetime.fromtimestamp(photodict[rP]['date']).strftime('%d/%m/%y')
            + '\t' + str(rP) + '\t' + captiondict[rP]  + '\t'+ ' '.join(photodict[rP]['nodes']) + '\t'+str(measurementContainer[rP]) + '\n')        
    finfile.close()