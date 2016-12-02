""""Main code for dox"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import os.path
import urllib
import multiprocessing
import threading
import requests
from GoogleScraper import scrape_with_config, GoogleSearchError

def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    """This is just a print wrapper"""
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        fup = lambda obj: str(obj).encode(enc, errors='replace').decode(enc)
        print(*map(fup, objects), sep=sep, end=end, file=file)

procpath = "C:\\Users\\nnikh\\Documents\\redox\\p1"
def get_immediate_subdirectories(a_dir):
    """ Get only the immediate subfolders """
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]

class FetchResource(threading.Thread):
    """ Gets the content of a url """
    def __init__(self, target, furls, fphrase):
        super().__init__()
        self.target = target
        self.furls = furls
        self.phrase = fphrase
    def run(self):
        for furl in self.furls:
            furl = urllib.parse.unquote(furl)
            if not os.path.exists(os.path.join(self.target)):
                os.makedirs(os.path.join(self.target))
            name = furl.split('/')[-1]
            with open(os.path.join(self.target, str(name.split('?', 1)[0])), 'wb') as fname:
                try:
                    content = requests.get(furl).content
                    fname.write(content)
                except OSError:
                    pass

class Chapterproc(multiprocessing.Process):
    """ Reads phraselist and calls FetchResource for each phrase """
    def __init__(self, cprocpath, cdirname, ckeywords):
        super().__init__()
        self.cprocpath = cprocpath
        self.cdirname = cdirname
        self.ckeywords = ckeywords
        self.config = {}
        self.image_urls = []
        self.threads = []
    def run(self):
        for cphrase in self.ckeywords:
            cphrase = cphrase.strip()
            config = {
                'keyword': cphrase,
                'database_name' : 'redoxsql'+ cphrase}
            try:
                search = scrape_with_config(config)
            except GoogleSearchError as e:
                uprint(e)
            image_urls = []
            for serp in search.serps:
                image_urls.extend(
                    [link.link for link in serp.links])
            num_threads = 30
            chapterimages = os.path.join(self.cprocpath, self.cdirname, 'images', cphrase)
            threads = [FetchResource(chapterimages, [], cphrase)
                       for i in range(num_threads)]
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
            uprint('downloaded {} images for {}'.format(b, cphrase))
            fileiter = (os.path.join(root, f) for root, _, files in os.walk(
                self.cprocpath +'\\images\\' + cphrase) for f in files)
            smallfileiter = (f for f in fileiter if os.path.getsize(f) < 300 * 800)
            for small in smallfileiter:
                os.remove(small)
            print("\nRemoved small images from {}\n____________________\n".format(
                self.cdirname))
        print("Downloaded all images for {}\n____________________\n".format(
            self.cdirname))

dirnames = get_immediate_subdirectories(procpath)

for chapter in dirnames:
    script = os.path.join(procpath, chapter, 'scrsipt.txt')
    kwfile = os.path.join(procpath, chapter, 'phraselist.txt')
    with open(kwfile, mode='r', encoding='utf-8') as g:
        keywords = list(set(g.read().splitlines()))
    uprint("\n____________________\n\nRead all phrases for {}\n\n"
            .format(chapter))
    num_procs = int(len(dirnames))

if __name__ == '__main__':
    procs = [Chapterproc(procpath, chapter, keywords) for chapter in dirnames]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    uprint('downloaded images for {}'.format(chapter.split('\\')[-1]))
