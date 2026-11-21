;------------------------------------------------------------------------------
;  loader.s - Stronkie's Olympics loader
;
;  Shows the loading picture (an OS View, so the disk keeps running), loads
;  SOlymp.game with its own hunk loader while a progress bar fills, then runs
;  the game and frees it afterwards.  Created By Mark Stronks, Stronkie Soft 2026
;------------------------------------------------------------------------------

_LVOForbid	equ	-132
_LVOFindTask	equ	-294
_LVOGetMsg	equ	-372
_LVOReplyMsg	equ	-378
_LVOWaitPort	equ	-384
_LVOAllocMem	equ	-198
_LVOFreeMem	equ	-210
_LVOCloseLibrary equ	-414
_LVOOpenLibrary	equ	-552
; graphics
_LVOLoadRGB4	equ	-192
_LVOInitVPort	equ	-204
_LVOMrgCop	equ	-210
_LVOMakeVPort	equ	-216
_LVOLoadView	equ	-222
_LVOWaitTOF	equ	-270
_LVOInitView	equ	-360
_LVOInitBitMap	equ	-390
_LVOFreeVPortCopLists equ -540
_LVOFreeCprList	equ	-564
_LVOGetColorMap	equ	-570
_LVOFreeColorMap equ	-576
; dos
_LVOOpen	equ	-30
_LVOClose	equ	-36
_LVORead	equ	-42
_LVOSeek	equ	-66
_LVOCurrentDir	equ	-126
_LVODelay	equ	-198

PLANESIZE	equ	40*256
MAXHUNKS	equ	32
IOBUFSIZE	equ	4096
CHUNK		equ	16384

	section	code,code
start:
	move.l	sp,stacksave
	move.l	4.w,a6
	sub.l	a1,a1
	jsr	_LVOFindTask(a6)
	move.l	d0,a4
	tst.l	172(a4)
	bne.s	.cli
	lea	92(a4),a0
	jsr	_LVOWaitPort(a6)
	lea	92(a4),a0
	jsr	_LVOGetMsg(a6)
	move.l	d0,wbmsg
.cli	lea	gfxname,a1
	moveq	#0,d0
	jsr	_LVOOpenLibrary(a6)
	move.l	d0,gfxbase
	beq	exit
	lea	dosname,a1
	moveq	#0,d0
	jsr	_LVOOpenLibrary(a6)
	move.l	d0,dosbase
	beq	closegfx
	move.l	wbmsg,d0		; from Workbench: work in the game's drawer
	beq.s	.nodir
	move.l	d0,a0
	move.l	36(a0),a0		; sm_ArgList
	move.l	(a0),d1			; wa_Lock
	move.l	dosbase,a6
	jsr	_LVOCurrentDir(a6)
	move.l	d0,olddir
	st	dirset
.nodir
	bsr	show_picture
	bsr	load_game
	tst.l	d0
	bne.s	.ok
	lea	str_notfound,a0		; no game file
	bsr	draw_status
	move.l	dosbase,a6
	move.l	#150,d1
	jsr	_LVODelay(a6)
	bsr	hide_picture
	bra.s	.free
.ok	move.l	dosbase,a6
	moveq	#20,d1
	jsr	_LVODelay(a6)
	bsr	hide_picture
	move.l	hunk_base,a0		; run the game
	move.l	#'SOLY',d7
	movem.l	d0-d7/a0-a6,-(sp)
	jsr	(a0)
	movem.l	(sp)+,d0-d7/a0-a6
.free	bsr	free_hunks
	tst.b	dirset
	beq.s	.nd
	move.l	olddir,d1
	move.l	dosbase,a6
	jsr	_LVOCurrentDir(a6)
.nd	move.l	4.w,a6
	move.l	dosbase,a1
	jsr	_LVOCloseLibrary(a6)
closegfx
	move.l	4.w,a6
	move.l	gfxbase,a1
	jsr	_LVOCloseLibrary(a6)
exit	tst.l	wbmsg
	beq.s	.r
	move.l	4.w,a6
	jsr	_LVOForbid(a6)
	move.l	wbmsg,a1
	jsr	_LVOReplyMsg(a6)
.r	move.l	stacksave,sp
	moveq	#0,d0
	rts

