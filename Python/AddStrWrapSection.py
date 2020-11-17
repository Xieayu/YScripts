# encoding:utf-8
import re
import sys

def insertDef2Files(filePath,startAdd,endAdd, searchHead):
    with open(filePath,"r") as f:
        lines=f.readlines()
        newLines = []
        tmpSctionLines = []
        for line in lines:
            bSction = re.search(searchHead, line)

            if bSction:
                tmpSctionLines.insert(len(tmpSctionLines), line)
            else:
                # 如果是非包裹区间内，判断是否有要插入都区间，有则插入
                if len(tmpSctionLines) > 0:
                    newLines.insert(len(newLines), startAdd)

                    for bl in tmpSctionLines:
                        newLines.insert(len(newLines), bl)

                    newLines.insert(len(newLines), endAdd)
                    # tmpSctionLines.clear()
                    tmpSctionLines = []

                newLines.insert(len(newLines), line)

        #写入文件
        with open(filePath,"wt") as saveFile:
            saveFile.writelines(newLines)

def main():
    filePath = ""
    startAdd = "#ifndef __VAX11__\n"
    endAdd = "#endif\n"
    searchHead = "#pragma warning*"

    if len(sys.argv) >= 2:
        filePath = str(sys.argv[1])

    if len(sys.argv) >= 3:
        startAdd = str(sys.argv[2])
        startAdd = eval(repr(startAdd).replace('\\\\n', '\\n'))

    if len(sys.argv) >= 4:
        endAdd = str(sys.argv[3])
        endAdd = eval(repr(endAdd).replace('\\\\n', '\\n'))

    if len(sys.argv) >= 5:
        searchHead = str(sys.argv[4])

    insertDef2Files(filePath, startAdd, endAdd, searchHead)


if __name__ == "__main__":
     main()
