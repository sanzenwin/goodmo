# -*- coding:utf-8 -*-
import gc
import sys

REACHABLE = -10001
TENTATIVELY_UNREACHABLE = -10002


def get_unreachable_objects():
    gc_refs = {}
    for obj in gc.get_objects():
        assert id(obj) not in gc_refs
        gc_refs[id(obj)] = sys.getrefcount(obj) - 3
    obj = None

    for obj in gc.get_objects():
        for child in gc.get_referents(obj):
            if id(child) in gc_refs:
                gc_refs[id(child)] -= 1
        child = None
    obj = None

    is_running = True
    while is_running:
        for obj in gc.get_objects():
            assert id(obj) in gc_refs
            if gc_refs[id(obj)] == REACHABLE:
                continue
            if gc_refs[id(obj)] > 0:
                gc_refs[id(obj)] = REACHABLE
                for child in gc.get_referents(obj):
                    if id(child) in gc_refs:
                        if gc_refs[id(child)] == 0:
                            gc_refs[id(child)] = 1
                        elif gc_refs[id(child)] == TENTATIVELY_UNREACHABLE:
                            gc_refs[id(child)] = 1
                        else:
                            assert gc_refs[id(child)] > 0 or gc_refs[id(child)] == REACHABLE
                child = None
            elif gc_refs[id(obj)] == 0:
                gc_refs[id(obj)] = TENTATIVELY_UNREACHABLE
            else:
                assert gc_refs[id(obj)] in (REACHABLE, TENTATIVELY_UNREACHABLE)
        obj = None

        is_running = False
        for v in gc_refs.values():
            if v not in (REACHABLE, TENTATIVELY_UNREACHABLE):
                is_running = True
                break
        v = None

    unreachable = [k for k, v in gc_refs.items() if v == TENTATIVELY_UNREACHABLE]

    ret = []
    for obj in gc.get_objects():
        if id(obj) in unreachable:
            ret.append(obj)
    obj = None
    return ret
