""" A code editing widget for Enaml.

The widget is implemented by wrapping QTextEdit. The syntax highlighters use
Pygments and were originally written (by yours truly) for the (BSD-licensed)
IPython project.

An alternative implementation strategy would be to use Enaml's builtin
Scintilla wrapper. We cannot do this because QScintilla is only available in
PyQt (which is GPL-licensed), not PySide. This is no great loss as Scintilla 
has an appalling code base.
"""
from __future__ import absolute_import

import sys

from atom.api import Bool, Enum, Range, Typed, Unicode, observe, set_default
from enaml.core.declarative import d_
from enaml.fonts import FontMember, parse_font
from enaml.widgets.api import RawWidget
from enaml.qt.QtCore import *
from enaml.qt.QtGui import *
from enaml.qt.QtWidgets import *
from enaml.qt.q_resource_helpers import get_cached_qfont

from nemesis.ui.pygments_highlighter import PygmentsHighlighter


def _get_language_enum_items():
    from pygments.lexers import get_all_lexers
    languages = []
    for longname, aliases, patterns, mimetypes in get_all_lexers():
        languages.extend(aliases)
    languages.remove('python')
    languages.insert(0, 'python')
    return languages

def _get_style_enum_items():
    from pygments.styles import get_all_styles
    styles = list(get_all_styles())
    styles.remove('default')
    styles.insert(0, 'default')
    return styles

def _get_monospace_font():
    if sys.platform == 'win32':
        font = '11pt Consolas'
    elif sys.platform == 'darwin':
        font = '12pt Monaco'
    else:
        font = '12pt Monospace'
    return parse_font(font)


class CodeEditor(RawWidget):
    """ An Enaml widget for editing source code.
    """
    # The text to display.
    text = d_(Unicode())
    
    # The langauge of the text. Default is 'python'.
    language = d_(Enum(*_get_language_enum_items()))
    
    # The Pygments style to use for highlighting the text.
    style = d_(Enum(*_get_style_enum_items()))
    
    # The font to use for the text.
    # Note that the standard attribute 'font' has no effect no this widget.
    text_font = d_(FontMember(_get_monospace_font()))
    
    # Indentation settings.
    auto_indent = d_(Bool(True))
    tab_width = d_(Range(low=1, value=4))
    tabs_as_spaces = d_(Bool(True))
    
    # Expand the editor by default.
    hug_width = set_default('ignore')
    hug_height = set_default('ignore')
    
    # Underlying Qt objects.
    _highlighter = Typed(QSyntaxHighlighter)
    _text_edit = Typed(QTextEdit)
    _text_locked = Bool(False)
    
    #--------------------------------------------------------------------------
    # 'RawWidget' interface
    #--------------------------------------------------------------------------
    
    def create_widget(self, parent):
        """ Create the underlying Qt widget.
        """
        self._text_edit = text_edit = _CodeEditor(self, parent=parent)
        text_edit.textChanged.connect(self._signal_text_changed)
        text_edit.setWordWrapMode(QTextOption.NoWrap)
        
        self._highlighter = PygmentsHighlighter(
            parent = text_edit,
            lexer = self.language,
            style = self.style)
        self._update_font()
        self._update_text()
        return text_edit
    
    #--------------------------------------------------------------------------
    # 'CodeEditor' interface
    #--------------------------------------------------------------------------
    
    def backspace(self):
        if self.dedent() == 0:
            cursor = self._text_edit.textCursor()
            cursor.deletePreviousChar()
    
    def dedent(self):
        cursor = self._text_edit.textCursor()
        column = cursor.columnNumber()
        if not self.tabs_as_spaces or cursor.hasSelection() or column == 0:
            return 0
        
        # Set the number of characters to remove.
        text = cursor.block().text()
        tab_width = self.tab_width
        indent_column = self._get_indent_column(text)
        if column == indent_column and text[:column] == ' '*column:
            remove = (column - 1)%tab_width + 1
            if text[column-remove:column] != ' '*remove:
                return 0
        elif text[column-tab_width:column] == ' ' * tab_width:
            if column < indent_column or len(text[column:].strip()) > 0:
                remove = tab_width
            else:
                remove = (column - 1)%tab_width + 1
        else:
            return 0

        # Remove characters.
        for i in xrange(remove):
            cursor.deletePreviousChar()
        return remove
    
    def indent(self, cursor=None):
        if cursor is None:
            cursor = self._text_edit.textCursor()
        tab = ' ' * self.tab_width if self.tabs_as_spaces else '\t'
        cursor.insertText(tab)
        
    def newline(self):
        cursor = self._text_edit.textCursor()
        column = cursor.columnNumber()
        text = cursor.block().text()
        
        cursor.beginEditBlock()
        cursor.insertBlock()
        
        # Only auto indent when at end of line.
        if self.auto_indent and column == len(text):
            tab_width = self.tab_width
            indent_col = self._get_indent_column(text)
            space_required = len(text[:indent_col].replace('\t', ' '*tab_width))
            for i in xrange(space_required / tab_width):
                self.indent(cursor)
            cursor.insertText(' ' * (space_required % tab_width))
        
        cursor.endEditBlock()
        self._text_edit.ensureCursorVisible()
    
    #--------------------------------------------------------------------------
    # Protected interface
    #--------------------------------------------------------------------------
    
    def _get_indent_column(self, line):
        trimmed = line.lstrip()
        if len(trimmed) != 0:
            return line.index(trimmed)
        else:
            # If the line is all spaces, treat it as indentation.
            return len(line)
    
    def _observe_language(self, change):
        if self._highlighter:
            self._highlighter.set_lexer(self.language)
    
    def _observe_style(self, change):
        if self._highlighter:
            self._highlighter.set_style(self.style)
    
    @observe('tab_width', 'text_font')
    def _update_font(self, change=None):
        if self._text_edit:
            if self.text_font is not None:
                qfont = get_cached_qfont(self.text_font)
            else:
                qfont = QFont()
            
            document = self._text_edit.document()
            document.setDefaultFont(qfont)
            
            fm = QFontMetrics(qfont)
            self._text_edit.setTabStopWidth(self.tab_width * fm.width(' '))
    
    @observe('text')
    def _update_text(self, change=None):
        if self._text_edit and not self._text_locked:
            self._text_edit.setPlainText(self.text)
    
    def _signal_text_changed(self):
        self._text_locked = True
        try:
            self.text = self._text_edit.toPlainText()
        finally:
            self._text_locked = False


class _CodeEditor(QTextEdit):
    
    def __init__(self, editor, parent=None):
        super(_CodeEditor, self).__init__(parent)
        self.editor = editor
    
    def keyPressEvent(self, event):
        """ Reimplemented to intercept certain key presses.
        """
        key_sequence = QKeySequence(event.key()+int(event.modifiers()))
        
        if key_sequence.matches(QKeySequence(QtCore.Qt.Key_Return)):
            event.accept()
            self.editor.newline()
            return
        
        elif key_sequence.matches(QKeySequence(QtCore.Qt.Key_Backspace)):
            event.accept()
            self.editor.backspace()
            return
        
        elif key_sequence.matches(QKeySequence(QtCore.Qt.Key_Tab)):
            event.accept()
            self.editor.indent()
            return
        
        return super(_CodeEditor, self).keyPressEvent(event)