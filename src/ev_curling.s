;------------------------------------------------------------------------------
;  ev_curling.s - PENGUIN CURLING: six penguins to the house.  Up/down to
;  aim, fire to start the power and fire again to slide; left/right in turn
;  to sweep (it slides further).  Close to the middle: 10, 8, 6, 4, 2 points.
;  An event of Stronkie's Olympics (Curling.evt; see kernel.i).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"cur_equ.i"

CPU_LO		equ	15			; the others: 15 .. 40 points
CPU_HI		equ	40
NPENG		equ	6
POW_W		equ	96			; the power bar (pixels)

	section	code,code
	bra.w	entry
	dc.l	'SOEV'
	dc.w	CPU_LO,CPU_HI
	dc.w	0

entry:	movem.l	d1-d7/a0-a6,-(sp)
	move.l	sp,ev_sp
	lea	pal_cur,a0
	lea	bg_rle,a1
	bsr	ev_start
	clr.w	score
	move.w	#1,peng
	clr.w	pshown
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
.peng	bsr	clear_msg
	bsr	draw_top
	move.w	#X_START*16,gx		; the penguin, standing at the start
	move.w	#Y_MID*16,gy
	move.w	#Y_MID,aim
	move.w	#2,gfr
	st	show_m
	clr.w	power
	move.w	#-1,pshown
	bsr	draw_power
	; aim: up/down, fire
.aim	move.w	held,d0
	btst	#J_UP,d0
	beq.s	.nu
	cmp.w	#HY-40,aim
	ble.s	.nu
	subq.w	#1,aim
.nu	btst	#J_DOWN,d0
	beq.s	.nd
	cmp.w	#HY+40,aim
	bge.s	.nd
	addq.w	#1,aim
.nd	bsr	frame
	move.w	pressed,d0
	btst	#J_FIRE,d0
	beq.s	.aim
	; the power: up and down until fire
	moveq	#3,d6			; +3 / -3 a tick
.pw	add.w	d6,power
	cmp.w	#100,power
	blt.s	.p1
	move.w	#100,power
	neg.w	d6
.p1	tst.w	power
	bgt.s	.p2
	clr.w	power
	neg.w	d6
.p2	bsr	draw_power
	bsr	frame
	move.w	pressed,d0
	btst	#J_FIRE,d0
	beq.s	.pw
	; the slide: v = 40 + power * 4/5 (1/16 px a tick), slower by 1 a tick (sweeping: every other)
	sf	show_m
	move.w	power,d0
	mulu	#4,d0
	divu	#5,d0
	add.w	#40,d0
	move.w	d0,speed
	; dy per dx (1/256): (aim - Y_MID) * 256 / (HX - X_START)
	move.w	aim,d0
	sub.w	#Y_MID,d0
	asl.w	#8,d0
	ext.l	d0
	divs	#HX-X_START,d0
	move.w	d0,slope
	lea	snd_slide,a0
	moveq	#48,d1
	jsr	K_SFX(a5)
	clr.w	stick
.sl	moveq	#0,d0			; x
	move.w	speed,d0
	add.w	d0,gx
	muls	slope,d0		; y
	asr.l	#8,d0
	add.w	d0,gy
	addq.w	#1,stick
	bsr	waggle			; sweeping: no slowing down this tick
	tst.w	d0
	beq.s	.fr
	moveq	#3,d0
	and.w	stick,d0
	bne.s	.sw
	lea	snd_swish,a0
	moveq	#32,d1
	jsr	K_SFX(a5)
.sw	btst	#0,stick
	bne.s	.nf
.fr	subq.w	#1,speed
.nf	moveq	#4,d1			; the flippers
	and.w	stick,d1
	lsr.w	#2,d1
	move.w	d1,gfr
	bsr	frame
	cmp.w	#316*16,gx		; off the ice
	bge	.gone
	tst.w	speed
	bgt.s	.sl
	; it stops: stays on the ice, the points
	move.w	#2,gfr
	lea	pg_tab+8,a0
	move.l	(a0),a0
	move.w	gx,d0
	asr.w	#4,d0
	subq.w	#8,d0
	move.w	gy,d1
	asr.w	#4,d1
	subq.w	#8,d1
	jsr	K_STAMP(a5)
	move.w	gx,d0			; the distance to the button
	asr.w	#4,d0
	sub.w	#HX,d0
	muls	d0,d0
	move.w	gy,d1
	asr.w	#4,d1
	sub.w	#HY,d1
	muls	d1,d1
	add.l	d1,d0			; d0 = distance^2
	moveq	#10,d2			; 10 points under 6 pixels, 8 under 12 ...
	moveq	#6,d3
