#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.Qt import (
    QBoxLayout,
    QToolBar,
    QLabel,
    pyqtSignal
)
import widgets
import dialogs
import threads
import helpers
import object
from pandoc import Pandoc


class MarkdownEditor(widgets.MainWindow):
    """docstring for MarkdownEditor."""

    documentIsSaveSig = pyqtSignal(str)
    exportDocumentSig = pyqtSignal(str, bool)
    documentTitleDefault = 'New document'
    defaultPath = helpers.joinpath_to_cwd('example', 'example.md')
    configPath = helpers.joinpath_to_cwd('config.json')

    def __init__(self, pathnameSrc = None):
        super(MarkdownEditor, self).__init__('Markdown Editor', 800, 400)
        self.box = widgets.Box(QBoxLayout.TopToBottom, self)
        self.subBox = widgets.Box(QBoxLayout.LeftToRight, self.box)
        self.textFileChooser = dialogs.TextFileChooser(self)
        if pathnameSrc:
            self.pathnameSrc = helpers.Path(pathnameSrc).absolute()
            self.documentTitle = self.pathnameSrc.name
        else:
            self.pathnameSrc = None
            self.documentTitle = MarkdownEditor.documentTitleDefault

        self.labelDocumentState = QLabel(self.box)
        self.box.addWidget(self.labelDocumentState)

        self.addAction('file-document-new', object.Action('New document', self.newDocument, 'Ctrl+N', 'document-new'))
        self.addAction('file-document-open', object.Action('Open document', self.triggeredOpenDocument, 'Ctrl+O', 'document-open'))
        self.addAction('file-document-save', object.Action('Save document', self.triggeredSaveDocument, 'Ctrl+S', 'document-save'))
        self.addAction('file-document-save-as', object.Action('Save document as', self.triggeredSaveAsDocument, 'Ctrl+Shift+S', 'document-save-as'))
        self.addAction('file-export-html', object.Action('Export in html', self.triggeredExport))
        self.addAction('edit-undo', object.Action('Undo', self.triggeredUndo, 'Ctrl+Z', 'edit-undo'))
        self.addAction('edit-redo', object.Action('Redo', self.triggeredRedo, 'Ctrl+Y', 'edit-redo'))
        self.addAction('edit-cut', object.Action('Cut', self.triggeredCut, 'Ctrl+X', 'edit-cut'))
        self.addAction('edit-copy', object.Action('Copy', self.triggeredCopy, 'Ctrl+C', 'edit-copy'))
        self.addAction('edit-paste', object.Action('Paste', self.triggeredPaste, 'Ctrl+V', 'edit-paste'))
        self.addAction('edit-find', object.Action('Find', self.triggeredFind, 'Ctrl+F', 'edit-find'))
        self.addAction('edit-preference', object.Action('Preferences', self.triggeredPreference, 'Ctrl+,', 'preferences-system'))
        self.addAction('view-about', object.Action('About', self.triggeredAbout))

        with helpers.joinpath_to_cwd('requirements.txt').open(encoding='utf8') as requirements:
            self.aboutDialog = dialogs.About(self,
                copyright='Loïc Penaud ©',
                programName='Markdown-Editor',
                version='1.2',
                website='https://github.com/lpenaud/markdown-editor-qt',
                websiteLabel='Github',
                comments='A markdown editor written in Python3.7 with Qt5 and pandoc2',
                licenseName='GPL-3.0',
                licenseUrl=helpers.joinpath_to_cwd('LICENSE').as_uri(),
                authors=('Loïc Penaud',),
                dependencies=[l.strip() for l in requirements.readlines()],
            )

        self.pandoc = threads.PandocThread(
            self,
            'markdown',
            'html5',
            self.exportDocumentSig,
        )
        self.pandoc.convertedText.connect(self.cbPandoc)

        self.saveThread = threads.SaveThread(self)
        self.saveThreading = True

        self.preferenceDialog = dialogs.Preferences(self)
        self.preferenceDialog.themeChooser.themeChanged.connect(self.triggeredThemeChanged)
        self.preferenceDialog.saveOption.saveOptionChanged.connect(self.triggeredSaveOptionChanged)

        self.menubar = widgets.MenuBar(self)
        self.menubar.appendMenu('File')
        self.menubar.addActionsToMenu('File', self.findActionsLike('file'))
        self.menubar.insertSeparatorToMenu('File', self.getAction('file-document-save'))
        self.menubar.insertSeparatorToMenu('File', self.getAction('file-export-html'))
        self.menubar.appendMenu('Edit')
        self.menubar.addActionsToMenu('Edit', self.findActionsLike('edit'))
        self.menubar.insertSeparatorToMenu('Edit', self.getAction('edit-cut'))
        self.menubar.insertSeparatorToMenu('Edit', self.getAction('edit-find'))
        self.menubar.insertSeparatorToMenu('Edit', self.getAction('edit-preference'))
        self.menubar.appendMenu('View')
        self.setMenuBar(self.menubar)

        self.toolbar = QToolBar(self)
        self.toolbar.addActions(self.actions())
        self.toolbar.insertSeparator(self.getAction('file-export-html'))
        self.toolbar.insertSeparator(self.getAction('edit-cut'))
        self.toolbar.insertSeparator(self.getAction('edit-undo'))
        self.toolbar.insertSeparator(self.getAction('edit-find'))
        self.toolbar.removeAction(self.getAction('edit-preference'))
        self.addToolBar(self.toolbar)

        self.textEditor = widgets.TextEditor(self.subBox)
        self.textEditor.setDocumentTitle('New document')
        self.textEditor.timeout.connect(self.triggeredTextTimeout)
        self.textEditor.textChanged.connect(self.triggeredTextChanged)
        if self.pathnameSrc:
            self.textEditor.textContent = self.pathnameSrc.read_text(encoding='utf8')
        else:
            self.newDocument()

        self.overview = widgets.WebView(self)

        self.subBox.addWidget(self.textEditor)
        self.subBox.addWidget(self.overview)

        self.box.addWidget(self.subBox)
        self.setCentralWidget(self.box)
        self.documentIsSave = True
        self.documentIsSaveSig.connect(self.documentIsSaveSigCb)
        self.readConfig()

    @property
    def documentIsSave(self):
        return self.__documentIsSave

    @documentIsSave.setter
    def documentIsSave(self, documentIsSave):
        if documentIsSave:
            self.setWindowTitle(self.documentTitle)
            self.labelDocumentState.setText('Document is save')
        else:
            if not(self.windowTitle().startswith('*')):
                self.setWindowTitle('*' + self.windowTitle())
            self.labelDocumentState.setText('Document has been modified')
        self.__documentIsSave = documentIsSave

    def documentIsSaveSigCb(self):
        self.documentIsSave = True

    def saveDocument(self, forceAs = False):
        writable = False
        self.textFileChooser.mode = 'w'

        if not(self.pathnameSrc) or forceAs:
            self.textFileChooser.setDefaultFilter(0)
            self.textFileChooser.setWindowTitle('Save file')
            if dialogs.isAccepted(self.textFileChooser.exec_()):
                self.pathnameSrc = self.textFileChooser.pathname
                self.documentTitle = self.pathnameSrc.name
                writable = True
        else:
            writable = True

        if writable and not(self.documentIsSave):
            self.pathnameSrc.write_text(self.textEditor.textContent, encoding='utf8')
            self.documentIsSaveSig.emit(str(self.pathnameSrc))

    def openDocument(self):
        self.textFileChooser.mode = 'r'
        response = self.textFileChooser.exec_()
        if dialogs.isAccepted(response):
            self.textEditor.textContent = self.textFileChooser.readText()
            self.pathnameSrc = self.textFileChooser.pathname
            self.documentTitle = self.pathnameSrc.name

    def newDocument(self):
        template = MarkdownEditor.defaultPath.read_text()
        author = helpers.get_username()
        self.pathnameSrc = None
        self.documentTitle = MarkdownEditor.documentTitleDefault
        self.textEditor.textContent = template.format(
            title=self.documentTitle,
            author=author,
            email='{}@example.com'.format(author.replace(' ', '.'))
        )
        self.documentIsSave = True

    def closeEvent(self, evt):
        if self.documentIsSave:
            evt.accept()
        else:
            response = dialogs.MessageBox.documentIsNotSave(self)
            if dialogs.MessageBox.isDiscardClicked(response):
                evt.accept()
            elif dialogs.MessageBox.isSaveClicked(response):
                self.saveDocument()
                evt.accept()
            else:
                evt.ignore()

    def triggeredTextTimeout(self):
        self.exportDocumentSig.emit(self.textEditor.textContent, False)
        if self.saveThreading:
            self.saveThread.start()

    def triggeredTextChanged(self):
        self.documentIsSave = False

    def triggeredPaste(self):
        self.textEditor.paste()

    def triggeredCopy(self):
        self.textEditor.copy()

    def triggeredCut(self):
        self.textEditor.cut()

    def triggeredUndo(self):
        self.textEditor.undo()

    def triggeredFind(self):
        self.textEditor.find(self.textEditor.textCursor().selectedText())

    def triggeredRedo(self):
        self.textEditor.redo()

    def triggeredOpenDocument(self):
        self.openDocument()

    def triggeredSaveAsDocument(self):
        self.saveDocument(forceAs=True)

    def triggeredSaveDocument(self):
        self.saveDocument()

    def cbPandoc(self, converted_text, pathname):
        if pathname:
            print(pathname)
        self.overview.html = converted_text

    def triggeredExport(self):
        self.saveDocument()
        if self.pathnameSrc:
            self.textFileChooser.setDefaultFilter(1)
            self.textFileChooser.setWindowTitle('Export html')
            if dialogs.isAccepted(self.textFileChooser.exec_()):
                self.pandoc.pathname = self.textFileChooser.pathname
                self.exportDocumentSig.emit(
                    self.textEditor.textContent,
                    True
                )

    def triggeredThemeChanged(self, themeName):
        for action in self.actions():
            action.refreshIcons()

    def triggeredSaveOptionChanged(self, saveThreading):
        self.saveThreading = saveThreading

    def triggeredPreference(self):
        response = self.preferenceDialog.exec_()
        if dialogs.isRejected(response):
            self.preferenceDialog.rollback()
        elif dialogs.isAccepted(response):
            self.preferenceDialog.commit()

    def triggeredAbout(self):
        self.aboutDialog.exec_()

    def readConfig(self):
        config = helpers.serialize_json(MarkdownEditor.configPath)
        themeConfig = config['theme']
        documentConfig = config['document']
        self.pandoc.read_config(config['pandoc'])
        if not(themeConfig['name'] == 'SYSTEM'):
            self.preferenceDialog.themeChooser.comboBox.setCurrentText(themeConfig['name'])
        self.preferenceDialog.saveOption.checkBox.setChecked(documentConfig['autosave'])
