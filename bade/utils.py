# -*- coding: utf-8 -*-

import pipes
import subprocess
import types


class ExcetutionError(RuntimeError):
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
