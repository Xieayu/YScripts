#
# Proto to bp.
#
#

import os, sys
from ProtoParser import *


buildin_type = (
    "int", "int16", "int32", "int64",
    "uint", "uint16", "uint32", "uint64",
    "float", "float32", "float64",
    "double",
    "string",
    "bool",
    "bytes",
)


buildin_type_convert = {
    "int16": "int",
    "int32": "int",
    "int64": "int64",

    "uint": "int",
    "uint16": "int",
    "uint32": "int",
    "uint64": "uint64",

    "float": "float",
    "float32": "float",
    "float64": "double",

    "double": "double",
    "string": "FString",

    "bool": "bool",
    "bytes": "std::string",


}

buildin_type_close_uproperty = (
    "int64", "uint64", "double", "bytes", "std::string", "CSMsgID"
)

bp_h_file_header = '''/*
Proto buf => BP

*/
#pragma once

\n'''


def cmp_message_rc(m1):
    return m1.ref_count


def fuck_pb_name(name):
    if name == "Character":
        return "Character_PB"
    elif name == "Player":
        return "Player_PB"
    elif name == "NULL":
        return "NULL_PB"

    return name


def unfuck_pb_name(name):
    if name == "Switch":
        name = "Switch_"

    if name == "Class":
        name = "Class_"

    if name == "TypeId":
        name = "TypeId_"

    if name.endswith("_PB"):
        return name[0:-3]
    else:
        return name


def fix_std_namespace(key):
    if key == "string":
        return "::std::string"
    return key


class BPEnumMember:
    def __init__(self, name, common):
        self.name = name
        self.common = common
        self.export_bp = True

    def out(self):
        t = ""
        t += "\t" + self.name

        if self.export_bp:
            t += ' UMETA(DisplayName="' + self.name + '"),'
        else:
            t += ","

        if len(self.common) > 0:
            t += "\t" + self.common

        t += "\n"
        return t


class BPEnum:
    def __init__(self):
        self.name = ""
        self.common = ""
        self.members = []
        self.export_bp = True

    def out(self):
        self.export_bp = self.name != "ECSMsgID"

        t = ""
        if len(self.common) > 0:
            t += self.common + "\n"

        if self.export_bp:
            t += "UENUM(BlueprintType)\n"

        if self.export_bp:
            t += "enum class " + self.name + ": uint8 {\n"
        else:
            t += "enum class " + self.name + ": uint32 {\n"

        for m in self.members:
                t += m.out()

        t += "};\n\n"
        return t


class BPDef:
    def __init__(self, encode, name, type_name, common, owner_msg, is_export_bp=True):
        self.type = type_name
        self.origin_type = self.type
        self.name = name
        self.common = common
        self.is_export_bp = is_export_bp
        self.encode = encode
        self.ref_msg = None
        self.owner_msg = owner_msg
        
        # last run.
        self.__on_init__()

    def __on_init__(self):
        pass

    def add_ref_msg_count(self):
        pass

    def out(self):
        t = ""
        if self.is_export_bp:
            t += "\tUPROPERTY(EditAnywhere, BlueprintReadWrite)\n"

        t += "\t" + self.type + " " + self.name + ";"
        if len(self.common) > 0:
            t += "\t" + self.common
        t += "\n"
        return t

    def out_pb_msg(self):
        pass

    def out_msg_pb(self):
        pass


class BPBuildinDef(BPDef):
    def __on_init__(self):
        self.type = buildin_type_convert[self.type]

    def out_pb_msg(self):
        pb_name = unfuck_pb_name(self.name).lower()
       

        if self.type == "FString":
            t = "\tmsg." + self.name + "=UTF8_TO_TCHAR(pb->" + pb_name + "().c_str());\n"
        else:
            t = "\tmsg." + self.name + "=pb->" + pb_name + "();\n"
        return t

    def out_msg_pb(self):
        pb_name = unfuck_pb_name(self.name).lower()
        if self.type == "FString":
            t = "\tpb->set_" + pb_name + "(TCHAR_TO_UTF8(*msg." + self.name + "));\n"
        else:
            t = "\tpb->set_" + pb_name + "(msg." + self.name + ");\n"
        return t


