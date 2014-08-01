# -*- coding: utf-8 -*-

import click
import os
import re

from .. import utils


_status_regex = re.compile(r'^(?P<hash>\w+)\s(?P<name>[\w\-\_]+)\s.*')
_module_regex = re.compile(
    r'path\s*=\s*(?P<path>[\w\/\-_]+)\s*\n'
     '\s*url\s*=\s*(?P<url>[\w\.\/\:\-_]+)\n'
)


@utils.retry(count=3, retry_on=utils.ExecutionError)
def initialize_repo(path, remote, base_branch, patches_repo):
    """Either clones repo if it does not exits on 'path' already or just adds
    new remote according to 'base_branch' name. In case repo is cloned origin
    remote is renamed according to 'base_branch' name. Returns name of added
    remote.
    """
    remote_name = 'origin-{0}'.format(base_branch)
    _locals = locals()
    if os.path.exists(path) and os.path.exists('{0}/.git'.format(path)):
        # repository already exists
        rc, stdout, stderr = utils.execute(
            'cd {path} && git remote show {remote_name}'.format(**_locals),
            can_fail=False
        )
        if rc:
            # remote does not exist so we add it
            rc, stdout, stderr = utils.execute(
                'cd {path} && '
                'git remote add {remote_name} {remote}'.format(**_locals)
            )
        else:
            # remote already exists so we just change url
            rc, stdout, stderr = utils.execute(
                'cd {path} && '
                'git remote set-url {remote_name} {remote}'.format(**_locals)
            )
    else:
        # repository does not exist
        rc, stdout, stderr = utils.execute(
            'git clone {remote} {path} && '
            'cd {path} && '
            'git remote rename origin {remote_name}'.format(**_locals)
        )

    # add patches remote for patches repo if it does not exists
    rc, stdout, stderr = utils.execute(
        'cd {path} && '
        '(git remote show patches && '
        ' git remote set-url patches {patches_repo}) || '
        'git remote add patches {patches_repo} &&'
        'git fetch --all'.format(**_locals)
    )
    return remote_name


@utils.retry(count=3, retry_on=utils.ExecutionError)
def initialize_patch_branch(path, commit, patch_branch):
    """Either creates new 'patch_branch' from 'commit' and pushes it to
    patches repo or pulls existing 'patch_branch' from patches repo.
    """
    _locals = locals()
    rc, stdout, stderr = utils.execute(
        'cd {path} && '
        'git branch | grep "{patch_branch}"'.format(**_locals),
        can_fail=False
    )
    if not rc:
        rc, stdout, stderr = utils.execute(
            'cd {path} && '
            'git checkout {patch_branch} && '
            'git pull patches {patch_branch}'.format(**_locals)
        )
    else:
        rc, stdout, stderr = utils.execute(
            'cd {path} && '
            'git checkout -b {patch_branch} {commit} && '
            'git push patches {patch_branch}'.format(**_locals)
        )


def load_modules(repo, target, patches_repo_base, branches):
    """Loads information about all submodules in given 'repo' for the list
    of 'branches'.
    """

    modules = {}
    for branch in branches:
        rc, stdout, stderr = utils.execute(
            'cd {repo} &>/dev/null && '
            'git checkout {branch} &>/dev/null && '
            'git submodule sync && '
            'git submodule update --init &>/dev/null && '
            'git submodule status'.format(**locals())
        )
        modules[branch] = parse_submodule_status(stdout)

        for module, info in modules[branch].items():
            rc, stdout, stderr = utils.execute(
                'cd {repo} && cat .gitmodules | '
                'grep -A2 "\\[submodule \\"{module}\\"\\]"'.format(**locals())
            )
            module_def = parse_gitmodule(stdout)
            modules[branch][module]['path'] = os.path.join(target,
                                                           module_def['path'])
            modules[branch][module]['url'] = url = module_def['url']

            base_name = os.path.basename(url)
            if base_name.endswith('.git'):
               base_name = base_name[:-4]
            modules[branch][module]['patches_repo'] = os.path.join(
                patches_repo_base,
                '{0}-patches.git'.format(base_name)
            )
    return modules


def command(config, repo, base, target, branches, name):
    """Clones all submodule repos of 'repo' to 'target' directory and sets
    them remote named patches with url composed from
    <base>/<submodule-basename>-patches. Patches remotes have to exist
    in advance. If list of 'branches' are given also patches branches
    are created and pushed to patches repos. Format of branches item is:
    main-repo-branch:patches-repo-branch.
    """
    # initial setup
    if not branches:
        branches = 'master:patches'
    branches = map(
        lambda x: tuple(x.split(':', 1)),
        [i.strip() for i in branches.split(',')]
    )
    branch_map = {}
    for br in branches:
        branch_map.setdefault(br[0], []).append(br[1])

    repo = os.path.abspath(repo)
    target = os.path.abspath(target)
    _locals = locals()

    if not os.path.exists(repo):
        click.echo('Given repo does not exist: {repo}'.format(**_locals))
        return 1

    config_dir = os.path.expanduser('~/.config/bade/environments')
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    utils.shout('Creating target directory: {target}'.format(**_locals),
          config.verbose)
    os.makedirs(os.path.abspath(target))

    utils.shout('Loading module map', config.verbose)
    module_map = load_modules(repo, target, base, branch_map.keys())

    # creation of patches repos
    module_list = {}
    for branch, modules in module_map.items():
        for module, info in modules.items():
            index = '{0}:{1}'.format(branch, module)
            module_list.setdefault(index, {'path': info['path']}
            )
            utils.shout(
                'Initializing patches repo for module {module} '
                    'on branch {branch}:'.format(**locals()),
                config.verbose
            )
            remote = initialize_repo(info['path'], info['url'], branch,
                                     info['patches_repo'])
            for patch_branch in branch_map[branch]:
                module_list[index].setdefault('branches', []).append(
                    patch_branch
                )
                utils.shout(
                    ' - initializing patch branch '
                        '{patch_branch}'.format(**locals()),
                    config.verbose
                )
                initialize_patch_branch(info['path'], info['commit'],
                                        patch_branch)

    # safe environment
    with open(os.path.join(config_dir, '{0}.conf'.format(name)), 'w') as env:
        env.writelines([
            '[meta]\n',
            'base_repo={0}\n'.format(repo),
            'base_branches={0}'.format(','.join(branch_map.keys())),
            'patches_path={0}\n'.format(target),
            'modules={0}\n'.format(','.join(module_list.keys())),
            '\n',
        ])
        for module, info in module_list.items():
            env.writelines([
                '[{0}]\n'.format(module),
                'path={0}\n'.format(info['path']),
                'branches={0}\n'.format(','.join(info['branches'])),
                '\n'
            ])
