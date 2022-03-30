import global_var as gl
from src.compiler.parser.AttributesExtend import AttributesExtend


class Production:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __eq__(self, other):
        return self.left == other.left and self.right == other.right

    def __str__(self):
        return self.left + " -> " + str(self.right)


class ProductionItem:
    def __init__(self, production, index=0, forward=None):
        if forward is None:
            forward = {'#'}
        # 产生式
        self.production = production
        # 向前看的单词的位置
        self.index = index
        # 向前搜索符
        self.forward = forward

    def __eq__(self, other):
        if self.index != other.index:
            return False
        if self.forward != other.forward:
            return False
        if self.production != other.production:
            return False
        return True

    def __str__(self):
        return str(self.production) + "," + str(self.forward) + ", index=" + str(self.index)


class Closure:
    def __init__(self):
        # 定义静态全局变量
        self.id = gl.global_closure_num
        self.item_list = []
        self.shift_closure = {}

    def add_item(self, item):
        self.item_list.append(item)

    def __eq__(self, other):
        if self.item_list == other.item_list:
            return True
        if len(self.item_list) != len(other.item_list):
            return False
        flag = True
        for item in self.item_list:
            if item not in other.item_list:
                flag = False
                break
        return flag

    def __str__(self):
        res = ""
        for pro in self.item_list:
            res += str(pro) + "\n"

        return res


class DFA:
    def __init__(self, file_path, start_of_grammar):
        self.attributes = AttributesExtend(file_path)
        self.production_list = self.get_production_list()
        self.production_map = self.get_production_map()
        self.start_of_grammar = start_of_grammar
        self.closure_list = []
        self.get_closure_list()

    def get_production_list(self):
        production_list = []
        for pro in self.attributes.production_list:
            production = Production(left=pro['left'], right=pro['right'])
            production_list.append(production)
        return production_list

    def get_production_map(self):
        production_map = {}
        for left in self.attributes.production_map.keys():
            production_list = []
            for right in self.attributes.production_map[left]:
                production_list.append(Production(left=left, right=right))
            production_map[left] = production_list
        return production_map

    # item_set是Closure类型的
    def get_closure(self, closure):
        # print(get_closure_item_set.id)
        for tmp in closure.item_list:
            if tmp.index == len(tmp.production.right) - 1:
                # 点 后面只有一个符号 是否是非终结符
                may_left = tmp.production.right[tmp.index]
                # 是 非终结符
                if may_left in self.attributes.nonTerminator_list:
                    for production in self.production_map[may_left]:
                        closure1 = ProductionItem(production=production, index=0, forward=tmp.forward)
                        if closure1 not in closure.item_list:
                            closure.item_list.append(closure1)
            elif tmp.index < len(tmp.production.right) - 1:
                # 点 后面有超过一个符号 是否为非终结符
                may_left = tmp.production.right[tmp.index]
                # 是 非终结符
                if may_left in self.attributes.nonTerminator_list:
                    forward1 = set([])
                    is_all_space = True
                    for token in tmp.production.right[tmp.index + 1:]:
                        if token not in self.attributes.space_nonTerminator:
                            is_all_space = False
                            forward1 |= self.attributes.first_set_map[token]
                            break
                        forward1 |= self.attributes.first_set_map[token]
                    if is_all_space:
                        forward1 |= tmp.forward
                    for production in self.production_map[may_left]:
                        closure1 = ProductionItem(production=production, index=0, forward=forward1)
                        if closure1 not in closure.item_list:
                            closure.item_list.append(closure1)

    # item_set是Closure类型的
    def search_forward(self, closure):
        s_map = {}
        keys = []
        # tmp是当前产生式项目
        for tmp in closure.item_list:
            # 如果tmp不是规约项目而是移进项目
            if tmp.index < len(tmp.production.right):
                # ss是要被移进的字符
                ss = tmp.production.right[tmp.index]
                # 如果移进ss已经被执行
                if ss in s_map.keys():
                    # 在ss的已移进项目集中添加当前被移进项目
                    closure1 = s_map[ss]
                    closure1.add_item(
                        ProductionItem(production=tmp.production, index=tmp.index + 1, forward=tmp.forward))
                else:
                    # 否则产生新项目集
                    closure1 = Closure()
                    # 新项目集中加入当前被移进项目
                    closure1.add_item(
                        ProductionItem(production=tmp.production, index=tmp.index + 1, forward=tmp.forward))
                    # 添加映射
                    s_map[ss] = closure1
                    keys.append(ss)
        # 解决冲突重复问题
        for key in keys:
            # 各自建完整项目集
            closure1 = s_map[key]
            self.get_closure(s_map[key])
            # 如果已经存在
            if closure1 in self.closure_list:
                ind = self.closure_list.index(closure1)
                closure.shift_closure[key] = ind
                # gl.global_closure_num -= 1
            else:
                gl.global_closure_num += 1
                closure1.id = gl.global_closure_num
                closure.shift_closure[key] = closure1.id
                self.closure_list.append(closure1)

    def get_closure_list(self):
        # 增广文法中产生式开始符对应的产生式只有一条，取出之
        start_production = self.production_map[self.start_of_grammar][0]
        start_item = Closure()
        self.closure_list.append(start_item)
        start_item.add_item(ProductionItem(start_production))
        cnt = 0
        while 1:
            self.get_closure(self.closure_list[cnt])
            self.search_forward(self.closure_list[cnt])
            cnt += 1
            num = len(self.closure_list)
            if cnt == num:
                break