class BPEnumDef(BPDef):
    def __on_init__(self):
        self.type = "E" + self.type

    def out_pb_msg(self):
        pb_name = unfuck_pb_name(self.name).lower()
        t = "\tmsg." + self.name + "=(" + self.type + ")pb->" + pb_name + "();\n"
        return t

    def out_msg_pb(self):
        pb_name = unfuck_pb_name(self.name).lower()
        pb_type = unfuck_pb_name(self.type)[1:]
        t = "\tpb->set_" + pb_name + "((::msg::" + pb_type + ")msg." + self.name + ");\n"
        return t


class BPMsgDef(BPDef):
    def __on_init__(self):
        self.type = "F" + self.type
        msg = self.encode.find_msg(self.type)
        # may be outside
        if msg is not None:
            msg.ref_count += 1

    def add_ref_msg_count(self):
        tm = self.encode.find_msg(self.type)
        if tm is not None:
            tm.ref_count += self.owner_msg.ref_count

    def out_pb_msg(self):
        pb_name = unfuck_pb_name(self.name).lower()
        t = "\t_ConvertPbTo" + self.type + "(msg." + self.name + ", " + "&pb->" + pb_name + "());\n"
        return t

    def out_msg_pb(self):
        pb_name = unfuck_pb_name(self.name).lower()
        t = "\t_Convert" + self.type + "ToPb(pb->mutable_" + pb_name + "(), msg." + self.name + ");\n"
        return t


class BPArrayDef(BPDef):
    def __on_init__(self):
        self.array_type = None
        if self.type.startswith("TArray<"):
            tt = self.type.replace("TArray<", "").replace(">", "")
            self.array_type = self.encode.create_msg_def(self.name, tt.strip(), "", self.owner_msg)
            self.type = "TArray<" + self.array_type.type + ">"
            self.is_export_bp = self.array_type.is_export_bp
        else:
            print("Invalid array define: Name:" + self.name + " Type:" + self.type)

    def add_ref_msg_count(self):
        self.array_type.add_ref_msg_count()

    def out_pb_msg(self):
        pb_name = unfuck_pb_name(self.name).lower()

        t = "\tfor (int i = 0; i < pb->" + pb_name + "().size(); i++) {\n"
        t += "\t\tauto &a = pb->" + pb_name + "().Get(i);\n"
        t += "\t\t" + self.array_type.type + " tmp;\n"
        t += "\t" + self.array_type.out_pb_msg().replace(
            "msg." + self.name, "tmp").replace(
            "pb->" + pb_name + "()", "a")
        t += "\t\tmsg." + self.name + ".Add(tmp);\n"
        t += "\t}\n"
        return t

    def out_msg_pb(self):
        _template='''
    for (auto& it : msg.{var_name}) {
        auto p = pb->mutable_{pb_name}();
        {origin_vname} v;
        {convert}
        {add}
    }
'''
        pb_name = unfuck_pb_name(self.name).lower()
        if isinstance(self.array_type, BPMsgDef):
            origin_vname = "::msg::" + self.array_type.origin_type
        else:
            origin_vname = self.array_type.origin_type
        origin_vname = fix_std_namespace(origin_vname)

        t = _template.\
            replace("{origin_vname}", origin_vname).\
            replace("{pb_name}", pb_name).\
            replace("{var_name}", self.name).\
            replace("{convert}", self.array_type.out_msg_pb().\
                    replace("\t", "").\
                    replace("\n", "").\
                    replace("pb->mutable_" + pb_name + "()", "&v").\
                    replace("msg." + self.name, "*it")).\
            replace("{add}", "pb->mutable_" + pb_name + "()->add_" + self.array_type.name + "(v);")

        return t


