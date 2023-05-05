import sys
from nltk import data, CFG

from sentence_generator import generate_sentence

grammar = data.load(resource_url="./p1_grammar.cfg")

if not isinstance(grammar, CFG):
    sys.exit(-1)

generate_sentence(grammar=grammar)

