# -*- coding: utf-8 -*-

import codecs
import datetime
import jinja2
import os

from .. import utils
from . import init


# setup jinja environment
jinja_env = jinja2.Environment(
    block_start_string='[@',
    block_end_string='@]',
    variable_start_string='[[',
    variable_end_string=']]',
    trim_blocks=True,
    loader=jinja2.FileSystemLoader([
        # bades built-in templates
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'templates'
        ),
        # user's templates
        os.path.join(
            os.path.expanduser('~'), '.bade', 'templates'
        )
    ])
)

def format_datetime(value):
    return value.strftime('%a %b %d %Y')
jinja_env.filters['datetime'] = format_datetime


def format_global(value):
    return value.replace('-', '_')
jinja_env.filters['global'] = format_global


def format_rjust(value, value_from, offset):
    space = offset - len(value_from) + len(value)
    return value.rjust(space)
jinja_env.filters['rjust'] = format_rjust


def command(config, repo, version, release, old, output, template):
    """Generates SPEC file from template and tags repo accordingly.
    """
    puppetfile = utils.PuppetFile(repo)
    puppetfile.load()

    # fill required metadata to puppetfile
    for module, info in puppetfile.items():
        info['fullname'] = (
            os.path.basename(info['git']).split('.', 1)[0]
        )
        for key, value in info.items():
            info[key] = unicode(value)

    # get changelog from old spec
    _locals = locals()
    rc, stdout, stderr = utils.execute(
        'tail -n +$('
            'grep -n -e "^%changelog" {old} | cut -d\':\' -f1'
        ') {old}'.format(**_locals),
        can_fail=False
    )
    old_changelog = u'' if rc else stdout[len('%changelog'):]
    old_changelog = old_changelog.decode('utf-8')

    # get patches from old spec
    rc, stdout, stderr = utils.execute(
        'grep "^Patch[0-9]*:" {old}'.format(**_locals),
        can_fail=False
    )
    patches_list = u'' if rc else stdout.decode('utf-8')

    rc, stdout, stderr = utils.execute(
        'grep "^%patch[0-9]*" {old}'.format(**_locals),
        can_fail=False
    )
    patches_apply = u'' if rc else stdout.decode('utf-8')

    # get current date
    current_date = datetime.datetime.today()

    # get name and email from git repo
    rc, stdout, stderr = utils.execute(
        'cd {repo} && '
        'git config --get user.name && '
        'git config --get user.email'.format(**_locals)
    )
    user_name, user_email = stdout.strip().split('\n', 1)
    user_name = user_name.decode('utf-8')
    user_email = user_email.decode('utf-8')

    # generate message for a tag
    msg = '{0}-{1}\\n'.format(version, release)
    for module, info in puppetfile.items():
        msg += '{0}{1}\\n'.format(
            module, format_rjust(info['commit'], module, 10)
        )

    # generate spec file
    _locals = locals()
    template_obj = jinja_env.get_template(template)
    with codecs.open(os.path.abspath(output), 'wb', 'utf-8') as ofile:
        ofile.write(template_obj.render(**_locals))

    # tag repo
    rc, stdout, stderr = utils.execute(
        'cd {repo} && '
        'git tag -a -m $\'{msg}\' {version}'.format(**_locals)
    )
    utils.shout(
        'New tag {version} has been created in repo. Please run '
        '"git push origin {version}" to upload tag '
        'to upstream'.format(**_locals),
        verbose=True,
        level='info'
    )
