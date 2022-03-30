from src.compiler.parser.Parser import *
import global_var as gl

type_list = [
    "DECLARE_INTER_START",  # 变量声明语句
    "BLOCK_STMT_EXPRESSION_START",  # 单纯的赋值语句
    "PRINT_STMT_START",  # print语句
    "RETURN_STMT_START",  # return 语句
    "IF_STMT_START",  # if-else语句
    "WHILE_STMT_START",  # while循环语句
    "DO_WHILE_STMT_START",  # do-while循环语句
    "FOR_STMT_START"  # for循环语句
]
# 运算优先级映射：“非算关与或赋”
op_map = {'=': 0, '||': 1, '&&': 2, '==': 2.5, '!=': 2.5, '<=': 2.5, '>=': 2.5, '>': 2.5, '<': 2.5, '+': 3, '-': 3,
          '*': 4, '/': 4, '%': 4}
double_op = ["+=", "-=", "++", "--"]


class TAC:
    def __init__(self, tac_tuple):
        self.label = gl.global_label_cnt
        gl.global_label_cnt += 1
        self.tac_tuple = list(tac_tuple)

    def __str__(self):
        return '{' + "'label':{},'TAC':{}".format(self.label, tuple(self.tac_tuple)) + '}'


# tac = TAC(('1', 2, 3, 4))
# print(tac)


class MatchParser:
    def __init__(self, parser_config_file_path, token_list, start_of_grammar):
        gl.global_closure_num = 0
        self.ag = ActionGoto(file_path=parser_config_file_path, start_of_grammar=start_of_grammar)
        # lexer = Lexer(config_file_path=lexer_config_file_path, main_file_path=main_file_path)
        # 输入串
        self.input_token_list = []
        self.input_val_line_list = []
        self.error_line = 0
        self.error_token = None

        for token in token_list:
            self.input_val_line_list.append({'val': token['val'], 'line': token['line']})
            if token['type'] == 'ID' or token['type'] == 'CONSTANT' or token['type'] == 'ERROR':
                self.input_token_list.append(token['type'])
            else:
                self.input_token_list.append(token['val'])
        self.input_token_list.append('#')
        self.is_matched = self.parser()

    # 判断是否出错
    def is_error(self, state, input_token):
        return input_token not in self.ag.action_list[state].keys()

    def parser(self):
        # 状态栈
        state_stack = [0]
        # 符号栈
        token_stack = ['#']
        while 1:
            state = state_stack[-1]
            input_token = self.input_token_list[0]

            # 出错
            if self.is_error(state, input_token):
                self.error_state = state
                return False

            action = self.ag.action_list[state][input_token]

            # S{action}，移进
            if type(action) == int:
                state_stack.append(action)
                token_stack.append(input_token)
                self.input_token_list.pop(0)


            # r{x}，规约
            elif type(action) == Production:
                len_pop = len(action.right)
                for i in range(len_pop):
                    state_stack.pop(-1)
                    token_stack.pop(-1)
                token_stack.append(action.left)
                state_stack.append(self.ag.goto_list[state_stack[-1]][action.left])

            # 接受
            elif action == 'acc':
                return True


