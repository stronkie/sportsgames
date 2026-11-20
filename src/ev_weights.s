;------------------------------------------------------------------------------
;  ev_weights.s - WEIGHTLIFTING: three attempts, 30 kg more after a good lift.
;  Left/right in turn fill the power bar: get it over the line and fire for
;  the clean, then once more for the jerk.  Fire too soon: no lift.
;  An event of Stronkie's Olympics (Weights.evt; see kernel.i).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"wgt_equ.i"

CPU_LO		equ	150			; the others: 150 .. 230 kg
CPU_HI		equ	230
FIRST		equ	150			; the first attempt (kg)
STEP		equ	30
STROKE		equ	160			; power per step (of 1000)
PHASE_T		equ	150			; ticks for each part of the lift

	section	code,code
	bra.w	entry
	dc.l	'SOEV'
	dc.w	CPU_LO,CPU_HI
	dc.w	0

entry:	movem.l	d1-d7/a0-a6,-(sp)
	move.l	sp,ev_sp
	lea	pm_tab,a0
	tst.w	CX_WOMAN(a4)
	beq.s	.m
	lea	pw_tab,a0
.m	move.l	a0,pl_tab
	clr.w	lfr
	lea	pal_wgt,a0
	lea	bg_rle,a1
	bsr	ev_start
	clr.w	best
	move.w	#FIRST,weight
	move.w	#1,attempt
	clr.w	power
	move.w	#-1,shown
	moveq	#1,d0
	bsr	frames
	jsr	K_FADEIN(a5)
	lea	v_title,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	s_help,a0
	bsr	message_small
	moveq	#50,d0
	bsr	frames
.att	clr.w	lfr
	clr.w	power
	bsr	draw_top
	lea	strbuf,a1		; "150 KG"
	moveq	#0,d0
	move.w	weight,d0
	bsr	catnum
	lea	s_kg,a0
	bsr	cat
	lea	strbuf,a0
	bsr	message
	moveq	#40,d0
	bsr	frames
	bsr	clear_msg
	; the clean: up to the shoulders
	move.w	weight,d0		; the line: weight * 1000 / 350
	mulu	#20,d0
	divu	#7,d0
	move.w	d0,need
	bsr	lift
	tst.w	d0
	beq	.fail
	move.w	#2,lfr
	lea	snd_grunt,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#12,d0
	bsr	frames
	move.w	#3,lfr
	clr.w	power
	moveq	#20,d0
	bsr	frames
	; the jerk: over the head (the line a little higher)
	add.w	#50,need
	bsr	lift
	tst.w	d0
	beq.s	.fail
	move.w	#4,lfr
	lea	snd_grunt,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#14,d0
	bsr	frames
	move.w	#5,lfr
	lea	s_good,a0
	bsr	message
	moveq	#CS_CHEER,d0
	moveq	#56,d1
	jsr	K_CSFX(a5)
	move.w	weight,best
	add.w	#STEP,weight
	bra.s	.next
.fail	move.w	#6,lfr			; the bar on the floor
	lea	snd_clang,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	s_nolift,a0
	bsr	message
	moveq	#CS_OHNO,d0
	moveq	#48,d1
	jsr	K_CSFX(a5)
.next	moveq	#60,d0
	bsr	frames
	bsr	clear_msg
	addq.w	#1,attempt
	cmp.w	#3,attempt
	bls	.att
	moveq	#0,d0			; the result: the best lift
	move.w	best,d0
	bsr	result_pts
	lea	CX_RESULT(a4),a1	; (KG, not PTS)
.f	tst.b	(a1)+
	bne.s	.f
	subq.l	#4,a1
	move.b	#'K',(a1)+
	move.b	#'G',(a1)+
	clr.b	(a1)
	lea	CX_RESULT(a4),a0
	bsr	message
	bra	ev_done

; lift: waggle the power over the line, fire -> d0 = 1 lifted, 0 failed (too soon, too late)
lift:	clr.w	power
	clr.w	ltime
.l	bsr	waggle
	tst.w	d0
	beq.s	.nw
	add.w	#STROKE,power
	cmp.w	#1000,power
	bls.s	.nw
	move.w	#1000,power
