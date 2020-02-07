from __future__ import absolute_import

import os, shutil, tempfile
import logging
import subprocess
from traceback import format_exception_only
try:
    from concurrent import futures # version 3
except ImportError:
    import futures # version 2

from traits.api import (HasTraits, Bool, Callable, Directory, File, Instance,
                        Property)

from .data.data_source import DataSource
from .data.sql_data_source import SQLDataSource
from .model import Model
from .run_results import RunResults
from .r import ast, ast_transform
from .r.pretty_print import write_ast
from .r import R_HOME

logger = logging.getLogger(__name__)


class Runner(HasTraits):
    """ Runs a model on data.
    """
    
    # The model to run.
    model = Instance(Model)
    
    # Whether the model is currently running.
    running = Property(Bool)
    
    # The input data for the model.
    input_source = Instance(DataSource)
    
    # The destination for model results. 
    output_source = Instance(SQLDataSource)
    
    # The results from the model run.
    results = Instance(RunResults)
    
    # The handler for model run errors, a callable of form:
    #     handler(msg, detail)
    # If not specified, errors are logged using the `logging` module.
    error_handler = Callable()
    
    # Private storage.
    _proc = Instance(subprocess.Popen)
    _log_path = File()
    _output_dir = Directory()
    
    # Runner interface
    
    def ast(self):
        """ Generate the AST for a complete R program executing the model.
        """
        # Build program body.
        prog = self._ast_impl()
        
        # Extract required libraries and load them first.
        libs = ast_transform.find_libraries(prog)
        lib_block = ast.Block([
            ast.Call(ast.Name('library'), ast.Name(lib)) for lib in libs
        ])
        prog.value.insert(0, lib_block)
        
        return prog
        
    def run(self):
        """ Run the model asynchronously.
        
        Returns the Future instance for the run.
        """
        if not self.model:
            raise RuntimeError('No model defined')
        elif not self.input_source:
            raise RuntimeError('No input data for model run')

        self._proc = self._run_start()
        return self._proc
        
    def run_and_wait(self):
        """ Run the model synchronously.
        
        Returns the run results.
        """
        self.run()
        while self.running: pass
        return self.results

    def output(self):
        if os.path.exists(self._log_path):
            return open(self._log_path, 'r').read()
        return ''

    def cancel(self):
        if self._proc is not None:
            self._proc.cancelled = True

            if os.name == 'nt':
                # On Windows, calling terminate() does not kill the grandchild
                # processes that the R executable spawns.
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.call([
                    'taskkill', '/pid', str(self._proc.pid), '/T', '/F'
                ], shell=False, startupinfo=startupinfo)

            else:
                self._proc.terminate()

    def write_program(self, out):
        """ Write the complete R program to a file-like object.
        """
        write_ast(self.ast(), out)

    # Private interface

    def _get_running(self):
        if self._proc is None:
            return False

        if self._proc.poll() is None:
            return True

        self._run_finish(self._proc)
        self._proc = None
        return False

    def _ast_impl(self):
        nodes = [ self.model.ast() ]
        if self.input_source:
            run_args = self.input_source.ast()
            if isinstance(run_args, ast.Node):
                run_args = [ (ast.Name('input'), run_args) ]
            if self.output_source:
                conn = self.output_source.ast_for_dbi_call(
                    ast.Name('dbConnect'))
                run_args += [ 
                    (ast.Name('output'), conn),
                    (ast.Name('store_input'),
                     ast.Constant(self.model.store_input)),
                ]
            run_nodes = [
                ast.Call(ast.Name('run_model'), run_args, print_hint='long'),
            ]
            nodes += [
                ast.Comment('Execute model'),
                ast.Block(run_nodes),
            ]
        return ast.Block(nodes, print_hint='long')
    
    def _handle_error(self, msg, detail):
        handled = False
        if self.error_handler:
            try:
                self.error_handler(msg, detail)
            except:
                logger.exception('Error in error handler!')
            else:
                handled = True
        if not handled:
            logger.error(msg + '\n\n' + detail)
    
    def _run_start(self):
        # Create output directory.
        self._output_dir = tempfile.mkdtemp(prefix='elite_')
        
        # Write the R script to disk.
        prog_path = os.path.join(self._output_dir, 'model.R')
        with open(prog_path, 'w') as f:
            self.write_program(f)
    
        # Run the R script. 
        r_path = os.path.join(R_HOME, 'bin', 'R')
        self._log_path = os.path.join(self._output_dir, 'run.Rout')
        cmd = [r_path, 'CMD', 'BATCH', '--vanilla', prog_path, self._log_path]
        
        startupinfo = None
        if os.name == 'nt':
            # Don't show a console in Windows.
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            return subprocess.Popen(cmd, shell=False, startupinfo=startupinfo)
        except OSError as exc:
            msg = 'Exception raised during model run.'
            detail = ''.join(format_exception_only(type(exc), exc))
            self._handle_error(msg, detail)

    def _run_finish(self, proc):
        try:
            results = None

            if getattr(proc, 'cancelled', False):
                logger.info('Model run cancelled')

            elif proc.returncode != 0:
                msg = 'Exit code %i from model run.' % proc.returncode
                try:
                    output = self.output()
                except:
                    detail = 'Cannot recover any output from R.'
                else:
                    detail = 'Captured R output:\n' + '-' * 70 + '\n' + output
                self._handle_error(msg, detail)

            # No errors so far. Try to retrieve the results.
            else:
                if self.model.store_input:
                    input_source = None
                else:
                    input_source = self.input_source
                try:
                    results = RunResults(input_source=input_source,
                                         output_source = self.output_source)
                except Exception as exc:
                    msg = 'Exception raised while reading run results.'
                    detail = ''.join(format_exception_only(type(exc), exc))
                    self._handle_error(msg, detail)

            self.results = results
        
        finally:
            if os.path.isdir(self._output_dir):
                shutil.rmtree(self._output_dir)
