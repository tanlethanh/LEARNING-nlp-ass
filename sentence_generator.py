import random
from nltk import data, CFG, Production
import sys

MAX_DEPTH = 30
NUMBER_OF_SENTENCES = 100
INFINITE_LOOP_COUNT = 1000000


def print_to_file(generated_sentences, filename):
    with open(filename, "+w", encoding='utf-8') as file:
        for sentence in generated_sentences:
            file.write(sentence + "\n")

def create_sentence(start, grammar: CFG):
    created_string = []

    def dfs(root):
        prod = random.choice(grammar.productions(lhs=root))
        if not isinstance(prod, Production):
            return ""
        else:
            for ele in list(prod.rhs()):
                if isinstance(ele, str):
                    created_string.append(ele)
                else:
                    dfs(ele)
    dfs(start)
    return " ".join(created_string)

def generate_sentence(grammar: CFG):
    try:
        generated_sentences = []
        for i in range(0, INFINITE_LOOP_COUNT):
            sentence = create_sentence(grammar.start(), grammar)
            if len(sentence.split()) > MAX_DEPTH:
                continue
            if len(generated_sentences) >= NUMBER_OF_SENTENCES:
                break
            print(sentence)
            
            if sentence not in generated_sentences:
                generated_sentences.append(sentence)
        
        print("Count", len(generated_sentences))

        print_to_file(generated_sentences, "output/samples.txt")
        print("------------------------------------------------------")
    except RecursionError:
        print("Please RUN again! RecursionError: maximum recursion depth exceeded.")
