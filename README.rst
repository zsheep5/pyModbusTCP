pyModbusTCP
===========

A simple Modbus/TCP Server and client library for Python.

Forked version 0.9

Several modifications made to the Modbus server.  
1. It no longer unpacks binary data using struct libary converting to python data type.
2. Added several class methods to the DataBank to convert from bytes streams to python type but you must know the location in the databank and how many registers data type is using.
4. Added class methods to convert python types to C data type using struct libary
5. Added a few functions to make it easier to write to ASCII data types into registers.



In Process 
==========
Changing the logging/error reporting to use python's logging server...
Adding Discrete Inputs to server:  read only : example is switch or relay closure in the real world
Adding Input Registers to server:  read only : typicaly an AtoD input or other physical real world device...  


pyModbusTCP is pure Python code without any extension or external module
dependency.

Test
----

The module is currently working on Python  3.5.

Tested with PLC
---------------
Automation Direct P series
Koyo DOL6 series 


Status:

  :target: http://pymodbustcp.readthedocs.io/en/latest/?badge=latest



Documentation
-------------

Documentation available online at http://pymodbustcp.readthedocs.io/.
