#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, glob, threading, requests, os, os.path, urllib
from GoogleScraper import scrape_with_config, GoogleSearchError
from textblob import TextBlob
from textblob.np_extractors import FastNPExtractor
from itertools import islice
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
folderlocation = 'C:\\redox\\pipeline\\current\\*'
pipelinechapters = glob.glob(folderlocation)

# iterate through chapters
for chapter in pipelinechapters:
    # read phrases from text file
    kwfile = chapter + '\\phraselist.txt'
    with open(kwfile, mode='r', encoding='utf-8') as g:
        keywords = set(g.read().splitlines())
    uprint("\n____________________\n\nRead all phrases for {}\n\n".format(chapter.split('\\')[-1]))
    # launch scraping operation for phrase
    for phrase in keywords:
        phrase = phrase.strip()
        # overwrite some of the scraping parameters
        # more in Googlescraper.scraper_config
        config = {
            'keyword': phrase,
            'search_engines': ['yandex'],
            'search_type': 'image',
            'scrape_method': 'selenium',
            'sel_browser' : 'phantomjs',
            'do_caching': True,
            'num_results_per_page' : 3,
            'num_pages_for_keyword' : 1,
            'num_workers' : 1,
            'maximum_workers' : 1}
        
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
                    if not os.path.exists(str(chapter.strip()) +'\\images\\'+ str(phrase.strip())):
                        os.makedirs(str(chapter.strip()) +'\\images\\'+str(phrase.strip()))
                except FileExistsError:
                    pass
                name = url.split('/')[-1]
                name = ''.join([i if (ord(i) < 128 and ord(i) > 31 and ord(i) != 42) else ' ' for i in name])
                with open(os.path.join(self.target, name.split('?',1)[0]), 'wb') as f:
                    try:
                        content = requests.get(url).content
                        f.write(content)
                    except Exception as e:
                        pass
     
        # create 500 threads to get the images
        # each fetch image content from a url
        num_threads = 200
        chapterimages = str(chapter.strip()) +'\\images\\'+str(phrase.strip())
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
        uprint('downloaded {} images for {}'.format(b, phrase))

    # remove all images smaller than required
    print("Downloaded all images for {}\n____________________\n".format(chapter.split('\\')[-1]))
    fileiter = (os.path.join(root, f)
        for root, _, files in os.walk(str(chapter.strip()) +'\\images\\'+str(phrase.strip()))
        for f in files)
    smallfileiter = (f for f in fileiter if os.path.getsize(f) < 300 * 800)
    for small in smallfileiter:
        os.remove(small)
    print("\nRemoved small images from {}\n____________________\n".format(chapter.split('\\')[-1]))
