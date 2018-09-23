#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import widgets
import dialogs
from PyQt5.Qt import QApplication, QBoxLayout


class MarkdownEditor(widgets.MainWindow):
    """docstring for MarkdownEditor."""
    def __init__(self):
        super(MarkdownEditor, self).__init__('Markdown Editor', 800, 400)
        self._box = widgets.Box(QBoxLayout.LeftToRight)
        self._textFileChooser = dialogs.TextFileChooser(self)

        self._toolbar = widgets.ToolBar()
        self._toolbar.addAction('document-new', 'New document', self.triggeredNewDocument)
        self._toolbar.addAction('document-open', 'Open document', self.triggeredOpenDocument)
        self._toolbar.addAction('document-save', 'Save document', self.triggeredSaveDocument)
        self._toolbar.addSeparator()
        self._toolbar.addAction('edit-cut', 'Cut', self.triggeredCut)
        self._toolbar.addAction('edit-copy', 'Copy', self.triggeredCopy)
        self._toolbar.addAction('edit-paste', 'Paste', self.triggeredPaste)
        self._toolbar.addSeparator()
        self._toolbar.addAction('edit-undo', 'Undo', self.triggeredUndo)
        self._toolbar.addAction('edit-redo', 'Redo', self.triggeredRedo)
        self.addToolBar(self._toolbar)

        self._textEditor = widgets.TextEditor()
        self._textEditor.textChanged.connect(self.onTextChanged)

        self._webview = widgets.WebView()
        self.onTextChanged()

        self._box.addWidget(self._textEditor)
        self._box.addWidget(self._webview)

        self.setCentralWidget(self._box)

    def saveDocument(self, forceAs = False):
        writable = False
        self._textFileChooser.mode = 'w'

        if not(self._textEditor.textContent.endswith('\n')):
            self._textEditor.appendPlainText('')

        if self._textFileChooser.pathname.is_dir() or forceAs:
            response = self._textFileChooser.exec_()
            if dialogs.isAccepted(response):
                writable = True
        else:
            writable = True

        if writable:
            self._textFileChooser.writeText(self._textEditor.textContent)

    def openDocument(self):
        self._textFileChooser.mode = 'r'
        response = self._textFileChooser.exec_()
        if dialogs.isAccepted(response):
            self._textEditor.textContent = self._textFileChooser.readText()

    def onTextChanged(self):
        template = '<!DOCTYPE html><html lang="en" dir="ltr"><head><meta charset="utf-8"><title>Hello world</title></head><body><pre>{}</pre></body></html>'
        self._webview.html = template.format(self._textEditor.textContent)

    def triggeredPaste(self):
        self._textEditor.paste()

    def triggeredCopy(self):
        self._textEditor.copy()

    def triggeredCut(self):
        self._textEditor.cut()

    def triggeredUndo(self):
        self._textEditor.undo()

    def triggeredRedo(self):
        self._textEditor.redo()

    def triggeredNewDocument(self):
        self._textEditor.clear()
        self._textFileChooser.pathname = None

    def triggeredOpenDocument(self):
        self.openDocument()

    def triggeredSaveAsDocument(self):
        self.saveDocument(forceAs = True)

    def triggeredSaveDocument(self):
        self.saveDocument()


def main():
    app = QApplication(sys.argv)
    mainWin = MarkdownEditor()
    mainWin.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
