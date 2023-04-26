import sys
import re
from processpiper.text2diagram import render

# from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QFileDialog,
    QGraphicsScene,
    QGraphicsView,
    QVBoxLayout,
    QSizePolicy,
    QScrollArea,
)

from PyQt6.QtGui import QImage, QPixmap, QIcon
from PyQt6.Qsci import *

from PIL import Image


class MyLexer(QsciLexerCustom):
    def __init__(self, parent):
        super(MyLexer, self).__init__(parent)
        # Default text settings
        # ----------------------
        self.setDefaultColor(QColor("#ff000000"))
        self.setDefaultPaper(QColor("#ffffffff"))
        self.setDefaultFont(QFont("Consolas", 11))

        # Initialize colors per style
        # ----------------------------
        self.setColor(QColor("#ff000000"), 0)  # Style 0: black
        self.setColor(QColor("#ff7f0000"), 1)  # Style 1: red
        self.setColor(QColor("#ff0000bf"), 2)  # Style 2: blue
        self.setColor(QColor("#ff007f00"), 3)  # Style 3: green

        # Initialize paper colors per style
        # ----------------------------------
        self.setPaper(QColor("#ffffffff"), 0)  # Style 0: white
        self.setPaper(QColor("#ffffffff"), 1)  # Style 1: white
        self.setPaper(QColor("#ffffffff"), 2)  # Style 2: white
        self.setPaper(QColor("#ffffffff"), 3)  # Style 3: white

        # Initialize fonts per style
        # ---------------------------
        self.setFont(
            QFont("Consolas", 11, weight=QFont.Weight.Bold), 0
        )  # Style 0: Consolas 14pt
        self.setFont(
            QFont("Consolas", 11, weight=QFont.Weight.Bold), 1
        )  # Style 1: Consolas 14pt
        self.setFont(
            QFont("Consolas", 11, weight=QFont.Weight.Bold), 2
        )  # Style 2: Consolas 14pt
        self.setFont(
            QFont("Consolas", 11, weight=QFont.Weight.Bold), 3
        )  # Style 3: Consolas 14pt

    def language(self):
        return "SimpleLanguage"

    def description(self, style):
        if style == 0:
            return "myStyle_0"
        elif style == 1:
            return "myStyle_1"
        elif style == 2:
            return "myStyle_2"
        elif style == 3:
            return "myStyle_3"
        ###
        return ""

    def styleText(self, start, end):
        # 1. Initialize the styling procedure
        # ------------------------------------
        self.startStyling(start)

        # 2. Slice out a part from the text
        # ----------------------------------
        text = self.parent().text()[start:end]

        # 3. Tokenize the text
        # ---------------------
        # p = re.compile(r"[*]\/|\/[*]|\s+|\w+|\W")

        # p = re.compile(r'\[.*?\]|\(.*?\)|\<.*?\>|->|-"|"->|\s+|\w+|\W')
        p = re.compile(r"\[.*?\]|\(.*?\)|\<.*?\>|\s+|\w+|-\".*?\"->|->|\W")

        # 'token_list' is a list of tuples: (token_name, token_len)
        token_list = [
            (token, len(bytearray(token, "utf-8"))) for token in p.findall(text)
        ]

        # token_list = []
        # for token in p.findall(text):
        #     print(f"token: '{token}'")

        # raise SystemExit()
        # token_list.append((token, len(bytearray(token, "utf-8"))))

        # 4. Style the text
        # ------------------
        # 4.1 Check if multiline comment
        multiline_comm_flag = False
        editor = self.parent()
        if start > 0:
            previous_style_nr = editor.SendScintilla(editor.SCI_GETSTYLEAT, start - 1)
            if previous_style_nr == 3:
                multiline_comm_flag = True
        # 4.2 Style the text in a loop
        for i, token in enumerate(token_list):
            if multiline_comm_flag:
                self.setStyling(token[1], 3)
                if token[0] == "*/":
                    multiline_comm_flag = False
            else:
                if token[0] in ["title", "colourtheme", "pool", "lane", "as", "footer"]:
                    # Red style
                    self.setStyling(token[1], 1)
                elif (
                    (token[0].startswith("[") and token[0].endswith("]"))
                    or (token[0].startswith("(") and token[0].endswith(")"))
                    or (token[0].startswith("<") and token[0].endswith(">"))
                ):
                    # Green style
                    self.setStyling(token[1], 3)
                elif token[0].startswith('-"') and token[0].endswith('"->'):
                    self.setStyling(token[1], 2)
                elif token[0] in ["->"]:
                    # Red style
                    self.setStyling(token[1], 2)
                elif token[0] == "/*":
                    multiline_comm_flag = True
                    self.setStyling(token[1], 3)
                else:
                    # Default style
                    self.setStyling(token[1], 0)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        test_text = """title: Make pizza process
lane: Pizza Shop
    (start) as start
    [Put the pizza in the oven] as put_pizza_in_oven
    [Check to see if pizza is done] as check_pizza_done
    <Done baking?> as done_baking
    [Take the pizza out of the oven] as take_pizza_out_of_oven
    (end) as end
    
start->put_pizza_in_oven->check_pizza_done->done_baking
done_baking-"Yes"->take_pizza_out_of_oven->end
done_baking-"No"->put_pizza_in_oven
"""

        self.__myFont = QFont()
        self.__myFont.setPointSize(11)

        self.text_input = QsciScintilla()
        self.text_input.setText(test_text)
        self.text_input.setLexer(None)  # We install lexer later
        self.text_input.setUtf8(True)  # Set encoding to UTF-8
        self.text_input.setFont(self.__myFont)  # Gets overridden by lexer later on

        # 1. Text wrapping
        # -----------------
        self.text_input.setWrapMode(QsciScintilla.WrapMode.WrapWord)
        self.text_input.setWrapVisualFlags(QsciScintilla.WrapVisualFlag.WrapFlagByText)
        self.text_input.setWrapIndentMode(
            QsciScintilla.WrapIndentMode.WrapIndentIndented
        )

        # 2. End-of-line mode
        # --------------------
        self.text_input.setEolMode(QsciScintilla.EolMode.EolWindows)
        self.text_input.setEolVisibility(False)

        # 3. Indentation
        # ---------------
        self.text_input.setIndentationsUseTabs(False)
        self.text_input.setTabWidth(4)
        self.text_input.setIndentationGuides(True)
        self.text_input.setTabIndents(True)
        self.text_input.setAutoIndent(True)

        # 4. Caret
        # ---------
        self.text_input.setCaretForegroundColor(QColor("#ff0000ff"))
        self.text_input.setCaretLineVisible(True)
        self.text_input.setCaretLineBackgroundColor(QColor("#1f0000ff"))
        self.text_input.setCaretWidth(2)

        # 5. Margins
        # -----------
        # Margin 0 = Line nr margin
        self.text_input.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.text_input.setMarginWidth(0, "0000")
        self.text_input.setMarginsForegroundColor(QColor("#ff888888"))

        self.text_input.setMinimumHeight(400)

        # -------------------------------- #
        #          Install lexer           #
        # -------------------------------- #
        self.__lexer = MyLexer(self.text_input)
        self.text_input.setLexer(self.__lexer)

        self.generate_button = QPushButton("Generate")
        self.save_button = QPushButton("Save")
        self.output_image = QLabel()

        # self.output_image.setSizePolicy(
        #     QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        # )

        # Create a scroll area widget
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        # self.scroll_area.setFixedSize(1200, 800)
        self.scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # Create a widget to contain the scrollable content
        scroll_content = QWidget(self.scroll_area)
        self.scroll_area.setWidget(scroll_content)

        self.layout = QVBoxLayout(scroll_content)
        self.layout.addWidget(self.text_input)
        self.layout.addWidget(self.generate_button)

        self.image = QImage()
        self.pixmap = QPixmap()

        self.layout.addWidget(self.output_image)
        self.layout.addWidget(self.save_button)

        scroll_content.setLayout(self.layout)

        # Create a layout for the main window and add the scroll area to it
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)

        self.generate_button.clicked.connect(self.generate_diagram)
        self.save_button.clicked.connect(self.save_diagram)

    def generate_diagram(self):
        user_input = str(self.text_input.text())

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
                aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
            )
        )

        self.output_image.setPixmap(self.pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scroll_area.setGeometry(0, 0, self.width(), self.height())

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
    icon = QIcon("flow.ico")

    # Set the window icon
    main_window.setWindowIcon(icon)

    # Other name Piperella
    main_window.setWindowTitle("Piperino v0.1 (a graphical frontend for ProcessPiper)")
    main_window.setGeometry(0, 0, 1200, 800)
    screen = QApplication.instance().primaryScreen()

    main_window.move(
        (screen.size().width() - main_window.width()) // 2,
        (screen.size().height() - main_window.height()) // 2,
    )
    main_window.show()

    sys.exit(app.exec())
