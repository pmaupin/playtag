Playtag Debugging Utilities
===========================

Copyright (c) 2011, 2022 Patrick Maupin


Introduction
-------------

These scripts are designed to allow easy playing with JTAG.

The model is that there are cable drivers, and multiple
layers of library functions, and then programs to support specific
functions, with the library functions making the programs
insensitive to which cable driver is being used.

### Python supported

This should support Python 3.6+, and work on any OS.
_However_, it was originally written for Python 2 and
ported in a hurry, so some idiom and optimization work
might be warranted.

### Cable drivers supported

 - This can communicate with anything providing a Xilinx XVC
   cable driver (although currently it only supports the
   shift command).
 - This can communicate with FTDI chips that support
   MPSSE using FTDI's D2XX drivers.

### Front end programs supported

  - The 'discover.py' script allows you to discover
    supported adapters and the JTAG chain.
  - This can provide a server to be able to use a generic
    FTDI cable with Xilinx tools, via an XVC cable driver.
    Several example start-up scripts are provided.
  - This can program an Artix FPGA (e.g. for the Digilent
    Nexys Video) from a bitfile
  - This can communicate with the Artix FPGA, using
    some example Verilog give.

### Future work

  - Better support for targeting devices in chains
    of multiple devices.

  - Whatever I need (or anybody else wants to contribute)
    for JTAG.  The main utility of this is the abstraction
    of JTAG, and the optimizations for the FTDI cable.

Historical functionality
------------------------

The original impetus for the program was the high cost
of the Gaisler Research debug dongle, so this was done
in a hurry to support the LEON3 core (with a gdb server)
communicating with a digilent cable.

Later, a driver to drive any FTDI chip directly in MPSSE
mode was added.  Several programs were added, included
cable chain discovery, an SVF parser, some parsers for
BSDL files (that do not directly use the chain drivers,
but that provide data for the chain discovery), and,
finally, a program that provides a server for the
Xilinx XVC virtual JTAG cable.

This was all under Python2, and is still available
in a branch in the github repository.

Current functionality
----------------------

The currently supported code has been ported to _only_
work on Python 3.  Many things were dropped, although
they could be added again if upgraded and tested.

Dropped features include the digilent cable driver
(just use the FTDI one), the SVF parser, and the
LEON gdb server.

Installation
---------------

There is currently no automated installer.
If you clone it from github, the tools in
the tools/jtag directory will access the
library in the playtag directory.

If you are using the FTDI adapter, you must have
their MPSSE driver installed and the DLL available
for Windows.  For Linux, one version of the .so file
is shipped with playtag.

Chain discovery
------------------

A simple test to see if everything is working is to discover the JTAG chain::

    $ cd playtag/tools/jtag
    $ ./discover.py

will show the available cable types.  Then, e.g.::

    $ ./discover.py ftdi

will show available FTDI cables, and::

    $ ./discover.py ftdi 1

will show the chain based on that particular cable index.  You can also select
a cable by serial number or description.

You can also enter options on the command line.  For example, if you are using
an FTDI-based cable, you can set the frequency, which currently defaults to
15 MHz, and you want to slow it down to 500KHz, you can use::

    $ ./discover.py ftdi 1 FTDI_JTAG_FREQ=500000