;------------------------------------------------------------------ picture
show_picture:
	move.l	4.w,a6			; chip memory for the picture, freed before the game runs
	move.l	#PLANESIZE*5,d0
	move.l	#$10002,d1
	jsr	_LVOAllocMem(a6)
	move.l	d0,picptr
	beq	.x
	lea	loadpic_rle,a0		; unpack into the 5 bitplanes
	move.l	d0,a1
	move.l	a1,a2
	add.l	#PLANESIZE*5,a2
.ul	moveq	#0,d1
	move.b	(a0)+,d1
	bmi.s	.run
.lit	move.b	(a0)+,(a1)+
	dbf	d1,.lit
	bra.s	.chk
.run	and.w	#$7f,d1
	addq.w	#2,d1
	move.b	(a0)+,d2
.rep	move.b	d2,(a1)+
	dbf	d1,.rep
.chk	cmp.l	a2,a1
	blo.s	.ul
	lea	str_loading,a0
	bsr	draw_status
	move.l	gfxbase,a6
	move.l	34(a6),oldview		; gb_ActiView
	lea	view,a1
	jsr	_LVOInitView(a6)
	lea	vport,a0
	jsr	_LVOInitVPort(a6)
	move.l	#vport,view		; v_ViewPort
	lea	bitmap,a0
	moveq	#5,d0
	move.l	#320,d1
	move.l	#256,d2
	jsr	_LVOInitBitMap(a6)
	lea	bitmap+8,a0
	move.l	picptr,d0
	moveq	#4,d1
.pl	move.l	d0,(a0)+
	add.l	#PLANESIZE,d0
	dbf	d1,.pl
	move.l	#bitmap,rasinfo+4
	lea	vport,a0
	move.w	#320,24(a0)		; DWidth
	move.w	#256,26(a0)		; DHeight
	move.l	#rasinfo,36(a0)
	moveq	#32,d0
	jsr	_LVOGetColorMap(a6)
	move.l	d0,vport+4
	beq.s	.x
	lea	vport,a0
	lea	loadpal,a1
	moveq	#32,d0
	jsr	_LVOLoadRGB4(a6)
	lea	view,a0
	lea	vport,a1
	jsr	_LVOMakeVPort(a6)
	lea	view,a1
	jsr	_LVOMrgCop(a6)
	lea	view,a1
	jsr	_LVOLoadView(a6)
	st	shown
.x	rts

hide_picture:
	tst.b	shown
	beq.s	.x
	clr.b	shown
	move.l	gfxbase,a6
	move.l	oldview,a1
	jsr	_LVOLoadView(a6)
	jsr	_LVOWaitTOF(a6)
	jsr	_LVOWaitTOF(a6)
	lea	vport,a0
	jsr	_LVOFreeVPortCopLists(a6)
	move.l	view+4,a0		; LOFCprList
	jsr	_LVOFreeCprList(a6)
	move.l	vport+4,a0
	jsr	_LVOFreeColorMap(a6)
.x	move.l	picptr,d0
	beq.s	.y
	clr.l	picptr
	move.l	d0,a1
	move.l	#PLANESIZE*5,d0
	move.l	4.w,a6
	jsr	_LVOFreeMem(a6)
.y	rts

; draw_status: a0 = text (at most 25 characters) on the line under the bar
draw_status:
	movem.l	d0-d7/a0-a3,-(sp)
	lea	statbuf,a1		; pad to 25
	moveq	#24,d0
.c	move.b	(a0)+,d1
	beq.s	.pad
	move.b	d1,(a1)+
	dbf	d0,.c
	bra.s	.z
.pad	move.b	#' ',(a1)+
	dbf	d0,.pad
.z	clr.b	(a1)
	move.l	picptr,d0
	beq	.done
	lea	statbuf,a0
	move.l	d0,a1
	add.l	#TXT_Y*40+TXT_X,a1
.ch	moveq	#0,d0
	move.b	(a0)+,d0
	beq.s	.done
	sub.b	#32,d0
	lsl.w	#3,d0
	lea	font8,a2
	add.w	d0,a2
	moveq	#0,d6			; row
.row	move.b	(a2)+,d4
	move.b	d4,d5
	not.b	d5
	move.l	a1,a3
	move.w	d6,d0
	mulu	#40,d0
	add.w	d0,a3
	moveq	#0,d3			; plane
