# -*- coding: utf-8 -*-

try:
    # Python2.x
    import ConfigParser as configparser
except ImportError:
    # Python 3.x
    import configparser

import click
import os
import re

from .. import utils


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


def update_base_branch(repo, branch):
    """Updates given branch in given repo."""
    _locals = locals()
    rc, stdout, stderr = utils.execute(
        'cd {repo} && '
        'git checkout {branch} && '
        'git pull origin {branch} && '
        'git submodule sync && '
        'git submodule update --init'.format(**_locals)
    )


def get_modules_status(repo, branch):
    """Returns current modules status on given branch."""
    rc, stdout, stderr = utils.execute(
        'cd {repo} && '
        'git checkout {branch} &>/dev/null && '
        'git submodule status'.format(**locals())
    )
    return utils.parse_submodule_status(stdout)


def rebase_patch_branch(config, path, base_branch, patch_branch, base_commit):
    """Rebases patches repo given by patch in branch patch_branch
    to base_commit."""
    rc, stdout, stderr = utils.execute(
        'cd {path} && '
        'git fetch origin-{base_branch} && '
        'git checkout {patch_branch} && '
        '(git branch -D new-base-{patch_branch} || echo -n) && '
        'git checkout -b new-base-{patch_branch} {base_commit} && '
        'git checkout {patch_branch} && '
        'git rebase new-base-{patch_branch}'.format(**locals()),
        can_fail=False
    )
    if rc:
        utils.shout(
            'Failed to rebase module {path} because:\n{stderr}\n'
            'Please finish rebase manually.'.format(**locals()),
            config.verbose
        )

def command(config, environment, patch_branch, module):
    """Rebases patch_branch for given module of given environment"""
    env = load_environment(environment)
    base_branch = get_base_branch(env, patch_branch)
    update_base_branch(env['base_repo'], base_branch)

    status = get_modules_status(env['base_repo'], base_branch)
    if module:
        modules = [
            i for i in env['modules']
            if i['module'] == '{0}:{1}'.format(base_branch, module)
        ]
    else:
        modules = [
            i for i in env['modules']
            if i['module'].split(':')[0].strip() == base_branch
        ]

    for module in modules:
        rebase_patch_branch(
            config,
            module['path'],
            base_branch, patch_branch,
            status[module['module'].split(':')[1].strip()]['commit']
        )
