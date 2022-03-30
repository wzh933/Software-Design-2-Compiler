from src.compiler.lexer.Lexer import *
from src.compiler.parser.ActionGoto import *
import global_var as gl


class Parser:
    def __init__(self, lexer_config_file_path, parser_config_file_path, main_file_path, result_file_path,
                 start_of_grammar):
        gl.global_closure_num = 0
        self.ag = ActionGoto(file_path=parser_config_file_path, start_of_grammar=start_of_grammar)
        lexer = Lexer(config_file_path=lexer_config_file_path, main_file_path=main_file_path)
        # 输入串
        self.input_token_list = []
        self.input_val_line_list = []
        self.error_line = 0
        self.error_token = None
        # 存储分析表的结果文件
        self.result_file = result_file_path
        for token in lexer.token:
            self.input_val_line_list.append({'val': token['val'], 'line': token['line']})
            if token['type'] == 'ID' or token['type'] == 'CONSTANT' or token['type'] == 'ERROR':
                self.input_token_list.append(token['type'])
            else:
                self.input_token_list.append(token['val'])
        self.input_token_list.append('#')
        self.data = open(self.result_file, 'w+')
        self.is_parser_error = not self.parser()
        # if lexer.is_lexer_error:
        #     print('No!', file=self.data)
        #     print('出现了词法错误,出错在第{}行,出错词为"{}"'.format(self.error_line, self.input_val_line_list[0]['val']))
        if self.is_parser_error:
            error_keys = []
            for key in self.ag.action_list[self.error_state].keys():
                if key != '#':
                    error_keys.append(key)
            print('No!', file=self.data)
            print('出现了语法错误,出错在第{}行,出错词为"{}",出错词后应为{}'.format(self.error_line, self.error_token, error_keys))
        else:
            print('Yes!')
            print('Yes!', file=self.data)
        self.data.close()

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
            # input_token0 = self.input_token0_list[0]
            input_token = self.input_token_list[0]
            # print(state_stack, token_stack, self.input_token_list, file=self.data)
            print("状态栈:{}   符号栈:{}    输入串:{}".format(state_stack, token_stack, self.input_token_list), file=self.data)
            # 出错
            if self.is_error(state, input_token):
                self.error_state = state
                return False

            action = self.ag.action_list[state][input_token]
            # print(action)
            # print(type(action))

            # S{action}，移进
            if type(action) == int:
                state_stack.append(action)
                token_stack.append(input_token)
                self.input_token_list.pop(0)

                # 出错词
                self.error_token = self.input_val_line_list[0]['val']
                # 出错行
                self.error_line = self.input_val_line_list[0]['line']

                self.input_val_line_list.pop(0)


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
