# UCSB AS Elections Tabulator
Software by Associated Students, UC Santa Barbara.
Code - Ryan Tse.
Project - Sean Lieberman.

A Python-based elections tabulator utilizing a single transferable vote system with support for custom election configurations and dynamic ballot format parsing.

## Screenshot
<img align="center" src="https://cloud.githubusercontent.com/assets/12377481/14589208/0bc4ae68-0491-11e6-89cc-4e80bef73a9e.png" alt="UCSB AS Elections Tabulator Screenshot">

## Installation
Prerequisites:
- Python 3.3.0+
- pip

Installation:
```
pip install --upgrade -r requirements.txt
pip install --upgrade --pre --trusted-host wxpython.org -f http://wxpython.org/Phoenix/snapshot-builds/ wxPython_Phoenix
```

## Usage
The application can be started with: ``python ElectionApplication.py``.

For advanced configuration options, refer to the help documentation available by invoking ``python ElectionApplication.py --help``.

**References:**
The data format schemas for configuration, candidate, and ballot files can be found in the ``/schemas/`` directory. Configuration, candidate, and ballot file data are automatically compared against the provided JSON schemas prior to usage by the application. To verify a custom configuration/implementation, utilize a service like [JSON Schema Lint](http://jsonschemalint.com/draft4/ "JSON Schema Lint").

**_Sample Data:_**
Sample configuration and data can be found in ``/data/``. Existing format compatibility has been developed for UC Santa Barbara (``/data/ucsb/``) and UC Berkeley (``/data/ucb/``) ballot formats.

Refer to the ``/data/*/generated/`` folder for each respective directory for a random data generator for the file format. To invoke the generator, run ``python generator.py``. The resulting files will be created in the same directory.

## Compatibility
Tested on Mac OS X 10.11.4 and Windows 10 with:
- Python 3.5.1 (64-bit)
- wxPython-Phoenix 3.0.3.dev1964+f780b21
- jsonschema 2.5.1
- terminaltables 2.1.0

_Note: The application's performance has not been optimized for Windows._
