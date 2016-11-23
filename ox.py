#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, glob, threading, requests, os, urllib, re
from GoogleScraper import scrape_with_config, GoogleSearchError
from itertools import islice
from path import path
from more_itertools import unique_everseen
from PIL import Image

# custom print wrapper to handle encoding issues
def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='replace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file)

# read chapter folders containing plaintext phraselist        
folderlocation = path('C:\\redox\\pipeline\\current\\*')
kwfilelocation = path('C:\\redox\\pipeline\\current\\*\\phraselist.txt')
pipelinechapters = glob.glob(folderlocation)
kwfilelist = glob.glob(kwfilelocation)

# iterate through chapters
for chapter, kwfile in zip(pipelinechapters, kwfilelist):
    # read phrases from text file
    with open(kwfile, mode='r', encoding='utf-8') as g:
        keywords = g.read().splitlines()
    
    # launch scraping operation for phrase
    for phrase in keywords:
        
        # overwrite soem of the scraping parameters
        # more in Googlescraper.scraper_config
        config = {
            'keyword': phrase, # :D hehe have fun my dear friends
            'search_engines': ['yandex', 'yahoo'], # duckduckgo not supported
            'search_type': 'image',
            'scrape_method': 'selenium',
            'sel_browser' : 'Chrome',
            'do_caching': True}
        
        # pass config to scraper
        try:
            search = scrape_with_config(config)
        except GoogleSearchError as e:
            uprint(e)
        
        # initialize list of urls
        # get urls from search engine result page links
        image_urls = []
        for serp in search.serps:
            image_urls.extend(
                [link.link for link in serp.links]
            )        
        
        # use urllib to get image content from url
        # write image to file
        class FetchResource(threading.Thread):
            def __init__(self, target, urls):
                super().__init__()
                self.target = chapterimages
                self.urls = urls
                self.phrase = phrase
            def run(self):
                for url in self.urls:
                    url = urllib.parse.unquote(url)
                try:
                    if not os.path.exists(str(chapter.strip()) +'\\images\\'+phrase.strip()):
                        os.makedirs(str(chapter.strip()) +'\\images\\'+phrase.strip())
                except FileExistsError:
                    pass
                name = url.split('/')[-1]
                with open(os.path.join(self.target, name.split('?',1)[0]), 'wb') as f:
                    try:
                        content = requests.get(url).content
                        f.write(content)
                    except Exception as e:
                        pass
     
        # create 500 threads to get the images
        # each fetch image content from a url
        num_threads = 500
        chapterimages = str(chapter + '\\images\\' + phrase + '\\')
        threads = [FetchResource(chapterimages, []) for k in range(num_threads)]
        while image_urls:
            for t in threads:
                try:
                    t.urls.append(image_urls.pop())
                except IndexError as e:
                    break
        threads = [t for t in threads if t.urls]
        b = 0
        for t in threads:
            t.start()
        for t in threads:
            t.join()
            b += 1
        uprint('[+] downloaded {} images for {}\n...\n'.format(b, phrase))

    # remove all images smaller than required
    for phrase in keywords:
        chapterimages = str(chapter + '\\images\\' + phrase + '\\')
        for filename in os.listdir(chapterimages):
            filepath = os.path.join(chapterimages, filename)
            with Image.open(filepath) as im:
                x, y = im.size
            totalsize = x*y
            if totalsize < 240000:
                os.remove(filepath)
        uprint("small images removed for {}".format(phrase))
