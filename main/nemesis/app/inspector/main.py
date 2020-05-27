from __future__ import absolute_import

import argparse

from enaml.qt.qt_application import QtApplication
import traits_enaml

from nemesis.app.inspector import init_plot_config, init_plot_editors
from nemesis.data.sql_data_source import SQLDataSource
from nemesis.run_results import RunResults

from ..common.error_handling import init_error_handlers
from .main_window_controller import MainWindowController
with traits_enaml.imports():
    from .main_window import Main


def create_inspector(**traits):
    """ Create the main inspector window.
    """
    window = Main()
    traits['window'] = window
    controller = MainWindowController(**traits)

    init_plot_config()
    init_plot_editors()

    return window


def main():
    # Parse command-line arguments.
    parser = argparse.ArgumentParser(description = 'Nemesis Results Inspector',)
    parser.add_argument('--input', metavar='PATH', dest='input_path',
                        help='input database to load')
    parser.add_argument('--output', metavar='PATH', dest='output_path',
                        help='output database to load')
    parser.add_argument('--session', metavar='PATH', dest='session_path',
                        help='session file to load')
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    # At this point, we have valid arguments, so proceed with initialization.    
    
    # Create the application object.
    app = QtApplication()
    init_error_handlers(debug = args.debug)

    
    # Obtain the session and input and output sources.
    if args.session_path:
        main_window = create_inspector()
        main_window.main_controller.load_file(args.session_path)
    else:
        if args.input_path:
            input_source = SQLDataSource(dialect = 'sqlite',
                                         database = args.input_path)
        else:
            input_source = None

        if args.output_path:
            output_source = SQLDataSource(dialect = 'sqlite',
                                          database = args.output_path)
        else:
            output_source = None

        results = RunResults(input_source=input_source,
                             output_source=output_source)
        main_window = create_inspector(results=results)

    # Show the main window.
    main_window.show()
    app.start()


if __name__ == '__main__':
    main()
