"""Automatic vox changer"""
import os
import sys
from pathlib import Path
import xonsh.lazyasd as lazyasd
import xontrib.voxapi as voxapi

__all__ = ()


class _AvoxHandler:
    """Automatic vox"""
    def parser():
        from argparse import ArgumentParser
        parser = ArgumentParser(prog='avox', description=__doc__)
        subparsers = parser.add_subparsers(dest='command')

        create = subparsers.add_parser('new', aliases=['create'], help='Create a new virtual environment')
        create.add_argument('--system-site-packages', default=False,
                            action='store_true', dest='system_site',
                            help='Give the virtual environment access to the '
                                 'system site-packages dir.')
        from xonsh.platform import ON_WINDOWS

        group = create.add_mutually_exclusive_group()
        group.add_argument('--symlinks', default=not ON_WINDOWS,
                           action='store_true', dest='symlinks',
                           help='Try to use symlinks rather than copies, '
                                'when symlinks are not the default for '
                                'the platform.')
        group.add_argument('--copies', default=ON_WINDOWS,
                           action='store_false', dest='symlinks',
                           help='Try to use copies rather than symlinks, '
                                'even when symlinks are the default for '
                                'the platform.')
        create.add_argument('--without-pip', dest='with_pip',
                            default=True, action='store_false',
                            help='Skips installing pip in the '
                                 'virtual environment (pip is bootstrapped '
                                 'by default)')

        subparsers.add_parser('remove', aliases=['rm', 'delete', 'del'], help='Remove virtual environment')
        subparsers.add_parser('help', help='Show this help')
        return parser

    parser = lazyasd.LazyObject(parser, locals(), 'parser')

    aliases = {
        'create': 'new',
        'rm': 'remove',
        'delete': 'remove',
        'del': 'remove',
    }

    @classmethod
    def handler(cls, args, stdin=None):
        return cls()(args, stdin)

    def __init__(self):
        if not __xonsh__.env.get('PROJECT_DIRS'):
            print("Warning: Unconfigured $PROJECT_DIRS. Using ~/code")
            home_path = os.path.expanduser('~')
            self.projdirs = [os.path.join(home_path, 'code')]
            __xonsh__.env['PROJECT_DIRS'] = self.projdirs
        else:
            self.projdirs = __xonsh__.env['PROJECT_DIRS']
            if isinstance(self.projdirs, str):
                self.projdirs = [self.projdirs]

        self.vox = voxapi.Vox()

    def env(self, pwd=None, exact=False):
        """
        Figure out the environment name for a directory.
        """
        proj = self.envForNew(pwd)
        if proj is None:
            return

        envs = set(self.vox)
        while proj:
            if proj in envs:
                return proj
            if exact:
                return
            proj = os.path.dirname(proj)  # Abuse, this is actually a vox venv name
        else:
            return

    def envForNew(self, pwd=None):
        """
        Guess an environment name for a directory without actually seeing what environments exist.
        """
        if pwd is None or pwd is ...:
            pwd = Path.cwd()
        else:
            pwd = Path(pwd)
        for pd in self.projdirs:
            try:
                proj = pwd.relative_to(Path(pd))
            except ValueError:
                continue
            else:
                return str(proj)
        else:
            return

    def __call__(self, args, stdin=None):
        args = self.parser.parse_args(args)
        cmd = self.aliases.get(args.command, args.command)
        if cmd is None:
            self.parser.print_usage()
        else:
            getattr(self, 'cmd_'+cmd)(args, stdin)

    def cmd_new(self, args, _=None):
        if self.vox.active():
            self.vox.deactivate()
        if self.env() is not None:
            print("Working directory already has a virtual environment.", file=sys.stderr)
            return
        proj = self.envForNew()
        if proj is None:
            print("Working directory not a project. Is $PROJECT_DIRS configured correctly?", file=sys.stderr)
            return
        if proj in self.vox:
            print("Conflict! Project matches name of existing virtual environment, but wasn't detected. Possibly a bug?", file=sys.stderr)
            return
        print("Creating virtual environment {}...".format(proj))
        self.vox.create(proj)
        print("Activating...")
        self.vox.activate(proj)

    def cmd_remove(self, args, _=None):
        if self.vox.active():
            self.vox.deactivate()
        proj = self.env()
        if proj is None:
            print("No virtual environment for the current directory", file=sys.stderr)
            return
        print("Deleting {}...".format(proj))
        del self.vox[proj]

    def cmd_help(self, args, stdin=None):
        self.parser.print_help()


@events.autovox_policy
def avox_policy(path, **_):
    self = _AvoxHandler()
    return self.env(path, exact=True)


aliases['avox'] = _AvoxHandler.handler
