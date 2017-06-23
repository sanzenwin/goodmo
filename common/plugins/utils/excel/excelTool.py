# -*- coding: gb2312 -*-
import os
import xlrd


class ExcelTool:
    """
    �򵥵ķ�װexcel���ֲ���
    ϵͳҪ�� windowsϵͳ�� ��װpython2.6�Լ�pywin32-214.win32-py2.6.exe, �Լ�ms office
    """

    def __init__(self, fileName):
        self.__xlsx = None
        self.fileName = os.path.abspath(fileName)

    def getWorkbook(self, forcedClose=False):
        """
        ���Workbook�Ѿ�����Ҫ�ȹرպ��
        forcedClose���Ƿ�ǿ�ƹرգ���򿪸�Workbook
        """
        self.__xlsx = xlrd.open_workbook(self.fileName)
        return True

    def close(self, saveChanges=False):
        """
        �ر�excelӦ��
        """
        self.__xlsx.release_resources()

    def getSheetCount(self):
        """
        ��ù��������
        """
        return len(self.__xlsx.sheets())

    def getSheetNameByIndex(self, index):
        """
        ���excel��ָ������λ���ϵı�����
        """
        return self.__xlsx.sheet_by_index(index - 1).name

    def getSheetByIndex(self, index):
        """
        ���excel��ָ������λ���ϵı�
        """
        return self.__xlsx.sheet_by_index(index - 1)

    def getRowCount(self, sheetIndex):
        """
        ���һ���ж���Ԫ��
        """
        return self.getSheetByIndex(sheetIndex).ncols

    def getColCount(self, sheetIndex):
        """
        ���һ���ж���Ԫ��
        """
        return self.getSheetByIndex(sheetIndex).nrows

    def getValue(self, sheet, row, col):
        """
        ���ĳ���������ĳ��λ���ϵ�ֵ
        """
        return sheet.cell_value(row, col).value

    def getText(self, sheet, row, col):
        """
        ���ĳ���������ĳ��λ���ϵ�ֵ
        """
        return sheet.cell_value(row, col).value

    def getRowValues(self, sheet, row):
        """
        ����
        """
        return sheet.row_values(row)

    def getSheetRowIters(self, sheet, row):
        """
        �е�����
        """
        return iter(sheet.row_values(row))

    def getSheetColIters(self, sheet, col):
        """
        �е�����
        """
        return iter(sheet.col_values(col))

    def getColValues(self, sheet, col):
        """
        ����
        """
        return sheet.col_values(col)


# ---------------------------------------------------------------------
#   ʹ������
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
