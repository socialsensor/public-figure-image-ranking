#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:
# Purpose:       This .py file creates htmls containing all the extracted images illustrated scenario by scenario and instance to instance
#
# Required libs: webbrowser,glob,os,shutil
# Author:        konkonst
#
# Created:       30/03/2014
# Copyright:     (c) ITI (CERTH) 2014
# Licence:       <apache licence 2.0>
#-------------------------------------------------------------------------------
import webbrowser,glob,os,shutil, pickle
listofdirs = os.listdir("./data/")
filename = [x for x in listofdirs if x.startswith('GETTY')]
for idx,files in enumerate(filename):
    print(str(idx+1) + '.' + files)
selection = int(input('Select a dataset from the above: '))-1
requestedPhotos = int(input('How many photos do you want to see?: '))
dataset_path = './data/'+filename[selection]+'/'
eventPopFlag, peoplePopFlag = False, False
text_files = [name for name in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, name))]
for scenario in text_files:
    print(scenario)
    if os.path.exists(dataset_path+scenario+'_JS.html'):
        os.remove(dataset_path+scenario+'_JS.html')
    f = open(dataset_path+scenario+'_JS.html','w')
    message = '<html>\n<head>Image Ranking based on graph structure analysis<br>'
    meth_path = dataset_path+scenario+'/results/'
    meth_path_tmp = dataset_path+scenario+'/tmp/'
    #Write scenario's header
    message += '<hr><body><p>The scenario studied here is: '+scenario+'</p></body><hr />'
    message += '<script src="http://ajax.googleapis.com/ajax/libs/jquery/2.0.2/jquery.min.js"></script>'
    message += '<title>'+scenario+'</title>'
    message += '<style id="jsbin-css">.collapse{font-size: 20px;display:block;}.collapse + input{display:none;}.collapse + input + *{display:none;}.collapse+ input:checked + *{display:block;}</style></head>'
    if scenario.startswith('static'):
        if os.path.exists(meth_path+'crowdSource/'):
            shutil.rmtree(meth_path+'crowdSource/')
            os.makedirs(meth_path+'crowdSource/')
        else:
            os.makedirs(meth_path+'crowdSource/')
        meth_path2 = meth_path+'html_New/'
        if 'PersonCentered' in scenario or 'EventCentered' in scenario:
            result_folders = [name for name in os.listdir(meth_path2) if os.path.isdir(os.path.join(meth_path2, name))]
            for folder in result_folders:
                folder_path = meth_path2+folder+'/'
                try:
                    int(folder)
                    if not eventPopFlag:
                        eventPopFlag = True
                        eventPopFile = open(meth_path+'rankedEvents.txt','r').readlines()
                        eventPopularity = {}
                        for line in eventPopFile:
                            newline = line.strip().split('\t')
                            eventPopularity[newline[0]] = newline[1]
                    intro = '<p>The event chosen has ' + str(eventPopularity[folder])+' images and its ID is: '
                    eventFlag = True
                except:
                    if not peoplePopFlag:
                        peoplePopularity = pickle.load(open(meth_path_tmp+"peoplePopularity.pck", "rb"))
                        peoplePopPerSlot = peoplePopularity['countPeople']
                        peoplePopFlag = True
                    intro = '<p>The queried person appears in ' + str(peoplePopPerSlot[folder])+' images and his/er name is: '
                    eventFlag = False
                    pass
                message += '<body>'+intro+folder+'</p>'
                if eventFlag:
                    message += '<br>'.join([x.split('\t')[4] for x in (open(folder_path+'ReciprocalRanks.txt')).readlines()[:5]]) #print 5 event captions
                # message += ''
                # message += '.\t'.join([x.strip() for x in (open(folder_path+'basicStats.txt'))]) #write instance's basic stats
                # message += ''
                urlfiles = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
                for k, urlf in enumerate(urlfiles):
                    theFile =  open(meth_path+'crowdSource/'+urlf,'a')
                    message += '<label class="collapse" for="_'+folder+urlf[:-4]+'">'+urlf[:-4]+'</label><input id="_'+folder+urlf[:-4]+'" type="checkbox"><div>'
                    fileList = list(open(folder_path + urlf,'r'))
                    urlList = [x.split('\t') for x in fileList]
                    message += '<table>'
                    message += '<tr>'
                    for line in urlList[:requestedPhotos]:
                        theFile.write('\t'.join(line))
                        message += '<td>'+line[2]+'</td>'
                    theFile.close()
                    message += '</tr>'
                    message += '<tr>'
                    for line in urlList[:requestedPhotos]:
                        message += '<td><a href="'+line[1]+'"><img src="'+line[1]+'" width="175"/></a></td>'
                    message += '</tr>'
                    message += '<tr>'
                    for line in urlList[:requestedPhotos]:
                        message += '<td>'+'<br>'.join(line[5].split(' '))+'</td>'
                    message += '</tr>'
                    message += '</table></div>'

        else:
            urlfiles = [f for f in os.listdir(meth_path2) if f.endswith('.txt')]
            for  k, urlf in enumerate(urlfiles):
                theFile =  open(meth_path+'crowdSource/'+urlf,'a')
                message += '<label class="collapse" for="_'+folder+urlf[:-4]+'">'+urlf[:-4]+'</label><input id="_'+folder+urlf[:-4]+'" type="checkbox"><div>'
                fileList = list(open(meth_path2 + urlf,'r'))
                urlList = [x.split('\t') for x in fileList]
                message += '<table>'
                message += '<tr>'
                for line in urlList[:requestedPhotos]:
                    theFile.write('	'.join(line))
                    message += '<td>'+line[2]+'</td>'
                theFile.close()
                message += '</tr>'
                message += '<tr>'
                for line in urlList[:requestedPhotos]:
                    message += '<td><a href="'+line[1]+'"><img src="'+line[1]+'" width="175"/></a></td>'
                message += '</tr>'
                message += '<tr>'
                for line in urlList[:requestedPhotos]:
                    message += '<td>'+'<br>'.join(line[5].split(' '))+'</td>'
                message += '</tr>'
                message += '</table></div>'
    else:
        granularity_folders = [name for name in os.listdir(meth_path) if os.path.isdir(os.path.join(meth_path, name))]
        for granul in granularity_folders:
            message += '<hr />Granularity used is: '+granul[3:]+''
            granul_path = meth_path+granul+'/html_New/'
            if os.path.exists(meth_path+granul+'/crowdSource/'):
                shutil.rmtree(meth_path+granul+'/crowdSource/')
                os.makedirs(meth_path+granul+'/crowdSource/')
            else:
                os.makedirs(meth_path+granul+'/crowdSource/')
            if 'PersonCentered' in scenario:
                result_folders = [f for f in os.listdir(granul_path) if not f.endswith('.txt')]
                for folder in result_folders:
                    folder_path = granul_path+folder+'/'
                    intro = 'The queried person is: '
                    message += '<hr />'+intro+folder+''
                    # message += ''
                    # message += '.\t'.join([x.strip() for x in (open(folder_path+'basicStats.txt'))]) #write instance's basic stats
                    # message += ''
                    urlfiles = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
                    for  k, urlf in enumerate(urlfiles):
                        theFile =  open(meth_path+granul+'/crowdSource/'+urlf,'a')                        
                        message += '<label class="collapse" for="_'+folder+urlf[:-4]+granul+'">'+urlf[:-4]+'</label><input id="_'+folder+urlf[:-4]+granul+'" type="checkbox"><div>'
                        fileList = list(open(folder_path + urlf,'r'))
                        urlList = [x.split('\t') for x in fileList]
                        message += '<table>'
                        message += '<tr>'
                        for line in urlList[:requestedPhotos]:
                            theFile.write('	'.join(line))
                            message += '<td>'+line[2]+'</td>'
                        theFile.close()
                        message += '</tr>'
                        message += '<tr>'
                        for line in urlList[:requestedPhotos]:
                            message += '<td><a href="'+line[1]+'"><img src="'+line[1]+'" width="175"/></a></td>'
                        message += '</tr>'
                        message += '<tr>'
                        for line in urlList[:requestedPhotos]:
                            message += '<td>'+'<br>'.join(line[5].split(' '))+'</td>'
                        message += '</tr>'
                        message += '</table></div>'
            else:
                # message += ''+'.\t'.join([x.strip() for x in (open(granul_path+'Demon_'+granul+'_stats.txt'))]) #write instance's basic stats
                # message += ''
                urlfiles = [f for f in os.listdir(granul_path) if f.endswith('.txt')]
                for k, urlf in enumerate(urlfiles):
                    theFile =  open(meth_path+granul+'/crowdSource/'+urlf,'a')
                    message += '<label class="collapse" for="_'+folder+urlf[:-4]+granul+'">'+urlf[:-4]+'</label><input id="_'+folder+urlf[:-4]+granul+'" type="checkbox"><div>'
                    fileList = list(open(granul_path + urlf,'r'))
                    urlList = [x.split('\t') for x in fileList]
                    message += '<table>'
                    message += '<tr>'
                    for line in urlList[:requestedPhotos]:
                        theFile.write('	'.join(line))
                        message += '<td>'+line[2]+'</td>'
                    theFile.close()
                    message += '</tr>'
                    message += '<tr>'
                    for line in urlList[:requestedPhotos]:
                        message += '<td><a href="'+line[1]+'"><img src="'+line[1]+'" width="175"/></a></td>'
                    message += '</tr>'
                    message += '<tr>'
                    for line in urlList[:requestedPhotos]:
                        message += '<td>'+'<br>'.join(line[5].split(' '))+'</td>'
                    message += '</tr>'
                    message += '</table></div>'
                message += '<hr />'
    message += '</html>'

    f.write(message)
    f.close()

##webbrowser.open_new_tab('./data/gettyEvolution.html')
