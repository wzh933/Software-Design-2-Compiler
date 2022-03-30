from src.compiler.parser.Attributes import Attributes


class First:
    def __init__(self, file_path, s):
        self.s = s
        self.a = Attributes(file_path)
        self.visited_nonTerminator_list = []
        self.first_set = set(self.get_first(self.s))

    def get_first(self, s):
        # 避免死递归
        if s in self.visited_nonTerminator_list:
            return []
        if s in self.a.nonTerminator_list:
            self.visited_nonTerminator_list.append(s)
        if s in self.a.terminator_list:
            return [s]
        first_list = []
        for pro_right in self.a.production_map[s]:
            for word in pro_right:
                if word not in self.a.space_nonTerminator:
                    first_list += self.get_first(word)
                    break
                first_list += self.get_first(word)
        return first_list


# file_path = "config.json"
# a = Attributes(file_path)
# f_list = [First(file_path, s) for s in a.nonTerminator_list]
# for f in f_list:
#     print(f.s, ":", f.first_set)
# f = First("config.json", "BLOCK_STMT")
# print(f.first_list)
# print(f.visited_nonTerminator_list)
