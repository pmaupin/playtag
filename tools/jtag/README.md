Playtag JTAG tools
===================

This needs to be cleaned up and a real interface added.  Currently, the
files in this directory are:

  - 52-ftdi-jtag.rules  -- Use this in /etc/udev/rules.d to access FTDI devices
  - artix_comm.py -- example of communication with Nexys Video board, with
    example FPGA loaded.
  - discover.py -- chain discovery
  - parse_log.py -- examines log file from the XVC server for debugging
  - playtag.py -- creates a playtag package, pointing over to the library/cable code
  - start_server_xxxx   -- start up server for various FTDI configurations
  - xilinx_xvc.py -- server program invoked by start_server_xxx
