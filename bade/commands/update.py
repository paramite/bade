# -*- coding: utf-8 -*-

import os

from .. import utils
from . import init


def merge_module_branch(repo, branch, module, commit):
    """Merges new state of module branch to base branch."""
    rc, stdout, stderr = utils.execute(
        'cd {repo} && '
        'git merge -s ours --squash --no-commit {branch}-{module} && '
        'git read-tree --prefix={module} '
            '-u {branch}-{module} {commit}'.format(**locals())
    )


def command(config, repo, module, new_commit, commit):
    """Updates git subtree module to given commit and updates Puppetfile."""

    # initialization
    puppetfile = utils.PuppetFile(repo)
    puppetfile.load()
    old_commit = puppetfile[module]['commit']
    branch = utils.get_current_branch(repo)
    _locals = locals()

    utils.shout(
        'Updating module {module} for branch {branch} '
            'in {repo}'.format(**_locals),
        verbose=config.verbose,
        level='info'
    )

    # updates module branch and base branch
    init.create_module_branch(repo, branch, module, puppetfile[module])
    merge_module_branch(repo, branch, module, new_commit)
    # updates Puppetfile
    puppetfile[module]['commit'] = new_commit
    puppetfile.save()

    if commit:
        utils.shout(
            'Generating commit',
            verbose=config.verbose,
            level='info'
        )
        status = (
            '{module}\\n - old commit: {old_commit}\\n'
                ' - new commit: {new_commit}\\n\\n'.format(**_locals)
        )
        _locals['msg'] = utils.COMMIT_MSG.format(status)
        rc, stdout, stderr = utils.execute(
            'cd {repo} && '
            'git add Puppetfile && '
            'git add {module} --ignore-errors && '
            'git commit -m $\'{msg}\''.format(**_locals)
        )
