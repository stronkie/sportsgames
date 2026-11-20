;------------------------------------------------------------------------------
;  whdload.s - WHDLoad slave for Stronkie's Olympics
;
;  No Kickstart image needed: the slave loads the game (data/SOlymp.game, a
;  normal AmigaDOS executable) into WHDLoad's memory itself and gives it the
;  few OS calls it makes (a small exec/graphics/dos stand-in): AllocMem for
;  its chip memory, and reading any file from data/ (the events are loaded
;  one by one).  The records file Olympics.dat is saved through WHDLoad.
;  F10 quits to Workbench.
;  Must be position independent: no absolute addresses in here.
;  Created By Mark Stronks, Stronkie Soft 2026
;------------------------------------------------------------------------------

CHIPSIZE	equ	$80000			; base memory: 512K chip
EXPSIZE		equ	$80000			; expansion memory: 512K
FREECHIP	equ	$1000			; chip below this: vectors, the stand-in OS

; where the stand-in OS lives in chip memory
EXECBASE	equ	$700			; vectors $4d8-$6ff, the base $700-$82f
GFXBASE		equ	$a00			; vectors $832-$9ff
DOSBASE		equ	$c00			; vectors $b3a-$bff
PROC		equ	$c40			; a process (pr_CLI set: no WB message)
COPINIT		equ	$d00			; an empty copper list
FILEBUF		equ	$d40			; a file being written (the records: 128 of 256 bytes)
FBUFSIZE	equ	256

; resload functions
resload_Abort		equ	4
resload_LoadFile	equ	8
resload_SaveFile	equ	12
resload_GetFileSize	equ	36
resload_LoadFileOffset	equ	76
TDREASON_OK		equ	-1
TDREASON_DOSREAD	equ	22

	section	code,code
_base	moveq	#-1,d0			; (not to be run from the CLI)
	rts
	dc.b	'WHDLOADS'
	dc.w	17			; ws_Version
	dc.w	2+4+4096		; ws_Flags: NoError, EmulTrap, ClearMem
	dc.l	CHIPSIZE		; ws_BaseMemSize
	dc.l	0			; ws_ExecInstall
	dc.w	slave_start-_base	; ws_GameLoader
	dc.w	s_dir-_base		; ws_CurrentDir
	dc.w	0			; ws_DontCache
	dc.b	0			; ws_keydebug
	dc.b	$59			; ws_keyexit: F10
	dc.l	EXPSIZE			; ws_ExpMem
	dc.w	s_name-_base		; ws_name
	dc.w	s_copy-_base		; ws_copy
	dc.w	s_info-_base		; ws_info
	dc.w	0			; ws_kickname (none: no Kickstart needed)
	dc.l	0			; ws_kicksize
	dc.w	0			; ws_kickcrc
	dc.w	0			; ws_config

s_dir	dc.b	'data',0
s_name	dc.b	'Stronkie',39,'s Olympics',0
s_copy	dc.b	'2026 Mark Stronks, Stronkie Soft',0
s_info	dc.b	'Installed by Stronkie Soft',10
	dc.b	'F10 = quit to Workbench',0
s_game	dc.b	'SOlymp.game',0
	even

; the stand-in library calls: offset, routine
exec_table	dc.w	-30,os_super-_base,-198,os_allocmem-_base,-210,os_nop-_base,-120,os_nop-_base,-126,os_nop-_base,-132,os_nop-_base,-138,os_nop-_base
		dc.w	-294,os_findtask-_base,-372,os_zero-_base,-378,os_nop-_base,-384,os_zero-_base
		dc.w	-408,os_openlib-_base,-414,os_nop-_base,-552,os_openlib-_base,0
gfx_table	dc.w	-222,os_nop-_base,-270,os_waittof-_base,-456,os_nop-_base,-462,os_nop-_base
		dc.w	-228,os_waitblit-_base,0
dos_table	dc.w	-30,os_open-_base,-36,os_close-_base,-42,os_read-_base,-48,os_write-_base
		dc.w	-198,os_nop-_base,-132,os_zero-_base,-126,os_zero-_base,0

