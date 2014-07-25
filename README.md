public-figure-image-ranking
===========================

###A framework for analyzing the community structure and interaction in graphs that emerge from coappearances of tagged entities in image datasets. We use this framework to rank the images in a set of static and dynamic scenarios that can be used in a timeline, person or an event-centered query.
We apply it on a well known image dataset and show that it can serve as a means of providing editorial boards with suggestions of interesting photos depending on their needs.
The methods employed in the framework require a dataset that contains valid timestamps and metadata concerning the entities that appear in the images. Using the coappearances of these entities as they appear in the images, we measure their importance, identify the communities to which they belong
as well as discover any nodes that exist in the union of overlapping communities.

##Distribution Information##
This distribution contains the following:  
* a readme.txt file with instructions on how to use the different parts of the framework;
* a set of Python scripts (in the /python folder) used to conduct image ranking using the coappearances between people that are tagged in the images.

##Structure and interaction analysis using Python##

Any new data (txt files) to be analysed should be placed in the _../data/txt/_ folder.
In order for the python files to work, the data should be consistent for all the methods and in the following form:
date \TAB eventId \TAB imageURL \TAB peopleTags(comma separated) \TAB caption \newline
(In the case where an entry is not available, insert a single space for structure purposes. In the case where only one person is tagged in the image, that image will be skipped. There is also an option to include a stopNodes.txt in the _./data/txt_ directory which may contain unwanted nodes.)

###Code###
The python code consists of 13 files containing friendly user scripts for performing Image Ranking using community structure and interaction Analysis.
The framework was implemented using Python 3.3 and the 3rd party libraries required for the framework to work are _dateutil_ (requires _pyparsing_), _numpy_, _matplotlib_, _urllib.request_, _webbrowser_, _shutil_ and _networkx_ (http://www.lfd.uci.edu/~gohlke/pythonlibs/). 

The python folder contains 13 files:
* <code>mainStaticPersonTask.py</code>  
    This .py file is the main Framework file. It ranks images of a specific person of interest in a static manner.
* <code>mainStaticEventTask.py</code>  
    This .py file is the main Framework file. It ranks images in specific events in a static manner.
* <code>mainDynamicPersonTask.py</code>  
    This .py file is the main Framework file. It ranks images of a specific person of interest in a dynamic manner.
* <code>staticCommPersonTask.py</code>  
    This .py file is the class file that ranks images of a specific person of interest in a static manner.
* <code>staticCommEventTask.py</code>  
    This .py file is the class file that ranks images in specific events.
* <code>dynamicCommPersonTask.py</code>  
    This .py file is the class file that ranks images of a specific person of interest in a dynamic manner.
* <code>community.py</code>  
    This is a copy of Aynaud's implementation of the Louvain community detection algorithm.
* <code>Demon.py</code>  
    This is a copy of M. Coscia's implementation of the Demon community detection algorithm.
* <code>copra.jar</code>  
    This is a copy of the COPRA community detection algorithm.
* <code>link_clustering_din.py</code>  
    This is a copy of J. Bagrow's implementation of the Ahn community detection algorithm.
* <code>eventPopularity.py</code>  
    This .py file extracts popularity of events (frequency of images in events)
* <code>personPopularity.py</code>  
    This .py file extracts popularity of people (frequency of appearance)
* <code>createImageHTML.py</code>  
    This .py file creates htmls containing all the extracted images illustrated method by method and instance to instance


###Python Results###
The results are indexed in separate folders in a dataset/scenario/method order. The user has two choices, either to extract all the results for every event and every person in the ./results/analysis folder or to provide a set of events/persons and approve of every image one by one. In the latter case the results are stored in the ./results/html folder and the createImageHTML.py file can be used to create html files in order to view the results.