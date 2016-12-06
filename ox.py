"""" Function definitions """
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import urllib
import threading
import multiprocessing
import requests
from GoogleScraper import scrape_with_config, GoogleSearchError


projectpath = "C:\\Users\\nnikh\\Google Drive\\nikhilatphyzok\\automation\\scraping"
procpathS = get_immediate_subdirectories(projectpath)


def get_immediate_subdirectories(a_dir):
    """ Get only the immediate subfolders """
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(
                os.path.join(
                    a_dir, name))]


def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    """This is just a print wrapper"""
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        fup = lambda obj: str(obj).encode(enc, errors='replace').decode(enc)
        print(*map(fup, objects), sep=sep, end=end, file=file)


def chapterscraper(aprocpath):
    """ Reads the contents of a chapter and calls phrase operations"""

    kwfile = os.path.join(projectpath, aprocpath, 'phraselist.txt')
    with open(kwfile, mode='r', encoding='utf-8') as g:
        chapterphrases = list(
            set(g.read().splitlines()))


    uprint("\n____________________\n\nRead all phrases for {}\n\n".format(aprocpath))
    for phrase in chapterphrases:
        phrase = phrase.strip()
    phraseprocs = [multiprocessing.Process(target=phrasescraper(
        phrase, aprocpath)) for phrase in chapterphrases]


    if __name__ == '__main__':
        for phraseproc in phraseprocs:
            phraseproc.daemon = False
            phraseproc.start()
            uprint("Running phrase operations")
        for phraseproc in phraseprocs:
            phraseproc.join()
        uprint('Started phrase operations for {}'.format(aprocpath.split('\\')[-1]))


def phrasescraper(aphrase, aprocpath):
    """ Gets images for a phrase and writes them to the phrase folder """
    config = {
        'keyword': aphrase,
        'database_name' : 'redox',
        'print_results' : 'summarize',
        'log_level' : 'INFO',
        'num_results_per_page' : 30,
        'num_pages_for_keyword' : 1,
        'num_workers' : 1,
        'maximum_workers' : 2
        }


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
    threads = [FetchResource(phraseimages, []) for i in range(num_threads)]
    while image_urls:
        for t in threads:
            try:
                t.furls.append(image_urls.pop())
                ## add check for an empty image_urls if serp has no links
            except IndexError:
                break


    threads = [t for t in threads if t.furls]
    b = 0
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        b += 1
    uprint('downloaded {} images for {}'.format(b, aphrase))


    fileiter = (os.path.join(root, f) for root, _, files in os.walk(
        aprocpath +'\\images\\' + aphrase) for f in files)
    smallfileiter = (f for f in fileiter if os.path.getsize(f) < 300 * 800)
    for small in smallfileiter:
        os.remove(small)
        print("\nRemoved small images from {}\n____________________\n".format(aphrase))


class FetchResource(threading.Thread):
    """ Gets the content of a url """


    def __init__(self, target, furls):
        super().__init__()
        self.target = target
        self.furls = furls


    def run(self):
        if not os.path.exists(self.target.strip()):
            os.makedirs(self.target.strip())
        for furl in self.furls:
            furl = urllib.parse.unquote(furl)
            name = furl.split('/')[-1]
            with open(os.path.join(self.target, name), 'wb') as fname:
                content = requests.get(furl).content
                fname.write(content)


def main():
    """ Reads target folder and calls chapter operations """
    chapterprocs = [multiprocessing.Process(
        target=chapterscraper(procpath)) for procpath in procpathS]
    if __name__ == '__main__':
        for chapterproc in chapterprocs:
            chapterproc.start()
            uprint("Started processing chapters in parallel")
        for chapterproc in chapterprocs:
            chapterproc.join()
    uprint("Finished processing everything")


if __name__ == '__main__':
    main()