;------------------------------------------------------------------ start
; a0 = resload
slave_start:
	lea	_resload(pc),a1
	move.l	a0,(a1)
	lea	_expmem(pc),a1
	lea	_base(pc),a0
	move.l	32(a0),(a1)		; ws_ExpMem: WHDLoad put the address there
	lea	s_game(pc),a0		; the game's size (to read it in pieces)
	move.l	_resload(pc),a2
	jsr	resload_GetFileSize(a2)
	lea	_flen(pc),a0
	move.l	d0,(a0)

	; the stand-in OS
	lea	EXECBASE,a0
	lea	exec_table(pc),a1
	bsr	make_lib
	lea	GFXBASE,a0
	lea	gfx_table(pc),a1
	bsr	make_lib
	lea	DOSBASE,a0
	lea	dos_table(pc),a1
	bsr	make_lib
	move.l	#EXECBASE,4.w
	clr.w	EXECBASE+296		; AttnFlags: a 68000 (vectors at 0)
	clr.l	GFXBASE+34		; gb_ActiView
	move.l	#COPINIT,GFXBASE+38	; gb_copinit
	move.l	#$01000200,COPINIT
	move.l	#$fffffffe,COPINIT+4
	move.l	#1,PROC+172		; pr_CLI: started from a "CLI"

	; load the game
	lea	_chipp(pc),a0
	move.l	#FREECHIP,(a0)
	lea	_expp(pc),a0
	move.l	_expmem(pc),(a0)
	bsr	load_game
	tst.l	d0
	beq	.fail
	move.l	d0,a1			; and start it
	move.l	#'WHDL',d7
	lea	s_dummyarg(pc),a0
	moveq	#1,d0
	jsr	(a1)
	move.l	#TDREASON_OK,-(sp)	; the game returned: back to Workbench
	move.l	_resload(pc),a2
	jmp	resload_Abort(a2)
.fail	pea	s_game(pc)
	move.l	#TDREASON_DOSREAD,-(sp)
	move.l	_resload(pc),a2
	jmp	resload_Abort(a2)

s_dummyarg	dc.b	10,0
	even

; make_lib: a0 = base, a1 = table (offset.w, routine.w (from _base)), 0 ends
make_lib:
	lea	_base(pc),a2
.l	move.w	(a1)+,d0
	beq.s	.x
	move.w	(a1)+,d1
	lea	(a2,d1.w),a3
	move.w	#$4ef9,(a0,d0.w)	; JMP routine
	move.l	a3,2(a0,d0.w)
	bra.s	.l
.x	rts

;------------------------------------------------------------------ the hunk loader
; load_game -> d0 = the first hunk's code (0 = failed)
load_game:
	movem.l	d1-d7/a0-a6,-(sp)
	lea	_fpos(pc),a0
	clr.l	(a0)
	bsr	inval
	bsr	get_long
	cmp.l	#$3f3,d0
	bne	.bad
	bsr	get_long		; (no resident libraries)
	bsr	get_long		; number of hunks
	move.l	d0,d7
	cmp.l	#16,d7			; (room for 16)
	bhi	.bad
	bsr	get_long		; first
	bsr	get_long		; last
	lea	_hunks(pc),a4
	moveq	#0,d6
.al	bsr	get_long		; size + memory type
	move.l	d0,d1
	move.l	d0,d2
	and.l	#$c0000000,d2
	cmp.l	#$c0000000,d2		; (an extra attribute long: any memory)
	bne.s	.na
	bsr	get_long
	moveq	#0,d0
.na
	and.l	#$3fffffff,d1
	lsl.l	#2,d1
	addq.l	#8,d1			; (+ the segment list longs)
	btst	#30,d0
	bne.s	.chip
	move.l	_expp(pc),a0		; any memory: expansion, if it fits
	move.l	a0,d2
	add.l	d1,d2
	move.l	_expmem(pc),d3
	add.l	#EXPSIZE,d3
	cmp.l	d3,d2
	bhi.s	.chip
	lea	_expp(pc),a1
	bra.s	.got
.chip	move.l	_chipp(pc),a0
	move.l	a0,d2
	add.l	d1,d2
	cmp.l	#CHIPSIZE,d2
	bhi	.bad
	lea	_chipp(pc),a1
.got	addq.l	#7,d2			; (8 byte steps)
	and.w	#$fff8,d2
	move.l	d2,(a1)
	move.l	d1,d2			; clear it
	lsr.l	#2,d2
	move.l	a0,a1
.clr	clr.l	(a1)+
	subq.l	#1,d2
	bne.s	.clr
	move.l	d1,(a0)			; (size, next segment)
	clr.l	4(a0)
	addq.l	#8,a0
	move.l	a0,(a4,d6.w)
	addq.w	#4,d6
	move.l	d7,d0
	lsl.l	#2,d0
	cmp.w	d0,d6
	blo	.al
	; the hunks
	moveq	#0,d6			; current hunk * 4