class GenTAC:
    def __init__(self, parser_config_file_path, token_list):
        self.parser_config_file_path = parser_config_file_path
        self.token_list = token_list
        self.type = self.match_type()

    def match_type(self):

        if self.token_list[0]['val'] == 'if' \
                or self.token_list[0]['val'] == 'else' and self.token_list[1]['val'] == 'if':
            return "IF_STMT_START"

        if self.token_list[0]['val'] == 'while':
            return "WHILE_STMT_START"

        if self.token_list[0]['val'] == 'for':
            return "FOR_STMT_START"

        for start_token in type_list:
            match_parser = MatchParser(parser_config_file_path=self.parser_config_file_path,
                                       token_list=self.token_list,
                                       start_of_grammar=start_token)
            if match_parser.is_matched:
                return start_token



    # 生成运算语句的TAC
    @staticmethod
    def gen_OP_TAC(token_list):
        result = []
        to_process_list = []
        LRD_stack = []
        op_stack = []
        token_cnt = 0
        for token in token_list:
            if token['type'] == 'ID' or token['type'] == 'CONSTANT':
                LRD_stack.append(token)
            elif token['val'] in op_map.keys():
                op = token
                while 1:
                    if len(op_stack) == 0 or op_stack[-1]['val'] == '(' or op_map[op['val']] > op_map[
                        op_stack[-1]['val']]:
                        break
                    LRD_stack.append(op_stack[-1])
                    op_stack.pop(-1)
                op_stack.append(op)
            elif token['val'] == '(':
                op_stack.append(token)
            elif token['val'] == ')':
                while 1:
                    if op_stack[-1]['val'] != '(':
                        LRD_stack.append(op_stack[-1])
                        op_stack.pop(-1)
                    else:
                        op_stack.pop(-1)
                        break
            elif token['val'] == '++' or token['val'] == '--':
                op = token['val'][0]
                if token_cnt == 0:
                    result.append(TAC((op, token_list[token_cnt + 1]['val'], 1, "T" + str(gl.global_var_cnt))))
                    result.append(TAC(('=', "T" + str(gl.global_var_cnt), '-', token_list[token_cnt + 1]['val'])))
                    gl.global_var_cnt += 1
                else:
                    if token_list[token_cnt + 1]['type'] == 'ID':
                        result.append(TAC((op, token_list[token_cnt + 1]['val'], 1, "T" + str(gl.global_var_cnt))))
                        result.append(TAC(('=', "T" + str(gl.global_var_cnt), '-', token_list[token_cnt + 1]['val'])))
                        gl.global_var_cnt += 1
                    elif token_list[token_cnt - 1]['type'] == 'ID':
                        to_process_list.append((op, token_list[token_cnt - 1]['val'], 1))
                        to_process_list.append(('=', '-', token_list[token_cnt - 1]['val']))
            # elif token['val'] == '--':
            #     if token_cnt == 0:
            #         result.append(('-', token_list[token_cnt + 1]['val'], 1, "T" + str(gl.global_var_cnt)))
            #     else:
            #         if token_list[token_cnt + 1]['type'] == 'ID':
            #             result.append(('-', token_list[token_cnt + 1]['val'], 1, "T" + str(gl.global_var_cnt)))
            #             gl.global_var_cnt += 1
            #         elif token_list[token_cnt - 1]['type'] == 'ID':
            #             to_process_list.append(('-', token_list[token_cnt - 1]['val'], 1))

            token_cnt += 1

        while 1:
            if len(op_stack) == 0:
                break
            LRD_stack.append(op_stack[-1])
            op_stack.pop(-1)

        var_stack = []
        # print(LRD_stack)

        for token in LRD_stack:
            # print(token)
            if token['type'] == 'ID' or token['type'] == 'CONSTANT':
                var_stack.append(token['val'])
            # # 单操作数运算符单独处理
            # elif token['val'] == '!':
            #     print(1)
            #     var = var_stack[-1]
            #     var_stack.pop(-1)
            #     process_var = "T" + str(gl.global_var_cnt)
            #     tac = (token['val'], var, '-', process_var)
            #     print('wzh', tac)
            #     gl.global_var_cnt += 1
            #     result.append(tac)
            #     var_stack.append(process_var)

            elif token['type'] == 'OP':
                var2 = var_stack[-1]
                var_stack.pop(-1)
                var1 = var_stack[-1]
                var_stack.pop(-1)
                process_var = "T" + str(gl.global_var_cnt)
                if token['val'] == '=':
                    tac = TAC((token['val'], var2, '-', var1))
                else:
                    tac = TAC((token['val'], var1, var2, process_var))
                    gl.global_var_cnt += 1
                result.append(tac)
                # print(tac)
                var_stack.append(process_var)

        for to_process_tac in to_process_list:
            process_var = "T" + str(gl.global_var_cnt)
            if to_process_tac[0] == '=':
                tac = TAC(to_process_tac[:1] + (process_var,) + to_process_tac[1:])
                result.append(tac)
                gl.global_var_cnt += 1
            else:
                to_process_tac += (process_var,)
                result.append(TAC(to_process_tac))
        # result.append(('=', var_stack[0], '-', var0))
        # 返回TAC语句序列和运算结果
        return result, var_stack[0]

    # 生成赋值语句的TAC
    def gen_BLOCK_STMT_EXPRESSION_TAC(self, token_list, is_declare_inter=False):
        # 如果是在变量声明时则沿用前面的后缀表达式
        # 用以区别双目运算符的赋值语句和存在双目运算符的表达式
        if is_declare_inter:
            return self.gen_OP_TAC(token_list)[0]

        global marked_op
        result = []
        exist_double_op = False

        for token in token_list:
            if token['val'] in double_op:
                marked_op = token['val']
                exist_double_op = True
                break

        # 存在双目运算符且不是变量声明时的赋值
        if exist_double_op:
            process_var = "T" + str(gl.global_var_cnt)
            global var0
            for token in token_list:
                if token['type'] == 'ID':
                    var0 = token['val']
                    break
            if marked_op == '+=' or marked_op == '-=':
                result.append(TAC((marked_op[0], var0, token_list[2]['val'], process_var)))
                result.append(TAC(('=', process_var, '-', var0)))
                gl.global_var_cnt += 1
                # result.append((marked_op[0], var0, token_list[2]['val'], var0))
            elif marked_op == '++' or marked_op == '--':
                # result.append((marked_op[0], var0, 1, var0))
                result.append(TAC((marked_op[0], var0, 1, process_var)))
                result.append(TAC(('=', process_var, '-', var0)))
                gl.global_var_cnt += 1

        else:
            result = self.gen_OP_TAC(token_list)[0]
            # var0 = token_list[0]['val']
            # tac_list = self.gen_OP_TAC(token_list)[0]
            # for tac in tac_list:
            #     result.append(tac)
            # result.append(('=', res, '-', var0))
        return result

    # 生成变量声明的TAC语句
    def gen_DECLARE_INTER_TAC(self, token_list):
        result = []
        declare_type = token_list[0]['val']
        # result.append((declare_type, token_list[1]['val'], '-', '-'))
        expression_list = []
        expression = []
        after_comma_list = []
        is_after_comma = True
        for token in token_list[1:-1]:
            if is_after_comma:
                after_comma_list.append(token)
                is_after_comma = False
            if token['val'] != ',':
                expression.append(token)
            else:
                expression_list.append(expression)
                expression = []
                is_after_comma = True
        if len(expression) != 0:
            expression_list.append(expression)
        for expression in expression_list:
            if len(expression) > 1:
                if expression[0] in after_comma_list:
                    result.append(TAC((declare_type, expression[0]['val'], '-', '-')))
                for tac in self.gen_BLOCK_STMT_EXPRESSION_TAC(expression, is_declare_inter=True):
                    result.append(tac)
                # print(self.gen_BLOCK_STMT_EXPRESSION_TAC(expression))
            else:
                result.append(TAC((declare_type, expression[0]['val'], '-', '-')))
                # print((declare_type, expression[0]['val'], '-', '-'))
        # print(expression_list)

        return result

    def gen_PRINT_STMT_TAC(self, token_list):
        result = []
        if len(token_list[2:]) == 1:
            result.append(TAC(('print', token_list[2]['val'], '-', '-')))
        else:
            tac_list, res = self.gen_OP_TAC(token_list[2:-2])
            for tac in tac_list:
                result.append(tac)
            result.append(TAC(('print', res, '-', '-')))
        return result

    def gen_RETURN_STMT_TAC(self, token_list):
        result = []
        # 返回一个表达式的值
        if len(token_list[1:]) > 1:
            tac_list, res = self.gen_OP_TAC(token_list[1:])
            for tac in tac_list:
                result.append(tac)
            result.append(TAC(('return', res, '-', '-')))
        # 返回仅仅一个值
        elif len(token_list[1:]) == 1:
            result.append(TAC(('return', token_list[1]['val'], '-', '-')))
        # 返回空值
        else:
            result.append(TAC(('return', '-', '-', '-')))
        return result

    def gen_IF_STMT_TAC(self, token_list):
        result = []
        start_pos = 2
        if token_list[0]['val'] == 'else':
            start_pos = 3
        tac_list, res = self.gen_OP_TAC(token_list[start_pos:-2])
        for tac in tac_list:
            result.append(tac)
        result.append(TAC(('!=', res, 'True', 0)))
        # gl.global_if_goto_label = gl.global_label_cnt
        # result.append(TAC(('!=', res, 'True', 0)))
        return result

    def gen_WHILE_STMT_TAC(self, token_list):
        result = []
        gl.global_while_label_stack.append(gl.global_label_cnt)
        tac_list, res = self.gen_OP_TAC(token_list[2:-2])
        for tac in tac_list:
            result.append(tac)
        result.append(TAC(('!=', res, 'True', 0)))
        return result

    def gen_FOR_STMT_TAC(self, token_list):
        result = []
        # gl.global_for_label_stack.append(gl.global_label_cnt)
        semicolon_index = []  # 分号下标
        for i in range(len(token_list)):
            if token_list[i]['val'] == ';':
                semicolon_index.append(i)
        declare_token_list = token_list[2:semicolon_index[0] + 1]
        judge_token_list = token_list[semicolon_index[0] + 1:semicolon_index[1]]
        operator_token_list = token_list[semicolon_index[1] + 1:-2]
        if len(declare_token_list) > 4:
            # 变量声明 int i = 0;这段变量声明的代码长度至少为4
            tac_list1 = self.gen_DECLARE_INTER_TAC(declare_token_list)
        else:
            tac_list1 = self.gen_BLOCK_STMT_EXPRESSION_TAC(declare_token_list)
        gl.global_for_label_stack.append(gl.global_label_cnt)
        tac_list2, res2 = self.gen_OP_TAC(judge_token_list)
        # tac_list3 = self.gen_BLOCK_STMT_EXPRESSION_TAC(operator_token_list)
        # for tac in tac_list3:
        #     print(tac)
        gl.global_for_operator_stack.append(operator_token_list)
        # print(tac_list1)
        for tac in tac_list1 + tac_list2:
            result.append(tac)
        result.append(TAC(('!=', res2, 'True', 0)))
        return result

    def gen_TAC(self):
        if self.type == 'BLOCK_STMT_EXPRESSION_START':
            return self.gen_BLOCK_STMT_EXPRESSION_TAC(self.token_list)
        if self.type == 'DECLARE_INTER_START':
            return self.gen_DECLARE_INTER_TAC(self.token_list)
        if self.type == 'PRINT_STMT_START':
            return self.gen_PRINT_STMT_TAC(self.token_list)
        if self.type == 'RETURN_STMT_START':
            return self.gen_RETURN_STMT_TAC(self.token_list)
        if self.type == 'IF_STMT_START':
            return self.gen_IF_STMT_TAC(self.token_list)
        if self.type == 'WHILE_STMT_START':
            return self.gen_WHILE_STMT_TAC(self.token_list)
        if self.type == 'FOR_STMT_START':
            return self.gen_FOR_STMT_TAC(self.token_list)
        # return self.token_list
        return []


