;------------------------------------------------------------------------------
;  ev_tpthrow.s - TOILET PAPER THROW: run, throw at the line (fire), hold fire for the angle.
;  Three throws, the best counts.
;  Mind the wind: it can carry the roll a long way - or not.
;  An event of Stronkie's Olympics (TPThrow.evt; see kernel.i, field.s).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"tpt_equ.i"

LINE_X		equ	BOARD
RACE_LEN	equ	(BOARD+12-START_X)*16	; (on from there: over the line)
RACE_SHIFT	equ	4
CPU_LO		equ	1500
CPU_HI		equ	3500
MAXD		equ	4000			; cm at top speed, 45 degrees
WASTE		equ	3			; cm lost per pixel before the line
WINDY		equ	1
ROLL		equ	1

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

	include	"throwfly.s"
	include	"field.s"
	include	"fieldcommon.s"
	include	"evcommon.s"
	include	"race.s"

	section	data,data
	include	"tpt_data.i"
bg_rle		incbin	"tpt_bg.rle"
	even
field_rle	incbin	"tpt_field.rle"
	even
	section	chip,data_c
tpt_chip	incbin	"tpt_chip.bin"