.blk	bsr	get_long
	and.l	#$3fffffff,d0
	cmp.l	#$3e9,d0
	beq.s	.data
	cmp.l	#$3ea,d0
	beq.s	.data
	cmp.l	#$3eb,d0
	beq.s	.bss
	cmp.l	#$3ec,d0
	beq.s	.reloc
	cmp.l	#$3f2,d0
	beq	.end
	cmp.l	#$3f0,d0
	beq.s	.symbols
	cmp.l	#$3f1,d0
	beq.s	.debug
	bra	.bad
.data	bsr	get_long		; longs
	lsl.l	#2,d0
	move.l	(a4,d6.w),a1
	bsr	get_block
	beq	.bad
	bra.s	.blk
.bss	bsr	get_long		; (cleared already)
	bra.s	.blk
.reloc	bsr	get_long		; count
	tst.l	d0
	beq.s	.blk
	move.l	d0,d5
	bsr	get_long		; target hunk
	lsl.l	#2,d0
	move.l	(a4,d0.w),d4
	move.l	(a4,d6.w),a1
.ro	bsr	get_long
	add.l	d4,(a1,d0.l)
	subq.l	#1,d5
	bne.s	.ro
	bra.s	.reloc
.symbols
.sy	bsr	get_long		; name length
	tst.l	d0
	beq	.blk
	addq.l	#1,d0			; + the value
	move.l	d0,d5
.sk	bsr	get_long
	subq.l	#1,d5
	bne.s	.sk
	bra.s	.sy
.debug	bsr	get_long
	move.l	d0,d5
	beq	.blk
.dk	bsr	get_long
	subq.l	#1,d5
	bne.s	.dk
	bra	.blk
.end	addq.w	#4,d6
	move.l	d7,d0
	lsl.l	#2,d0
	cmp.w	d0,d6
	blo	.blk
	move.l	_hunks(pc),d0
	bra.s	.x
.bad	moveq	#0,d0
.x	movem.l	(sp)+,d1-d7/a0-a6
	rts

; reading the file through a 1K window
inval	lea	_bufpos(pc),a0
	move.l	#$7fffffff,(a0)		; (far ahead: the next read refills)
	rts
; get_long -> d0
get_long:
	movem.l	d1-d3/a0-a2,-(sp)
	move.l	_fpos(pc),d2
	move.l	_bufpos(pc),d3
	move.l	d2,d1
	sub.l	d3,d1
	bmi.s	.fill
	cmp.l	#1024-4,d1
	bls.s	.ok
.fill	move.l	d2,d1			; offset
	move.l	_flen(pc),d0		; (not past the end)
	sub.l	d2,d0
	cmp.l	#1024,d0
	bls.s	.sz
	move.l	#1024,d0
.sz
	lea	s_game(pc),a0
	lea	_buf(pc),a1
	move.l	_resload(pc),a2
	jsr	resload_LoadFileOffset(a2)
	lea	_bufpos(pc),a0
	move.l	_fpos(pc),(a0)
	moveq	#0,d1
.ok	lea	_buf(pc),a0
	move.l	(a0,d1.l),d0
	lea	_fpos(pc),a0
	addq.l	#4,(a0)
	movem.l	(sp)+,d1-d3/a0-a2
	rts
; get_block: d0 = bytes -> a1 (read straight from the file); ne = ok
get_block:
	movem.l	d0-d3/a0-a2,-(sp)
	tst.l	d0
	beq.s	.x
	move.l	d0,d3
	move.l	_fpos(pc),d1
	lea	s_game(pc),a0
	move.l	_resload(pc),a2
	jsr	resload_LoadFileOffset(a2)
	lea	_fpos(pc),a0
	add.l	d3,(a0)
	bsr	inval
.x	movem.l	(sp)+,d0-d3/a0-a2
	moveq	#1,d0
	rts

;------------------------------------------------------------------ the stand-in OS
os_nop	rts
os_zero	moveq	#0,d0
	rts
os_findtask
	move.l	#PROC,d0
	rts
os_openlib				; a1 = name: graphics / dos
	move.l	#GFXBASE,d0
	cmp.b	#'g',(a1)
	beq.s	.x
	move.l	#DOSBASE,d0
	cmp.b	#'d',(a1)
	beq.s	.x
	moveq	#0,d0
.x	rts
os_super				; (AttnFlags say 68000: not called)
	moveq	#0,d0
	rts
os_waittof
.w1	btst	#0,$dff005		; to line 256+ ...
	beq.s	.w1
