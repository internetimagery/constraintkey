# Constrain using keyframes

import report
import itertools
import functools
import maya.mel as mel
import maya.cmds as cmds

def warning(text):
    cmds.warning(text)
    cmds.confirmDialog(t="Uh oh...", m=text)

def shift(iterable, size):
    """ iterate in groups ie [1,2,3] [2,3,4] """
    i = itertools.tee(iterable, size)
    for a, b in enumerate(i):
        for c in range(a):
            b.next()
    return itertools.izip(*i)

def chunk(iterable, size, default=None):
    """ iterate in chunks ie [1,2,3] [4,5,6] """
    i = iter(iterable)
    return itertools.izip_longest(*[i]*size, fillvalue=default)

class Callback(object):
    """ generic callback """
    def __init__(s, func, *args, **kwargs): s.__dict__.update(**locals())
    def __call__(s, *_): return s.func(*s.args, **s.kwargs)


class Main(object):
    """ Constain quickly using keyframes """
    def __init__(s):
        with report.Report():
            name = "constrainkeywin"

            if cmds.window(name, q=True, ex=True):
                cmds.deleteUI(name)

            win = cmds.window(name, t="Constraint Key", rtf=True)
            cmds.gridLayout(nc=2, cwh=(100, 30))
            cmds.button(l="PARENT", c=Callback(s.constrain, cmds.parentConstraint, [0,1]))
            cmds.button(l="PIVOT", c=Callback(s.constrain, cmds.parentConstraint, [1])) # Parent constraint rotation only
            cmds.button(l="AIM", c=Callback(s.constrain, cmds.aimConstraint, [1]))
            cmds.button(l="ORIENT", c=Callback(s.constrain, cmds.orientConstraint, [1]))
            cmds.button(l="POINT", c=Callback(s.constrain, cmds.pointConstraint, [0]))
            cmds.button(l="SCALE", c=Callback(s.constrain, cmds.scaleConstraint, [2]))
            cmds.showWindow(win)

    def get_selection(s):
        """ Grab selected objects. Returns [obj1, obj2] """
        sel = cmds.ls(sl=True, type="transform") or []
        if len(sel) < 3: return sel
        return []

    def get_range(s):
        """ Get frame range. Returns [min, max, is_selection] """
        slider = mel.eval("$tmp = $gPlayBackSlider")
        if cmds.timeControl(slider, q=True, rv=True):
            return tuple(cmds.timeControl(slider, q=True, ra=True)), True
        return (
            cmds.playbackOptions(q=True, min=True),
            cmds.playbackOptions(q=True, max=True)
            ), False

    @report.Report()
    def constrain(s, constraint, attr):
        """ Constrain objects """
        selection = s.get_selection()
        if not selection: return warning("Please select one or two objects.")

        frame_range, selected = s.get_range()
        if not selected and "Yes" != cmds.confirmDialog(b=("Yes", "No"), t="Confirming...", m="You have chosen to key the entire timeline.\nIs this ok?"):
            return

        err = cmds.undoInfo(openChunk=True)
        try:
            if len(selection) == 1: # Constrain to world
                data = s.stationary_data(frame_range, selection[0])
                driven = selection[0]
            if len(selection) == 2: # Constrain first obj to second
                data = s.follow_data(constraint, frame_range, *selection)
                driven = selection[1]

            s.apply_keys(data, frame_range, attr, driven)

        except Exception as err:
            raise
        finally:
            cmds.undoInfo(closeChunk=True)
            if err: cmds.undo()

    def follow_data(s, constraint, frame_range, driver, driven):
        """ Stick one object to another! """
        marker = cmds.spaceLocator()[0]
        try:
            matrix = cmds.xform(driven, q=True, ws=True, m=True)
            roo = cmds.xform(driven, q=True, roo=True) # Copy across rotation order
            cmds.xform(marker, roo=roo, m=matrix) # Move marker to driven object
            constraint(driver, marker, mo=True) # Stick it in place

            # Get our base to work from
            cmds.bakeResults(marker, t=frame_range, sm=True)

            # Record keyframes
            num_keys = int(frame_range[1] - frame_range[0]) + 1
            attr = [".".join((marker, a)) for a in "trs"]
            time = cmds.keyframe(attr, q=True, tc=True) or []
            keys = cmds.keyframe(attr, q=True, vc=True) or []
            data = itertools.izip(time[:num_keys], *chunk(keys, num_keys))
        finally:
            cmds.delete(marker) # clean up!
        return data

    def stationary_data(s, frame_range, driven):
        """ Stick one object to the world """
        t = cmds.xform(driven, ws=True, q=True, t=True)
        r = cmds.xform(driven, ws=True, q=True, ro=True)
        s = cmds.xform(driven, ws=True, q=True, s=True)
        data = ([a]+t+r+s for a in range(int(frame_range[0]), int(frame_range[1]+1)))
        return data

    def apply_keys(s, data, frame_range, filter_, driven):
        """ Apply keyframe data to the object """
        if not filter_: return warning("No attributes provided")
        state = cmds.autoKeyframe(q=True, st=True)
        cmds.autoKeyframe(st=False)
        try:
            kwargs = {"ws": True} # Set up our arguments
            attrs = []
            if 0 in filter_:
                attrs.append("%s.t" % driven)
                kwargs["t"] = None
            if 1 in filter_:
                attrs.append("%s.r" % driven)
                kwargs["ro"] = None
            if 2 in filter_:
                attrs.append("%s.s" % driven)
                kwargs["s"] = None

            cmds.cutKey(attrs, t=frame_range, cl=True) # Remove keys first. Prevents keys between frames

            for t, tx, ty, tz, rx, ry, rz, sx, sy, sz in data:
                cmds.currentTime(t) # Move to the current frame
                if "t" in kwargs: kwargs["t"] = (tx, ty, tz)
                if "ro" in kwargs: kwargs["ro"] = (rx, ry, rz)
                if "s" in kwargs: kwargs["s"] = (sx, sy, sz)
                cmds.xform(driven, **kwargs)
                cmds.setKeyframe(attrs)
            if "ro" in kwargs: # Clean up with euler filter
                cmds.filterCurve("%s.r" % driven)
        finally:
            cmds.autoKeyframe(st=state)
