#!/usr/bin/env python3
import signal
from Scraper import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from threading import *
import math

DEFAULT_DIR_BUTTON = 'Select Folder'


class ScraperGui(QMainWindow):
    def __init__(self):
        super(ScraperGui, self).__init__()

        self.setWindowTitle('VSCO Scraper')
        self.setWindowIcon(QIcon('/lib/favicon.ico'))  # FIXME doesn't show up on mac?

        self.scraper = Scraper()
        self.genParams = {'username': self.scraper.username}

        vbox = QVBoxLayout()
        boxWidget = QWidget()
        boxWidget.setLayout(vbox)
        self.setCentralWidget(boxWidget)

        self.downloadButton = QPushButton('Download')
        self.downloadButton.clicked.connect(self.thread)

        self.username = QLineEdit('')
        self.username.setFixedWidth(200)
        self.username.textChanged.connect(self.checkGenInputs)
        # self.username.returnPressed.connect(self.downloadButton.click)

        self.directoryButton = QPushButton(DEFAULT_DIR_BUTTON)
        self.directoryButton.clicked.connect(self.selectDirectory)

        self.progressData = QLabel('')

        self.quitButton = QPushButton('Quit')
        self.quitButton.clicked.connect(self.clickQuit)

        # OPTIONS
        h = QHBoxLayout()
        h.addWidget(QLabel('Username: '))
        h.addWidget(self.username)
        h.addWidget(self.directoryButton)
        h.addStretch(1)
        vbox.addLayout(h)

        # DOWNLOAD
        h = QHBoxLayout()
        h.addWidget(self.downloadButton)
        self.downloadButton.setEnabled(False)
        h.addStretch(1)
        vbox.addLayout(h)

        # PROGRESS
        h = QHBoxLayout()
        h.addWidget(self.progressData)
        h.addStretch(1)
        vbox.addLayout(h)

        # QUIT
        h = QHBoxLayout()
        h.addWidget(self.quitButton)
        h.addStretch(1)
        vbox.addLayout(h)

        self.show()

    def thread(self):
        t1 = Thread(target=self.downloadClicked)
        t1.start()

    def downloadClicked(self):
        logging.info('username is: ' + self.username.text())
        logging.info('download button clicked')
        self.directoryButton.setEnabled(False)
        self.downloadButton.setEnabled(False)
        self.progressData.setText('Preparing images...')
        self.scraper.initBrowser(self.username.text())
        self.scraper.buildDirectory()
        self.scraper.totalPhotos = len(self.scraper.images)

        for img in self.scraper.images:
            self.scraper.process(img)
            percent = math.ceil((self.scraper.downloadedPhotos / self.scraper.totalPhotos) * 100)
            self.progressData.setText(
                'Downloading '
                + str(self.scraper.downloadedPhotos)
                + ' of ' + str(self.scraper.totalPhotos)
                + ' photos'
                + ' (' + str(percent) + '%)')

        self.scraper.browser.close()
        self.progressData.setText('Download complete.')
        logging.info('Download complete.')
        self.reset()
        logging.info('reset scraper')

    def selectDirectory(self):
        folderPath = QFileDialog.getExistingDirectory(self, DEFAULT_DIR_BUTTON)
        self.scraper.downloadPath = folderPath
        if folderPath == '':
            self.directoryButton.setText(DEFAULT_DIR_BUTTON)
            self.downloadButton.setEnabled(False)
        else:
            self.directoryButton.setText('...' + os.path.basename(folderPath))
        if folderPath != '' and self.username != '':
            self.downloadButton.setEnabled(True)

    def checkGenInputs(self):
        username = self.username.text()

        if self.genParams['username'] == username and self.downloadButton.text() == DEFAULT_DIR_BUTTON:
            self.downloadButton.setEnabled(True)
        else:
            self.downloadButton.setEnabled(False)

    def reset(self):
        self.username.setText('')
        self.directoryButton.setText(DEFAULT_DIR_BUTTON)
        self.directoryButton.setEnabled(True)
        self.scraper = Scraper()

    def clickQuit(self):
        logging.info('quit button clicked')
        if self.scraper.browser is not None:
            self.scraper.browser.close()
        self.close()


def makePretty(app):
    app.setStyle("Fusion")
    qp = QPalette()
    qp.setColor(QPalette.ButtonText, Qt.black)
    qp.setColor(QPalette.Window, Qt.white)
    qp.setColor(QPalette.Button, Qt.white)
    app.setPalette(qp)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # ctrl-c to kill

    scraperApp = QApplication(sys.argv)
    makePretty(scraperApp)
    w = ScraperGui()
    sys.exit(scraperApp.exec())