.p	moveq	#0,d0
	btst	d3,#C_TXT
	beq.s	.n1
	or.b	d4,d0
.n1	btst	d3,#C_TXTBG
	beq.s	.n2
	or.b	d5,d0
.n2	move.b	d0,(a3)
	add.l	#PLANESIZE,a3
	addq.w	#1,d3
	cmp.w	#5,d3
	blo.s	.p
	addq.w	#1,d6
	cmp.w	#8,d6
	blo.s	.row
	addq.l	#1,a1
	bra.s	.ch
.done	movem.l	(sp)+,d0-d7/a0-a3
	rts

; progress: total_read / file_size -> bar and "LOADING... 62%"
progress:
	tst.l	picptr
	beq	.none
	movem.l	d0-d7/a0-a1,-(sp)
	move.l	total_read,d0
	lsr.l	#8,d0
	move.l	file_size,d7
	lsr.l	#8,d7
	addq.l	#1,d7
	move.l	d0,d2
	mulu	#BAR_X1-BAR_X0-1,d2
	divu	d7,d2			; filled pixels
	and.l	#$ffff,d2
	cmp.w	#BAR_X1-BAR_X0-1,d2
	bls.s	.ok
	move.w	#BAR_X1-BAR_X0-1,d2
.ok	move.w	bar_done,d3
.col	cmp.w	d2,d3			; new columns: light segments, a dark gap every 6th
	bhs.s	.text
	move.w	d3,d0
	add.w	#BAR_X0+1,d0
	moveq	#C_BARFG,d4
	move.w	d3,d5
	and.l	#$ffff,d5
	divu	#6,d5
	swap	d5
	cmp.w	#5,d5
	bne.s	.cc
	moveq	#C_BARBG,d4
.cc	move.w	#BAR_Y0+2,d1
.y	bsr	pset
	addq.w	#1,d1
	cmp.w	#BAR_Y1-1,d1
	blo.s	.y
	addq.w	#1,d3
	bra.s	.col
.text	move.w	d3,bar_done
	move.l	total_read,d0		; percent
	lsr.l	#8,d0
	mulu	#100,d0
	divu	d7,d0
	cmp.w	#100,d0
	bls.s	.p
	moveq	#100,d0
.p	lea	str_pct+11,a0		; "LOADING... 100%"
	and.l	#$ffff,d0
	divu	#100,d0
	move.b	#' ',d2
	tst.w	d0
	beq.s	.h
	moveq	#'1',d2
.h	move.b	d2,(a0)+
	clr.w	d0
	swap	d0
	divu	#10,d0
	move.b	#' ',d2
	tst.w	d0
	bne.s	.t
	cmp.b	#' ',-1(a0)
	beq.s	.t2
.t	move.b	d0,d2
	add.b	#'0',d2
.t2	move.b	d2,(a0)+
	swap	d0
	add.b	#'0',d0
	move.b	d0,(a0)+
	lea	str_pct,a0
	bsr	draw_status
	movem.l	(sp)+,d0-d7/a0-a1
.none	rts

pset:					; d0 = x, d1 = y, d4 = colour
	movem.l	d0-d3/a0,-(sp)
	move.w	d1,d2
	mulu	#40,d2
	move.w	d0,d3
	lsr.w	#3,d3
	add.w	d3,d2
	move.l	picptr,a0
	add.l	d2,a0
	not.w	d0
	and.w	#7,d0
	moveq	#0,d3
.p	btst	d3,d4
	beq.s	.c
	bset	d0,(a0)
	bra.s	.n
.c	bclr	d0,(a0)
.n	add.l	#PLANESIZE,a0
	addq.w	#1,d3
	cmp.w	#5,d3
	blo.s	.p
	movem.l	(sp)+,d0-d3/a0
	rts