class ActionGoto:
    def __init__(self, file_path, start_of_grammar):
        self.dfa = DFA(file_path=file_path, start_of_grammar=start_of_grammar)
        self.action_list, self.goto_list = self.get_action_goto_list()

    def get_action_goto_list(self):
        action_list = []
        goto_list = []
        for item_set in self.dfa.closure_list:
            action_dict = {}
            goto_dict = {}
            # 移进项目
            for key in item_set.shift_closure.keys():
                if key in self.dfa.attributes.terminator_list:
                    action_dict[key] = item_set.shift_closure[key]
                else:
                    goto_dict[key] = item_set.shift_closure[key]
            # 规约项目
            for production_item in item_set.item_list:
                if production_item.index == len(production_item.production.right):
                    for token in production_item.forward:
                        # 为了打印出ActionGoto表，将用于规约的产生式toString，打印完之后再注释掉
                        # action_dict[token] = str(production_item.production)
                        action_dict[token] = production_item.production
            action_list.append(action_dict)
            goto_list.append(goto_dict)
        # 接受
        action_list[1]['#'] = "acc"
        return action_list, goto_list


# ag = ActionGoto(file_path='parser_config.json', start_of_grammar="CLASS_S")
# # ag = ActionGoto(file_path='config_test1.json', start_of_grammar="START")
# #
# data = open('action_goto_list', 'w+')
# for i in range(len(ag.dfa.item_set_list)):
#     # print(i, ":", ag.action_list[i], ag.goto_list[i])
#     print("{}:Action:{},Goto:{}".format(i, ag.action_list[i], ag.goto_list[i]))
# data.close()

# dfa = DFA(file_path='config_test1.json', start_of_grammar=gl.start_of_grammar)
# dfa = DFA(file_path='config.json', start_of_grammar=gl.start_of_grammar)
# # print(dfa.item_set_list[60])
# data = open("item_set_list1", 'w+')
# for closure in dfa.item_set_list:
#     print("I{}:".format(closure.id), file=data)
#     print(closure, closure.shift_closure, file=data)
#     print(file=data)
# print("项目集族个数为：", gl.global_closure_num, file=data)
# data.close()

# print(dfa.item_set_list)
# for production in dfa.production_map["START"]:
#     print(production)
# for production in dfa.production_list:
#     print(str(production))
# print(len(dfa.production_list))
# print(dfa.production_list)
# print(dfa.attributes.first_set_map)
# p1 = Production("S", ['a', 'B'])
# p2 = Production("S", ['a', 'B'])
# l = [p1, p2]
# print(l)
# p1 = ProductionItem(Production("S", ['a', 'B']))
# p2 = ProductionItem(Production("S", ['a', 'B']))
# p3 = ProductionItem(Production("S", ['a', 'C']))
# p4 = ProductionItem(Production("S", ['a', 'D']))

# l1 = [p1, p3]
# l2 = [p4, p3]
# flag = True
# for item in l1:
#     if item not in l2:
#         flag = False
#         break
# print(flag)
# print(p1)
# print(p2)

# c1 = Closure()
# c1.add_item(p1)
# c1.add_item(p3)
# c2 = Closure()
# c2.add_item(p4)
# c2.add_item(p3)
# print(c1.item_list)
# print(c2.item_list)
# print(c1 == c2)

# p_list = [p1]
# print(p2 in p_list)

# p1 = Production("S", ['a', 'B'])
# p2 = Production("S", ['a', 'B'])

# print(p1 == p2)
# c1 = Closure()
# c2 = Closure()
# c3 = Closure()
# print(c3.id)
# print(gl.global_closure_num)
