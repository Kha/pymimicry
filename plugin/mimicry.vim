if exists("g:loaded_mimicry") || &cp
  finish
endif
let g:loaded_mimicry= 1

command! -nargs=0 MimicryFromUndo call mimicry#FromUndoStep()
