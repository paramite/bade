# -*- coding: utf-8 -*-

import os

from .. import utils
from . import init


def check_module_branch(repo, branch, module, info):
    """Returns current commit hash in module branch. Module branch
    is created according to Puppetfile if it does not exist.
    """
    _locals = locals()
    rc, stdout, stderr = utils.execute(
        'cd {repo} &>/dev/null && '
        'git checkout {branch}-{module}'.format(**_locals),
        can_fail=False
    )
    if rc:
        init.create_module_branch(repo, branch, module, info)

    # get current state
    rc, stdout, stderr = utils.execute(
        'cd {repo} &>/dev/null && '
        'git checkout {branch}-{module} &>/dev/null && '
        'git rev-parse HEAD && '
        'git checkout {branch} &>/dev/null'.format(**_locals)
    )
    return stdout.strip()


def merge_module_branch(repo, branch, module):
    """Merges new state of module branch to base branch."""
    rc, stdout, stderr = utils.execute(
        'cd {repo} && '
        'git checkout {branch} && '
        'git merge --squash -s subtree '
            '--no-commit {branch}-{module} && '
        'git stash'.format(**locals())
    )


def command(config, repo, branch):
    """Updates git subtree hierarchy according to the Puppetfile
    located in given 'repo'.
    """
    current_branch = utils.get_current_branch(repo)
    rc, stdout, stderr = utils.execute(
        'cd {repo} && '
        'git checkout {branch}'.format(**locals())
    )

    puppetfile = utils.PuppetFile(repo)
    puppetfile.load()

    branches = [
        '{0}-{1}'.format(branch, module) for module in puppetfile.keys()
    ]
    can_go_back = current_branch not in branches

    for module_branch in branches:
        _locals = locals()
        utils.shout(
            'Removing branch {module_branch}'.format(**_locals),
            verbose=config.verbose,
            level='info'
        )
        rc, stdout, stderr = utils.execute(
            'cd {repo} && '
            'git branch -D {module_branch}'.format(**_locals),
            can_fail=False
        )
        if rc:
            utils.shout(
                'Failed to remove branch {module_branch}'.format(**_locals),
                verbose=config.verbose,
                level='warning'
            )

    if can_go_back:
        rc, stdout, stderr = utils.execute(
            'cd {repo} && '
            'git checkout {current_branch}'.format(**locals())
        )