.nw	move.w	power,d0		; it fades
	lsr.w	#4,d0
	sub.w	d0,power
	moveq	#0,d0			; the frame: the bar comes up with the power (clean only)
	cmp.w	#3,lfr
	beq.s	.fr
	move.w	power,d1
	cmp.w	need,d1
	blo.s	.fr
	moveq	#1,d0
	move.w	d0,lfr
	bra.s	.dr
.fr	cmp.w	#3,lfr
	beq.s	.dr
	move.w	d0,lfr
.dr	bsr	draw_meter
	bsr	frame
	move.w	pressed,d0
	btst	#J_FIRE,d0
	beq.s	.nf
	move.w	power,d0
	cmp.w	need,d0
	shs	d0
	and.w	#1,d0
	rts
.nf	addq.w	#1,ltime
	cmp.w	#PHASE_T,ltime
	blo	.l
	moveq	#0,d0
	rts

; the power meter (only when it changed: 50 steps of 2 pixels)
draw_meter:
	movem.l	d0-d6,-(sp)
	move.w	power,d0
	ext.l	d0
	divu	#20,d0			; 0..50
	cmp.w	shown,d0
	beq.s	.x
	move.w	d0,shown
	move.w	d0,d6
	add.w	d6,d6			; full height
	moveq	#MET_H,d5
	sub.w	d6,d5			; empty height
	beq.s	.f
	move.w	#MET_X,d0		; empty
	move.w	#MET_Y,d1
	moveq	#16,d2
	move.w	d5,d3
	moveq	#0,d4
	jsr	K_FILL(a5)
.f	tst.w	d6
	beq.s	.l
	move.w	#MET_X,d0		; full: green, red under the line
	move.w	#MET_Y,d1
	add.w	d5,d1
	moveq	#16,d2
	move.w	d6,d3
	moveq	#4,d4
	move.w	power,d0
	cmp.w	need,d0
	blo.s	.r
	moveq	#13,d4
.r	move.w	#MET_X,d0
	jsr	K_FILL(a5)
.l	move.w	need,d0			; the line
	ext.l	d0
	divu	#10,d0
	moveq	#MET_H,d1
	sub.w	d0,d1
	add.w	#MET_Y,d1
	move.w	#MET_X,d0
	moveq	#16,d2
	moveq	#1,d3
	moveq	#2,d4
	jsr	K_FILL(a5)
.x	movem.l	(sp)+,d0-d6
	rts

draw_top:
	movem.l	d0-d3/a0-a1,-(sp)
	lea	strbuf,a1
	lea	s_att,a0
	bsr	cat
	moveq	#0,d0
	move.w	attempt,d0
	bsr	catnum
	lea	strbuf,a0
	moveq	#8,d0
	moveq	#3,d2
	bsr	top_text
	lea	strbuf,a1
	lea	s_best,a0
	bsr	cat
	moveq	#0,d0
	move.w	best,d0
	bsr	catnum
	lea	s_kg,a0
	bsr	cat
	lea	strbuf,a0
	move.w	#192,d0
	moveq	#3,d2
	bsr	top_text
	movem.l	(sp)+,d0-d3/a0-a1
	rts

frame:
	movem.l	d0-d3/a0,-(sp)
	jsr	K_BEGIN(a5)
	move.w	lfr,d0
	lsl.w	#2,d0
	move.l	pl_tab,a0
	move.l	(a0,d0.w),a0
	move.w	#LX,d0
	move.w	#LY-79,d1
	jsr	K_BOB(a5)
	jsr	K_END(a5)
	bsr	read_input
	movem.l	(sp)+,d0-d3/a0
	rts

	include	"evcommon.s"

	section	data,data
s_help		dc.b	'LEFT/RIGHT: POWER OVER THE LINE, FIRE!',0
s_kg		dc.b	' KG',0
s_att		dc.b	'ATTEMPT ',0
s_best		dc.b	'BEST ',0
s_good		dc.b	'GOOD LIFT!',0
s_nolift	dc.b	'NO LIFT!',0
	even
	include	"wgt_data.i"
bg_rle	incbin	"wgt_bg.rle"
	even
	section	bss,bss
pl_tab		ds.l	1
lfr		ds.w	1
best		ds.w	1
weight		ds.w	1
attempt		ds.w	1
power		ds.w	1
need		ds.w	1
shown		ds.w	1
ltime		ds.w	1
	even
	section	chip,data_c
wgt_chip	incbin	"wgt_chip.bin"
