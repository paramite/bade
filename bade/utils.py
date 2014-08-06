# -*- coding: utf-8 -*-

try:
    # Python2.x
    import ConfigParser as configparser
except ImportError:
    # Python 3.x
    import configparser

import click
import os
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


def load_environment(name):
    """Returns given environment configuration dict."""
    env = {}

    env_cfg_path = os.path.expanduser(
        os.path.join('~/.config/bade/environments', '{0}.conf'.format(name))
    )
    env_cfg = configparser.SafeConfigParser()
    if not env_cfg.read(env_cfg_path):
        raise RuntimeError('Failed to parse config file %s.' % env_cfg_path)

    env['base_repo'] = env_cfg.get('meta', 'base_repo')
    env['base_branches'] = [
        i.strip()
        for i in env_cfg.get('meta', 'base_branches').split(',')
        if i.strip()
    ]
    env['patches_path'] = env_cfg.get('meta', 'patches_path')

    env['modules'] = []
    for module in env_cfg.get('meta', 'modules').split(','):
        module = module.strip()
        env['modules'].append({
            'module': module,
            'path': env_cfg.get(module, 'path'),
            'branches': [
                i.strip()
                for i in env_cfg.get(module, 'branches').split(',')
                if i.strip()
            ],
        })
    return env


def get_base_branch(env, patch_branch):
    """Returns base branch for given patch branch."""
    base_branch = None
    for module in env['modules']:
        for branch in module['branches']:
            if branch != patch_branch:
                continue
            base = module['module'].split(':', 1)[0].strip()
            if base_branch is None:
                base_branch = base
            elif base != base_branch:
                raise RuntimeError(
                    'Base branch for branch {patch_branch} differs for module '
                    '{module} from other modules ({base_branch}). Please fix '
                    'that manually in ~/.config/bade/environments/{env}.conf '
                    'and try again.'.format(**locals())
                )
    return base_branch
