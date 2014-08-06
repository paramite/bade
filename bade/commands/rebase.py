# -*- coding: utf-8 -*-

from .. import utils


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
    env = utils.load_environment(environment)
    base_branch = utils.get_base_branch(env, patch_branch)
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
