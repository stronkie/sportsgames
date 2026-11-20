;------------------------------------------------------------------------------
;  ev_sprint.s - 100M SPRINT: you against a runner from another country.
;  An event of Stronkie's Olympics (Sprint.evt; see kernel.i, race.s).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"spr_equ.i"

RACE_LEN	equ	(FINISH_X-START_X)*16
RACE_SHIFT	equ	4
CPU_LO		equ	1000			; the rival: 10.00 .. 12.50 s
CPU_HI		equ	1250

	section	code,code
	bra.w	entry
	dc.l	'SOEV'
	dc.w	CPU_LO,CPU_HI
	dc.w	1			; (lower is better)

entry:	movem.l	d1-d7/a0-a6,-(sp)
	move.l	sp,ev_sp
	move.l	#-1,p_fr
	move.l	#-1,c_fr
	clr.w	c_up
	clr.l	hook_frame
	clr.w	p_up
	bsr	race_setup
	bsr	race_init
	moveq	#1,d0
	bsr	frames
	jsr	K_FADEIN(a5)
	lea	v_title,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#20,d0
	bsr	frames
	bsr	race_countdown
	lea	snd_gun,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
.run	moveq	#5,d1			; a step adds 5, the top speed is 22
	moveq	#22,d2
	bsr	race_run
	bsr	race_tick
	bsr	frame
	tst.b	p_done
	beq.s	.run
	bsr	race_finish
	bra	ev_done

	include	"racecommon.s"
	include	"evcommon.s"
	include	"race.s"

	section	data,data
	include	"spr_data.i"
bg_rle	incbin	"spr_bg.rle"
	even
	section	chip,data_c
spr_chip	incbin	"spr_chip.bin"
