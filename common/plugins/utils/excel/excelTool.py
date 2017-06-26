# -*- coding:utf-8 -*-
import os
import xlrd


class ExcelTool:
    """
    简单的封装excel各种操作
    系统要求， windows系统， 安装python2.6以及pywin32-214.win32-py2.6.exe, 以及ms office
    """

    def __init__(self, fileName):
        self.__xlsx = None
        self.fileName = os.path.abspath(fileName)

    def getWorkbook(self, forcedClose=False):
        """
        如果Workbook已经打开需要先关闭后打开
        forcedClose：是否强制关闭，后打开该Workbook
        """
        self.__xlsx = xlrd.open_workbook(self.fileName)
        return True

    def close(self, saveChanges=False):
        """
        关闭excel应用
        """
        self.__xlsx.release_resources()

    def getSheetCount(self):
        """
        获得工作表个数
        """
        return len(self.__xlsx.sheets())

    def getSheetNameByIndex(self, index):
        """
        获得excel上指定索引位置上的表名称
        """
        return self.__xlsx.sheet_by_index(index - 1).name

    def getSheetByIndex(self, index):
        """
        获得excel上指定索引位置上的表
        """
        return self.__xlsx.sheet_by_index(index - 1)

    def getRowCount(self, sheetIndex):
        """
        获得一排有多少元素
        """
        return self.getSheetByIndex(sheetIndex).ncols

    def getColCount(self, sheetIndex):
        """
        获得一列有多少元素
        """
        return self.getSheetByIndex(sheetIndex).nrows

    def getValue(self, sheet, row, col):
        """
        获得某个工作表的某个位置上的值
        """
        return sheet.cell_value(row, col).value

    def getText(self, sheet, row, col):
        """
        获得某个工作表的某个位置上的值
        """
        return sheet.cell_value(row, col).value

    def getRowValues(self, sheet, row):
        """
        整排
        """
        return sheet.row_values(row)

    def getSheetRowIters(self, sheet, row):
        """
        行迭代器
        """
        return iter(sheet.row_values(row))

    def getSheetColIters(self, sheet, col):
        """
        列迭代器
        """
        return iter(sheet.col_values(col))

    def getColValues(self, sheet, col):
        """
        整列
        """
        return sheet.col_values(col)


# ---------------------------------------------------------------------
#   使用例子
# ---------------------------------------------------------------------
def main():
    xbook = ExcelTool("d:\\test1.xlsx")

    print("sheetCount=%i" % xbook.getSheetCount())

    for x in range(1, xbook.getSheetCount() + 1):
        print("      ", xbook.getSheetNameByIndex(x))

    print("sheet1:rowCount=%i, colCount=%i" % (xbook.getRowCount(1), xbook.getColCount(1)))

    for r in range(1, xbook.getRowCount(1) + 1):
        for c in range(1, xbook.getColCount(1) + 1):
            val = xbook.getValue(xbook.getSheetByIndex(2), r, c)
            if val:
                print("DATA:", val)


if __name__ == "__main__":
    main()
