import json
import regex


class Lexer:
    def __init__(self, config_file_path, main_file_path):
        # 读取配置文件以进行正则匹配
        self.config_file_path = config_file_path
        self.main_file_path = main_file_path
        self.config_dict = self.read_config()
        self.key_word_list = self.config_dict['KEY_WORD']
        self.op_list = self.config_dict['OP']
        self.symbol_list = self.config_dict['SYMBOL']
        self.constant_pattern = "^" + self.config_dict['CONSTANT']
        self.id_pattern = "^" + self.config_dict['ID']
        # 判断是否为词法错误
        self.is_lexer_error = False
        # 获得token表
        self.token = self.get_token()

    # 读取配置文件
    def read_config(self):
        with open(self.config_file_path) as json_file:
            config = json.load(json_file)
        return config

    # 判断token类型
    def get_token_type(self, token):
        if token in self.key_word_list:
            return "KEYWORD"
        if token in self.op_list:
            return "OP"
        if token in self.symbol_list:
            return "SYMBOL"
        # 对于正则表达式的匹配，即使匹配上，也要检查是否完全匹配，方法是检查被匹配成功的字符串长度与token长度是否一致
        # 比如拿"ccc?"去匹配ID，匹配结果是True，因为"ccc?"中的前三个字符串与ID匹配，但是类型错误
        if regex.match(self.id_pattern, token) and \
                len(regex.match(self.id_pattern, token).group()) == len(token):
            return "ID"
        if regex.match(self.constant_pattern, token) \
                and len(regex.match(self.constant_pattern, token).group()) == len(token):
            return "CONSTANT"
        return "ERROR"

    def get_token(self):
        # 匹配注释的正则表达式
        note_pattern = regex.compile("//[^\r\n]*|/\*.*?\*/")

        # test = "/* 哈哈哈哈 */"
        # print(note_pattern.match(test))

        main_file = open(self.main_file_path, encoding='utf-8')
        code_list0 = []
        line_num = 0
        for line in main_file.readlines():
            line_num += 1
            code = {'code_val': line.strip(" ").strip("\n"), 'code_line': 0}
            # 去掉单行注释
            if note_pattern.match(line.strip(" ")):
                continue
            code['code_line'] = line_num
            code_list0.append(code)

        # 去掉多行注释
        for i in range(len(code_list0)):
            if code_list0[i]['code_val'] == "/**":
                temp = code_list0[i]['code_val']
                code_list0[i]['code_line'] = 0
                for j in range(i + 1, len(code_list0)):
                    if note_pattern.match(temp):
                        code_list0[j]['code_line'] = 0
                        break
                    temp += code_list0[j]['code_val']
                    code_list0[j]['code_line'] = 0

        code_list = []
        for code in code_list0:
            if code['code_val'] != "" and code['code_line'] != 0:
                code_list.append(code)

        # print(code_list)

        # 停用词表
        stop_list = self.symbol_list
        stop_list.remove(".")
        # stop_list += op_list

        # 终结符列表
        token_list = []
        line_list = []
        for code in code_list:
            token = ""
            # 根据双引号判断是否为字符串常量
            is_string = False
            i = 0
            while i < len(code['code_val']):
                c = code['code_val'][i]
                # 判断是否进入字符串常量状态
                if c == '"':
                    if is_string == False:
                        is_string = True
                    else:
                        is_string = False
                # 如果此时不是字符串常量状态，则正常按照停用词表进行分词
                if is_string == False:
                    # 遇到空格
                    if c == " ":
                        if token != '':
                            token_list.append(token)
                            line_list.append(code['code_line'])
                        token = ""
                    # 确定停顿词
                    elif c in stop_list:
                        if token != '':
                            token_list.append(token)
                            line_list.append(code['code_line'])
                        token_list.append(c)
                        line_list.append(code['code_line'])
                        token = ""
                    # 处理双目运算符
                    elif c in self.op_list and code['code_val'][i + 1] in self.op_list:
                        cc = c + code['code_val'][i + 1]
                        if token != '':
                            token_list.append(token)
                            line_list.append(code['code_line'])
                        token_list.append(cc)
                        line_list.append(code['code_line'])
                        token = ""
                        i += 1
                    # 处理科学计数法的数据表示
                    elif c in self.op_list and code['code_val'][i - 1] == 'E':
                        token += c
                        i += 1
                        continue
                    # 仅仅只有一个运算符却没有被空格分开的公式的情况
                    elif c in self.op_list:
                        if token != '':
                            token_list.append(token)
                            line_list.append(code['code_line'])
                        token_list.append(c)
                        line_list.append(code['code_line'])
                        token = ""
                    else:
                        token += c
                        # 如果一行结束还未遇到停用词，则将识别出的token加入token列表
                        if i == len(code['code_val']) - 1:
                            token_list.append(token)
                            line_list.append(code['code_line'])
                # 如果此时是字符串常量状态，则一直向token中加入新字符
                else:
                    token += c
                    # 如果一行结束还未遇到‘”’，则将识别出的token加入token列表，其类型为ERROR
                    if i == len(code['code_val']) - 1:
                        token_list.append(token)
                        line_list.append(code['code_line'])
                i = i + 1
        token_dict_list = []
        for i in range(len(token_list)):
            token_dict_list.append(
                {'val': token_list[i], 'type': self.get_token_type(token_list[i]), 'line': line_list[i]})
            if self.get_token_type(token_list[i]) == 'ERROR':
                self.is_lexer_error = True
                self.error_line = line_list[i]
                self.error_token = token_list[i]
                break
        return token_dict_list

# l = Lexer(config_file_path='config.json', main_file_path='E:\PC_Python\Compiler\wzh\main1.wzh')
# for token in l.token:
#     print(token)
