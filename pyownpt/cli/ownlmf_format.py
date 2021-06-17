# -*- coding: utf-8 -*-

import sys
import argparse
import logging

from six import with_metaclass
logger = logging.getLogger()

from rdflib import Graph
from rdflib.util import guess_format
from pyownpt.ownlmf import OWNPT_LMF

def _parse(args):
    ownpt_filapaths = args.owp
    ili_map_filapath = args.ili
    lexicon_id = args.l
    output_filepath = args.o

    # configs logging
    fileHandler = logging.FileHandler(filename="log-format", mode="w")
    fileHandler.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler(stream=sys.stdout)
    streamHandler.setLevel(level=30-10*args.v)

    logging.basicConfig(level=logging.DEBUG, handlers=[streamHandler,fileHandler])

    # calls main function
    lmf_format(ownpt_filapaths, ili_map_filapath, lexicon_id, output_filepath)


def lmf_format(
    ownpt_filapaths,
    ili_map_filapath,
    lexicon_id,
    output_filepath):

    # loading data
    ownpt = Graph()
    for ownpt_filapath in ownpt_filapaths:
        logger.info(f"loading data from file '{ownpt_filapath}'")
        ownpt_format = _get_format(ownpt_filapath)
        ownpt.parse(ownpt_filapath, format=ownpt_format)

    ili_map = Graph()
    logger.info(f"loading data from file '{ili_map_filapath}'")
    ili_map_format = _get_format(ili_map_filapath)
    ili_map.parse(ili_map_filapath, format=ili_map_format)

    # formats into LMF format
    logger.info(f"formatting into LMF format")
    ownpt_lmf = OWNPT_LMF(ownpt, ili_map, lexicon_id).format()

    # serializes output
    logger.info(f"serialiing output to {output_filepath}")
    open(output_filepath, "w", encoding="utf8").write(ownpt_lmf)


def _get_format(filepath:str):
    """"""

    filepath_format = guess_format(filepath, {"jsonld":"json-ld"})    
    return filepath_format if filepath_format else filepath.split(".")[-1]


# sets parser and interface function
parser = argparse.ArgumentParser()

# sets the user options
parser.add_argument("owp", help="fileS from own-pt", nargs="+")
parser.add_argument("ili", help="rdf file from ili-map")
parser.add_argument("-l", help="lexicon id (default: own-pt)", default="own-pt")
parser.add_argument("-o", help="output file (default: output.xml)", default="output.xml")

parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# cals the parser
_parse(parser.parse_args())


# lmf_format(
#     "/home/fredson/openWordnet-PT/own-pt-morpho.nt",
#     "/home/fredson/openWordnet-PT/own-en-morpho.nt",
#     "/home/fredson/openWordnet-PT/ili-map.ttl",
#     "own-pt",
#     "output.xml"
#     )