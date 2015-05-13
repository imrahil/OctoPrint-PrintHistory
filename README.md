# Plugin for OctoPrint - saves filename, print time and filament usage for each print

![PrintHistory](printhistory.png?raw=true) 

## Setup

Install the plugin like you would install any regular Python package from source:

    pip install https://github.com/imrahil/OctoPrint-PrintHistory/archive/master.zip
    
Make sure you use the same Python environment that you installed OctoPrint under, otherwise the plugin
won't be able to satisfy its dependencies.

## Upgrade to newest version
    pip install --ignore-installed --force-reinstall --no-deps https://github.com/imrahil/OctoPrint-NavbarTemp/archive/master.zip

## Installation for OctoPi users
(taken from https://github.com/markwal/OctoPrint-GPX)

1. Start with OctoPi: Get your Raspberry Pi up and running by following the
   instructions on [OctoPi](https://github.com/guysoft/OctoPi)

2. OctoPi runs OctoPrint in a virtualenv. You'll want to switch to the
   virtualenv for installing packages so they'll be available to OctoPrint.
   Activating the environment means that when you type python or pip, it'll use
   the ones out of ~/oprint/bin and use ~/oprint/lib for all package installs
   and dependencies.  You can tell it is working by the "(oprint)" in front of
   your prompt
    ```
    source ~/oprint/bin/activate
    ```

3. Switch to the devel branch of OctoPrint
  (https://github.com/foosel/OctoPrint/wiki/FAQ#how-can-i-switch-the-branch-of-the-octoprint-installation-on-my-octopi-image)
    ```
    cd ~/OctoPrint
    git pull & git checkout devel
    python setup.py clean
    python setup.py install
    ```
4. run

    ```
    pip install https://github.com/imrahil/OctoPrint-PrintHistory/archive/master.zip
    sudo service octoprint restart
    ```
