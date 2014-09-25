# -*- coding: utf-8 -*-

import os

from .. import utils
from . import init


def check_module_branch(repo, branch, module):
    """Returns current commit hash in module branch."""
    # get current state
    rc, stdout, stderr = utils.execute(
        'cd {repo} &>/dev/null && '
        'git checkout {branch}-{module} &>/dev/null && '
        'git rev-parse HEAD && '
        'git checkout {branch} &>/dev/null'.format(**locals())
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


def command(config, repo, commit):
    """Updates git subtree hierarchy according to the Puppetfile
    located in given 'repo'.
    """
    puppetfile = utils.PuppetFile(repo)
    puppetfile.load()
    branch = utils.get_current_branch(repo)

    changed = []
    for module, info in puppetfile.items():
        utils.shout(
            'Checking branch for {0} on branch {1}'.format(
                module, branch
            ),
            verbose=config.verbose,
            level='info'
        )
        current = check_module_branch(repo, branch, module)
        if current != info['commit']:
            # recreate module branch
            init.create_module_branch(repo, branch, module, info)
            utils.shout(
                'Merging module branch {0}-{1} to branch {0}'.format(
                    branch, module
                ),
                verbose=config.verbose,
                level='info'
            )
            # merge new module branch and stash changes
            merge_module_branch(repo, branch, module)
            changed.insert(0, (module, current))

    # get changes back from stash
    for module, old in changed:
        _locals = locals()
        rc, stdout, stderr = utils.execute(
            'cd {repo} && '
            'git checkout {branch} && '
            'git stash apply && '
            'git stash drop'.format(**_locals),
            can_fail=False
        )
        if rc:
            utils.shout(
                'Failed to unstash changes for {module}:'
                    '\n{stdout}'.format(**_locals),
                verbose=True,
                level='warning'
            )

    if changed and commit:
        utils.shout(
            'Generating commit',
            verbose=config.verbose,
            level='info'
        )
        paths = ' '.join([i[0] for i in changed])
        status = ''
        for mod, old in sorted(changed):
            status += (
                '{mod}\\n - old commit: {old}\\n'
                    ' - new commit: {new}\\n\\n'.format(
                    mod=mod, old=old, new=puppetfile[mod]['commit']
                )
            )
        msg = utils.COMMIT_MSG.format(status)
        rc, stdout, stderr = utils.execute(
            'cd {repo} && '
            'git add {paths} --ignore-errors && '
            'git commit -m $\'{msg}\''.format(**locals())
        )
