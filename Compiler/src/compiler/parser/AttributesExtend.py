from src.compiler.parser.Attributes import Attributes
from src.compiler.parser.AttributesFirst import First


class AttributesExtend(Attributes):
    def __init__(self, file_path):
        super(AttributesExtend, self).__init__(file_path)
        self.first_set_map = {}
        for s in self.terminator_list:
            self.first_set_map[s] = {s}
        f_list = [First(file_path, s) for s in self.nonTerminator_list]
        for f in f_list:
            self.first_set_map[f.s] = f.first_set


# a_e = AttributesExtend('config.json')
# data = open('first_set', 'w+')
# for key in a_e.first_set_map.keys():
#     print(key, ":", a_e.first_set_map[key], file=data)
# data.close()