class Semantic:

    def __init__(self, lexer_config_file_path, semantic_config_file_path, main_file_path, result_file_path):
        line_list = []
        each_line = []

        lexer = Lexer(config_file_path=lexer_config_file_path,
                      main_file_path=main_file_path)

        is_for_stmt = False
        for token in lexer.token:
            each_line.append(token)
            if token['val'] == 'for':
                is_for_stmt = True
            if is_for_stmt:
                if token['val'] == '{' or token['val'] == '}':
                    line_list.append(each_line)
                    each_line = []
                    is_for_stmt = False
            else:
                if token['val'] == ';' or token['val'] == '{' or token['val'] == '}':
                    line_list.append(each_line)
                    each_line = []

        # 条件分支语句列表
        branch_list = ['if', 'else', 'while', 'for']

        branch_state_stack = [line_list[0][0]['val']]
        # print(branch_state_stack)

        tac_list = []
        for line in line_list:
            # print(line)
            gen_tac = GenTAC(parser_config_file_path=semantic_config_file_path,
                             token_list=line)
            gen_tac_list = gen_tac.gen_TAC()
            # tac_num = len(gen_tac_list)
            for tac in gen_tac_list:
                tac_list.append(tac)
            if line[0]['val'] in branch_list:
                if line[0]['val'] == 'if':
                    branch_state_stack.append('if')
                    gl.global_if_goto_label_stack.append(gl.global_label_cnt - 1)
                elif line[0]['val'] == 'else':
                    if line[1]['val'] == 'if':
                        branch_state_stack.append('elif')
                        gl.global_if_goto_label_stack.append(gl.global_label_cnt - 1)
                    else:
                        branch_state_stack.append('else')
                elif line[0]['val'] == 'for':
                    branch_state_stack.append('for')

                elif line[0]['val'] == 'while':
                    branch_state_stack.append('while')

            elif line[0]['val'] == '}':
                if branch_state_stack[-1] == 'if':
                    branch_state_stack.pop(-1)
                    tac_list[gl.global_if_goto_label_stack[-1]].tac_tuple[3] = gl.global_label_cnt + 1
                    gl.global_if_goto_label_stack.pop(-1)
                    gl.global_goto_label_stack.append([gl.global_label_cnt])
                    tac_list.append(TAC(('goto', '-', '-', gl.global_label_cnt + 1)))  # 若没有else语句则默认跳转下一条语句

                elif branch_state_stack[-1] == 'elif':
                    branch_state_stack.pop(-1)
                    tac_list[gl.global_if_goto_label_stack[-1]].tac_tuple[3] = gl.global_label_cnt + 1
                    gl.global_if_goto_label_stack.pop(-1)
                    gl.global_goto_label_stack[-1].append(gl.global_label_cnt)
                    tac_list.append(TAC(('goto', '-', '-', gl.global_label_cnt + 1)))  # 若没有else语句则默认跳转下一条语句

                elif branch_state_stack[-1] == 'else':
                    branch_state_stack.pop(-1)
                    for label in gl.global_goto_label_stack[-1]:
                        tac_list[label].tac_tuple[3] = gl.global_label_cnt
                    gl.global_goto_label_stack.pop(-1)

                elif branch_state_stack[-1] == 'while':
                    branch_state_stack.pop(-1)
                    tac_list[gl.global_while_label_stack[-1] + 1].tac_tuple[3] = gl.global_label_cnt + 1
                    tac_list.append(TAC(('goto', '-', '-', gl.global_while_label_stack[-1])))
                    gl.global_while_label_stack.pop(-1)

                elif branch_state_stack[-1] == 'for':
                    branch_state_stack.pop(-1)
                    # tac_list += gl.global_for_operator_stack[-1]
                    tac_list += gen_tac.gen_BLOCK_STMT_EXPRESSION_TAC(gl.global_for_operator_stack[-1])
                    gl.global_for_operator_stack.pop(-1)
                    tac_list[gl.global_for_label_stack[-1] + 1].tac_tuple[3] = gl.global_label_cnt + 1
                    tac_list.append(TAC(('goto', '-', '-', gl.global_for_label_stack[-1])))
                    gl.global_for_label_stack.pop(-1)

                else:
                    tac_list.append(TAC(('end', '-', '-', '-')))

        self.tac_list = tac_list

        semantic_result = open(result_file_path, 'w+')
        for tac in tac_list:
            print(tac, file=semantic_result)
        semantic_result.close()

