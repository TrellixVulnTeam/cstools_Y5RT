# -*- coding: UTF-8 -*-
#
# Tools/pythonlibs/SjBTools.py
# Copyright © 2015 SjB <steve@sagacity.ca>. All Rights Reserved.

import glob
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile

try: 
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve

protobuild_url = 'https://github.com/SjB/Protobuild/blob/master/Protobuild.exe?raw=true'
nuget_url = 'http://nuget.org/nuget.exe'

def getplatform():
    p = sys.platform
    if p.startswith('linux'):
        return 'Linux'
    elif p == 'darwin':
        return 'MacOS'
    elif p == 'win32':
        return 'Windows'

    print("Unsuppored Platform.")
    return ''


if "Windows" == getplatform():
   pythoncmd = "py.exe"
else:
   pythoncmd = "python"


def configure(project_path, platform):
    cmd = [pythoncmd, os.path.join(project_path, 'bootstrap.py'), 'configure', '--platform', platform];
    run(cmd)


def build(solution, args):
    platform = getplatform()
    build_tool = 'xbuild'
    if "Windows" == platform:
        build_tool='msbuild'

    cmd = [build_tool, solution]
    cmd.extend(args)

    run(cmd)


def delete(*args):
    path = os.path.join(*args)

    for f in glob.glob(path):
        if os.path.isdir(f):
            shutil.rmtree(f)

        if os.path.isfile(f):
            os.unlink(f)


def gitclone(repo, path, branch=None):
    if not os.path.exists(path):
        cmd = ['git', 'clone']
        if (branch != None):
            cmd.extend(['-b', branch])

        cmd.extend([repo, path])
        run(cmd)


def run(*args, **kwargs):
    returncode = subprocess.call(*args, **kwargs)
    if returncode != 0:
        sys.exit(returncode)


def tar(url, path):
    filename = os.path.basename(url)
    wget(url, filename=filename)
    with tarfile.open(filename) as tar:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tar, path)

    os.unlink(filename)


def wget(url, filename=None):
    if filename:
        dir = os.path.dirname(filename)
        if dir and not os.path.exists(dir):
            os.makedirs(dir)

    (filename, header) = urlretrieve(url, filename)
    print('Fetching: ' + filename)


def zip(url, path):
    filename = os.path.basename(url)
    wget(url, filename=filename)
    with zipfile.ZipFile(filename, 'r') as zip:
        zip.extractall(path)

    os.unlink(filename)


class NuGet:

    def __init__(self, workspace):
        self.workspace = workspace
        self.cliapp = os.path.join(workspace, 'nuget.exe')

    def exists(self):
        return os.path.exists(self.cliapp)

    def fetch(self):
        wget(nuget_url, filename=self.cliapp)

    def run(self, command, *args):
        if os.path.exists(self.cliapp):
            cmd = []

            platform = getplatform()
            if "Windows" != platform:
                cmd.append('/usr/bin/mono')

            out = os.path.join(self.workspace, 'packages')
            cmd.extend([self.cliapp, command, '-OutputDirectory',  out])
            cmd.extend(args)
            return run(cmd)

        print("Missing %s." % self.cliapp)
        return False


    def install(self, platform=None, args=[], exclude = []):
        if platform == None:
            platform = getplatform()

        args.append(' ')

        for root, dirs, files in os.walk(self.workspace):
            for dname in dirs:
                if os.path.join(root, dname) in exclude:
                    dirs.remove(dname)

            for name in files:
                if name in ['packages.config', 'packages.%s.config' % platform]:
                    args[-1] = os.path.join(root, name)
                    self.run('install', *args)


    def get(self, package, path, version=None):
        cmd = [package]
        if version:
            cmd.extend(['-version', version])

        self.run('install', *cmd)


    def clean(self):
        delete(self.workspace, 'packages')

class Protobuild:

    def __init__(self, workspace):
        self.workspace = workspace
        self.cliapp = os.path.join(workspace, 'Protobuild.exe')

    def generate(self, platform = None):
        if platform == None:
            platform = getplatform()
        self.run('-generate', platform)

    def run(self, *args):
        if os.path.exists(self.cliapp):
            cmd = []

            platform = getplatform()
            if "Windows" != platform:
                cmd.append('/usr/bin/mono')

            cmd.append(self.cliapp)
            cmd.extend(args)

            return run(cmd)

        print("Missing %s." % self.cliapp)
        return False

    def exists(self):
        return os.path.exists(self.cliapp)

    def fetch(self):
        wget(protobuild_url, filename=self.cliapp)

    def clean(self, platform = None, exclude = []):
        if platform == None:
            platform = getplatform()

        self.run('-clean', platform)

        delete(self.workspace, '*.speccache')

        exclude.append('.git')
        for root, dirs, files in os.walk(self.workspace):
            for name in dirs:
                if name in exclude:
                    dirs.remove(name)
                    continue

                if name in ['obj', 'bin']:
                    p = os.path.join(root, name)
                    print("Removing: %s" % p)
                    shutil.rmtree(p);


        
