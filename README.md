public-figure-image-ranking
===========================

###A framework for analyzing the community structure and interaction in graphs that emerge from co-appearances of tagged entities in image datasets.###
We use this framework to rank the images in a set of static and dynamic scenarios that can be used in a person or an event-centered query. We apply it on a well known image dataset and show that it can serve as a means of providing editorial boards with suggestions of interesting photos depending on their needs.  
The methods employed in the framework require a dataset that contains valid timestamps and metadata concerning the entities that appear in the images. Using the co-appearances of these entities as they appear in the images, we measure their importance, identify the communities to which they belong as well as discover any nodes that exist in the union of overlapping communities.

##Distribution Information##
This distribution contains the following:  
* a readme.txt file with instructions on how to use the different parts of the framework;
* a set of Python scripts (in the /python folder) used to conduct image ranking using the co-appearances between people that are tagged in the images.

##Structure and interaction analysis using Python##

Any new data (txt files) to be analysed should be placed in the _../data/txt/_ folder.
In order for the python files to work, the data should be consistent for all the methods and in the following form:  
<code>_date \TAB eventId \TAB imageURL \TAB peopleTags(comma separated) \TAB caption \newline_</code>   
(In the case where an entry is not available, insert a single space for structure purposes. In the case where only one person is tagged in the image, that image will be skipped. In the case where the images are not stored on the web, substituting the _imageURL_ entry with the _imageDirectory_ entry will also work. There is also an option to include a stopNodes.txt in the _./data/txt_ directory which may contain unwanted nodes.)

###Code###
The python code consists of 13 files containing friendly user scripts for performing Image Ranking using community structure and interaction Analysis.
The framework was implemented using Python 3.3 and the 3rd party libraries required for the framework to work are _dateutil_ (requires _pyparsing_), _numpy_, _matplotlib_, _urllib.request_, _webbrowser_, _shutil_ and _networkx_ (http://www.lfd.uci.edu/~gohlke/pythonlibs/). Additional libraries may be required depending on the release.  
Utilization of the framework requires an initial editing of the desired main file via any text editor. There are a number of parameters (all of which are fully documented) that can be tweaked as required by the users' (e.g. the user has a choice between the Demon, Ahn and COPRA community detection algorithms) or the dataset's needs (e.g. there is practically no use in employing the mainDynamicPersonTask if the dataset to be used has a time range of less than a year since the default sampling times in the script (applicable to our dataset) are a year and month long). The script can then be executed in a straightforward fashion which will present the user with a choice; either to extract all the results for every event/person in the dataset or to provide a set of events/persons and approve of every individual image.   

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
The results are indexed in separate folders in a dataset/scenario/method order. Depending on the user's choice of extracting the results they are either stored in the ./results/analysis folder for every event/person in the dataset or in the ./results/html folder provided the user has included a set of events/persons. The createImageHTML.py file can be used to create html files in order to view the results.   
Additional option: In each of the class files there is a commented section that creates .txt files which can be used as input in the Gephi software in order to visualize the graphs and extract additional information.