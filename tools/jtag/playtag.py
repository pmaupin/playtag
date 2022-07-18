# Create a python package on the fly
import os
__package__ = None
__path__ = [os.path.normpath(os.path.join(__file__, '..','..','..', 'playtag'))]
