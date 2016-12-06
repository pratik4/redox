""" Generates a raw phraselist for the author """
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from more_itertools import unique_everseen
from textblob import TextBlob
from textblob.np_extractors import ConllExtractor
from textblob_aptagger import PerceptronTagger
extractor = ConllExtractor()
ap_tagger = PerceptronTagger()

def get_immediate_subdirectories(a_dir):
    """ Get only the immediate subfolders """
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(
                os.path.join(
                    a_dir, name))]


drive = "C:\\Users\\nnikh\\Google Drive"
author = os.path.join(
    drive, "nikhilatphyzok")
projectpath = os.path.join(
    author, "automation", "phrase extraction")


def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    """ This is just a print wrapper """
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        l = lambda obj: str(obj).encode(
            enc, errors='replace').decode(enc)
        print(*map(l, objects), sep=sep, end=end, file=file)
dirnames = get_immediate_subdirectories(projectpath)
for chapter in dirnames:
    script = os.path.join(
        projectpath, chapter, 'script.txt')
    kwfile = os.path.join(
        projectpath, chapter, 'phraselist.txt')
    with open(
        script, mode='r', encoding='utf-8') as g:
        wiki = g.read()
        blob = TextBlob(
            wiki, np_extractor=extractor,
            pos_tagger=ap_tagger)
    print("\nReading script for {}"
          .format(chapter.split('\\')[-1]))
    
    
    with open(
        kwfile, mode='wt', encoding='utf-8') as h:
        phraseset = unique_everseen(
            blob.noun_phrases)
        for phrase in phraseset:
            h.write(phrase+'\n')
    print("Wrote phrases for {}\n____________________".format(chapter.split('\\')[-1]))
