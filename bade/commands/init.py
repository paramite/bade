# -*- coding: utf-8 -*-

import os

from .. import utils


def create_module_branch(repo, branch, module, info):
    """Creates module branch for given 'module' from git repo and
    commit given by 'info' dict. Parameter 'branch' states to which
    branch will be the module branch imported.
    """
    _locals = locals()
    @utils.retry(count=3, retry_on=utils.ExecutionError)
    def fetch():
        rc, stdout, stderr = utils.execute(
            'cd {repo} && '
            'git fetch {branch}-{module}'.format(**_locals)
        )

    # cleanup
    rc, stdout, stderr = utils.execute(
        'cd {repo} && '
        'git remote rm {branch}-{module}'.format(**_locals),
        can_fail=False
    )
    rc, stdout, stderr = utils.execute(
        'cd {repo} && '
        'git checkout {branch} && '
        'git branch -D {branch}-{module}'.format(**_locals),
        can_fail=False
    )
    # fetch remote repo
    rc, stdout, stderr = utils.execute(
        'cd {repo} && '
        'git remote add {branch}-{module} '
            '{info[git]}'.format(**_locals)
    )
    fetch()
    # (re)create branch from given commit
    rc, stdout, stderr = utils.execute(
        'cd {repo} && '
        'git checkout -b {branch}-{module} {info[commit]} && '
        'git checkout {branch}'.format(**_locals)
    )


def import_module_branch(repo, branch, module):
    """Pulls appropriate repo branch to given branch."""
    _locals = locals()
    # cleanup
    rc, stdout, stderr = utils.execute(
        'cd {repo} && '
        'git checkout {branch} && '
        'git reset HEAD {module} && '
        'git checkout -- {module}'.format(**_locals),
        can_fail=False
    )
    rc, stdout, stderr = utils.execute(
        'cd {repo} && '
        'git checkout {branch} && '
        'rm -fr {module}'.format(**_locals)
    )
    # pull the branch
    rc, stdout, stderr = utils.execute(
        'cd {repo} && '
        'git checkout {branch} && '
        'git read-tree --prefix={module}/ '
            '-u {branch}-{module}'.format(**_locals)
    )


def command(config, repo, commit):
    """Creates git subtree hierarchy according to the Puppetfile
    located in given 'repo'.
    """
    puppetfile = utils.PuppetFile(repo)
    puppetfile.load()
    branch = utils.get_current_branch(repo)

    for module, info in puppetfile.items():
        utils.shout(
            'Initializing branch for {0} on branch {1}'.format(
                module, branch
            ),
            verbose=config.verbose,
            level='info'
        )
        create_module_branch(repo, branch, module, info)
        utils.shout(
            'Pulling module branch {0}-{1} to branch {0}'.format(
                branch, module
            ),
            verbose=config.verbose,
            level='info'
        )
        import_module_branch(repo, branch, module)

    if commit:
        utils.shout(
            'Generating commit',
            verbose=config.verbose,
            level='info'
        )
        paths = ' '.join(puppetfile.keys())
        status = ''
        for mod in sorted(puppetfile.keys()):
            status += (
                '{mod}\\n - initial commit: {commit}\\n\\n'.format(
                    mod=mod, commit=puppetfile[mod]['commit']
                )
            )
        msg = utils.COMMIT_MSG.format(status)
        rc, stdout, stderr = utils.execute(
            'cd {repo} && '
            'git add {paths} --ignore-errors && '
            'git commit -m $\'{msg}\''.format(**locals())
        )
