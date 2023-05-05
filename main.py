from nltk import data, Tree
from custom_parser import Parser
from utils import context_filter, cv_query
import re

print('----------------------------- Load Parser -----------------------------')

cp = Parser(data.load('./grammar.fcfg'))

print('----------------------------- Parsing -----------------------------')

special_tokens = [
    'Hồ Chí Minh', 
    'Đà Nẵng', 
    'Nha Trang', 
    'Phú Quốc',
    'nhắc lại',
    'phương tiện',
    'bao lâu',
    'bao nhiêu',
    'gì vậy',
    'nào nhỉ',
    'tất cả',
    'có thể',
    'được không'
    ]

queries = [
    'đi từ Hồ Chí Minh tới Nha Trang hết bao lâu',
    'đi từ Hồ Chí Minh tới Đà Nẵng hết bao lâu',
    'có bao nhiêu tour đi Phú Quốc vậy bạn',
    'tour Nha Trang đi bằng phương tiện gì vậy',
    'đi Nha Trang có những ngày nào nhỉ',
    'em có thể nhắc lại tất cả các tour được không'
    ]

for idx, query in enumerate(queries):
    for tok in special_tokens:
        queries[idx] = queries[idx].replace(tok, '_'.join(tok.split()))
        
    queries[idx] = queries[idx].split()
        
# print(queries)

database = {
    "RUN-TIME": {
        "HCMC-PQ": "2:00 HR",
        "HCMC-DN": "2:00 HR",
        "HCMC-NT": "5:00 HR",
    },
    "BY": {
        "PQ": "airplane",
        "DN": "airplane",
        "NT": "train"
    },
    "DTIME": [
        { "HCMC-PQ": "7AM 1/7" },
        { "HCMC-PQ": "8AM 5/7" },
        { "HCMC-DN": "7AM 1/7" },
        { "HCMC-DN": "7AM 4/7" },
        { "HCMC-NT": "7AM 1/7" },
        { "HCMC-NT": "7AM 5/7" },
    ],
    "ATIME": [
        { "HCMC-PQ": "9AM 1/7" },
        { "HCMC-PQ": "10AM 5/7" },
        { "HCMC-DN": "9AM 1/7" },
        { "HCMC-DN": "9AM 4/7" },
        { "HCMC-NT": "12AM 1/7" },
        { "HCMC-NT": "12AM 5/7" },
    ]
}

print('----------------------------- Result ----------------------------- \n')

for (index, query) in enumerate(queries):
    print(f"------------------------ {index} ------------------------")
    trees = cp.parse_all(query)
    
    print("Current query: ", query)
    
    for tree in trees:
        try:
            if not isinstance(tree, Tree):
                continue    
            full_sematic = tree.label()['SEM']
            full_sematic = list(filter(lambda ele: ele != '', full_sematic))
            print('SEM: ', str(full_sematic))
            try:
                ctx = context_filter(full_sematic)
            except Exception as e:
                print("Some thing wrong", e)
                
            print(ctx)
                
            # context = {
            #     "From": None,
            #     "To": None,
            #     "Aim": [],
            #     "Question": None
            # }
            
            result = None
            query_form = cv_query(ctx["From"]) + "-" + cv_query(ctx["To"])

            if ctx['Question'] == 'How_long':
                result = []
                data = database["RUN-TIME"]
                
                for key in data.keys():
                    if re.match(query_form, key):
                        result.append(data[key])

            elif ctx['Question'] == "How_many":
                data = database["DTIME"]
                result = 0
                for dtime in data:
                    if re.match(query_form, list(dtime.keys())[0]):
                        result += 1
            
            elif ctx['Question'] == "What":
                
                if ctx['Topic'] == 'date':
                    data = database["DTIME"]
                    result = []
                    for dtime in data:
                        key = list(dtime.keys())[0]
                        if re.match(query_form, key):
                            result += [dtime[key].split()[1]]
                    
                elif ctx['Topic'] == 'vehicle':
                    data = database["BY"]
                    result = data[ctx["To"]]                

                elif ctx['Topic'] is None:
                    result = database["ATIME"]
            
            print("result", result) 
            break
        except:
            print("Not suited")
            continue
    else:
        print('No parsed tree')
