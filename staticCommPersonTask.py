#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, codecs, os, glob, time, dateutil.parser, collections, datetime, pickle, re, math
import urllib.request, webbrowser
import networkx as nx


class communitystatic:

    @classmethod
    def from_txt(cls,filename,dataset_path_results,dataset_path_tmp):

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

        timeLimit = 1071561600#1071561600:1355702400

        '''Parse the txt files into authors/mentions lists'''
        authors, mentions =  [], []
        totPics,totPeople = 0,0
        photodict={}
        userdict = {}
        captiondict = {}
        print(filename)
        with codecs.open(filename, "r", 'utf-8') as f:
            for line in f:
                read_line = line.strip().encode('utf-8')
                read_line = read_line.decode('utf-8')
                try:
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
                        if numofpeople > 1: #numofpeople > 1 and numFaces>=numofpeople and
                            photodict[totPics] = {}
                            photodict[totPics]['nodes'] = peopleLine
                            photodict[totPics]['url'] = splitLine[2]
                            photodict[totPics]['date'] = mytime
                            captiondict[totPics] = splitLine[-2]
                            totPeople+=numofpeople
                            for idx,tmpAuth in enumerate(peopleLine[:-1]):
                                if tmpAuth in userdict:
                                    userdict[tmpAuth].append(totPics)
                                else:
                                    userdict[tmpAuth]=[totPics]
                                theRest=peopleLine[idx+1:]
                                for tmpMent in theRest:
                                    authors.append(tmpAuth)
                                    mentions.append(tmpMent)
                            if peopleLine[-1] in userdict:
                                userdict[peopleLine[-1]].append(totPics)
                            else:
                                userdict[peopleLine[-1]]=[totPics]
                            totPics+=1
                except:
                    pass
        f.close()

        statsfile = open(dataset_path_tmp+"basicstats.txt",'w')
        statement = ('Total # of Pics= ' + str(totPics)+
            "\nTotal # of People in Pics: "+str(totPeople)+
            "\nTotal # of edges is: " + str(len(authors)))
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

    def extraction(self,commDetectMethod):
        '''Extract adjacency lists,mats,user and community centrality and communities bags'''
        import community,link_clustering_din
        import Demon as D

        self.commPgRnkBag = {}

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

        '''Make pairs of users with weights'''
        usersPair = list(zip(self.authors, self.mentions))
        #Create weighted adjacency list
        weighted = collections.Counter(usersPair)
        weighted = list(weighted.items())
        adjusrs, weights = zip(*weighted)
        adjauthors, adjments = zip(*adjusrs)
        adjList = list(zip(adjauthors, adjments, weights))
        '''Make pairs of users(their uniqueUsers Ids) with weights for Copra'''
        if commDetectMethod[0] == 'Copra':
            authorsNum,mentionsNum = [], []
            for idx,auth in enumerate(adjauthors):
                authorsNum.append(uniqueUsers[auth])
                mentionsNum.append(uniqueUsers[adjments[idx]])
            adjListNum = list(zip(authorsNum, mentionsNum, weights))
            del(authorsNum, mentionsNum)
        del(adjusrs,adjauthors,adjments,weights,weighted,usersPair, self.authors, self.mentions, self.captiondict)

        '''Write pairs of users to txt file for Gephi'''
        my_txt = codecs.open(self.dataset_path_tmp[:-4]+"forGephi.txt", "w", "utf-8")
        my_txt.write("Source,Target,Weight,Type"+"\n")
        for line in adjList:
            line = list(line)
            line.append('Undirected')
            my_txt.write(",".join(str(x) for x in line) + "\n")
        my_txt.close()

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
        modularity=community.modularity(partitionLouv,tempGraph)
        inv_partitionLouv = {}
        for k, v in partitionLouv.items():
            inv_partitionLouv[v] = inv_partitionLouv.get(v, [])
            inv_partitionLouv[v].append(k)
            inv_partitionLouv[v].sort()
        strCommsLouv = [inv_partitionLouv[x] for x in inv_partitionLouv]
        strCommsLouv.sort(key=len, reverse=True)
        if commDetectMethod[0] == 'Ahn':
            '''Detect Communities using the Ahn algorithm'''
            inv_partition = link_clustering_din.ahnsmethod(adjList, threshold=commDetectMethod[1])
            strComms = [inv_partition[x] for x in inv_partition]
            strComms.sort(key=len, reverse=True)
        elif commDetectMethod[0] == 'Demon':
            '''Detect Communities using the Demon algorithm'''
            DemObj = D.Demon()
            strComms = DemObj.execute(tempGraph, weighted=True, min_community_size=1)
            strComms.sort(key=len, reverse=True)
            inv_partition=0
        elif commDetectMethod[0] == 'Copra':
            '''Detect Communities using the Copra algorithm'''
            os.system("java -cp ./copra.jar COPRA " + self.dataset_path_tmp + "forCopra.txt -w -v 10 -mo -repeat 3")   #-extrasimplify
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

        #Check for overlapping nodes in between communities
        overlNodes = {}
        for node in self.uniqueUsers.keys():
            nodeComms = []
            for idx, comms in enumerate(strComms):
                if node in comms:
                    nodeComms.append(idx)
            if len(nodeComms) > 1:
                overlNodes[node]=nodeComms
        self.overlNodes = overlNodes

        self.partitionLouv = partitionLouv

        self.commDetectMethod = commDetectMethod[0]

        statement = ('Total # of communities is '+str(len(strComms)) + '\n'+
            'Overlapping of '+str(len(overlNodes))+' occurred.'+ '\n'+
            'Total # of unique nodes is '+str(len(uniqueUsers)) + '\n')
        statsfile = open(self.dataset_path_results+"basicstats.txt",'a')
        print(statement)
        statsfile.write(statement)
        statsfile.close()

        dataCommPck = open(self.dataset_path_tmp+'comm_'+self.commDetectMethod+'.pck','wb')
        pickle.dump(self, dataCommPck , protocol = 2)
        dataCommPck.close()
        return self

    def photoRetrieval(self, topImages, person, captiondict, decisionforAll):

        decisionforAll = str(decisionforAll).lower()
        self.decisionforAll = decisionforAll
        '''Create persons own pool of images'''
        personPool = self.userdict[person]

        '''Rank users in accordance to their centrality'''
        usrCentrSorted = sorted(self.userPgRnkBag, key = self.userPgRnkBag.get, reverse = True)
        maxPGR=max((pgr for k,(pgr) in self.userPgRnkBag.items()))
        for k in self.userPgRnkBag.items():
            self.userPgRnkBag[k[0]]/=maxPGR

        overlNodesFile = codecs.open(self.dataset_path_tmp+'overlappingNodes.txt','w','utf-8')
        rankedOverlNodes = sorted(self.overlNodes, key=lambda k: len(self.overlNodes[k]), reverse=True)
        for k in rankedOverlNodes:
            overlNodesFile.write(str(k)+'\t'+str(len(self.overlNodes[k]))+'\n')
        overlNodesFile.close()

        '''Retrieve images in respect to their overlapping of communities'''

        rankedOverlNodes = sorted(self.overlNodes, key=lambda k: len(self.overlNodes[k])+self.userPgRnkBag[k], reverse=True)
        try:
            personIdx = rankedOverlNodes.index(person)
            del(rankedOverlNodes[personIdx])
        except:
            pass
        #combinationDict is used to retrieve images if the presented one is incorrect
        photoPool, countOverlaps, poolIntersex, combinationDict = [], 0, {}, {}
        for image in personPool:
            commonNodes = list(set(self.photodict[image]['nodes']) & set(rankedOverlNodes))
            imageOverlapperPopularity = len(commonNodes)
            if ','.join(self.photodict[image]['nodes']) in combinationDict:
                combinationDict[','.join(self.photodict[image]['nodes'])].append(image)
                combinationDict[','.join(self.photodict[image]['nodes'])].sort()
            else:
                combinationDict[','.join(self.photodict[image]['nodes'])] = [image]
            if imageOverlapperPopularity:
                # poolIntersex[image] = imageOverlapperPopularity
                poolIntersex[image] = sum([len(self.overlNodes[k]) for k in commonNodes])
                countOverlaps+=1

        self.combinationDict = combinationDict

        if len(poolIntersex) > 0:
            '''Retrieve photos with most common overlappers'''
            if decisionforAll == str('y') or decisionforAll == str(3):
                doIt = input('\nRetrieve photos with most common overlappers???(y or n)')
            else:
                doIt = 'y'
            if str(doIt).lower() == 'y' or str(doIt).lower() == 3:
                sortedPoolIntersex = sorted(poolIntersex, key = poolIntersex.get, reverse = True)
                mostcomm=[]
                measureCoappOverl = {}
                mostcommEntr = []
                entropy = {}
                for image in sortedPoolIntersex:
                    entropyList =  [self.partitionLouv[x] for x in self.photodict[image]['nodes']]
                    entropy[image] = myentropy(entropyList)
                    tmp = [rankedOverlNodes.index(x) for x in self.photodict[image]['nodes'] if x in rankedOverlNodes]
                    mostcomm.append([image, poolIntersex[image], entropy[image], recRankCustom(tmp)])
                    measureCoappOverl[image] = poolIntersex[image]*(1+entropy[image])
                    mostcommEntr.append([image, entropy[image], recRankCustom(tmp)])
                mostcomm.sort(key=lambda k: (k[1]*(1+k[2]),k[3]), reverse = True)
                mostcommEntr.sort(key=lambda k: (k[1],k[2]), reverse = True)
                sortedPoolIntersex = [x[0] for x in mostcomm]
                sortedPoolIntersexEntr = [x[0] for x in mostcommEntr]

                #Save results
                methodName = 'Coappearing_Overlappers'
                print('\n'+methodName)
                if decisionforAll == str('y') or decisionforAll == str(3):
                    resultsSaver(methodName,topImages,person,sortedPoolIntersex,measureCoappOverl,self.photodict,self.dataset_path_results,captiondict,combinationDict)
                else:
                    resultsSaverAll(methodName,topImages,person,sortedPoolIntersex,measureCoappOverl,self.photodict,self.dataset_path_results,captiondict,combinationDict)

                # #Save results
                # methodName = 'Coappearing_OverlappersEntropy'
                # print('\n'+methodName)
                # if decisionforAll == str('y') or decisionforAll == str(3):
                #     resultsSaver(methodName,topImages,person,sortedPoolIntersexEntr,entropy,self.photodict,self.dataset_path_results,captiondict,combinationDict)
                # else:
                #     resultsSaverAll(methodName,topImages,person,sortedPoolIntersexEntr,entropy,self.photodict,self.dataset_path_results,captiondict,combinationDict)

            '''Retrieve photos according to the overlappers' ranking'''
            if decisionforAll == str('y') or decisionforAll == str(3):
                doIt = input('\nRetrieve photos according to the overlappers\' ranking???(y or n)')
            else:
                doIt = 'y'
            if str(doIt).lower() == 'y' or str(doIt).lower() == 3:
                plainRanking = {}
                photokeys = poolIntersex.keys()
                measurementContainer = {}
                maxPlain = 0
                rankedtmpnodes = []
                for node in rankedOverlNodes:
                    photoRank = {}
                    plainRanking[node] = []
                    for photoId in photokeys:
                        if node in self.photodict[photoId]['nodes'] and photoId not in measurementContainer:
                            tmp = [usrCentrSorted.index(x) for x in self.photodict[photoId]['nodes']]
                            photoRank[photoId] = recRankCustom(tmp)
                            measurementContainer[photoId] = photoRank[photoId]
                            if node not in rankedtmpnodes:
                                rankedtmpnodes.append(node)
                    plainRanking[node] = sorted(photoRank, key = photoRank.get, reverse = True)
                    maxPlain = max(maxPlain,len(photoRank))
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

                #Save results
                methodName = 'Ranked_Overlappers'
                print('\n'+methodName)
                if decisionforAll == str('y') or decisionforAll == str(3):
                    resultsSaver(methodName,topImages,person,rankedPhotos,measurementContainer,self.photodict,self.dataset_path_results,captiondict,combinationDict)
                else:
                    resultsSaverAll(methodName,topImages,person,rankedPhotos,measurementContainer,self.photodict,self.dataset_path_results,captiondict,combinationDict)

        else:
            print('No common photos of '+person+' with the overlapping crowd occurred')

        '''Rank images by creating measuring value for each photo using reciprocal of ranks of the contained nodes'''
        if decisionforAll == str('y') or decisionforAll == str(3):
            doIt = input('\nRank images by reciprocal of ranks of the contained nodes???(y or n)')
        else:
            doIt = 'y'
        if str(doIt).lower() == 'y' or str(doIt).lower() == 3:
            photoRank = {}
            for photoId in personPool:
                tmp = [usrCentrSorted.index(x) for x in self.photodict[photoId]['nodes']]
                photoRank[photoId] = recRankCustom(tmp)

            plainRanking = sorted(photoRank, key = photoRank.get, reverse = True)#sort photos by RRF value

            #Save results
            methodName = 'ReciprocalRanks'
            print('\n'+methodName)
            if decisionforAll == str('y') or decisionforAll == str(3):
                resultsSaver(methodName,topImages,person,plainRanking,photoRank,self.photodict,self.dataset_path_results,captiondict,combinationDict)
            else:
                resultsSaverAll(methodName,topImages,person,plainRanking,photoRank,self.photodict,self.dataset_path_results,captiondict,combinationDict)


    '''Create baseline solutions'''
    def popularity_coappearence(self, topImages, person, captiondict):

        decisionforAll = self.decisionforAll

        peoplePopularity = pickle.load(open(self.dataset_path_tmp+"peoplePopularity.pck", "rb"))
        sortedPeople = peoplePopularity['sortedPeople']
        peoplePopPerSlot = peoplePopularity['countPeople']

        '''Create persons own pool of images'''
        personPool = self.userdict[person]

        '''Aggregate node frequency (popularity)'''
        photoRankRRF, photoRankSum = {}, {} #use node popularity in person to compute photo overall popularity
        nodePool = []#create photopool for coappearence frequency below
        photoPool = []
        for photo in personPool:
            photoPool.append(photo)
            tmpPop = [sortedPeople.index(x) for x in self.photodict[photo]['nodes']]
            photoRankRRF[photo] = recRankCustom(tmpPop)
            tmpPopSum = [peoplePopPerSlot[x] for x in self.photodict[photo]['nodes']]
            photoRankSum[photo] = sum(tmpPopSum)
            nodePool.append(self.photodict[photo]['nodes'])#create photopool for coappearence frequency below
        if decisionforAll == str('y') or decisionforAll == str(3):
            doIt = input('\nRank images by node popularity (frequency)???(y or n)')
        else:
            doIt = 'y'
        if str(doIt).lower() == 'y' or str(doIt).lower() == 3:
            plainRankingRRF = sorted(photoRankRRF, key = photoRankRRF.get, reverse = True)
            plainRankingSum = sorted(photoRankSum, key = photoRankSum.get, reverse = True)

            #Save results
            methodName = 'basePopularityRRF'
            print('\n'+methodName)
            if decisionforAll == str('y') or decisionforAll == str(3):
                resultsSaver(methodName,topImages,person,plainRankingRRF,photoRankRRF,self.photodict,self.dataset_path_results,captiondict,self.combinationDict)
            else:
                resultsSaverAll(methodName,topImages,person,plainRankingRRF,photoRankRRF,self.photodict,self.dataset_path_results,captiondict,self.combinationDict)

            #Save results
            methodName = 'basePopularitySum'
            print('\n'+methodName)
            if decisionforAll == str('y') or decisionforAll == str(3):
                resultsSaver(methodName,topImages,person,plainRankingSum,photoRankSum,self.photodict,self.dataset_path_results,captiondict,self.combinationDict)
            else:
                resultsSaverAll(methodName,topImages,person,plainRankingSum,photoRankSum,self.photodict,self.dataset_path_results,captiondict,self.combinationDict)


        '''Coappearence frequency'''
        methodName = 'baseCoappearence'
        if decisionforAll == str('y') or decisionforAll == str(3):
            doIt = input('\nRank images by Coappearence frequency???(y or n)')
        else:
            doIt = 'y'
        if str(doIt).lower() == 'y' or str(doIt).lower() == 3:
            print('\n'+methodName)
            photoCoappearence = {} #use node coappearence in person dataset to compute photo overall popularity
            for idx,nodes in enumerate(nodePool):
                for idx2,poolnodes in enumerate(nodePool[idx:]):
                    commonNodes = list(set(nodes) & set(poolnodes))
                    commonNodes.sort()
                    if len(commonNodes) > 1:
                        nodestr = ','.join(commonNodes)
                        if nodestr not in photoCoappearence:
                            photoCoappearence[nodestr] = [photoPool[idx]]
                            if photoPool[idx2+idx] not in photoCoappearence[nodestr]:
                                photoCoappearence[nodestr].append(photoPool[idx2+idx])
                        else:
                            if photoPool[idx2+idx] not in photoCoappearence[nodestr]:
                                photoCoappearence[nodestr].append(photoPool[idx2+idx])
                            if photoPool[idx] not in photoCoappearence[nodestr]:
                                photoCoappearence[nodestr].append(photoPool[idx])
            photoCoappearence = {k: v for k, v in photoCoappearence.items() if len(v)>1}
            plainRanking = sorted(photoCoappearence, key=lambda k: len(photoCoappearence[k])*len(k.split(',')), reverse = True)
            photoRank = []
            maxPlain2 = 0
            for plain in plainRanking:
                photoCoappearence[plain].sort()
                photoRank.append(photoCoappearence[plain])
                maxPlain2 = max(maxPlain2,len(photoCoappearence[plain]))

            if decisionforAll == str('y') or decisionforAll == str(3):
                #save results
                finPhotoPool, measurement, Coapps = {}, {}, {}
                cnt,nodeChckPool = 0,[]
                while len(finPhotoPool) < topImages:
                    for k,coappPhotos in enumerate(photoRank):
                        try:
                            cnt2 = cnt
                            while self.photodict[coappPhotos[cnt2]]['nodes'] in nodeChckPool:
                                cnt2+=1
                            webbrowser.open(self.photodict[coappPhotos[cnt2]]['url'])
                            print('\n'+'\n'.join(plainRanking[k].split(',')))
                            print(str(len(photoCoappearence[plainRanking[k]])*len(plainRanking[k].split(','))))
                            decision = str(input('\nIs the url ok? Press Enter for Yes or 3|n for No?: '))
                            if decision == 'move':
                                nodeChckPool.append(self.photodict[coappPhotos[cnt2]]['nodes'])
                                continue
                            cnt3=cnt2
                            while decision == 'N' or decision == 'n' or decision == str(3):
                                cnt3+=1
                                if self.photodict[coappPhotos[cnt3]]['nodes'] not in nodeChckPool:
                                    webbrowser.open(self.photodict[coappPhotos[cnt3]]['url'])
                                    decision = input('\nIs this duplicate ok?: ')
                                cnt2 = cnt3
                            else:
                                finPhotoPool[coappPhotos[cnt2]] = self.photodict[coappPhotos[cnt2]]['date']
                                nodeChckPool.append(self.photodict[coappPhotos[cnt2]]['nodes'])
                                measurement[coappPhotos[cnt2]] = str(len(photoCoappearence[plainRanking[k]])*len(plainRanking[k].split(',')))
                                Coapps[coappPhotos[cnt2]] = plainRanking[k]
                            if len(finPhotoPool)>=topImages:
                                break
                        except:
                            pass
                            continue
                    cnt+=1
                    if cnt > maxPlain2:
                        break
                finPhotos = sorted(finPhotoPool, key = finPhotoPool.get)
                finfile = codecs.open(self.dataset_path_results+'html/'+person+"/"+methodName+".txt",'w','utf-8')
                for rP in finPhotos:
                        finfile.write(person + '\t' + self.photodict[rP]['url'] + '\t' + datetime.datetime.fromtimestamp(self.photodict[rP]['date']).strftime('%d/%m/%y')
                            + '\t' + str(rP) + '\t' + captiondict[rP]  + '\t'+ ' '.join(Coapps[rP].split(',')) + '\t'+str(measurement[rP]) + '\n')
                finfile.close()
            else:
                finPhotoPool, measurement = {}, {}
                cnt = 0
                finfile = codecs.open(self.dataset_path_results+'analysis/'+methodName+".txt",'a','utf-8')
                while cnt <= maxPlain2:
                    for k,coappPhotos in enumerate(photoRank):
                        try:
                            finPhotoPool[coappPhotos[cnt]] = self.photodict[coappPhotos[cnt]]['date']
                            finfile.write(person + '\t' + self.photodict[coappPhotos[cnt]]['url'] + '\t' + datetime.datetime.fromtimestamp(self.photodict[coappPhotos[cnt]]['date']).strftime('%d/%m/%y')
                                + '\t' + str(coappPhotos[cnt]) + '\t' + captiondict[coappPhotos[cnt]]  + '\t'+ ' '.join(plainRanking[k].split(',')) + '\t'+str(len(photoCoappearence[plainRanking[k]])*len(plainRanking[k].split(','))) + '\n')
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
    return sum(finscore)/len(mylist)


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

