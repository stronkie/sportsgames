;------------------------------------------------------------------------------
;  ev_cycle.s - CYCLING, 500M on the velodrome: you against a rider from
;  another country.  Left/right in turn to pedal, up/down to change gear:
;  low gears pick up speed quickly, high gears go faster but need fast legs.
;  An event of Stronkie's Olympics (Cycling.evt; see kernel.i, race.s).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"cyc_equ.i"

RACE_LEN	equ	(FINISH_X-START_X-40)*64
RACE_SHIFT	equ	6
CPU_LO		equ	3200			; the rival: 32.00 .. 40.00 s
CPU_HI		equ	4000
GEAR_X		equ	232
GEAR_Y		equ	109

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
	clr.w	p_up
	clr.l	hook_frame
	move.w	#1,gear
	bsr	race_setup
	bsr	race_init
	bsr	draw_gear
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
.loop	move.w	pressed,d0		; the gears
	btst	#J_UP,d0
	beq.s	.nu
	cmp.w	#5,gear
	beq.s	.nu
	addq.w	#1,gear
	bsr	gear_click
.nu	btst	#J_DOWN,d0
	beq.s	.nd
	cmp.w	#1,gear
	beq.s	.nd
	subq.w	#1,gear
	bsr	gear_click
.nd	moveq	#10,d1			; gear g: a stroke adds 10-g, the top is 6+4g
	sub.w	gear,d1
	move.w	gear,d2
	lsl.w	#2,d2
	addq.w	#6,d2
	bsr	race_run
	tst.b	stroked
	beq.s	.t
	addq.b	#1,strokes
	moveq	#3,d0
	and.b	strokes,d0
	bne.s	.t
	lea	snd_whirr,a0
	moveq	#24,d1
	jsr	K_SFX(a5)
.t	bsr	race_tick
	bsr	frame
	tst.b	p_done
	beq	.loop
	bsr	race_finish
	bra	ev_done

gear_click:
	lea	snd_gear,a0
	moveq	#48,d1
	jsr	K_SFX(a5)
draw_gear:
	movem.l	d0-d3/a0-a1,-(sp)
	lea	strbuf,a1
	lea	s_gear,a0
	bsr	cat
	move.w	gear,d0
	add.b	#'0',d0
	move.b	d0,(a1)+
	clr.b	(a1)
	lea	strbuf,a0
	move.w	#GEAR_X,d0
	move.w	#GEAR_Y,d1
	moveq	#3,d2
	moveq	#13,d3			; (on the blue strip)
	jsr	K_TEXT(a5)
	movem.l	(sp)+,d0-d3/a0-a1
	rts

	include	"racecommon.s"
	include	"evcommon.s"
	include	"race.s"

	section	data,data
s_gear		dc.b	'GEAR ',0
	even
	include	"cyc_data.i"
bg_rle	incbin	"cyc_bg.rle"
	even
	section	bss,bss
gear		ds.w	1
strokes		ds.b	1
	even
	section	chip,data_c
cyc_chip	incbin	"cyc_chip.bin"