class BPMapDef(BPDef):
    def __on_init__(self):
        self.key_type = None
        self.value_type = None
        if self.type.startswith("TMap<"):
            tt = self.type.replace("TMap<", "").replace(">", "").split(",")
            self.key_type = self.encode.create_msg_def("key", tt[0].strip(), "key", self.owner_msg)
            self.value_type = self.encode.create_msg_def("value", tt[1].strip(), "value", self.owner_msg)
            self.type = "TMap<" + self.key_type.type + ", " + self.value_type.type + ">"
            self.is_export_bp = self.key_type.is_export_bp and self.value_type.is_export_bp
        else:
            print("Invalid map define: Name:" + self.name + " Type:" + self.type)

    def add_ref_msg_count(self):
        self.key_type.add_ref_msg_count()
        self.value_type.add_ref_msg_count()

    def out_pb_msg(self):
        _template = '''
    for (auto it = pb->{pb_name}().begin(); it != pb->{pb_name}().end(); it++) {
        {value_type} tmp_value;
        {value_convert}
        {key_type} tmp_key;
        {key_convert}
        msg.{var_name}.Add(tmp_key, tmp_value);
    }
'''
        pb_name = unfuck_pb_name(self.name).lower()
        t = _template.replace("{pb_name}", pb_name).\
            replace("{value_type}", self.value_type.type).\
            replace("{value_convert}",
                    self.value_type.out_pb_msg().
                    replace("\t", "").
                    replace("\n", "").
                    replace("msg.value", "tmp_value").
                    replace("pb->value()", "it->second")).\
            replace("{key_type}", self.key_type.type).\
            replace("{key_convert}", self.key_type.out_pb_msg().
                    replace("\t", "").
                    replace("\n", "").
                    replace("msg.key", "tmp_key").
                    replace("pb->key()", "it->first")).\
            replace("{var_name}", self.name)

        return t

    def out_msg_pb(self):
        _template = """
    for (auto &it : msg.{var_name}) {
        {origin_value_type} tmp_value;
        {value_convert}
        {origin_key_type} tmp_key;
        {key_convert}
        pb->mutable_{pb_name}()->insert({({origin_key_type})tmp_key, tmp_value});
    }
"""
        pb_name = unfuck_pb_name(self.name).lower()
        if isinstance(self.value_type, BPMsgDef):
            pb_vname = "::msg::" + unfuck_pb_name(self.value_type.type[1:])
            origin_vname = "::msg::" + self.value_type.origin_type
        else:
            pb_vname = unfuck_pb_name(self.value_type.type)
            origin_vname = self.value_type.origin_type

        origin_kname = fix_std_namespace(self.key_type.origin_type)
        origin_vname = fix_std_namespace(origin_vname)

        t = _template.replace("{pb_name}", pb_name).\
            replace("{value_type}", pb_vname).\
            replace("{value_convert}",
                    self.value_type.out_msg_pb().
                    replace("\t", "").
                    replace("\n", "").
                    replace("pb->set_value", "tmp_value=").
                    replace("pb->value()", "it->second").
                    replace("pb->mutable_value()", "&tmp_value").
                    replace("msg.value", "it.Value")).\
            replace("{key_type}", self.key_type.type).\
            replace("{key_convert}", self.key_type.out_msg_pb().
                    replace("\t", "").
                    replace("\n", "").
                    replace("pb->set_key", "tmp_key=").
                    replace("msg.key", "msg." + self.name).
                    replace("msg." + self.name, "it.Key")).\
            replace("{var_name}", self.name).\
            replace("{origin_key_type}", origin_kname).\
            replace("{origin_value_type}", origin_vname)

        return t


class BPMsg:
    def __init__(self):
        self.name = ""
        self.common = ""
        self.members = []
        self.api = ""
        self.export_bp = True
        self.ref_count = 0

    def out(self):
        t = ""
        if self.export_bp:
            t += "USTRUCT(BlueprintType)\n"

        t += "struct " + self.api + " " + self.name + " {\n"
        t += '\tGENERATED_BODY()\n\n'
        for m in self.members:
            t += m.out()
            t += "\n"
        t += "};\n"
        t += self.out_pb_msg()
        #t += self.out_msg_pb()
        t += "\n\n"
        return t

    def out_pb_msg(self):
        t = ""
        pb_name = unfuck_pb_name(self.name[1:])
        t += "static void _ConvertPbTo" + self.name + "(" + self.name + " &msg, " + "const msg::" + pb_name + " *pb) {\n"
        for mb in self.members:
            t += mb.out_pb_msg()
        t += "}\n"
        return t

    def out_msg_pb(self):
        t = ""
        pb_name = unfuck_pb_name(self.name[1:])
        t += "static void _Convert" + self.name + "ToPb(msg::" + pb_name + " *pb, " + self.name + " &msg) {\n"
        for mb in self.members:
            t += mb.out_msg_pb()
        t += "}\n"
        return t