.w2	btst	#0,$dff005		; ... and back to the top
	bne.s	.w2
	rts
os_waitblit
	tst.b	$dff002
.w	btst	#6,$dff002
	bne.s	.w
	rts

; AllocMem: d0 = size, d1 = flags: from the chip memory after the game (cleared)
os_allocmem
	movem.l	d1-d2/a0-a1,-(sp)
	addq.l	#7,d0
	and.w	#$fff8,d0
	move.l	_chipp(pc),a0
	move.l	a0,d2
	add.l	d0,d2
	cmp.l	#CHIPSIZE,d2
	bhi.s	.no
	lea	_chipp(pc),a1
	move.l	d2,(a1)
	move.l	a0,a1
	lsr.l	#2,d0
.c	clr.l	(a1)+
	subq.l	#1,d0
	bne.s	.c
	move.l	a0,d0
	bra.s	.x
.no	moveq	#0,d0
.x	movem.l	(sp)+,d1-d2/a0-a1
	rts

; dos: d1 = name (a "Volume:" in front is skipped). One file at a time.
; Handles: 1 = reading (any file in data/), 2 = writing (saved at Close)
os_open
	movem.l	d1-d3/a0-a2,-(sp)
	move.l	d1,a0			; the name without the volume
	move.l	a0,a1
.v	move.b	(a1)+,d0
	beq.s	.nv
	cmp.b	#':',d0
	bne.s	.v
	move.l	a1,a0
.nv	lea	_fname(pc),a1
	moveq	#30,d0
.cp	move.b	(a0)+,(a1)+
	dbeq	d0,.cp
	clr.b	(a1)
	lea	_frw(pc),a0
	clr.l	(a0)
	cmp.l	#1006,d2
	beq.s	.wr
	lea	_fname(pc),a0		; reading: is it there?
	move.l	_resload(pc),a2
	jsr	resload_GetFileSize(a2)
	lea	_fsize(pc),a0
	move.l	d0,(a0)
	tst.l	d0
	beq.s	.x
	moveq	#1,d0
	bra.s	.x
.wr	moveq	#2,d0
.x	movem.l	(sp)+,d1-d3/a0-a2
	rts
os_read					; d2 = buffer, d3 = length
	movem.l	d1-d3/a0-a2,-(sp)
	move.l	_fsize(pc),d0
	sub.l	_frw(pc),d0
	cmp.l	d3,d0
	bls.s	.n
	move.l	d3,d0
.n	tst.l	d0
	beq.s	.x
	move.l	d0,-(sp)
	move.l	_frw(pc),d1		; offset
	lea	_fname(pc),a0
	move.l	d2,a1
	move.l	_resload(pc),a2
	jsr	resload_LoadFileOffset(a2)
	move.l	(sp)+,d0
	lea	_frw(pc),a0
	add.l	d0,(a0)
.x	movem.l	(sp)+,d1-d3/a0-a2
	rts
os_write				; d2 = data, d3 = length
	movem.l	d1-d3/a0-a2,-(sp)
	move.l	_frw(pc),d0
	add.l	d3,d0
	cmp.l	#FBUFSIZE,d0
	bhi.s	.no
	lea	FILEBUF,a1
	add.l	_frw(pc),a1
	lea	_frw(pc),a2
	move.l	d0,(a2)
	move.l	d2,a0
	move.l	d3,d0
	beq.s	.x
	subq.l	#1,d3
.c	move.b	(a0)+,(a1)+
	dbf	d3,.c
	bra.s	.x
.no	moveq	#-1,d0
.x	movem.l	(sp)+,d1-d3/a0-a2
	rts
os_close				; writing: save it through WHDLoad
	movem.l	d0-d1/a0-a2,-(sp)
	cmp.l	#2,d1
	bne.s	.x
	move.l	_frw(pc),d0
	beq.s	.x
	lea	_fname(pc),a0
	lea	FILEBUF,a1
	move.l	_resload(pc),a2
	jsr	resload_SaveFile(a2)
.x	movem.l	(sp)+,d0-d1/a0-a2
	moveq	#-1,d0
	rts

;------------------------------------------------------------------ variables (in the slave)
	even
_resload	dc.l	0
_expmem		dc.l	0
_chipp		dc.l	0
_expp		dc.l	0
_fpos		dc.l	0
_bufpos		dc.l	0
_fsize		dc.l	0
_frw		dc.l	0
_flen		dc.l	0
_fname		ds.b	32
_hunks		ds.l	16
_buf		ds.b	1024