def resultsSaver(methodName,topImages,person,mainResults,measurementContainer,photodict,dataset_path_results,captiondict,combinationDict):
    #Save results
    nodeChckPool, finPhotoPool, measurement  = [], {}, {}
    for rP in mainResults:
        # commonInter = [len(list(set(photodict[rP]['nodes']) & set(x)))/len(photodict[rP]['nodes']) for x in nodeChckPool]
        if photodict[rP]['nodes'] in nodeChckPool:
            continue
        else:
            webbrowser.open(photodict[rP]['url'])
            print('\n'+'\n'.join(photodict[rP]['nodes']))
            print(str(measurementContainer[rP]))
            decision = str(input('\nIs the url ok? Press Enter for Yes or 3|n for No?: '))
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
    finfile = codecs.open(dataset_path_results+'html/'+person+"/"+methodName+".txt",'w','utf-8')
    for rP in finPhotos:
        finfile.write(str(person) + '\t' + photodict[rP]['url'] + '\t' + datetime.datetime.fromtimestamp(photodict[rP]['date']).strftime('%d/%m/%y')
            + '\t' + str(rP) + '\t' + captiondict[rP]  + '\t'+ ' '.join(photodict[rP]['nodes']) + '\t'+str(measurement[rP]) + '\n')
    finfile.close()

def resultsSaverAll(methodName,topImages,person,mainResults,measurementContainer,photodict,dataset_path_results,captiondict,combinationDict):
    #Save results
    if not os.path.exists(dataset_path_results+'analysis/'):
        os.makedirs(dataset_path_results+'analysis/')

    finPhotoPool, measurement = {}, {}
    finfile = codecs.open(dataset_path_results+'analysis/'+methodName+".txt",'a','utf-8')
    for rP in mainResults:
        finfile.write(str(person) + '\t' + photodict[rP]['url'] + '\t' + datetime.datetime.fromtimestamp(photodict[rP]['date']).strftime('%d/%m/%y')
            + '\t' + str(rP) + '\t' + captiondict[rP] + '\t' + ' '.join(photodict[rP]['nodes']) + '\t'+str(measurementContainer[rP]) + '\n')
    finfile.close()