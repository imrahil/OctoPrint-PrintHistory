# Plugin for OctoPrint - saves filename, print time and filament usage for each print

## Setup

Install the plugin like you would install any regular Python package from source:

    pip install https://github.com/imrahil/OctoPrint-PrintHistoryPlugin/archive/master.zip
    
Make sure you use the same Python environment that you installed OctoPrint under, otherwise the plugin
won't be able to satisfy its dependencies.

Restart OctoPrint. `octoprint.log` should show you that the plugin was successfully found and loaded:

    2014-09-18 17:49:21,500 - octoprint.plugin.core - INFO - Loading plugins from ... and installed plugin packages...
    2014-09-18 17:49:21,611 - octoprint.plugin.core - INFO - Found 2 plugin(s): Print History Plugin (0.1), Discovery (0.1)