;------------------------------------------------------------------ hunk loader
; load_game -> d0 = 1 ok, 0 failed
load_game:
	move.l	dosbase,a6
	move.l	#gamename,d1
	move.l	#1005,d2
	jsr	_LVOOpen(a6)
	move.l	d0,fh
	beq	.fail
	move.l	fh,d1			; the size: seek to the end and back
	moveq	#0,d2
	moveq	#1,d3
	jsr	_LVOSeek(a6)
	move.l	fh,d1
	moveq	#0,d2
	moveq	#-1,d3
	jsr	_LVOSeek(a6)
	move.l	d0,file_size
	bsr	get_long
	cmp.l	#$3f3,d0
	bne	.bad
	bsr	get_long		; no resident library names
	tst.l	d0
	bne	.bad
	bsr	get_long
	cmp.l	#MAXHUNKS,d0
	bhi	.bad
	move.w	d0,nhunks
	bsr	get_long		; first
	bsr	get_long		; last
	moveq	#0,d7
.alloc	cmp.w	nhunks,d7
	bhs.s	.hunks
	bsr	get_long
	move.l	d0,d2
	and.l	#$3fffffff,d0
	lsl.l	#2,d0			; bytes
	move.l	#$10001,d1		; MEMF_PUBLIC | MEMF_CLEAR
	btst	#30,d2
	beq.s	.nc
	or.l	#2,d1			; MEMF_CHIP
.nc	move.w	d7,d3
	lsl.w	#2,d3
	lea	hunk_size,a0
	move.l	d0,(a0,d3.w)
	tst.l	d0
	bne.s	.nz
	moveq	#4,d0
	move.l	d0,(a0,d3.w)
.nz	move.l	4.w,a6
	jsr	_LVOAllocMem(a6)
	lea	hunk_base,a0
	move.w	d7,d3
	lsl.w	#2,d3
	move.l	d0,(a0,d3.w)
	beq	.bad
	addq.w	#1,d7
	bra.s	.alloc
.hunks	moveq	#0,d7			; current hunk
.type	cmp.w	nhunks,d7
	bhs	.done
	bsr	get_long
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
	beq.s	.end
	cmp.l	#HUNK_PACKED,d0
	beq.s	.pack
	bra	.bad
.pack	lea	hunk_base,a0		; a crunched hunk (the floppy version)
	move.w	d7,d3
	lsl.w	#2,d3
	move.l	(a0,d3.w),a1
	lea	hunk_size,a0
	move.l	(a0,d3.w),d2
	bsr	unpack_hunk
	tst.l	d0
	beq	.bad
	bra	.type
.data	bsr	get_long
	lsl.l	#2,d0
	move.l	d0,d1
	lea	hunk_base,a0
	move.w	d7,d3
	lsl.w	#2,d3
	move.l	(a0,d3.w),a0
	bsr	read_block
	tst.l	d0
	beq	.bad
	bra	.type
.bss	bsr	get_long
	bra	.type
.end	addq.w	#1,d7
	bra	.type
.reloc	lea	hunk_base,a0
	move.w	d7,d3
	lsl.w	#2,d3
	move.l	(a0,d3.w),a2		; this hunk
.rl	bsr	get_long
	tst.l	d0
	beq	.type
	move.l	d0,d6			; count
	bsr	get_long
	cmp.w	nhunks,d0
	bhs	.bad
	lsl.w	#2,d0
	lea	hunk_base,a0
	move.l	(a0,d0.w),d5		; target base
.ro	bsr	get_long
	add.l	d5,(a2,d0.l)
	subq.l	#1,d6
	bne.s	.ro
	bra.s	.rl
.done	move.l	fh,d1
	move.l	dosbase,a6
	jsr	_LVOClose(a6)
	move.l	file_size,total_read
	bsr	progress
	moveq	#1,d0
	rts
.bad	move.l	fh,d1
	move.l	dosbase,a6
	jsr	_LVOClose(a6)
	bsr	free_hunks
.fail	moveq	#0,d0
	rts

free_hunks:
	movem.l	d0-d7/a0-a1/a6,-(sp)
	move.l	4.w,a6
	moveq	#0,d7
.l	cmp.w	nhunks,d7
	bhs.s	.x
	move.w	d7,d3
	lsl.w	#2,d3
	lea	hunk_base,a0
	move.l	(a0,d3.w),a1
	clr.l	(a0,d3.w)
	lea	hunk_size,a0
	move.l	(a0,d3.w),d0
	move.l	a1,d1
	beq.s	.n
	jsr	_LVOFreeMem(a6)
.n	addq.w	#1,d7
	bra.s	.l
.x	clr.w	nhunks
	movem.l	(sp)+,d0-d7/a0-a1/a6
	rts

