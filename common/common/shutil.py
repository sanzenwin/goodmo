import os
import shutil


def do_tree_ext(work, exts, src, dest):
    fp = {}
    extss = exts.lower().split()
    for dn, dns, fns in os.walk(src):
        for fl in fns:
            if os.path.splitext(fl.lower())[1][1:] in extss:
                if dn not in fp.keys():
                    fp[dn] = []
                fp[dn].append(fl)
    for k, v in fp.items():
        relativepath = k[len(src) + 1:]
        newpath = os.path.join(dest, relativepath)
        for f in v:
            oldfile = os.path.join(k, f)
            if not os.path.exists(newpath):
                os.makedirs(newpath)
            work(oldfile, newpath)


def cp_tree_ext(exts, src, dest):
    do_tree_ext(shutil.copy, exts, src, dest)


def mv_tree_ext(exts, src, dest):
    do_tree_ext(shutil.move, exts, src, dest)
