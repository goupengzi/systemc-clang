# Linux

We provide instructions for installation using Linux. 
You can install LLVM and Clang via source or via binaries. 

### LLVM/Clang from source 

* Follow the instructions to install clang: [Get Started](http://clang.llvm.org/get_started.html). Notice that you should also install LLVM as it is needed for compilation of the stand-along program. A suggestion is to install LLVM/clang in a location that is accessible by the user.
Note that the clang-llvm version systemc-clang supports is version 7.0.0.  It should work with higher versions as well.
 
* Clone systemc-clang repository.
```bash  
$ git clone gitlab@git.uwaterloo.ca/caesr-pub/systemc-clang.git
```

* Create a build directory for this stand-alone program.
```bash
$ mkdir systemc-clang-build
```

* Enter the cloned repository folder.
```bash
$ cd systemc-clang
```

* Edit the path for the `LLVM_INSTALL_DIR` in paths.sh, and set it to the appropriate path where LLVM/clang was installed.

* Source the paths file (assuming bash shell).  This should setup certain environment variables that cmake will use.
```bash
$ source scripts/paths.sh
```

* Go to the build directory.
```bash
$ cd ../systemc-clang-build
```

* Create the makefiles using cmake.  
```bash
$ cmake ../systemc-clang
```
* Alternatively, you could use cmake to generate [Ninja](https://ninja-build.org) build scripts.
```bash
$ cmake ../systemc-clang -G Ninja
```

* If there are no errors, then the compilation of Makefiles was successful.  So, you can go ahead and compile the stand-alone program.
```bash
$ make
```

* If using `ninja`:
```bash
$ ninja
```

Testing on a small example
==========================
* Copy the compiled binary in the bin folder of `LLVM_INSTALL_DIR`.
```bash
$ cp systemc-clang $LLVM_INSTALL_DIR/bin
```
* Set the `SYSTEMC` variable.
```bash
$ export SYSTEMC=<path-to-systemc-install>
```

* Execute it on a simple example.  You should see some (debug) information print out on the screen.  Hope to make this more meaningful in the future.
```bash 
$ $LLVM_INSTALL_DIR/bin/systemc-clang ../systemc-clang/tests/module1.hpp -- \
-D__STDC_CONSTANT_MACROS -D__STDC_LIMIT_MACROS  -I/usr/include  \
-I$SYSTEMC/include  -x c++ -w -c
```