; buffered reading -----------------------------------------------------------
refill:					; -> buffer full again (or 0 bytes at the end)
	movem.l	d1-d3/a0-a1/a6,-(sp)
	move.l	dosbase,a6
	move.l	fh,d1
	move.l	#iobuf,d2
	move.l	#IOBUFSIZE,d3
	jsr	_LVORead(a6)
	tst.l	d0
	bpl.s	.ok
	moveq	#0,d0
.ok	move.l	d0,buf_left
	move.l	#iobuf,buf_ptr
	add.l	d0,total_read
	bsr	progress
	movem.l	(sp)+,d1-d3/a0-a1/a6
	rts

get_byte:				; -> d0.b (d0 cleared above the byte)
	tst.l	buf_left
	bne.s	.have
	bsr	refill
	tst.l	buf_left
	bne.s	.have
	moveq	#0,d0			; end of file
	rts
.have	move.l	a0,-(sp)
	move.l	buf_ptr,a0
	moveq	#0,d0
	move.b	(a0)+,d0
	move.l	a0,buf_ptr
	subq.l	#1,buf_left
	move.l	(sp)+,a0
	rts

get_long:
	move.l	d1,-(sp)
	bsr	get_byte
	move.l	d0,d1
	bsr	get_byte
	lsl.l	#8,d1
	or.b	d0,d1
	bsr	get_byte
	lsl.l	#8,d1
	or.b	d0,d1
	bsr	get_byte
	lsl.l	#8,d1
	or.b	d0,d1
	move.l	d1,d0
	move.l	(sp)+,d1
	rts

; read_block: a0 = destination, d1 = bytes -> d0 = 1 ok
read_block:
	movem.l	d1-d3/a0-a1/a6,-(sp)
.drain	tst.l	d1			; what is left in the buffer first
	beq.s	.ok
	tst.l	buf_left
	beq.s	.direct
	bsr	get_byte
	move.b	d0,(a0)+
	subq.l	#1,d1
	bra.s	.drain
.direct	move.l	d1,d3			; then straight from the disk in chunks
	cmp.l	#CHUNK,d3
	bls.s	.c
	move.l	#CHUNK,d3
.c	move.l	d1,-(sp)
	move.l	a0,-(sp)
	move.l	dosbase,a6
	move.l	fh,d1
	move.l	a0,d2
	jsr	_LVORead(a6)
	move.l	(sp)+,a0
	move.l	(sp)+,d1
	tst.l	d0
	ble.s	.err
	add.l	d0,total_read
	add.l	d0,a0
	sub.l	d0,d1
	bsr	progress
	tst.l	d1
	bne.s	.c2
.ok	moveq	#1,d0
	bra.s	.x
.c2	move.l	d1,d3
	bra.s	.direct
.err	moveq	#0,d0
.x	movem.l	(sp)+,d1-d3/a0-a1/a6
	rts

	include	"depack.s"

;------------------------------------------------------------------ data
gfxname		dc.b	'graphics.library',0
dosname		dc.b	'dos.library',0
gamename	dc.b	'SOlymp.game',0
str_loading	dc.b	'LOADING...   0%',0
str_pct		dc.b	'LOADING...   0%',0
str_notfound	dc.b	'SOLYMP.GAME NOT FOUND!',0
		even

	section	data,data
	include	"loadpic.i"
	even
font8		incbin	"font8.bin"
loadpic_rle	incbin	"loadpic.rle"
	even

	section	bss,bss
stacksave	ds.l	1
wbmsg		ds.l	1
gfxbase		ds.l	1
dosbase		ds.l	1
oldview		ds.l	1
picptr		ds.l	1
olddir		ds.l	1
fh		ds.l	1
file_size	ds.l	1
total_read	ds.l	1
buf_left	ds.l	1
buf_ptr		ds.l	1
hunk_base	ds.l	MAXHUNKS
hunk_size	ds.l	MAXHUNKS
nhunks		ds.w	1
bar_done	ds.w	1
view		ds.b	20
vport		ds.b	40
rasinfo		ds.b	12
bitmap		ds.b	40
statbuf		ds.b	32
iobuf		ds.b	IOBUFSIZE
shown		ds.b	1
dirset		ds.b	1
