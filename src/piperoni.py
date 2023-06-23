import sys
import os
import re
from processpiper.text2diagram import render

from version import __version__

# from PyQt6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QFileDialog,
    QHBoxLayout,
    QVBoxLayout,
    QSizePolicy,
    QScrollArea,
    QToolBar,
    QStatusBar,
    QTextEdit,
)

from PySide6.QtGui import (
    QImage,
    QPixmap,
    QIcon,
    QFont,
    QFontDatabase,
    QColor,
    QSyntaxHighlighter,
    QTextCharFormat,
)

# from PyQt6.Qsci import *

from PIL import Image


class LineNumberedPlainTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def line_number_area_width(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value //= 10
            digits += 1

        space = 3 + self.fontMetrics().horizontalAdvance("9") * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(), self.line_number_area.width(), rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def highlight_current_line(self):
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            line_color = QColor(Qt.yellow).lighter(160)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selection.cursor.movePosition(QTextCursor.StartOfLine)
            selection.cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)

            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.black)
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width(),
                    self.fontMetrics().height(),
                    Qt.AlignRight,
                    number,
                )

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mapping = {}

    def add_mapping(self, pattern, pattern_format):
        self._mapping[pattern] = pattern_format

    def highlightBlock(self, text_block):
        for pattern, fmt in self._mapping.items():
            for match in re.finditer(pattern, text_block):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)


# re.compile(r"\[.*?\]|\(.*?\)|\<.*?\>|\s+|\w+|-\".*?\"->|->|\W")