.r	move.w	d3,d1
	mulu	d1,d1
	cmp.l	d1,d0
	blo.s	.pts
	addq.w	#6,d3
	subq.w	#2,d2
	bgt.s	.r
	moveq	#0,d2
.pts	add.w	d2,score
	lea	strbuf,a1
	move.b	#'+',(a1)+
	moveq	#0,d0
	move.w	d2,d0
	bsr	catnum
	lea	strbuf,a0
	bsr	message
	moveq	#CS_CLAP,d0
	tst.w	d2
	bne.s	.cl
	moveq	#CS_OOH,d0
.cl	moveq	#48,d1
	jsr	K_CSFX(a5)
	bra.s	.next
.gone	lea	snd_squawk,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	s_gone,a0
	bsr	message
.next	move.w	#-100,gx		; (out of sight)
	bsr	draw_top
	moveq	#40,d0
	bsr	frames
	addq.w	#1,peng
	cmp.w	#NPENG,peng
	bls	.peng
	moveq	#0,d0
	move.w	score,d0
	bsr	result_pts
	lea	CX_RESULT(a4),a0
	bsr	message
	moveq	#CS_GREAT,d0
	moveq	#64,d1
	jsr	K_CSFX(a5)
	bra	ev_done

draw_power:
	movem.l	d0-d4,-(sp)
	move.w	power,d0		; 12 blocks of 8 pixels
	mulu	#12,d0
	divu	#100,d0
	cmp.w	pshown,d0
	beq.s	.x
	move.w	d0,pshown
	move.w	d0,d2
	lsl.w	#3,d2
	beq.s	.e
	move.w	#POW_X,d0
	move.w	#POW_Y,d1
	moveq	#6,d3
	moveq	#4,d4
	jsr	K_FILL(a5)
.e	move.w	#POW_W,d3
	sub.w	d2,d3
	beq.s	.x
	move.w	#POW_X,d0
	add.w	d2,d0
	move.w	d3,d2
	move.w	#POW_Y,d1
	moveq	#6,d3
	moveq	#16,d4
	jsr	K_FILL(a5)
.x	movem.l	(sp)+,d0-d4
	rts

draw_top:
	movem.l	d0-d3/a0-a1,-(sp)
	lea	strbuf,a1
	lea	s_peng,a0
	bsr	cat
	moveq	#0,d0
	move.w	peng,d0
	cmp.w	#NPENG,d0
	bls.s	.p
	moveq	#NPENG,d0
.p	bsr	catnum
	lea	s_of6,a0
	bsr	cat
	lea	strbuf,a0
	moveq	#8,d0
	moveq	#3,d2
	bsr	top_text
	lea	strbuf,a1
	lea	s_score,a0
	bsr	cat
	moveq	#0,d0
	move.w	score,d0
	bsr	catnum
	lea	strbuf,a0
	move.w	#200,d0
	moveq	#3,d2
	bsr	top_text
	movem.l	(sp)+,d0-d3/a0-a1
	rts

frame:
	movem.l	d0-d3/a0,-(sp)
	jsr	K_BEGIN(a5)
	tst.b	show_m			; the aim
	beq.s	.nm
	lea	marker,a0
	move.w	#HX-7,d0
	move.w	aim,d1
	subq.w	#7,d1
	jsr	K_BOB(a5)
.nm	move.w	gx,d0			; the penguin
	bmi.s	.np
	asr.w	#4,d0
	subq.w	#8,d0
	bpl.s	.x0
	moveq	#0,d0
.x0	move.w	gy,d1
	asr.w	#4,d1
	subq.w	#8,d1
	move.w	gfr,d2
	lsl.w	#2,d2
	lea	pg_tab,a0
	move.l	(a0,d2.w),a0
	jsr	K_BOB(a5)
.np	jsr	K_END(a5)
	bsr	read_input
	movem.l	(sp)+,d0-d3/a0
	rts

	include	"evcommon.s"

	section	data,data
s_help		dc.b	'AIM: UP/DOWN, FIRE, FIRE. SWEEP: L/R!',0
s_peng		dc.b	'PENGUIN ',0
s_of6		dc.b	'/6',0
s_score		dc.b	'SCORE ',0
s_gone		dc.b	'OFF THE ICE!',0
	even
	include	"cur_data.i"
bg_rle	incbin	"cur_bg.rle"
	even
	section	bss,bss
gx		ds.w	1
gy		ds.w	1
gfr		ds.w	1
aim		ds.w	1
power		ds.w	1
pshown		ds.w	1
speed		ds.w	1
slope		ds.w	1
stick		ds.w	1
score		ds.w	1
peng		ds.w	1
show_m		ds.b	1
	even
	section	chip,data_c
cur_chip	incbin	"cur_chip.bin"