class BPImport:
    def __init__(self, import_name, include_proto=True, only_include_proto=False):
        self.import_name = import_name
        self.include_proto = include_proto
        self.only_include_proto = only_include_proto

    def out(self):
        t = ""
        if self.only_include_proto is False:
            t += '#include ' + self.import_name + '\n'

        if self.include_proto:
            filename = self.import_name.replace(".h", "").replace('"', "")
            t += '#include "' + filename + '.pb.h"' + "\n"
        else:
            t += '#include ' + self.import_name + "\n"

        return t


class BPEncode:
    def __init__(self, api_name=""):
        self.text = ""
        self.code_stack_top = 0
        self.code_list = []
        self.enum_list = []
        self.message_list = []
        self.import_list = []
        self.encode_list = []
        self.current_block = None
        self.self_filename = ""
        self.api_name = api_name

    def pop_code(self):
        if self.code_stack_top >= len(self.code_list):
            return None

        c = self.code_list[self.code_stack_top]
        self.code_stack_top += 1
        return c

    def create_enum_member(self, n, c):
        n = fuck_pb_name(n)
        return BPEnumMember(n, c)

    def create_msg_def(self, n, t, c, om):
        n = fuck_pb_name(n)
        t = fuck_pb_name(t)

        is_export_bp = t not in buildin_type_close_uproperty

        if self.is_type_in_enum(t):
            return BPEnumDef(self, n, t, c, om, is_export_bp)
        elif t.startswith("TArray<"):
            return BPArrayDef(self, n, t, c, om, is_export_bp)
        elif t.startswith("TMap<"):
            return BPMapDef(self, n, t, c, om, is_export_bp)
        elif t in buildin_type:
            return BPBuildinDef(self, n, t, c, om, is_export_bp)
        else:
            return BPMsgDef(self, n, t, c, om, is_export_bp)

    def find_enum(self, n):
        for e in self.enum_list:
            if e.name == n:
                return e
        return None

    def find_msg(self, n):
        for m in self.message_list:
            if m.name == n:
                return m
        return None

    def is_type_in_enum(self, t):
        for b in self.enum_list:
            if t == b.name[1:]:
                return True

        for e in self.encode_list:
            if e.is_type_in_enum(t):
                return True

        return False

    def is_type_in_message(self, t):
        for b in self.message_list:
            if b.name == t:
                return True

        for e in self.encode_list:
            if e.is_type_in_message(t):
                return True

        return False

    def reorder_message(self):
        for m in self.message_list:
            for mb in m.members:
                mb.add_ref_msg_count()

        self.message_list = sorted(self.message_list, key=cmp_message_rc, reverse=True)

    def export_import(self):
        for i in self.import_list:
            if i != self.import_list[0] and i != self.import_list[1]:
                proto_filename = i.import_name.replace('"', '')
                out_filename = i.import_name.replace('.proto', '.h').replace('"', "")

                pp = ProtoParser()
                pp.load_file(proto_filename)

                bp = BPEncode()
                bp.export_file(out_filename, pp.code_list)
                self.encode_list.append(bp)

        # fix proto to .h
        for i in self.import_list:
            i.import_name = i.import_name.replace(".proto", ".h")

        # append generated.h
        filename = self.self_filename.replace(".h", ".generated.h")
        self.import_list.append(BPImport('"' + filename + '"', False, True))

    def encode(self, code_list):
        if self.parse(code_list) is False:
            return False

        # reorder message structures.
        self.reorder_message()
        self.reorder_message()

        # output text.
        self.text = bp_h_file_header
        for i in self.import_list:
            self.text += i.out()

        self.text += "\n\n"

        for b in self.enum_list:
            self.text += b.out()

        for b in self.message_list:
            self.text += b.out()

        # generate convert method.
        # self.text += self.generate_convert_method()

        return self.text

    def export_file(self, filename, code_list):
        """

        :param filename:
        :param code_list:
        :return:
        """
        self.self_filename = filename
        self.import_list.append(BPImport('"CoreMinimal.h"', False, True))
        self.import_list.append(BPImport('"' + self.self_filename + '"', True, True))

        self.encode(code_list)

        f = open('./Code/'+filename, "w", encoding='utf-8')
        f.write(self.text)
        f.close()

    def parse_enum(self):
        """

        :return:
        """
        self.code_stack_top = 0
        while True:
            c = self.pop_code()
            if c is None:
                break

            if c.type == PCT_BeginEnum:
                self.current_block = BPEnum()
                self.current_block.common = c.common
                self.current_block.name = "E" + fuck_pb_name(c.tokens[1])
                self.enum_list.append(self.current_block)

    def parse_msg(self):
        self.code_stack_top = 0
        while True:
            c = self.pop_code()
            if c is None:
                break

            if c.type == PCT_BeginMessage:
                self.current_block = BPMsg()
                self.current_block.common = c.common
                self.current_block.name = "F" + fuck_pb_name(c.tokens[1])
                self.message_list.append(self.current_block)

    def parse_import(self):
        self.code_stack_top = 0
        while True:
            c = self.pop_code()
            if c is None:
                break

            elif c.type == PCT_Import:
                self.import_list.append(BPImport(c.tokens[1]))

    def parse(self, code_list=[]):
        self.code_list = code_list

        self.parse_import()
        self.export_import()

        self.parse_enum()
        self.parse_msg()

        self.current_block = None
        self.code_stack_top = 0
        while True:
            c = self.pop_code()
            if c is None:
                break

            if c.type == PCT_BeginEnum:
                if self.current_block is not None:
                    print("Error begin block line num:" + str(c.line_num)+ self.self_filename)
                    return False

                name = "E" + fuck_pb_name(c.tokens[1])
                self.current_block = self.find_enum(name)
                if self.current_block is None:
                    print("Error invalid block:", name)

            if c.type == PCT_BeginMessage:
                if self.current_block is not None:
                    print("Error begin block line num:" + str(c.line_num) + self.self_filename)
                    return False

                name = "F" + fuck_pb_name(c.tokens[1])
                self.current_block = self.find_msg(name)
                if self.current_block is None:
                    print("Error invalid block:", name)

            elif c.type == PCT_EndBlock:
                if self.current_block is None:
                    print("Error end block line num:" + str(c.line_num)+ self.self_filename)
                    return False

                self.current_block = None

            elif c.type == PCT_Define:
                if self.current_block is None:
                    print("Error define line num:" + str(c.line_num)+ self.self_filename)
                    return False

                if isinstance(self.current_block, BPEnum):
                    self.current_block.members.append(
                        self.create_enum_member(c.tokens[0], c.common))
                else:
                    if c.tokens[0] == "repeated":
                        msg_def = self.create_msg_def(c.tokens[2],
                                                      "TArray<" + c.tokens[1] + ">",
                                                      c.common,
                                                      self.current_block)
                        self.current_block.members.append(msg_def)

                    elif c.tokens[0].startswith("map<"):
                        first = c.tokens[0].replace("map", "").replace("<", "")
                        second = c.tokens[1].replace(">", "")
                        msg_def = self.create_msg_def(c.tokens[2],
                                                      "TMap<" + first + ", " + second + ">",
                                                      c.common,
                                                      self.current_block)
                        self.current_block.members.append(msg_def)

                    else:
                        msg_def = self.create_msg_def(c.tokens[1],
                                                      c.tokens[0],
                                                      c.common,
                                                      self.current_block)
                        self.current_block.members.append(msg_def)

        return True


def main():
    if len(sys.argv) < 3:
        print("Usage: ProtoToBp csxxx.proto csxxx.h [API Name]( from ./ to ./Code)")
        return

    pp = ProtoParser()
    pp.load_file(sys.argv[1])

    bp = BPEncode()
    bp.export_file(sys.argv[2], pp.code_list)


if __name__ == "__main__":
    main()


#pyinstaller  -F ProtoToBp.py