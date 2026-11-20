;------------------------------------------------------------------------------
;  ev_javelin.s - JAVELIN: run, throw at the line (fire), hold fire for the angle.
;  Three throws, the best counts.
;  An event of Stronkie's Olympics (Javelin.evt; see kernel.i, field.s).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"jav_equ.i"

LINE_X		equ	BOARD
RACE_LEN	equ	(BOARD+12-START_X)*16	; (on from there: over the line)
RACE_SHIFT	equ	4
CPU_LO		equ	5500
CPU_HI		equ	8500
MAXD		equ	9800			; cm at top speed, 45 degrees
WASTE		equ	5			; cm lost per pixel before the line
WINDY		equ	0
ROLL		equ	0

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
	include	"jav_data.i"
bg_rle		incbin	"jav_bg.rle"
	even
field_rle	incbin	"jav_field.rle"
	even
	section	chip,data_c
jav_chip	incbin	"jav_chip.bin"
