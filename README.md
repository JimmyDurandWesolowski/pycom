# PyCom
The not-so-lightweight, curses-based, serial command interface.

## Why
Many embedded device firmware cannot afford to have a complete command line handling, such has line edition, history, and search. Thus, this allows to have an serial terminal with these implemented on the host side.

Moreover, it implements rate-limiting: some microcontrollers, especially automative grade ones, have a limited serial communication hardware fifo. Due to safety related reasons, its handling priority is fixed and limited (which is not an issue as it is usually used as a debug communication). The result is non rate-limited typing can result in dropped characters.

**Note:** Having this split interface might be suboptimal, and future versions might see the command and serial output merged for the interface to feel more intuitive or at least similar to other serial terminal such as (c)Kermit, Picocom, or Teraterm.

## Features
### Implemented
* 3 *virtual* split terminal windows
* Customizable Window split
* Command line editing
* History file and buffer saving and retrieval
* Standard input command piping at start-up

### To be implemented
* History search
* Completion
* Scrolling of the serial terminal
* Rate-limiting

## Status
Please read the TODO.org for further information of the implementation progress.
