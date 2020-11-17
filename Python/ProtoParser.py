
PCT_None = "none"
PCT_Syntax = "syntax"
PCT_Package = "package"
PCT_Import = "import"
PCT_CommonLine = "//"

PCT_CommonBegin = "/*"
PCT_CommonEnd = "*/"

PCT_EndBlock = "}"
PCT_BeginEnum = "enum"
PCT_BeginMessage = "message"
PCT_Define = "def"


class ProtoCode:
    def __init__(self):
        self.type = PCT_None
        self.line_num = -1
        self.text = ""
        self.common = ""
        self.tokens = []

    def print(self):
        print(self.type + " " + str(self.tokens) + " " + self.common)


class ProtoParser:
    def __init__(self):
        self.lines = []
        self.code_list = []

    def load_file(self, filename):
        self.lines = open(filename, encoding='utf-8').readlines()
        #解决{}问题
        for i in range(len(self.lines)):
            line = self.lines[i].split("{}")
            if len(line)>1:
                self.lines[i] = line[0]+"{"
                self.lines.insert(i+1,"}"+line[1])

        self.parse_lines()

        for c in self.code_list:
            c.print()

    def parse_lines(self):
        line_num = 0
        for l in self.lines:
            c = ProtoParser.parse(l, line_num)
            line_num += 1
            if c.type != PCT_None:
                self.code_list.append(c)

    @staticmethod
    def parse(text, line_num):
        text = text.replace("\t", " ").strip()

        c = ProtoCode()
        c.line_num = line_num
        c.text = text

        if PCT_Syntax in text:
            c.type = PCT_Syntax
            ProtoParser.parse_syntax(text, c)
        elif PCT_Package in text:
            c.type = PCT_Package
            ProtoParser.parse_struct(text, c)
        elif PCT_Import in text:
            c.type = PCT_Import
            ProtoParser.parse_struct(text, c)
        elif PCT_CommonLine in text.strip()[0:2]:
            c.type = PCT_CommonLine
            c.common = text
        elif PCT_CommonBegin in text.strip()[0:2]:
            c.type = PCT_CommonLine
            c.common = text
        elif PCT_BeginEnum in text.strip()[0:len(PCT_BeginEnum)]:
            c.type = PCT_BeginEnum
            ProtoParser.parse_struct(text, c)
        elif PCT_BeginMessage in text.strip()[0:len(PCT_BeginMessage)]:
            c.type = PCT_BeginMessage
            ProtoParser.parse_struct(text, c)
        elif PCT_EndBlock in text.strip()[0:1]:
            c.type = PCT_EndBlock
        elif text.find("=") != -1:
            c.type = PCT_Define
            ProtoParser.parse_define(text, c)
        else:
            c.type = PCT_None

        return c

    @staticmethod
    def pop_line_common(text, code):
        it = text.strip().find("//")
        if it == -1:
            return text
        else:
            code.common = text[it:]
            return text[0:it]

    @staticmethod
    def parse_syntax(text, code):
        ll = ProtoParser.pop_line_common(text, code).strip().split("=")
        for l in ll:
            code.tokens.append(l.strip())

    @staticmethod
    def parse_define(text, code):
        ll = ProtoParser.pop_line_common(text, code).strip().split("=")

        for line in ll:
            line = line.strip()
            if len(line) > 0:
                token_list = line.split(" ")
                for token in token_list:
                    token = token.strip()
                    if len(token) > 0:
                        if token[-1] == ';':
                            token = token[0:-1]

                        sub_token = token.split(",")
                        for st in sub_token:
                            if len(st) > 0:
                                code.tokens.append(st)

    @staticmethod
    def parse_struct(text, code):
        ll = ProtoParser.pop_line_common(text, code).strip().split(" ")

        last_token = ll[-1].strip()
        if last_token != "{" and last_token[-1] == "{":   # message ABC{
            ll[-1] = ll[-1][0:-1]
            ll.append("{")

        for token in ll:
            token = token.strip()
            if len(token) > 0:
                token = token.replace(';', '')
                code.tokens.append(token)


