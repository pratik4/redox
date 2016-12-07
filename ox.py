"""" Function definitions """
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import urllib
import threading
import multiprocessing
import time
import requests
from GoogleScraper import scrape_with_config, GoogleSearchError


def get_immediate_subdirectories(a_dir):
    """ Get only the immediate subfolders """
    return [picname for picname in os.listdir(a_dir)
            if os.path.isdir(
                os.path.join(
                    a_dir, picname))]


drive = "/home/machine"
author = os.path.join(drive, "Downloads")
projectpath = os.path.join(author, "f1")
procpathS = get_immediate_subdirectories(projectpath)



#def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
#    """This is just a print wrapper"""
#    enc = file.encoding
#    if enc == 'UTF-8':
#        print(*objects, sep=sep, end=end, file=file)
#    else:
#        fup = lambda obj: str(obj).encode(
#            enc, errors='replace').decode(enc)
#        print(
#            *map(fup, objects), sep=sep, end=end, file=file)


def chapterscraper(aprocpath):
    """ Reads the contents of a chapter and calls phrase operations"""
    kwfile = os.path.join(
        projectpath, aprocpath, 'phraselist.txt')
    with open(
        kwfile, mode='r', encoding='utf-8') as g:
        chapterphrases = list(set(g.read().splitlines()))
    
    
    uprint("\n\nRead all phrases for {} at {}\n\n".
           format(aprocpath, time.strftime('%X')))
    for phrase in chapterphrases:
        phrase = phrase.strip()
    phraseprocs = [multiprocessing.Process(
        target=phrasescraper(
            phrase, aprocpath))
                   for phrase in chapterphrases]

    
    if __name__ == '__main__':
        for phraseproc in phraseprocs:
            phraseproc.daemon = False
            phraseproc.start()
            print("Running phrase operations")
        for phraseproc in phraseprocs:
            phraseproc.join()
        print('Phrase operations for {} at {}'
               .format(
                   aprocpath.split('\\')[-1], time.strftime('%X')))


def phrasescraper(aphrase, aprocpath):
    """ Gets images for a phrase and writes to the phrase folder """

    
    config = {
        'keyword': aphrase,
        'database_name' : 'redox'+aprocpath,
        'print_results' : 'summarize',
        'log_level' : 'WARN',
        'num_results_per_page' : 1,
        'num_pages_for_keyword' : 1,
        'num_workers' : 30,
        'maximum_workers' : 30}


    try:
        search = scrape_with_config(config)
    except GoogleSearchError as e:
        uprint(e)
        
        
    image_urls = []
    for serp in search.serps:
        image_urls.extend(
            [link.link for link in serp.links])
    
    
    num_threads = 30
    phraseimages = os.path.join(
        projectpath, aprocpath, 'images', aphrase)
    threads = [FetchResource(
        phraseimages, [])
               for i in range(
                   num_threads)]
    
    
    while image_urls:
        for thread in threads:
            if image_urls:
                try:
                    thread.furls.append(
                        image_urls.pop())
                except IndexError:
                    break
    
    
    threads = [thread for thread in threads if thread.furls]
    b = 0
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
        b += 1
    
    
    print('downloaded {} images for {} at {}'
           .format(b, aphrase, time.strftime('%X')))
    fileiter = (os.path.join(
        root, f) for root, _, files in os.walk(
            aprocpath +'\\images\\' + aphrase) for f in files)
    smallfileiter = (f for f in fileiter
                     if os.path.getsize(f) < 300 * 800)
    for small in smallfileiter:
        os.remove(small)
        print("\nRemoved small images from {} at {}"
              .format(aphrase, time.strftime('%X')))


class FetchResource(threading.Thread):
    """ Gets the content of a url """
    def __init__(self, target, furls):
        super().__init__()
        self.target = target
        self.furls = furls
    def run(self):
        if os.path.lexists(self.target.strip()):
            pass
        else:
            os.makedirs(self.target.strip())
        for furl in self.furls:
            furl = urllib.parse.unquote(furl)
            icname = furl.split('/')[-1]
            picname = ''.join([i if (ord(i) > 65)
                               or (ord(i) == 46) else ' ' for i in icname])
            with open(
                os.path.join(
                    self.target, picname), 'wb') as fname:
                content = requests.get(furl).content
                fname.write(content)


def main():
    """ Reads target folder
    and calls chapter operations """
    chapterprocs = [multiprocessing.Process(target=chapterscraper, args=(procpath))
                    for procpath in procpathS]
    if __name__ == '__main__':
        for chapterproc in chapterprocs:
            chapterproc.start()
        for chapterproc in chapterprocs:
            chapterproc.join()
    print("Finished processing everything")


if __name__ == '__main__':
    main()
