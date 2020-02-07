from __future__ import absolute_import
import pyface
import traits_enaml
import argparse
from enaml.qt.qt_application import QtApplication
from elite.data.file_data_source import FileDataSource
from elite.stdlib import init_stdlib
from elite.app.common.error_handling import init_error_handlers
from elite.app.builder.main_window_controller import MainWindowController

with traits_enaml.imports():
    from elite.app.builder.main_window import Main


def main():
    # Parse command-line arguments.
    parser = argparse.ArgumentParser(
        description='Nemesis Model Builder',
    )
    parser.add_argument('model_path', metavar='MODEL', nargs='?', help='model file to load')
    parser.add_argument('--data', metavar='PATH', dest='data_path', help='data file to load')
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    # At this point, we have valid arguments, so proceed with initialization.
    # Initialize the standard metrics and controls.
    init_stdlib()
    # Create the application object.
    app = QtApplication()
    init_error_handlers(debug=args.debug)
    if args.data_path:
        input_source = FileDataSource(path=args.data_path)
    else:
        input_source = None
    main_window = Main()
    controller = MainWindowController(
        input_source=input_source,
        debug_mode=args.debug,
        window=main_window,
    )
    if args.model_path:
        controller.load_file(args.model_path)
    main_window.show()
    app.start()


if __name__ == '__main__':
    main()
