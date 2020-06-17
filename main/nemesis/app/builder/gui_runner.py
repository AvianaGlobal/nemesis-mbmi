from __future__ import absolute_import
from enaml.qt import QtCore
from enaml.application import deferred_call, timed_call
from traits.api import HasTraits, Any, Instance
import traits_enaml
import enaml


from nemesis.ui.message_box import details_escape, warning, DialogButton

with traits_enaml.imports():
    from .run_dialog import RunDialog


class GUIRunner(HasTraits):
    """ Runs a model with a progress dialog and error reporting.
    """
    parent = Any()
    runner = Instance('nemesis.runner.Runner')

    def handle_error(self, msg, detail):
        """ Report a run error to the user.
        """
        warning(parent=self.parent,
                title='Run error',
                text='Run error',
                content=msg,
                details='<pre>%s</pre>' % details_escape(detail))

    def run(self):
        """ Run the model synchronously.
        Shows a modal dialog until the run completes.
        Returns the dialog.
        """
        runner = self.runner
        gui_handler = lambda *args: deferred_call(self.handle_error, *args)
        runner.error_handler = gui_handler
        dialog = RunDialog(
            parent=self.parent,
            title='Running model...',
            text='Please wait while the model runs.'
        )
        dialog.observe('rejected', lambda change: runner.cancel())
        dialog.show()
        event_loop = QtCore.QEventLoop()
        timer = QtCore.QTimer()

        def start_run():
            runner.run()
            timer.setInterval(50)
            timer.timeout.connect(check_loop)
            timer.start()

        def check_loop():
            dialog.output = runner.output()
            if not runner.running:
                timer.stop()
                event_loop.quit()

        timed_call(50, start_run)
        event_loop.exec_()
        dialog.accept()
        return dialog