class MainWindow(QMainWindow):
    def __init__(self):
        # super().__init__()
        super(MainWindow, self).__init__()
        self.setStyleSheet(
            """
			QWidget {
				font-size: 18px;
                font-weight: bold;
			}
		"""
        )

        self.test_text = """#Showcase Process Piper plain text to diagram capability
title: Make pizza process
colourtheme: BLUEMOUNTAIN

# Define the swimlane and BPMN elements
lane: Pizza Shop
    (start) as start
    [Put the pizza in the oven] as put_pizza_in_oven
    [Check to see if pizza is done] as check_pizza_done
    <@exclusive Done baking?> as done_baking
    [Take the pizza out of the oven] as take_pizza_out_of_oven
    (end) as end

# Connect all the elements    
start->put_pizza_in_oven->check_pizza_done->done_baking
done_baking-"Yes"->take_pizza_out_of_oven->end
done_baking-"No"->put_pizza_in_oven
"""

        self.highlighter = Highlighter()
        self.setUpEditor()
        self.generate_button = QPushButton("Generate")
        self.save_button = QPushButton("Save")
        self.output_image = QLabel()
        self.image = QImage()
        self.pixmap = QPixmap()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.editor)
        self.layout.addWidget(self.generate_button)
        self.layout.addWidget(self.output_image)
        self.layout.addWidget(self.save_button)

        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        # toolbar = QToolBar("My main toolbar")
        # toolbar.setIconSize(QSize(16, 16))
        # self.addToolBar(toolbar)

        # save_text_button_action = QAction(
        #     QIcon("icons/disk-black.png"), "Save text", self
        # )
        # save_text_button_action.setStatusTip("Save text")
        # save_text_button_action.triggered.connect(self.onMyToolBarButtonClick)
        # save_text_button_action.setCheckable(True)
        # toolbar.addAction(save_text_button_action)

        # save_png_button_action = QAction(QIcon("icons/disk.png"), "Save diagram", self)
        # save_png_button_action.setStatusTip("Save diagram")
        # save_png_button_action.triggered.connect(self.onMyToolBarButtonClick)
        # save_png_button_action.setCheckable(True)
        # toolbar.addAction(save_png_button_action)

        self.generate_button.clicked.connect(self.generate_diagram)
        self.save_button.clicked.connect(self.save_diagram)

        self.setStatusBar(QStatusBar(self))

    def setUpEditor(self):
        # define pattern rule #1: highlight class header
        element_format = QTextCharFormat()
        element_format.setForeground(QColor("#C55A11"))
        element_format.setFontWeight(QFont.Weight.Bold)
        pattern = r"\[.*?\]|\(.*?\)|\<.*?\>"
        self.highlighter.add_mapping(pattern, element_format)

        # pattern #2: title, pool and lane format
        title_format = QTextCharFormat()
        title_format.setForeground(QColor("#2E75B6"))
        title_format.setFontWeight(QFont.Weight.Bold)
        pattern = r"title:|width:|colourtheme:|pool:|lane:"
        self.highlighter.add_mapping(pattern, title_format)

        # pattern #3: 'as' format
        as_format = QTextCharFormat()
        as_format.setForeground(QColor("#2E75B6"))
        as_format.setFontWeight(QFont.Weight.Bold)
        pattern = r"\s+as\s+"
        self.highlighter.add_mapping(pattern, as_format)

        # pattern #3: 'as' format
        arrow_format = QTextCharFormat()
        arrow_format.setForeground(QColor("#2E75B6"))
        arrow_format.setFontWeight(QFont.Weight.Bold)
        pattern = r"-\".*?\"->|->"
        self.highlighter.add_mapping(pattern, arrow_format)

        # gateway attribute pattern format
        attribute_format = QTextCharFormat()
        attribute_format.setForeground(QColor("red"))
        attribute_format.setFontWeight(QFont.Weight.Bold)
        pattern = r"@timer|@intermediate|@subprocess|@parallel|@inclusive|@exclusive"
        self.highlighter.add_mapping(pattern, attribute_format)

        colourtheme_format = QTextCharFormat()
        colourtheme_format.setForeground(QColor("blue"))
        colourtheme_format.setFontWeight(QFont.Weight.Bold)
        pattern = r"BLUEMOUNTAIN"
        self.highlighter.add_mapping(pattern, colourtheme_format)

        colourtheme_format = QTextCharFormat()
        colourtheme_format.setForeground(QColor("orange"))
        colourtheme_format.setFontWeight(QFont.Weight.Bold)
        pattern = r"ORANGEPEEL"
        self.highlighter.add_mapping(pattern, colourtheme_format)

        colourtheme_format = QTextCharFormat()
        colourtheme_format.setForeground(QColor("green"))
        colourtheme_format.setFontWeight(QFont.Weight.Bold)
        pattern = r"GREENTURTLE"
        self.highlighter.add_mapping(pattern, colourtheme_format)

        colourtheme_format = QTextCharFormat()
        colourtheme_format.setForeground(QColor("grey"))
        colourtheme_format.setFontWeight(QFont.Weight.Bold)
        pattern = r"GREYWOLF"
        self.highlighter.add_mapping(pattern, colourtheme_format)

        # pattern 3: comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("green"))
        comment_format.setFontItalic(True)
        comment_format.setFontWeight(QFont.Weight.Normal)
        # pattern = r'^\s*#.*$' # hightlight from the beginning of the line
        pattern = r"#.*$"  # just the text
        self.highlighter.add_mapping(pattern, comment_format)

        # self.editor = QPlainTextEdit()
        self.editor = LineNumberedPlainTextEdit()
        self.editor.setPlainText(self.test_text)
        # self.editor.setTabStopDistance(40)
        self.editor.setTabStopDistance(
            QFontMetricsF(self.editor.font()).horizontalAdvance(" " * 14)
        )

        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        self.editor.setFont(font)

        self.highlighter.setDocument(self.editor.document())

    def generate_diagram(self):
        user_input = str(self.editor.toPlainText())

        output_image_file = "output.png"
        # Call the render function to generate the diagram
        try:
            render(user_input, output_image_file)
        except Exception as e:
            print(e)
            return

        # Load the diagram image
        self.pixmap.load(output_image_file)

        self.output_image.setPixmap(
            self.pixmap.scaled(
                self.output_image.size(),
                aspectMode=Qt.KeepAspectRatio,
            )
        )

        self.output_image.setPixmap(self.pixmap)

    def onMyToolBarButtonClick(self, s):
        print("click", s)

    def save_diagram(self):
        # Get the filename of the diagram to save
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Diagram", "", "PNG (*.png);;JPEG (*.jpg);;All Files (*)"
        )

        if not file_name:
            return

        # Save the diagram image to the file
        image = QImage("output.png")
        image.save(file_name)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create the main window
    main_window = MainWindow()

    basedir = os.path.dirname(__file__)

    # icon = QIcon("icons/flow.ico")
    print(os.path.join(basedir, "icons", "flow.ico"))
    icon = QIcon(os.path.join(basedir, "icons", "flow.ico"))

    # Set the window icon
    main_window.setWindowIcon(icon)

    # Other name Piperella
    version = __version__
    main_window.setWindowTitle(
        f"Piperoni {__version__} (a graphical frontend for ProcessPiper)"
    )
    # main_window.setWindowTitle(
    #     f"Piperoni v0.3.0 (a graphical frontend for ProcessPiper)"
    # )
    main_window.setGeometry(0, 0, 1200, 800)
    screen = QApplication.instance().primaryScreen()

    main_window.move(
        (screen.size().width() - main_window.width()) // 2,
        (screen.size().height() - main_window.height()) // 2,
    )
    main_window.show()

    sys.exit(app.exec())
