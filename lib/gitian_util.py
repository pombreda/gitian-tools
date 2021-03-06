import sys
import yaml
import os
import shutil
import fnmatch
from optparse import SUPPRESS_HELP

def prepare_build_package(ptr, do_clean = False):
    if not os.access("build", os.F_OK):
        os.makedirs("build")
        res = os.system("cd build && git init")
        if res != 0:
            print >> sys.stderr, "git init failed"
            sys.exit(1)

        do_clean = True

    if do_clean:
        os.system("cd build && git remote | grep --quiet '^origin$' && git remote rm origin")
        res = os.system("cd build && git remote add origin '%s'" % (ptr['url']))
        if res != 0:
            print >> sys.stderr, "git remote add failed"
            sys.exit(1)

        res = os.system("cd build && git fetch --quiet origin")
        if res != 0:
            print >> sys.stderr, "git fetch failed"
            sys.exit(1)

        res = os.system("cd build && git checkout -f '%s'" % (ptr['commit']))
        if res != 0:
            print >> sys.stderr, "git checkout failed"
            sys.exit(1)

        res = os.system("cd build && git clean -d -f -x")
        if res != 0:
            print >> sys.stderr, "git clean failed"
            sys.exit(1)

def open_package(name):
    repos = repository_root()

    package_dir = os.path.join(repos, "packages", name)

    try:
        control_f = open(os.path.join(package_dir, "control"))
    except IOError, e:
        print >> sys.stderr, "package does not exist - %s"%(name)
        sys.exit(1)

    control = yaml.load(control_f)
    control_f.close()

    name = control['name']
    ptr_f = open(os.path.join(package_dir, name + '.vcptr'))

    if ptr_f is None:
        print >> sys.stderr, "could not open version control pointer file"
        sys.exit(1)

    ptr = yaml.load(ptr_f)
    ptr_f.close()

    return (package_dir, control, ptr)

    
def repository_root():
    dir = os.getcwd()
    parent = os.path.dirname(dir)
    while (parent != dir):
        if os.access(os.path.join(dir, "gitian-repos"), os.F_OK):
            return dir

        dir = parent
        parent = os.path.dirname(dir)

    print >> sys.stderr, "must be run within the gitian repository"
    exit(1)

def shell_complete(option, opt, value, parser):
    for option in parser.option_list:
        for flag in str(option).split('/'):
            if option.help != SUPPRESS_HELP:
                print "(-)%s[%s]"%(flag, option.help)
    exit(0)

def optparser_extend(parser):
    parser.add_option ("", "--shell-complete", action="callback",
                       callback=shell_complete,
                       help=SUPPRESS_HELP
                      )

def find_command(command):
    progdir = os.path.dirname(sys.argv[0])

    for dir in [os.path.join(progdir, "../lib"), "/usr/lib/gitian"]:
        if os.access(os.path.join(dir, command), os.F_OK):
            found_dir = dir
            return os.path.join(dir, command)

    command = "gitian-" + command

    for dir in [os.path.join(progdir, "../lib"), "/usr/lib/gitian"]:
        if os.access(os.path.join(dir, command), os.F_OK):
            found_dir = dir
            return os.path.join(dir, command)

    print>>sys.stderr, "installation problem - could not find subcommand %s"%(command)
    exit(1)

def build_tar(package_dir, control, ptr, destination, do_copy=False, do_clean=False):
    name = control['name']

    os.chdir(package_dir)

    prepare_build_package(ptr, do_clean)

    packager_options = control.get('packager_options', {}) or {}

    build_cmd = packager_options.get('build_cmd', 'rake -t -rlocal_rubygems gem')
    os.chdir(package_dir)

    print "Building package %s (copy=%s)" % (name, do_copy)
    res = os.system("cd build && %s" % (build_cmd))
    if res != 0:
        print >> sys.stderr, "build failed"
        sys.exit(1)
    if do_copy:
        copy_tars_to_dist("build", destination)

def build_gem(package_dir, control, ptr, destination, do_copy=False, do_clean=False):
    name = control['name']

    os.chdir(package_dir)

    prepare_build_package(ptr, do_clean)

    packager_options = control.get('packager_options', {}) or {}

    build_cmd = packager_options.get('build_cmd', 'rake -t -rlocal_rubygems gem')
    packages = control.get('packages')

    depends = control.get('build_depends', []) or []
    for depend in depends:
        ensure_gem_installed(depend, destination)

    os.chdir(package_dir)

    if packages:
        for package in packages:
            print "Building package %s (copy=%s)" % (package, do_copy)
            # default to package name
            dir = control['directories'].get(package, package)
            subdir = os.path.join("build", dir)
            res = os.system("cd %s && %s" % (subdir, build_cmd))
            if res != 0:
                print >> sys.stderr, "build in build/%s failed" % (dir)
                sys.exit(1)
            if do_copy:
                copy_gems_to_dist(subdir, destination)

    else:
        print "Building package %s (copy=%s)" % (name, do_copy)
        res = os.system("cd build && %s" % (build_cmd))
        if res != 0:
            print >> sys.stderr, "build failed"
            sys.exit(1)
        if do_copy:
            copy_gems_to_dist("build", destination)

