# -*- coding: utf-8 -*-

import click
import pipes
import re
import subprocess
import time
import types


_status_regex = re.compile(r'^\s*(?P<hash>\w+)\s(?P<name>[\w\-\_]+)\s.*')
_module_regex = re.compile(
    r'\[submodule "(?P<name>[\w\/\-_\.]+)"\]\n'
     '\s*path\s*=\s*(?P<path>[\w\/\-_]+)\s*\n'
     '\s*url\s*=\s*(?P<url>[\w\.\/\:\-_]+)\n'
)


class ExecutionError(RuntimeError):
    def __init__(self, *args, **kwargs):
        self.stdout = kwargs.pop('stdout')
        self.stderr = kwargs.pop('stderr')
        super(ExecutionError, self).__init__(*args, **kwargs)


# taken from Kanzo (https://github.com/paramite/kanzo) and simplified
def execute(cmd, workdir=None, can_fail=True, log=True):
    """
    Runs shell command cmd. If can_fail is set to True RuntimeError is raised
    if command returned non-zero return code. Otherwise returns return code
    and content of stdout and content of stderr.
    """
    log_msg = ['Executing command: %s' % cmd]

    proc = subprocess.Popen(cmd, cwd=workdir, shell=True, close_fds=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if proc.returncode and can_fail:
        raise ExecutionError('Failed to execute command: %s' % cmd,
                             stdout=out, stderr=err)
    return proc.returncode, out, err


# taken from Kanzo (https://github.com/paramite/kanzo)
def retry(count=1, delay=0, retry_on=Exception):
    """Decorator which tries to run specified callable if the previous
    run ended by given exception. Retry count and delays can be also
    specified.
    """
    if count < 0 or delay < 0:
        raise ValueError('Count and delay has to be positive number.')

    def decorator(func):
        def wrapper(*args, **kwargs):
            tried = 0
            while tried <= count:
                try:
                    return func(*args, **kwargs)
                except retry_on:
                    if tried >= count:
                        raise
                    if delay:
                        time.sleep(delay)
                    tried += 1
        wrapper.func_name = func.func_name
        return wrapper
    return decorator


def shout(msg, verbose=False, nl=True):
    if verbose:
        click.echo(msg, nl=nl)


def parse_submodule_status(stdout):
    result = {}
    for line in stdout.split('\n'):
        match = _status_regex.match(line.strip())
        if not match:
            continue
        module = match.group('name')
        result.setdefault(module, {'commit': match.group('hash')})
    return result


def parse_gitmodule(stdout):
    result = {}
    match = _module_regex.search(stdout)
    if not match:
        raise RuntimeError('Module has not been found in .gitmodules')

    module = match.group('name')
    result.setdefault(module, {
        'path': match.group('path'),
        'url': match.group('url')
    })
    return result