# s = Semantic(lexer_config_file_path='E:\PC_Python\Compiler\wzh\config\lexer_config.json',
#              semantic_config_file_path='semantic_config.json',
#              main_file_path='E:\PC_Python\Compiler\wzh\main_file\main2.wzh', result_file_path='semantic_result')

# print(tac)
# print(branch_stack)
# print(gl.global_branch_list)
# print(gen_tac.gen_TAC())
# gen_tac = GenTAC(parser_config_file_path='semantic_config.json',
#                  token_list=lexer.token)
# print(gen_tac.type)
# for tac in gen_tac.gen_DECLARE_INTER_TAC():
#     print(tac)
# gen_tac.gen_DECLARE_INTER_TAC()
# gen_tac.gen_BLOCK_STMT_EXPRESSION_TAC()
# print(gen_tac.match_type())
# for start_token in type_list:
# print(match_parser.is_matched)

# print(match_parser.is_matched)
# print(gen_tac.match_type())
# print(match_parser.is_matched)

# print(match_parser2.is_matched)
# parser = Parser(lexer_config_file_path='E:\PC_Python\Compiler\wzh\config\lexer_config.json',
#                 parser_config_file_path='semantic_config.json',
#                 main_file_path='E:\PC_Python\Compiler\wzh\main_file\main5.wzh',
#                 start_of_grammar="DECLARE_INIT_START",
#                 result_file_path='semantic_result')

# print(parser.is_parser_error)
# print(match_parser.is_matched)
