;------------------------------------------------------------------------------
;  ev_longjump.s - LONG JUMP: run, jump from the board (fire), hold fire for
;  the angle.  Three jumps, the best counts.
;  An event of Stronkie's Olympics (LongJump.evt; see kernel.i, field.s).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"ljp_equ.i"

LINE_X		equ	BOARD
RACE_LEN	equ	(BOARD+12-START_X)*16	; (on from there: over the board)
RACE_SHIFT	equ	4
CPU_LO		equ	600			; the others: 6.00 .. 8.50 m
CPU_HI		equ	850
MAXD		equ	980			; cm at top speed, 45 degrees
WASTE		equ	7			; cm lost per pixel before the board
WINDY		equ	0

	section	code,code
	bra.w	entry
	dc.l	'SOEV'
	dc.w	CPU_LO,CPU_HI
	dc.w	0

entry:	movem.l	d1-d7/a0-a6,-(sp)
	move.l	sp,ev_sp
	clr.b	hide_me
	bsr	fld_setup
	moveq	#-1,d0
	move.l	d0,p_fr
	moveq	#1,d0
	bsr	frames
	jsr	K_FADEIN(a5)
	lea	v_title,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#20,d0
	bsr	frames
	bsr	fld_main
	bra	ev_done

; fly: d0.l = the distance (cm): the jump into the pit
fly:	movem.l	d0-d7,-(sp)
	move.l	p_pos,d0		; from here
	bsr	race_x
	move.w	d0,d6			; d6 = x at the take-off
	move.l	(sp),d0			; to the board + the distance
	mulu	#PX_M,d0
	divu	#100,d0
	add.w	#BOARD,d0
	move.w	d0,d7			; d7 = x at the landing
	move.w	angle,d5		; the height: 6 + angle / 2
	lsr.w	#1,d5
	addq.w	#6,d5
	moveq	#7,d0
	move.l	d0,p_fr
	moveq	#0,d4			; t = 0 .. 24
.t	; x = x0 + (x1 - x0) * t / 24
	move.w	d7,d0
	sub.w	d6,d0
	muls	d4,d0
	divs	#24,d0
	add.w	d6,d0
	sub.w	#START_X,d0		; back to a position
	ext.l	d0
	lsl.l	#RACE_SHIFT,d0
	move.l	d0,p_pos
	; up = h * 4 t (24 - t) / 576
	moveq	#24,d0
	sub.w	d4,d0
	mulu	d4,d0
	lsl.w	#2,d0
	mulu	d5,d0
	divu	#576,d0
	move.w	d0,p_up
	bsr	frame
	addq.w	#1,d4
	cmp.w	#25,d4
	blo.s	.t
	clr.w	p_up
	moveq	#8,d0			; in the sand
	move.l	d0,p_fr
	lea	snd_thud,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#20,d0
	bsr	frames
	movem.l	(sp)+,d0-d7
	rts

fld_reset:
	rts

	include	"field.s"
	include	"fieldcommon.s"
	include	"evcommon.s"
	include	"race.s"

	section	data,data
	include	"ljp_data.i"
bg_rle	incbin	"ljp_bg.rle"
	even
	section	chip,data_c
ljp_chip	incbin	"ljp_chip.bin"
