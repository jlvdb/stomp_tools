import os
import sys
from contextlib import contextmanager


@contextmanager
def stdout_redirected(dst=os.devnull):
    """
    Redirect all output from stdout temporarily to a file descriptor within the
    context manager.

    Parameters
    ----------
    dst : file descriptor
        File descriptor to which stdout is redirected (defaults to /dev/null).
    """

    term = sys.stdout.fileno()

    def redirect(dst):
        sys.stdout.close()
        os.dup2(dst.fileno(), term)  # redirects non-python output
        sys.stdout = os.fdopen(term, 'w')  # keep python on stdout

    with os.fdopen(os.dup(term), 'w') as term_restore:
        with open(dst, 'w') as file:
            redirect(file)
        try:
            yield
        finally:  # restore
            redirect(term_restore)


@contextmanager
def stderr_redirected(dst=os.devnull):
    """
    Redirect all output from stderr temporarily to a file descriptor within the
    context manager.

    Parameters
    ----------
    dst : file descriptor
        File descriptor to which stderr is redirected (defaults to /dev/null).
    """

    term = sys.stderr.fileno()

    def redirect(dst):
        sys.stderr.close()
        os.dup2(dst.fileno(), term)  # redirects non-python output
        sys.stderr = os.fdopen(term, 'w')  # keep python on stderr

    with os.fdopen(os.dup(term), 'w') as term_restore:
        with open(dst, 'w') as file:
            redirect(file)
        try:
            yield
        finally:  # restore
            redirect(term_restore)
