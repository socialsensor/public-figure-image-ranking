# -*- coding: utf-8 -*-
import glob, codecs, os, time, dateutil.parser, collections, pickle
print('personpopularity')
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

dataset_path_results = "./data/GETTY_"+filename[selection][24:-4]+"/staticPersonCentered_"+commDetectMethod+"/results/"
dataset_path_tmp = "./data/GETTY_"+filename[selection][24:-4]+"/staticPersonCentered_"+commDetectMethod+"/tmp/"

dataset_path_resultsDyn = "./data/GETTY_"+filename[selection][24:-4]+"/dynamicPersonCentered_"+commDetectMethod+"/results/"
dataset_path_tmpDyn = "./data/GETTY_"+filename[selection][24:-4]+"/dynamicPersonCentered_"+commDetectMethod+"/tmp/"

if not os.path.exists(dataset_path_results):
    os.makedirs(dataset_path_results)
    os.makedirs(dataset_path_tmp)

if not os.path.exists(dataset_path_resultsDyn):
    os.makedirs(dataset_path_resultsDyn)
    os.makedirs(dataset_path_tmpDyn)

#Nodes that will be removed
# stopNodes = ['entertainment_group','public_image_ltd','ricardo_tormo','name_of_person','sugarland','the_black_eyed_peas','ed_sullivan',' '] #,'graydon_carter'
stopNodes = open('./data/txt/stopNodes.txt').readlines()
stopNodes = [x.strip().lower() for x in stopNodes]
stopNodes = [x.replace(' - ','_').replace(' ','_') for x in stopNodes if x]

timeLimit = 1071561600#1071561600:1355702400

'''Parse the txt files into authors/mentions/alltime lists'''
emptyvalues = 0
print(filename[selection])
personContainer, totPics = [], 0
with codecs.open(filename[selection], "r", 'utf-8') as f:
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
        # except:
        #     pass
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
personfile2 = codecs.open(dataset_path_resultsDyn+"rankedPeople.txt",'w','utf-8')
for key in sortedPeople:
        personfile1.write(key+'\t'+str(countPeople[key])+'\n')
        personfile2.write(key+'\t'+str(countPeople[key])+'\n')
personfile1.close()
personfile2.close()

elapsed = time.time() - t
print('Time elapsed: %.2f seconds' % elapsed)
