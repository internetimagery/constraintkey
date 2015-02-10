# Constraintkey

Mimics a constriant setup, by keying an object in place. Perfect for simple / quick jobs where a full constraint setup is too much. Useful as a replacement to constraints as well, if you're ok with having to click the tool to refresh the keyframes.
The tool is also capable of constraining more than one object at a time. So it can be useful if you need to stick a bunch of things to one object in a hurry.

# Installation:

Simply copy the folder into your scripts directory in Maya. The folder should be named "constraintkey".

# Usage

Within Maya, create a shelf icon with the following PYTHON code:

	import constraintkey
	constraintkey.GUI()

IMPORTANT:
Due to the fact Constraintkey can constrain MORE THAN ONE thing at a time. The selection orders are reversed compared to normal constraints.

* Select the object(s) you want to FOLLOW first.

* Shift select the object you want to LEAD last. It should be green. Green is good.

* Select a time range in the time slider to pick the constraint range. Leave it empty if you wish to constrain across the entire range.

* Pick your constraint type.