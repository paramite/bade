# -*- coding: utf-8 -*-

from .. import utils


def update_patch_branch(config, path, patch_branch):
    """Updates patch_branch in give repo (by path) to state upstream patches
    repo is in.
    """
    _locals = locals()
    rc, stdout, stderr = utils.execute(
        'cd {path} && '
        'git checkout master && '
        '(git branch -D {patch_branch} || echo -n) && '
        'git fetch patches && '
        'git branch {patch_branch} patches/{patch_branch} && '
        'git checkout {patch_branch} && '
        'git pull patches {patch_branch}'.format(**_locals)
    )
    utils.shout('Updated {path}.'.format(**_locals), config.verbose)


def command(config, environment, patch_branch, module):
    """Rebases patch_branch for given module of given environment"""
    env = utils.load_environment(environment)
    base_branch = utils.get_base_branch(env, patch_branch)

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
        update_patch_branch(config, module['path'], patch_branch)
