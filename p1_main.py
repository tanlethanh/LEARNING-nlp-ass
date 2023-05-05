import sys
from nltk import data, CFG, Tree, ChartParser
from custom_parser import Parser
from utils import get_all_terminal_nodes, split_tokens

from sentence_generator import generate_sentence

grammar = data.load(resource_url="./p1_grammar.cfg")

if not isinstance(grammar, CFG):
    sys.exit(-1)

# generate_sentence(grammar=grammar)

accepted_tokens = get_all_terminal_nodes(grammar)
parser = ChartParser(grammar)

text = "tôi có thể bực"
with open("./output/parse_results.txt", "+w", encoding="utf-8") as out_file:
    with open("./input/sentences.txt", "r", encoding="utf-8") as in_file:
        for line in in_file:
            try:
                # sentence = in_file.readline()
                tokens = split_tokens(sentence=line, accepted_tokens=accepted_tokens)
                result = parser.parse_one(tokens)

                if not isinstance(result, Tree):
                    out_file.write("()\n")
                else:
                    out_file.write(result.pformat(margin=100000) + "\n")
            except:
                out_file.write("()\n")
