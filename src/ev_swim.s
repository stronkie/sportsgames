;------------------------------------------------------------------------------
;  ev_swim.s - SWIMMING, 50M FREESTYLE: you against a swimmer from another
;  country.  Fire at GO to dive (the sooner the better), left/right in turn
;  to swim, fire to breathe when the air runs low.
;  An event of Stronkie's Olympics (Swimming.evt; see kernel.i, race.s).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"swi_equ.i"

RACE_LEN	equ	(FINISH_X-START_X-24)*32
RACE_SHIFT	equ	5
CPU_LO		equ	2350			; the rival: 23.50 .. 30.00 s
CPU_HI		equ	3000
AIR_MAX		equ	120			; ticks of air (4.8 s)
AIR_X		equ	216
AIR_Y		equ	114

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
	clr.b	dived
	clr.w	dive_t
	clr.w	react
	move.w	#AIR_MAX,air
	move.w	#-1,air_shown
	bsr	race_setup
	bsr	race_init
	move.w	#6,c_wait		; the rival's reaction on the block
	bsr	race_speed
	lea	s_air,a0		; the air meter in the bottom bar
	move.w	#184,d0
	move.w	#AIR_Y-1,d1
	moveq	#1,d2
	moveq	#-1,d3
	jsr	K_TEXT(a5)
	bsr	draw_air
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
	moveq	#6,d0			; on the block until you dive
	move.l	d0,p_fr
.loop	bsr	rival_frame
	tst.b	dived
	bne.s	.swim
	; on the block: fire dives (by itself after 2 seconds)
	addq.w	#1,react
	move.w	pressed,d0
	btst	#J_FIRE,d0
	bne.s	.dive
	cmp.w	#50,react
	blo	.tick
.dive	st	dived
	lea	snd_splash,a0
	moveq	#56,d1
	jsr	K_SFX(a5)
	moveq	#7,d0
	move.l	d0,p_fr
	move.w	#8,dive_t
	move.w	#40,d0			; a quick dive glides further
	sub.w	react,d0
	bpl.s	.d0
	moveq	#0,d0
.d0	mulu	#12,d0
	add.w	#(FINISH_X-START_X)*32/20,d0	; (2.5 m at least)
	ext.l	d0
	add.l	d0,p_pos
	move.w	#12*16,p_spd
	bra	.tick
.swim	tst.w	dive_t			; still gliding after the dive
	beq.s	.arms
	subq.w	#1,dive_t
	bne.s	.glide
	move.l	#-1,p_fr
.glide	moveq	#0,d0
	move.w	p_spd,d0
	lsr.w	#4,d0
	add.l	d0,p_pos
	bra	.tick
.arms	; breathing
	move.w	pressed,d0
	btst	#J_FIRE,d0
	beq.s	.nb
	move.w	#AIR_MAX,air
	move.w	p_spd,d0		; (it costs a little speed)
	mulu	#3,d0
	lsr.w	#2,d0
	move.w	d0,p_spd
	lea	snd_gasp,a0
	moveq	#48,d1
	jsr	K_SFX(a5)
	tst.b	out_msg
	beq.s	.nb
	clr.b	out_msg
	bsr	clear_msg
.nb	tst.w	air
	beq.s	.noair
	subq.w	#1,air
	bne.s	.st
	lea	s_breathe,a0		; out of air
	bsr	message
	st	out_msg
	moveq	#CS_OHNO,d0
	moveq	#48,d1
	jsr	K_CSFX(a5)
.st	moveq	#3,d1			; a stroke adds 3, the top speed is 16
	moveq	#16,d2
	bra.s	.go
.noair	moveq	#1,d1			; no air: slow
	moveq	#5,d2
.go	bsr	race_run
	tst.b	stroked			; (a stroke: a splash now and then)
	beq.s	.tick
	addq.b	#1,strokes
	btst	#0,strokes
	beq.s	.tick
	lea	snd_stroke,a0
	moveq	#28,d1
	jsr	K_SFX(a5)
.tick	bsr	race_tick
	bsr	frame
	bsr	draw_air
	tst.b	p_done
	beq	.loop
	moveq	#-1,d0
	move.l	d0,c_fr
	bsr	race_finish
	bra	ev_done

; the rival: on the block, then the dive, then swimming
rival_frame:
	moveq	#6,d0
	tst.w	c_wait
	bne.s	.s
	moveq	#7,d0
	cmp.w	#8,ctick
	blo.s	.s
	moveq	#-1,d0
.s	tst.b	running
	bne.s	.r
	moveq	#-1,d0
.r	move.l	d0,c_fr
	rts

; the air meter (only when it changed: 8 steps)
draw_air:
	movem.l	d0-d4,-(sp)
	moveq	#0,d0
	move.w	air,d0
	mulu	#10,d0			; 0..10 blocks of 8 pixels
	divu	#AIR_MAX,d0
	cmp.w	air_shown,d0
	beq.s	.x
	move.w	d0,air_shown
	move.w	d0,d2
	lsl.w	#3,d2			; full part
	moveq	#12,d4			; light blue, red when low
	cmp.w	#3,d0
	bhi.s	.c
	moveq	#4,d4
.c	tst.w	d2
	beq.s	.e
	move.w	#AIR_X,d0
	move.w	#AIR_Y,d1
	moveq	#6,d3
	jsr	K_FILL(a5)
.e	moveq	#80,d3			; empty part
	sub.w	d2,d3
	beq.s	.x
	move.w	#AIR_X,d0
	add.w	d2,d0
	move.w	d3,d2
	move.w	#AIR_Y,d1
	moveq	#6,d3
	moveq	#16,d4
	jsr	K_FILL(a5)
.x	movem.l	(sp)+,d0-d4
	rts

	include	"racecommon.s"
	include	"evcommon.s"
	include	"race.s"

	section	data,data
s_air		dc.b	'AIR',0
s_breathe	dc.b	'BREATHE! PRESS FIRE',0
	even
	include	"swi_data.i"
bg_rle	incbin	"swi_bg.rle"
	even
	section	bss,bss
air		ds.w	1
air_shown	ds.w	1
dive_t		ds.w	1
react		ds.w	1
dived		ds.b	1
out_msg		ds.b	1
strokes		ds.b	1
	even
	section	chip,data_c
swi_chip	incbin	"swi_chip.bin"
