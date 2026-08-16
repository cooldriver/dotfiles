filetype plugin indent on
syntax enable

set number
set ruler
set showmatch
set wildmenu
set laststatus=2
set scrolloff=3

set ignorecase
set smartcase
set incsearch
set hlsearch

if has('autocmd')
  augroup checktime
    autocmd!
    autocmd FocusGained,BufEnter * checktime
  augroup END
endif
