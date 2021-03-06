function! s:Refresh()
	let existing_buffer = bufnr("__Mimicry__")
	if existing_buffer == -1
		botright new __Mimicry__
		setlocal previewwindow
		setlocal buftype=nofile
		setlocal bufhidden=hide
		setlocal noswapfile
		setlocal nobuflisted
		setlocal nomodifiable
		setlocal filetype=mimicry
		setlocal nonumber
		setlocal norelativenumber
		setlocal nowrap
		resiz 10

		let b:current_syntax = 'mimicry'
		syn match Comment '\v^".*$'

		nnoremap <script> <silent> <buffer> p :call mimicry#PreviewChanges()<CR>
		nnoremap <script> <silent> <buffer> c :call mimicry#PerformChanges()<CR>
		nnoremap <script> <silent> <buffer> u :call mimicry#PopChange()<CR>
		nnoremap <script> <silent> <buffer> - :python vimmimicry.zoom_out(-1)<CR>
		nnoremap <script> <silent> <buffer> + :python vimmimicry.zoom_out(+1)<CR>
		wincmd p
	endif
	python vimmimicry.refresh_output()
endfunction

function! mimicry#FromUndoStep()
	python vimmimicry.from_undo_step()
	call s:Refresh()
endfunction

function! mimicry#PreviewChanges()
	python vimmimicry.preview_changes()
endfunction

function! mimicry#PerformChanges()
	python vimmimicry.perform_changes()
endfunction

function! mimicry#PopChange()
	python vimmimicry.pop_change()
	call s:Refresh()
endfunction

if !has('python')
	echohl WarningMsg|echomsg "pymimicry requires +python"|echohl None
	finish
endif

let s:plugin_path = escape(expand('<sfile>:p:h:h'), '\')

py import sys
exe 'py sys.path.append("' . s:plugin_path . '")'
py import vimmimicry
