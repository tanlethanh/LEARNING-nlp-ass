
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