def copy_gems_to_dist(subdir, destination):
    print "installing to %s"%(destination)
    gems_destination = os.path.join(destination, "rubygems/gems")
    found = False
    for dirpath, dirs, files in os.walk(subdir):
        for file in fnmatch.filter(files, '*-*.*.gem'):
            if not os.access(gems_destination, os.F_OK):
                os.makedirs(gems_destination)
            shutil.copy(os.path.join(dirpath, file), gems_destination)
            found = True
    if not found:
        print >> sys.stderr, "no gem found"
        sys.exit(1)

def copy_tars_to_dist(subdir, destination):
    print "installing to %s"%(destination)
    tars_destination = os.path.join(destination, "rubygems/tars")
    found = False
    for dirpath, dirs, files in os.walk(subdir):
        for file in fnmatch.filter(files, '*-*.*.tar'):
            if not os.access(tars_destination, os.F_OK):
                os.makedirs(tars_destination)
            shutil.copy(os.path.join(dirpath, file), tars_destination)
            found = True
    if not found:
        print >> sys.stderr, "no tar found"
        sys.exit(1)

GEM_CHECK_COMMAND = "ruby -rlocal_rubygems -e 'exit(Gem.source_index.find_name(\"%s\").length==0?1:0)'"

def ensure_gem_installed(gem, dest):
    components = gem.split("/")
    if len(components) == 1:
        package = gem
    else:
        (package, gem) = components

    res = os.system(GEM_CHECK_COMMAND%(gem))
    if res != 0:
        (package_dir, control, ptr) = open_package(package)
        build_gem(package_dir, control, ptr, dest)
        install_built_gems(dest, gem)

        res = os.system(GEM_CHECK_COMMAND%(gem))
        if res != 0:
            print >>sys.stderr, "failed to install gem %s" % (gem)

def install_built_gems(dest, gem = None):
    gemrc = os.path.join(dest, "gemrc")
    for dirpath, dirs, files in os.walk('build'):
        if gem is None:
            pattern = '*.gem'
        else:
            pattern = "%s-*.gem"%(gem)

        for file in fnmatch.filter(files, pattern):
            cmd = "gem --config-file '%s' install --no-ri --no-rdoc --ignore-dependencies %s"%(
                gemrc, os.path.join(dirpath, file))
            res = os.system(cmd)
            if res != 0:
                print >>sys.stderr, "failed to install gem with: %s" % (cmd)

def ensure_rubygems_installed(dest):
    gemhome = os.path.join(dest, ".gem")
    if not os.access(os.path.join(gemhome, "bin", "gem1.8"), os.F_OK):
        (package_dir, control, ptr) = open_package("rubygems")
        os.chdir(package_dir)

        prepare_build_package(ptr)
        res = os.system("cd build && ruby setup.rb --no-ri --no-rdoc --prefix=%s > /dev/null" % (gemhome))
        if res != 0 or not os.access(os.path.join(gemhome, "bin", "gem1.8"), os.F_OK):
            print >>sys.stderr, "build failed in %s" % (dir)
            sys.exit(1)
    local_rubygems_rb = os.path.join(gemhome, "lib", "local_rubygems.rb")
    if not os.access(local_rubygems_rb, os.F_OK):
        rb_f = open(local_rubygems_rb, "w")
        print >>rb_f, """require "rubygems" 
Gem.configuration = Gem::ConfigFile.new [ "--config-file=/dev/null" ] 
Gem.sources = ["/dev/null"]
Gem.use_paths(ENV['GEM_HOME'], [ENV['GEM_HOME']])
"""
        rb_f.close()
    gemrc = os.path.join(dest, "gemrc")
    if not os.access(gemrc, os.F_OK):
        gemrc_f = open(gemrc, "w")
        print >>gemrc_f, """---
:gemhome: %s
:gempath:
- %s
:sources:
- bogus:
"""%(gemhome, gemhome)
        gemrc_f.close()
    os.environ['GEM_HOME'] = gemhome
    os.environ['PATH'] = os.path.join(gemhome, "bin") + ":" + os.environ['PATH']
    os.environ['RUBYLIB'] = os.path.join(gemhome, "lib")
    os.environ['RAKE_CMD'] = "rake -rlocal_rubygems"
    os.environ['RAKE_ARGS'] = "-rlocal_rubygems"
    os.environ['GEM_CMD'] = "gem1.8 --config-file=%s"%(gemrc)
    os.environ['GEM_ARGS'] = "--config-file=%s"%(gemrc)

