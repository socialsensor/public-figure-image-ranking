# -*- coding: utf-8 -*-
import glob, codecs, os, time, dateutil.parser, collections, pickle
import matplotlib.pyplot as plt
print('eventpopularity.py')
print(time.asctime( time.localtime(time.time()) ))
t = time.time()
    #Get filenames from txt dataset path
filename = glob.glob("./data/txt/*.txt")
filename = [x for x in filename if x[11:].startswith('noDups')]
for idx,files in enumerate(filename):
    print(str(idx+1) + '.' + files[11:-4])
selection = int(input('Select a dataset from the above: '))-1

#Community detection method. 'Ahn','Demon' and 'Copra' for overlapping and 'Louvain' for non.
commDetectMethod = 'Demon'

dataset_path_results = "./data/GETTY_"+filename[selection][24:-4]+"/staticEventCentered_"+commDetectMethod+"/results/"
dataset_path_tmp = "./data/GETTY_"+filename[selection][24:-4]+"/staticEventCentered_"+commDetectMethod+"/tmp/"

if not os.path.exists(dataset_path_results):
    os.makedirs(dataset_path_results)
    os.makedirs(dataset_path_tmp)

stopNodes = open('./data/txt/stopNodes.txt').readlines()
stopNodes = [x.strip().lower() for x in stopNodes]
stopNodes = [x.replace(' - ','_').replace(' ','_') for x in stopNodes if x]

timeLimit = 1071561600#1071561600:1355702400

alltime = []
totPics,totPeople = 0,0
emptyvalues = 0
print(filename[selection])
eventContainer = []
with codecs.open(filename[selection], "r", 'utf-8') as f:
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
        # except:
        #     pass

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
