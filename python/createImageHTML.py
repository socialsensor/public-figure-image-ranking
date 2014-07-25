#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:
# Purpose:       This .py file creates htmls containing all the extracted images illustrated method by method and instance to instance
#
# Required libs: webbrowser,glob,os,shutil
# Author:        konkonst
#
# Created:       30/03/2014
# Copyright:     (c) ITI (CERTH) 2014
# Licence:       <apache licence 2.0>
#-------------------------------------------------------------------------------
import webbrowser,glob,os,shutil
listofdirs = os.listdir("./data/")
filename = [x for x in listofdirs]
for idx,files in enumerate(filename):
    print(str(idx+1) + '.' + files)
selection = int(input('Select a dataset from the above: '))-1
requestedPhotos = int(input('How many photos do you want to see?: '))
dataset_path = './data/'+filename[selection]+'/'
text_files = [name for name in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, name))]
for method in text_files:
    print(method)
    if os.path.exists(dataset_path+method+'.html'):
        os.remove(dataset_path+method+'.html')
    f = open(dataset_path+method+'.html','w')
    message = '<html>\n<head>Image Ranking based on graph structure analysis</head>'
    meth_path = dataset_path+method+'/results/'
    #Write method's header
    message += '<hr style="color: red;"/><body><p>The method used here is: '+method+'</p></body>'
    # message += '<body><p>'
    # message += '.\t'.join([x.strip() for x in (open(meth_path+'basicStats.txt'))]) #write method's basic stats
    # message += '</p></body>'
    if method.startswith('static'):
        if os.path.exists(meth_path+'crowdSource/'):
            shutil.rmtree(meth_path+'crowdSource/')
            os.makedirs(meth_path+'crowdSource/')
        else:
            os.makedirs(meth_path+'crowdSource/')
        meth_path2 = meth_path+'html/'
        if 'PersonCentered' in method or 'EventCentered' in method:
            result_folders = [name for name in os.listdir(meth_path2) if os.path.isdir(os.path.join(meth_path2, name))]
            for folder in result_folders:
                folder_path = meth_path2+folder+'/'
                try:
                    int(folder)
                    intro = 'The event chosen is: '
                    eventFlag = True
                except:
                    intro = 'The person of interest is: '
                    eventFlag = False
                    pass
                message += '<hr /><body><p>'+intro+folder+'</p></body>'
                if eventFlag:
                    message += '<br>'.join([x.split('\t')[4] for x in (open(folder_path+'ReciprocalRanks.txt')).readlines()[:5]]) #print 5 event captions
                # message += '<body><p>'
                # message += '.\t'.join([x.strip() for x in (open(folder_path+'basicStats.txt'))]) #write instance's basic stats
                # message += '</p></body>'
                urlfiles = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
                for k, urlf in enumerate(urlfiles):                    
                    theFile =  open(meth_path+'crowdSource/'+urlf,'a')
                    message += '<body><p>'+urlf[:-4]+'</p></body>'
                    fileList = list(open(folder_path + urlf,'r'))
                    urlList = [x.split('\t') for x in fileList]
                    message += '<table>'
                    message += '<tr>'
                    for line in urlList[:requestedPhotos]:
                        theFile.write('\t'.join(line))
                        message += '<td><body><p>'+line[2]+'</p></body></td>'
                    theFile.close()
                    message += '</tr>'
                    message += '<tr>'
                    for line in urlList[:requestedPhotos]:
                        message += '<td><a href="'+line[1]+'"><img src="'+line[1]+'" width="175"/></a></td>'
                    message += '</tr>'
                    message += '<tr>'
                    for line in urlList[:requestedPhotos]:
                        message += '<td><body><p>'+'<br>'.join(line[5].split(' '))+'</p></body></td>'
                    message += '</tr>'
                    message += '</table>'

        else:
            urlfiles = [f for f in os.listdir(meth_path2) if f.endswith('.txt')]
            for  k, urlf in enumerate(urlfiles):
                theFile =  open(meth_path+'crowdSource/'+urlf,'a')
                message += '<body><p>'+urlf[:-4]+'</p></body>'
                fileList = list(open(meth_path2 + urlf,'r'))
                urlList = [x.split('\t') for x in fileList]
                message += '<table>'
                message += '<tr>'
                for line in urlList[:requestedPhotos]:
                    theFile.write('	'.join(line))
                    message += '<td><body><p>'+line[2]+'</p></body></td>'
                theFile.close()
                message += '</tr>'
                message += '<tr>'
                for line in urlList[:requestedPhotos]:
                    message += '<td><a href="'+line[1]+'"><img src="'+line[1]+'" width="175"/></a></td>'
                message += '</tr>'
                message += '<tr>'
                for line in urlList[:requestedPhotos]:
                    message += '<td><body><p>'+'<br>'.join(line[5].split(' '))+'</p></body></td>'
                message += '</tr>'
                message += '</table>'
    else:
        granularity_folders = [name for name in os.listdir(meth_path) if os.path.isdir(os.path.join(meth_path, name))]
        for granul in granularity_folders:
            message += '<hr /><body><p>Granularity used is: '+granul[3:]+'</p></body>'
            granul_path = meth_path+granul+'/html/'
            if os.path.exists(meth_path+granul+'/crowdSource/'):
                shutil.rmtree(meth_path+granul+'/crowdSource/')
                os.makedirs(meth_path+granul+'/crowdSource/')
            else:
                os.makedirs(meth_path+granul+'/crowdSource/')
            if 'PersonCentered' in method:
                result_folders = [f for f in os.listdir(granul_path) if not f.endswith('.txt')]
                for folder in result_folders:
                    folder_path = granul_path+folder+'/'
                    intro = 'The person of interest is: '
                    message += '<hr /><body><p>'+intro+folder+'</p></body>'
                    # message += '<body><p>'
                    # message += '.\t'.join([x.strip() for x in (open(folder_path+'basicStats.txt'))]) #write instance's basic stats
                    # message += '</p></body>'
                    urlfiles = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
                    for  k, urlf in enumerate(urlfiles):
                        theFile =  open(meth_path+granul+'/crowdSource/'+urlf,'a')
                        message += '<body><p>'+urlf[:-4]+'</p></body>'
                        fileList = list(open(folder_path + urlf,'r'))
                        urlList = [x.split('\t') for x in fileList]
                        message += '<table>'
                        message += '<tr>'
                        for line in urlList[:requestedPhotos]:
                            theFile.write('	'.join(line))
                            message += '<td><body><p>'+line[2]+'</p></body></td>'
                        theFile.close()
                        message += '</tr>'
                        message += '<tr>'
                        for line in urlList[:requestedPhotos]:
                            message += '<td><a href="'+line[1]+'"><img src="'+line[1]+'" width="175"/></a></td>'
                        message += '</tr>'
                        message += '<tr>'
                        for line in urlList[:requestedPhotos]:
                            message += '<td><body><p>'+'<br>'.join(line[5].split(' '))+'</p></body></td>'
                        message += '</tr>'
                        message += '</table>'
            else:
                # message += '<body><p>'+'.\t'.join([x.strip() for x in (open(granul_path+'Demon_'+granul+'_stats.txt'))]) #write instance's basic stats
                # message += '</p></body>'
                urlfiles = [f for f in os.listdir(granul_path) if f.endswith('.txt')]
                for k, urlf in enumerate(urlfiles):
                    theFile =  open(meth_path+granul+'/crowdSource/'+urlf,'a')
                    message += '<body><p>'+urlf[:-4]+'</p></body>'
                    fileList = list(open(granul_path + urlf,'r'))
                    urlList = [x.split('\t') for x in fileList]
                    message += '<table>'
                    message += '<tr>'
                    for line in urlList[:requestedPhotos]:
                        theFile.write('	'.join(line))
                        message += '<td><body><p>'+line[2]+'</p></body></td>'
                    theFile.close()
                    message += '</tr>'
                    message += '<tr>'
                    for line in urlList[:requestedPhotos]:
                        message += '<td><a href="'+line[1]+'"><img src="'+line[1]+'" width="175"/></a></td>'
                    message += '</tr>'
                    message += '<tr>'
                    for line in urlList[:requestedPhotos]:
                        message += '<td><body><p>'+'<br>'.join(line[5].split(' '))+'</p></body></td>'
                    message += '</tr>'
                    message += '</table>'
                message += '<hr />'
    message += '</html>'

    f.write(message)
    f.close()

