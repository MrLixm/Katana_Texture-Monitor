import re

# from Katana import UI4
# from UI4.App import MainWindow
#
# from PyQt5 import QtWidgets, QtCore, QtGui


# class Test:
#     def __init__(self):
#         self.main_widget = QtWidgets.QWidget()
#
#         self.lyt = QtWidgets.QVBoxLayout(self.main_widget)
#
#         self.btn = QtWidgets.QPushButton("Press me")
#         self.lyt.addWidget(self.btn)
#
#         self.btn.clicked.connect(self.foo)
#
#         return
#
#     def foo(self, *args, **kwargs):
#         print("Btn pressed")
#         print(args)
#         print(kwargs)
#         return
#
#
# tt = Test()
# tt.main_widget.show()

def test01():
    # match_grp = re.search(r'S\wRIPT', r"L:\SCRIPT\ImageProcessing\A1_test_bench\test03\Cabin_render_ORIGINAL.exr")
    original_string = r"L:\SCRIPT\ImageProcessing\A1_test_bench\test03\Cabin_render_ORIGINAL.exr"
    new_string = original_string.replace("SCRIPT", "ddd")
    if new_string:
        print(new_string)
        print(type(new_string))
    else:
        print('no match')


test01()
# end
