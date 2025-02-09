SystemC 2.2.0 Installation Notes
--------------------------------

We have tested this on Mac OSX, and Ubuntu 64bit.

Mutable errors
--------------

- Please see: [http://stackoverflow.com/questions/7285049/installing-systemc-2-2-0-compilation-with-gcc-4-6-and-package-for-fedora](http://stackoverflow.com/questions/7285049/installing-systemc-2-2-0-compilation-with-gcc-4-6-and-package-for-fedora)

Ubuntu Installation
-------------------

I recommend following the instructions [here](http://vinaydvd.wordpress.com/2012/05/30/installing-systemc-in-ubuntu/) for SystemC installation on Ubuntu OS. 


Mac OSX errors
--------------

- During `configure` the build is not recognized.  Run `configure` with the following build options `--build=i386-pc-linux`. 

- You may get errors of the following form:


`Assembler messages: qtmds.s:69: Error: suffix or operands invalid for push' qtmds.s:70: Error: suffix or operands invalid for push ... `

You can fix this by doing the following:
1. Remove the file xxxx/systemc-2.2.3/src/sysc/qt/qtmds.s 
2. Go under xxxx/systemc-2.2.3/src/sysc/qt and execute this command:

`ln -s md/iX86_64.s qtmds.s` to get the "qtmds.s" back but with the correct version (64 bits)
3. Execute `make` again

Taken from [http://gcc.gnu.org/ml/gcc-help/2009-10/msg00266.html](http://gcc.gnu.org/ml/gcc-help/2009-10/msg00266.html)
