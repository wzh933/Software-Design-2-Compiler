import wzh.config.start_of_grammar as s
from src.compiler.semantic.Semantic import *

main_file_path = 'main_file/main2.wzh'

# 删除先前文件的内容
result_file_list = ['result/lexer_result', 'result/parser_result', 'result/semantic_result']
for result_file in result_file_list:
    file = open(result_file, 'a')
    file.seek(0)
    file.truncate()
    file.close()
# file1 = open('result/lexer_result', 'a')
# file2 = open('result/parser_result', 'a')
# file3 = open('result/semantic_result', 'a')
# file1.seek(0)
# file2.seek(0)
# file3.seek(0)
# file1.truncate()
# file2.truncate()
# file3.truncate()
# file1.close()
# file2.close()
# file3.close()

# 词法分析器
lexer = Lexer(config_file_path='config/lexer_config.json', main_file_path=main_file_path)
lexer_data = open('result/lexer_result', 'w+')
for token in lexer.token:
    print(token, file=lexer_data)
if lexer.is_lexer_error:
    print('No!', file=lexer_data)
else:
    print('Yes!', file=lexer_data)
lexer_data.close()

if lexer.is_lexer_error:
    print('出现了词法错误,出错在第{}行,出错词为"{}"'.format(lexer.error_line, lexer.error_token))
else:
    # 语法分析器
    parser = Parser(lexer_config_file_path='config/lexer_config.json',
                    parser_config_file_path='config/parser_config.json',
                    main_file_path=main_file_path,
                    result_file_path='result/parser_result',
                    start_of_grammar=s.start_of_grammar)
    if not parser.is_parser_error:
        semantic = Semantic(lexer_config_file_path='config/lexer_config.json',
                            semantic_config_file_path='config/semantic_config.json',
                            main_file_path=main_file_path,
                            result_file_path='result/semantic_result')
