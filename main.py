from io import StringIO
from nltk import data
from custom_parser import BottomUpLeftCornerChartParser

class NullIO(StringIO):
    def write(self, txt):
        pass

filename = './grammar.fcfg'
data.show_cfg(filename)

print('\n ----------------------------- Load Parser ----------------------------- \n')

# cp = load_parser(filename, trace=3)
cp = BottomUpLeftCornerChartParser(data.load(filename))

print('\n ----------------------------- Parsing ----------------------------- \n')

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


print('\n ----------------------------- Result ----------------------------- \n')

for (index, query) in enumerate(queries):
    print(f"------------------------ {index} ------------------------")
    trees = cp.parse_all(query)
    
    print("\nCurrent query: ", query)
    
    if len(trees) > 0:
        print('Number of parsed trees', len(trees))
        print('First tree')
        print(trees[0])

        answer = trees[0].label()['SEM']
        ans_str = ' '.join(answer)
        print('\nSEM: ', ans_str)

    else:
        print('No parsed tree')

