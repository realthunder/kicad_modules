#!/usr/bin/python

import os, sys, re, glob

sys.path.append('scripts')

import util

def getConfPath(subpath):
    if 'APPDATA' in os.environ:
        confpath = os.path.join(util.getAbsolutePath(os.environ['APPDATA']),'kicad')
    else:
        confpath = '/usr/share/kicad'
    if subpath:
        return os.path.join(confpath,subpath)
    return confpath

def set3dmod():
    kicad_common = getConfPath('kicad_common')
    if not os.path.isfile(kicad_common):
        print 'no kicad_common'
        return 1
    with open(kicad_common,'rb') as f:
        content = f.read()
    match = re.search(r'^\s*KISYS3DMOD\s*=\s*([^\r\n]+)',content,re.MULTILINE)
    if not match:
        print 'no KISYS3DMOD found'
        return 1

    kisys3dmod = match.group(1).rstrip(' ')
    if sys.platform == 'cygwin':
        my3dmod = util.getAbsolutePath('packages3d/').replace('\\','\\\\')
    else:
        my3dmod = os.path.abspath('packages3d/')

    if kisys3dmod == my3dmod:
        return 1

    print 'change KISYS3DMOD {} => {}'.format(kisys3dmod,my3dmod)
    content = content[:match.start()] + 'KISYS3DMOD=' + my3dmod + \
            content[match.end():]

    util.backup(kicad_common)
    with open(kicad_common,'wb') as f:
        f.write(content)


def install(modules, replace):

    fp_table = getConfPath('fp-lib-table')
    if not os.path.isfile(fp_table):
        print 'no fp-lib-table'
        return 1

    with open(fp_table,'rb') as f:
        content = f.read()

    # find the last ')'
    eof = content.rindex(')')
    # find the '\n' preceed the last ')'
    eof = content.rindex('\n',0,eof)
    # trim the file so it ends with the '\n' before last ')'
    content = content[:eof+1]

    if content[eof-1] == '\r':
        eol = '\r\n'
    else:
        eol = '\n'

    dirty = False
    for module in modules:
        mpath = module
        if not mpath.endswith('.pretty'): mpath += '.pretty'
        if not os.path.isdir(mpath): 
            print 'skip ' + module
            continue

        mname = os.path.splitext(mpath)[0]
        mabspath = util.getAbsolutePath(mpath)

        if re.search(r'\(\s*uri\s*' + mabspath + r'\)', content):
            print 'skip '+mname
            continue

        newlib = '  (lib (name ' + mname + ')(type KiCad)(uri ' + mabspath + ')(options "")(descr ""))'

        match = re.search(r'^\s*\(\s*lib\s*\(\s*name\s+' + mname + r'\)[^\r\n]+', content, re.MULTILINE)
        if match:
            if replace:
                dirty = True
                print 'replace ' + mname
                print '    ' +  match.group()
                print '  =>' + newlib
                content = content[:match.start()] + newlib + \
                        content[match.end():]
            else:
                print 'warning! moudle named ' + mname + ' already exists'
                continue
        else:
            print 'insert ' + mname
            print '    ' + newlib
            dirty = True
            content += newlib+eol

    if not dirty: return 2

    content += ')' + eol

    util.backup(fp_table)
    with open(fp_table,'wb') as f:
        f.write(content)

    return 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='KiCad footprint module installer')
    parser.add_argument('modules', metavar='module name', type=str, nargs='*',
            help='one or more module names, default to all')
    parser.add_argument('-r', action='store_true',dest='replace',
            help='force replace of module with the same name')
    parser.add_argument('-s', action='store_true',dest='set3dmod',
            help='set KISYS3DMOD to point to this repository')
    args = parser.parse_args()

    if args.set3dmod:
        set3dmod()

    ret = install(args.modules,args.replace)
    sys.exit(ret)
