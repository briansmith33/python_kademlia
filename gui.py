from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import *
from datetime import datetime
import sys


class MainWindow(QMainWindow):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName('MainWindow')
        self.setWindowTitle('2Can')
        self.window_label = QLabel("2Can")
        self.windowControl = QFrame(self, None)
        self.windowControlLayout = QHBoxLayout(self)
        self.windowControl.setLayout(self.windowControlLayout)
        self.screen = app.desktop()
        self.menuBar = self.menuBar()
        self.menuBar.setFixedHeight(40)
        self.menuBar.setStyleSheet("background: #0f0f2d;")
        self.menuBar.setMouseTracking(True)

        self.mainLayout = QHBoxLayout()
        self.widget = QWidget(self)
        self.widget.setLayout(self.mainLayout)
        self.resize(900, 600)
        self.close_btn = QPushButton(self.menuBar)

        self.side_bar = QVBoxLayout()
        self.side_scroll = QScrollArea()
        self.scrollWidget = QWidget(self.side_scroll, None)
        self.scrollLayout = QVBoxLayout()

        self.view_port = QVBoxLayout()
        self.view_widget = QWidget(self.view_port, None)
        self.view_form = QFormLayout()

        self.feed = QScrollArea()
        self.feed_widget = QWidget(self.feed, None)
        self.feed_layout = QVBoxLayout()
        self.message_input = QLineEdit()

        self.oldPos = self.pos()
        self.winX = 0
        self.winY = 0
        self.move_to_center()
        self.pressed = False
        self.fullScreen = False

        self.font = "Lato"
        self.select_color = "#247ba0"
        self.theme_color = "#00fddc"
        self.light_color = "#BBBBBB"

        self.init()

    def init(self):
        self.move(self.winX, self.winY)

        self.setStyleSheet('background-color: #181735')
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.window_label.setFont(QFont(self.font, 12))
        self.window_label.setStyleSheet('color: #17BEBB; font-weight: bold; margin-left: 20px;')

        self.close_btn.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_MessageBoxCritical')))
        self.close_btn.setStyleSheet("border-radius: 50%;")
        self.close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.close_btn.clicked.connect(self.close_button)

        self.menuBar.setCornerWidget(self.window_label, Qt.TopLeftCorner)
        self.menuBar.setCornerWidget(self.windowControl, Qt.TopRightCorner)
        self.windowControlLayout.addWidget(self.close_btn)

        self.side_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.side_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.side_scroll.setWidgetResizable(True)

        self.scrollWidget.setStyleSheet('background: #cccccc; padding: 0px 20px;')
        self.side_scroll.setFixedWidth(250)
        self.side_scroll.setWidget(self.scrollWidget)
        self.scrollWidget.setLayout(self.scrollLayout)

        self.side_bar.addWidget(self.side_scroll)
        self.mainLayout.addLayout(self.side_bar)

        self.feed.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.feed.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.feed.setWidgetResizable(True)

        self.feed_widget.setStyleSheet('background: #cccccc; padding: 5px;')
        self.feed.setWidget(self.feed_widget)
        self.feed_layout.setAlignment(Qt.AlignTop)
        self.feed_widget.setLayout(self.feed_layout)
        self.view_form.addWidget(self.feed)

        self.message_input.setStyleSheet("background: #cccccc; padding: 5px;")
        self.message_input.setFont(QFont(self.font, 14))
        self.message_input.returnPressed.connect(self.send_message)

        self.view_form.addWidget(self.message_input)

        self.view_widget.setFixedWidth(650)
        self.view_widget.setLayout(self.view_form)
        self.view_port.addWidget(self.view_widget)
        self.mainLayout.addLayout(self.view_port)

        self.setLayout(self.mainLayout)

        self.setCentralWidget(self.widget)

    def send_message(self):
        new_message = QLabel(self.message_input.text())
        new_message.setFont(QFont(self.font, 12))
        new_message.setStyleSheet("font-weight: bold;")
        new_message.setWordWrap(True)

        message_time = QLabel(datetime.now().ctime())
        message_time.setAlignment(Qt.AlignRight)

        self.feed_layout.addWidget(new_message)
        self.feed_layout.addWidget(message_time)
        self.message_input.setText("")

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()
        self.pressed = True

    def mouseReleaseEvent(self, event):
        self.oldPos = event.globalPos()
        self.pressed = False

    def mouseMoveEvent(self, event):
        if self.pressed:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def move_to_center(self):
        self.winX = int((self.screen.width() / 2) - (self.width() / 2))
        self.winY = int((self.screen.height() / 2) - (self.height() / 2))
        self.move(self.winX, self.winY)

    @staticmethod
    def close_button():
        sys.exit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow(app)
    window.show()
    app.exec_()
