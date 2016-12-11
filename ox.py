""" Function definitions """
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from selenium import webdriver
import sys, os, time, concurrent.futures, threading, urllib, requests
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from GoogleScraper import scrape_with_config, GoogleSearchError

projectpath ="C:\\Users\\pratik\\Google Drive\\scrape"

def get_immediate_subdirectories(a_dir):
    """ Get only the immediate subfolders """
    return [chapter for chapter in os.listdir(a_dir) if os.path.isdir( os.path.join(a_dir, chapter))]

procpaths = get_immediate_subdirectories(projectpath)
def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    """This is just a print wrapper"""
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        fup = lambda obj: str(obj).encode(enc, errors='replace').decode(enc)
        print(*map(fup, objects), sep=sep, end=end, file=file)


class FetchResource(threading.Thread):
    """ Gets the content of a url """
   
    def __init__(self, target, furls):
        super().__init__()
        self.target = target.strip()
        self.furls = furls
   
    def run(self):
        try:
            os.makedirs(self.target.strip())
        except FileExistsError:
            pass
        for furl in list(self.furls):
            furl = urllib.parse.unquote(furl)
            picname = ''.join([i if (ord(i) > 65) or (ord(i) == 46) else '' for i in furl.split('/')[-1]])
            with open(os.path.join(self.target, picname), 'wb') as picfilename:
                content = requests.get(furl).content
                picfilename.write(content)


def phrasescraper(aphrase, aprocpath):
    """ Gets images for a phrase and writes to the phrase folder """
    uprint("Beginning scrape for {}".format(aphrase))
    config = {'keyword': aphrase, 'database_name' : 'redox'+aprocpath+aphrase}
    try:
        search = scrape_with_config(config)
    except GoogleSearchError as e:
        uprint(e)
    image_urls = []
    
    for serp in search.serps:
        image_urls.extend([link.link for link in serp.links])
    num_threads = 35
    phraseimages = os.path.join(projectpath, aprocpath, 'images', aphrase)
    threads = [FetchResource(phraseimages, []) for i in range(num_threads)]
    while image_urls:
        for thread in threads:
            if image_urls:
                try:
                    thread.furls.append(image_urls.pop())
                except IndexError:
                    break
    
    threads = [thread for thread in threads if thread.furls]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    uprint('finished phrase operations for {} at {}'.format(aphrase, time.strftime('%X')))
    
    fileiter = (os.path.join(root, f) for root, _, files in os.walk(aprocpath +'\\images\\' + aphrase) for f in files)
    smallfileiter = (f for f in fileiter if os.path.getsize(f) < 300 * 800)
    
    for small in smallfileiter:
        os.remove(small)
        uprint("\nRemoved small images from {} at {}".format(aphrase, time.strftime('%X')))

def chapterscraper(aprocpath):
    """ Reads the contents of a chapter and calls phrase operations"""
    
    kwfile = os.path.join(projectpath, aprocpath, 'phraselist.txt')    
    with open(kwfile, mode='r', encoding='utf-8') as g:
        chapterphrases = list(set(g.read().splitlines()))
    uprint("Running chapter operations for {} at {}"
           .format(aprocpath.split('\\')[-1], time.strftime('%X')))
    
    with ThreadPoolExecutor(max_workers=5) as phraseexecutor:
        # Start the load operations and mark each future with its chapter
        partial_phrasescraper = partial(phrasescraper, aprocpath=aprocpath)
        future_to_phrase = {phraseexecutor.submit(partial_phrasescraper, phrase): phrase for phrase in chapterphrases}
        for phrasefuture in concurrent.futures.as_completed(future_to_phrase):
            phrasefuture.result()

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=3) as chapterexecutor:
        # Start the load operations and mark each future with its chapter
        future_to_chapter = {chapterexecutor.submit(chapterscraper, procpath): procpath for procpath in procpaths}
        for chapterfuture in concurrent.futures.as_completed(future_to_chapter):
            chapterfuture.result()
