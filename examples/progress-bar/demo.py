"""
More complex demonstration of what's possible with the progress bar.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts.progress_bar import progress_bar
from prompt_toolkit import HTML
import time



with progress_bar(
        title=HTML('<b fg="#aa00ff">Progress bar example:</b> <u>nested progress bars...</u>'),
        bottom_toolbar=HTML('<b>[Control-L]</b> clear  <b>[Control-C]</b> abort')) as pb:

    for i in pb(range(6), title='Progress 1'):
        for j in pb(range(400), title='Progress 2'):
            time.sleep(.01)

