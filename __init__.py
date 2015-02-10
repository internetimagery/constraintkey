from functools import partial
import maya.cmds as cmds
import maya.mel as mel

# Created 12/03/14 Jason Dixon
# http://internetimagery.com/

#select objects that move first, then object to constrain to last.
class constraintKey(object):
    def __init__(self):
        self.selection = []
        self.timerange = []
        self.locator = []
        #begin!
        cmds.undoInfo( openChunk = True)
        self.selection = cmds.ls( selection=True )
        if self.selection:
            #check time range
            slider = mel.eval('$tempvar = $gPlayBackSlider')
            if cmds.timeControl( slider, rangeVisible = True, query=True ):
                self.timerange = cmds.timeControl ( slider, query = True, rangeArray = True )
            else:
                if cmds.confirmDialog( title = 'Just checking...' , message = "Clicking confirm will constrain to the ENTIRE timeline.\n\nIs this what you want?" ) == 'Confirm':
                    self.timerange = [ (cmds.playbackOptions( min = True, query = True )) , (cmds.playbackOptions( max = True, query = True )) ]
            if self.timerange:
                cmds.currentTime( self.timerange[0] )
                if len(self.selection) == 1:
                    self._createLocator( self.selection[0] )
                else:
                    for i in range(len(self.selection)-1):
                        self._createLocator( self.selection[i] )
        else:
            cmds.confirmDialog( title = 'Whoops...', message = 'Nothing selected.')
    def _translate(self, i, obj):
        if i == self.timerange[1]:
            cmds.cutKey( obj['obj'], at='translate', t=(self.timerange[0],self.timerange[1]), cl=True )
        cmds.xform( obj['obj'] , ws = True, translation = cmds.getAttr( (obj['loc']+'.translate') )[0] )
        cmds.setKeyframe( obj['obj'] , attribute = 'translate', time = i )
    def _rotate(self, i, obj):
        if i == self.timerange[1]:
            cmds.cutKey( obj['obj'], at='rotate', t=(self.timerange[0],self.timerange[1]), cl=True )
        rot = self._listmath( obj['offset'] , cmds.getAttr( (obj['loc']+'.rotate') )[0] , lambda x, y : x + y )
        cmds.rotate( rot[0], rot[1], rot[2], obj['obj'], a = True )
        cmds.setKeyframe( obj['obj'] , attribute = 'rotate', time = i )
    def _loop(self, methods):
        if self.locator and self.timerange:
            euler = 'cmds.filterCurve('
            bake = []
            for loc in self.locator:
                bake.append( loc['loc'] )
                for at in ['_rotateX','_rotateY','_rotateZ']:
                    euler+='"'+loc['loc']+at+'",'
            cmds.bakeResults( bake, sm=True, t=(self.timerange[0],self.timerange[1]) )
            eval( (euler+')') )
            for loc in self.locator:
                loc['offset'] = self._listmath( cmds.getAttr( (loc['loc']+'.rotate') )[0], loc['offset'], lambda x, y : y - x )
            timerange = int(self.timerange[1] - self.timerange[0])+1
            for i in range(timerange):
                i = self.timerange[1]-i #make it run in reverse... because it looks cooler that way - like a zip zap machine
                cmds.currentTime( i )
                for obj in self.locator:
                    for method in methods:
                        method( i, obj )
    def _createLocator(self, object):
        locator = cmds.spaceLocator()[0]
        cmds.xform( locator , roo = cmds.xform( object, query=True, roo=True ) )
        cmds.delete( cmds.parentConstraint( object , locator ) )
        self.locator.append( {  'loc':locator,
                                'obj': object,
                                'offset': cmds.getAttr( (object+'.rotate') )[0] } )
    def _listmath(self, list1, list2, method):
        try:
            new = []
            for i in range(len(list1)):
                new.append( self._listmath( list1[i] , list2[i], method ) )
        except:
            new = method( list1, list2 )
        return new
    def _glue(self, constraint, driver, locator, skip = []):
        command = 'cmds.'+constraint+'Constraint("'+driver+'","'+locator['loc']+'",mo=True'
        #maybe add in axis skips here? future update...
        eval( (command+')') )
    def __del__(self):
        for locator in self.locator:
            cmds.delete( locator['loc'] )
        cmds.select( clear = True )
        for obj in self.selection:
            cmds.select( obj , add = True )
        #end!
        cmds.undoInfo( closeChunk = True)

    #constraints! parent / pivot / orient / point / aim
    def parent(self):
        if len(self.selection) > 1:
            for obj in self.locator:
                self._glue( 'parent' , self.selection[-1], obj )
        self._loop([ self._translate , self._rotate ])
    def pivot(self):
        if len(self.selection) > 1:
            for obj in self.locator:
                self._glue( 'parent' , self.selection[-1], obj )
        self._loop([ self._translate ])
    def orient(self):
        if len(self.selection) > 1:
            for obj in self.locator:
                self._glue( 'orient' , self.selection[-1], obj )
        self._loop([ self._rotate ])
    def point(self):
        if len(self.selection) > 1:
            for obj in self.locator:
                self._glue( 'point' , self.selection[-1], obj )
        self._loop([ self._translate ])
    def aim(self): #requires two objects selected
        if len(self.selection) > 1:
            for obj in self.locator:
                cmds.parentConstraint( obj['obj'], obj['loc'], mo=True, sr=['x','y','z'] )
                self._glue( 'aim' , self.selection[-1], obj )
            self._loop([ self._rotate ])

class constraintKeyGUI(object):
    def __init__(self):
        #gui for constraints
        self.pane = cmds.window( title = 'Constraint Key')
        cmds.gridLayout( nc=2, cwh=[100, 30] )
        cmds.button( label = 'PARENT', command = partial(self.run, 'parent') )
        cmds.button( label = 'PIVOT', command = partial(self.run, 'pivot') )
        cmds.button( label = 'AIM', command = partial(self.run, 'aim') )
        cmds.button( label = 'ORIENT', command = partial(self.run, 'orient') )
        cmds.button( label = 'POINT', command = partial(self.run, 'point') )
        cmds.button( label = 'Create Shelf', command = self.shelf )
        cmds.setParent('..')
        cmds.showWindow( self.pane )
    def run(self, command, blah):
        run = 'constraintKey().'+command+'()'
        eval( run )
    def shelf(self, blah):
        shelf = cmds.tabLayout( (mel.eval('$tempvar = $gShelfTopLevel')), st=True, query = True )
        existing = cmds.shelfLayout( shelf , q=True, ca=True )
        shelfbutton = 'ConstraintKeyOMGYES'
        if shelfbutton not in existing: #isn't there
            cmds.shelfButton( shelfbutton , parent=shelf, image = 'activeSelectedAnimLayer.png', label = 'ConstraintKey', c="from constraintkey import *\nconstraintKeyGUI()" )

def GUI():
	constraintKeyGUI()

def parent():
	constraintKey().parent()

def pivot():
	constraintKey().pivot()

def orient():
	constraintKey().orient()

def point():
	constraintKey().point()

def aim():
	constraintKey().aim()