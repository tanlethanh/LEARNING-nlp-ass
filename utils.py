from nltk import CFG


def context_filter(sems):
    context = {
        "From": None,
        "To": None,
        "Topic": None,
        "Question": None
    }

    for idx, sem in enumerate(sems):
        if sem in context.keys():
            context[sem] = sems[idx + 1]

        elif sem in ['tour', 'vehicle', 'date']:
            context['Topic'] = sem

        elif sem in ['What', 'How_many', 'How_long']:
            context['Question'] = sem

    return context


def cv_query(text):
    return text if text is not None else ".*"


def get_all_terminal_nodes(grammar: CFG):
    nodes = []
    for prod in grammar.productions():
        for node in list(prod.rhs()):
            if isinstance(node, str):
                nodes.append(node)
    return nodes


def split_tokens(sentence: str, accepted_tokens):
    for tok in accepted_tokens:
        sentence = sentence.replace(tok, "_".join(tok.split()))

    tokens = sentence.split()
    for idx, tok in enumerate(tokens):
        tokens[idx] = " ".join(tok.split("_"))

    return tokens
