;------------------------------------------------------------------------------
;  ev_bowling.s - BOWLING: ten pin bowling, 10 frames.
;  An event of Stronkie's Olympics (loaded from Bowling.evt; see kernel.i).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"bow_equ.i"

BAR_X		equ	96			; the meters in the bottom bar: 128 wide
PIN_U		equ	43			; one pin column in lane units (1/256)

	section	code,code
	bra.w	entry
	dc.l	'SOEV'
	dc.w	110,200			; the computer athletes score 110..200 pins
	dc.w	0

entry:	movem.l	d1-d7/a0-a6,-(sp)
	move.l	sp,ev_sp
	lea	vars,a0
	move.w	#VARS_SIZE/2-1,d0
.cl	clr.w	(a0)+
	dbf	d0,.cl
	lea	bm_tab,a0
	tst.w	CX_WOMAN(a4)
	beq.s	.m
	lea	bw_tab,a0
.m	move.l	a0,bw_tabp
	lea	pal_bow,a0
	lea	bg_rle,a1
	bsr	ev_start
	bsr	pins_reset
	bsr	draw_box
	bsr	draw_score
	moveq	#1,d0
	bsr	frames
	jsr	K_FADEIN(a5)
	lea	v_bowling,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#20,d0
	bsr	frames
	bsr	score_frames
	bsr	draw_score

	clr.w	fr
.frame	bsr	pins_reset
	bsr	draw_box
	bsr	throw			; ball 1
	move.w	d0,d6
	cmp.w	#9,fr
	beq.s	.tenth
	cmp.w	#10,d6
	beq.s	.strike
	bsr	throw			; ball 2
	add.w	d0,d6
	cmp.w	#10,d6
	bne.s	.next
	bsr	say_spare
	bra.s	.next
.strike	bsr	say_strike
.next	addq.w	#1,fr
	bra.s	.frame
.tenth	cmp.w	#10,d6			; the 10th frame: 2 or 3 balls
	bne.s	.t1
	bsr	say_strike
	bsr	pins_reset
	bsr	draw_box
	bsr	throw
	cmp.w	#10,d0
	bne.s	.t3
	bsr	say_strike
	bsr	pins_reset
	bsr	draw_box
	bra.s	.t3
.t1	bsr	throw
	add.w	d0,d6
	cmp.w	#10,d6
	bne.s	.end
	bsr	say_spare
	bsr	pins_reset
	bsr	draw_box
.t3	bsr	throw
	cmp.w	#10,d0
	bne.s	.end
	bsr	say_strike
.end	bsr	score_frames
	moveq	#0,d0
	move.w	total,d0
	bsr	result_pts
	lea	s_pins,a0		; (pins, not points)
	lea	CX_RESULT(a4),a1
.e	tst.b	(a1)+
	bne.s	.e
	subq.l	#4,a1
	bsr	cat
	moveq	#CS_CLAP,d0
	moveq	#40,d1
	jsr	K_CSFX(a5)
	lea	CX_RESULT(a4),a0
	bsr	message
	bra	ev_done

say_strike:
	lea	v_strike,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#CS_CHEER,d0
	moveq	#40,d1
	jsr	K_CSFX(a5)
	lea	s_strike,a0
	bra.s	say
say_spare:
	lea	v_spare,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#CS_CLAP,d0
	moveq	#36,d1
	jsr	K_CSFX(a5)
	lea	s_spare,a0
say	bsr	message
	moveq	#40,d0
	bsr	frames
	bsr	clear_msg
	rts

;------------------------------------------------------------------ one ball
; throw -> d0 = pins knocked down (also into the rolls and the score)
throw:
	movem.l	d1-d7/a0-a3,-(sp)
	clr.w	bfr
	sf	ball_on
	; 1. where you stand
	lea	s_pos,a0
	bsr	message_small
.pos	move.w	held,d1
	btst	#J_LEFT,d1
	beq.s	.nl
	sub.w	#8,u0
.nl	btst	#J_RIGHT,d1
	beq.s	.nr
	add.w	#8,u0
.nr	cmp.w	#-200,u0
	bge.s	.a
	move.w	#-200,u0
.a	cmp.w	#200,u0
	ble.s	.b
	move.w	#200,u0
.b	bsr	frame
	btst	#J_FIRE,pressed+1
	beq.s	.pos
	moveq	#CS_BEEP,d0
	moveq	#40,d1
	jsr	K_CSFX(a5)
	; 2. the spin (hook)
	bsr	clear_msg
	lea	s_hook,a0
	moveq	#8,d0
	move.w	#244,d1
	moveq	#2,d2
	moveq	#-1,d3
	jsr	K_TEXT(a5)
	move.w	#-100,hook
	move.w	#7,hook_d
	moveq	#4,d0
	sub.w	CX_LEVEL(a4),d0
	sub.w	CX_LEVEL(a4),d0		; (faster on hard)
	neg.w	d0
	add.w	#11,d0
	move.w	d0,hook_d
.hk	move.w	hook,d0
	add.w	hook_d,d0
	cmp.w	#-100,d0
	bge.s	.h1
	move.w	#-100,d0
	neg.w	hook_d
.h1	cmp.w	#100,d0
	ble.s	.h2
	moveq	#100,d0
	neg.w	hook_d
.h2	move.w	d0,hook
	bsr	draw_hook
	bsr	frame
	btst	#J_FIRE,pressed+1
	beq.s	.hk
	moveq	#CS_BEEP,d0
	moveq	#40,d1
	jsr	K_CSFX(a5)
	; 3. the power
	bsr	clear_msg
	lea	s_power,a0
	moveq	#8,d0
	move.w	#244,d1
	moveq	#2,d2
	moveq	#-1,d3
	jsr	K_TEXT(a5)
	clr.w	power
	move.w	#6,pow_d
.pw	move.w	power,d0
	add.w	pow_d,d0
	bpl.s	.p1
	moveq	#0,d0
	neg.w	pow_d
.p1	cmp.w	#100,d0
	blt.s	.p2
	moveq	#100,d0
	neg.w	pow_d
.p2	move.w	d0,power
	bsr	draw_power
	bsr	frame
	btst	#J_FIRE,pressed+1
	beq.s	.pw
	bsr	clear_msg
	; 4. swing and let go
	move.w	#1,bfr
	moveq	#6,d0
	bsr	frames
	move.w	#2,bfr
	lea	snd_drop,a0
	moveq	#50,d1
	jsr	K_SFX(a5)
	; 5. the ball rolls down the lane
	move.w	u0,d0
	ext.l	d0
	lsl.l	#4,d0
	move.l	d0,u16
	clr.l	uvel
	clr.w	vpos
	sf	gutter
	st	ball_on
	lea	snd_roll,a0
	moveq	#56,d1
	jsr	K_SFX(a5)
	move.w	power,d5
	ext.l	d5
	divu	#6,d5
	add.w	#10,d5			; speed: 10..26 (1/16 of a lane step a tick)
.roll	add.w	d5,vpos
	cmp.w	#NV*16,vpos
	blo.s	.r1
	move.w	#NV*16,vpos
.r1	tst.b	gutter
	bne.s	.r3
	cmp.w	#NV*16/3,vpos		; the hook works after a third of the lane
	blo.s	.r2
	move.w	hook,d0
	ext.l	d0
	asr.l	#4,d0
	add.l	d0,uvel
.r2	move.l	uvel,d0
	add.l	d0,u16
	move.l	u16,d0
	asr.l	#4,d0
	cmp.l	#256,d0
	bgt.s	.gr
	cmp.l	#-256,d0
	bge.s	.r3
	move.l	#-282*16,u16		; in the left gutter
	bra.s	.gut
.gr	move.l	#282*16,u16
.gut	st	gutter
	lea	snd_gutter,a0
	moveq	#50,d1
	jsr	K_SFX(a5)
.r3	bsr	frame
	cmp.w	#NV*16,vpos
	blo	.roll
	sf	ball_on
	; 6. the pins
	moveq	#0,d7
	tst.b	gutter
	bne.s	.gutter
	bsr	knock			; -> d7 = how many fall
	tst.w	d7
	beq.s	.none
	lea	snd_crash,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	bsr	fall_anim
	bra.s	.counted
.gutter	lea	v_gutter,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	s_gutter,a0
	bsr	message
	bra.s	.counted
.none	lea	s_miss,a0
	bsr	message
.counted
	move.w	nroll,d0		; into the rolls
	lea	rolls,a0
	move.b	d7,(a0,d0.w)
	addq.w	#1,nroll
	bsr	score_frames
	bsr	draw_score
	tst.w	d7
	beq.s	.w
	cmp.w	#10,d7
	beq.s	.w
	lea	strbuf,a1		; "7 PINS"
	moveq	#0,d0
	move.w	d7,d0
	bsr	catnum
	lea	s_pinsn,a0
	bsr	cat
	lea	strbuf,a0
	bsr	message
.w	moveq	#30,d0
	bsr	frames
	bsr	clear_msg
	clr.w	bfr
	move.w	d7,d0
	movem.l	(sp)+,d1-d7/a0-a3
	rts

; knock: which standing pins go down -> d7 = count (phit = 1 for those)
knock:
	lea	phit,a0
	moveq	#9,d0
.c	clr.b	(a0)+
	dbf	d0,.c
	move.l	u16,d4
	asr.l	#4,d4			; u of the ball at the pins
	; the chance a falling pin takes its neighbours: 40 + power/2 %, more in the pocket
	move.w	power,d6
	ext.l	d6
	divu	#3,d6
	add.w	#28,d6
	move.w	d4,d0			; pocket: between the head pin and the 2nd/3rd
	bpl.s	.ab
	neg.w	d0
.ab	sub.w	#PIN_U/2,d0
	bpl.s	.ab2
	neg.w	d0
.ab2	cmp.w	#18,d0
	bhi.s	.np
	add.w	#18,d6
	move.w	hook,d0			; turning in to the middle: even better
	muls	d4,d0
	bpl.s	.np
	add.w	#8,d6
.np	; the ball itself: every pin within reach of its path
	lea	pin_pos,a2
	lea	pstand,a1
	lea	phit,a0
	moveq	#0,d1
.dir	tst.b	(a1,d1.w)
	beq.s	.dn
	move.w	d1,d0
	lsl.w	#2,d0
	move.w	(a2,d0.w),d0		; column
	muls	#PIN_U,d0
	sub.w	d4,d0
	bpl.s	.dp
	neg.w	d0
.dp	cmp.w	#PIN_U-6,d0
	bhi.s	.dn
	st	(a0,d1.w)
.dn	addq.w	#1,d1
	cmp.w	#10,d1
	blo.s	.dir
	; pins take pins: three times over
	moveq	#2,d5
.pass	moveq	#0,d1
.p	lea	phit,a0
	tst.b	(a0,d1.w)
	beq	.pn
	move.w	d1,d0
	lsl.w	#2,d0
	move.w	(a2,d0.w),d2		; column
	move.w	2(a2,d0.w),d3		; row
	moveq	#0,d0			; every other pin: a neighbour?
.q	cmp.w	d1,d0
	beq.s	.qn
	lea	pstand,a1
	tst.b	(a1,d0.w)
	beq.s	.qn
	lea	phit,a1
	tst.b	(a1,d0.w)
	bne.s	.qn
	move.w	d0,d7
	lsl.w	#2,d7
	move.w	(a2,d7.w),a3		; (its column)
	move.w	2(a2,d7.w),d7		; its row
	sub.w	d3,d7
	cmp.w	#1,d7			; the row behind, one column to the side
	bne.s	.sr
	move.w	a3,d7
	sub.w	d2,d7
	bpl.s	.s1
	neg.w	d7
.s1	cmp.w	#1,d7
	bne.s	.qn
	move.w	d6,d7
	bra.s	.try
.sr	tst.w	d7			; the same row, next to it: less often
	bne.s	.qn
	move.w	a3,d7
	sub.w	d2,d7
	bpl.s	.s2
	neg.w	d7
.s2	cmp.w	#2,d7
	bne.s	.qn
	move.w	d6,d7
	lsr.w	#2,d7
.try	movem.l	d0-d1,-(sp)
	moveq	#100,d0
	jsr	K_RAND(a5)
	cmp.w	d7,d0
	movem.l	(sp)+,d0-d1
	bhs.s	.qn
	lea	phit,a1
	st	(a1,d0.w)
.qn	addq.w	#1,d0
	cmp.w	#10,d0
	blo.s	.q
.pn	addq.w	#1,d1
	cmp.w	#10,d1
	blo	.p
	dbf	d5,.pass
	; count them
	moveq	#0,d7
	lea	phit,a0
	lea	pstand,a1
	moveq	#9,d0
.n	tst.b	(a0)+
	beq.s	.nn
	tst.b	(a1)
	beq.s	.nn
	addq.w	#1,d7
.nn	addq.l	#1,a1
	dbf	d0,.n
	rts

; fall_anim: the hit pins fall one after the other, then they are gone
fall_anim:
	moveq	#0,d1
.l	lea	phit,a0
	tst.b	(a0,d1.w)
	beq.s	.n
	lea	pstand,a0
	tst.b	(a0,d1.w)
	beq.s	.n
	lea	pfall,a0
	move.b	#14,(a0,d1.w)		; lies there for a while
	lea	pstand,a0
	clr.b	(a0,d1.w)
	bsr	frame
.n	addq.w	#1,d1
	cmp.w	#10,d1
	blo.s	.l
	bsr	draw_box
	moveq	#14,d0
	bsr	frames
	rts

pins_reset:
	lea	pstand,a0
	lea	pfall,a1
	moveq	#9,d0
.l	st	(a0)+
	clr.b	(a1)+
	dbf	d0,.l
	rts

;------------------------------------------------------------------ the score
; score_frames: rolls -> fscore (cumulative, -1 = not known yet), total
score_frames:
	movem.l	d0-d4/a0-a1,-(sp)
	lea	fscore,a1
	moveq	#9,d0
.cl	move.w	#-1,(a1)+
	dbf	d0,.cl
	lea	rolls,a0
	lea	fscore,a1
	moveq	#0,d1			; roll index
	moveq	#0,d2			; total
	moveq	#0,d3			; frame
.f	move.w	d3,d4
	add.w	d4,d4
	move.w	#-1,(a1,d4.w)
	cmp.w	nroll,d1
	bhs	.x
	moveq	#0,d0
	move.b	(a0,d1.w),d0
	cmp.w	#10,d0			; strike: 10 + the next two
	bne.s	.ns
	move.w	d1,d0
	addq.w	#2,d0
	cmp.w	nroll,d0
	bhs	.x
	add.w	#10,d2
	moveq	#0,d0
	move.b	1(a0,d1.w),d0
	add.w	d0,d2
	move.b	2(a0,d1.w),d0
	add.w	d0,d2
	addq.w	#1,d1
	bra.s	.st
.ns	move.w	d1,d0			; open or spare
	addq.w	#1,d0
	cmp.w	nroll,d0
	bhs.s	.x
	moveq	#0,d0
	move.b	(a0,d1.w),d0
	moveq	#0,d4
	move.b	1(a0,d1.w),d4
	add.w	d4,d0
	cmp.w	#10,d0
	bne.s	.open
	move.w	d1,d4			; spare: 10 + the next one
	addq.w	#2,d4
	cmp.w	nroll,d4
	bhs.s	.x
	moveq	#0,d4
	move.b	2(a0,d1.w),d4
	add.w	d4,d0
.open	add.w	d0,d2
	addq.w	#2,d1
.st	move.w	d3,d4
	add.w	d4,d4
	move.w	d2,(a1,d4.w)
	move.w	d2,total
	addq.w	#1,d3
	cmp.w	#10,d3
	blo	.f
.x	movem.l	(sp)+,d0-d4/a0-a1
	rts

; draw_score: the marks (X / - 1-9) and the scores of the 10 frames in the top bar
draw_score:
	movem.l	d0-d7/a0-a2,-(sp)
	moveq	#0,d0
	moveq	#0,d1
	move.w	#320,d2
	moveq	#23,d3
	moveq	#0,d4
	jsr	K_FILL(a5)
	lea	rolls,a2
	moveq	#0,d6			; roll index
	moveq	#0,d7			; frame
.f	lea	strbuf,a1
	cmp.w	nroll,d6
	bhs	.marks
	moveq	#0,d0
	move.b	(a2,d6.w),d0
	cmp.w	#9,d7
	beq.s	.tenth
	cmp.w	#10,d0
	bne.s	.n1
	move.b	#' ',(a1)+
	move.b	#'X',(a1)+
	addq.w	#1,d6
	bra.s	.marks
.n1	bsr	mark
	addq.w	#1,d6
	cmp.w	nroll,d6
	bhs.s	.marks
	moveq	#0,d1
	move.b	-1(a2,d6.w),d1
	moveq	#0,d0
	move.b	(a2,d6.w),d0
	add.w	d0,d1
	cmp.w	#10,d1
	bne.s	.n2
	move.b	#'/',(a1)+
	addq.w	#1,d6
	bra.s	.marks
.n2	bsr	mark
	addq.w	#1,d6
	bra.s	.marks
.tenth	moveq	#2,d5			; up to 3 balls, a strike shows X
.t	cmp.w	nroll,d6
	bhs.s	.marks
	moveq	#0,d0
	move.b	(a2,d6.w),d0
	cmp.w	#10,d0
	bne.s	.tm
	move.b	#'X',(a1)+
	bra.s	.tn
.tm	bsr	mark
.tn	addq.w	#1,d6
	dbf	d5,.t
.marks	clr.b	(a1)
	lea	strbuf,a0
	move.w	d7,d0
	mulu	#24,d0
	addq.w	#8,d0
	moveq	#3,d1
	moveq	#2,d2
	moveq	#-1,d3
	jsr	K_TEXT(a5)
	lea	fscore,a0		; the score so far
	move.w	d7,d0
	add.w	d0,d0
	move.w	(a0,d0.w),d0
	bmi.s	.nf
	ext.l	d0
	moveq	#1,d1
	jsr	K_NUM(a5)
	move.w	d7,d0
	mulu	#24,d0
	addq.w	#8,d0
	moveq	#13,d1
	moveq	#3,d2
	moveq	#-1,d3
	jsr	K_TEXT(a5)
.nf	addq.w	#1,d7
	cmp.w	#10,d7
	blo	.f
	; the frame now: a little marker under it
	move.w	fr,d0
	mulu	#24,d0
	addq.w	#8,d0
	moveq	#21,d1
	moveq	#16,d2
	moveq	#1,d3
	moveq	#3,d4
	jsr	K_FILL(a5)
	movem.l	(sp)+,d0-d7/a0-a2
	rts
mark:					; d0 = pins -> a1 ('-' for none)
	moveq	#'-',d1
	tst.w	d0
	beq.s	.m
	moveq	#'0',d1
	add.w	d0,d1
.m	move.b	d1,(a1)+
	rts

; the pins that still stand, in the box at the right
draw_box:
	movem.l	d0-d6/a0-a1,-(sp)
	moveq	#0,d6
.l	lea	pin_box,a0
	move.w	d6,d0
	lsl.w	#2,d0
	move.w	2(a0,d0.w),d1
	move.w	(a0,d0.w),d0
	moveq	#8,d2
	moveq	#6,d3
	moveq	#2,d4			; white: standing
	lea	pstand,a1
	tst.b	(a1,d6.w)
	bne.s	.u
	moveq	#9,d4			; grey: down
.u	jsr	K_FILL(a5)
	addq.w	#1,d6
	cmp.w	#10,d6
	blo.s	.l
	movem.l	(sp)+,d0-d6/a0-a1
	rts

draw_hook:				; the spin meter: -100 left .. 100 right
	movem.l	d0-d4,-(sp)
	move.w	#BAR_X,d0
	move.w	#243,d1
	move.w	#128,d2
	moveq	#10,d3
	moveq	#9,d4
	jsr	K_FILL(a5)
	move.w	#BAR_X+56,d0		; the middle
	moveq	#16,d2
	moveq	#10,d4
	jsr	K_FILL(a5)
	move.w	hook,d0			; the marker
	add.w	#100,d0
	mulu	#120,d0
	divu	#200,d0
	and.w	#$fff8,d0
	add.w	#BAR_X,d0
	moveq	#8,d2
	moveq	#3,d4
	jsr	K_FILL(a5)
	movem.l	(sp)+,d0-d4
	rts

draw_power:
	movem.l	d0-d5,-(sp)
	move.w	power,d5
	mulu	#16,d5
	divu	#100,d5			; 0-16 blocks of 8
	move.w	#BAR_X,d0
	move.w	#243,d1
	move.w	#128,d2
	moveq	#10,d3
	moveq	#9,d4
	jsr	K_FILL(a5)
	tst.w	d5
	beq.s	.x
	move.w	#BAR_X,d0
	move.w	d5,d2
	lsl.w	#3,d2
	moveq	#17,d4
	cmp.w	#13,d5
	blo.s	.c
	moveq	#4,d4
.c	jsr	K_FILL(a5)
.x	movem.l	(sp)+,d0-d5
	rts

;------------------------------------------------------------------ one frame
frame:
	movem.l	d0-d7/a0-a1,-(sp)
	jsr	K_BEGIN(a5)
	; the pins, back row first
	moveq	#9,d7
.p	lea	pin_scr,a1
	move.w	d7,d0
	lsl.w	#2,d0
	move.w	2(a1,d0.w),d1
	move.w	(a1,d0.w),d0
	lea	pstand,a1
	tst.b	(a1,d7.w)
	beq.s	.f
	lea	pin_up,a0
	jsr	K_BOB(a5)
	bra.s	.np
.f	lea	pfall,a1
	tst.b	(a1,d7.w)
	beq.s	.np
	subq.b	#1,(a1,d7.w)
	lea	pin_down,a0
	subq.w	#3,d0
	add.w	#10,d1
	jsr	K_BOB(a5)
.np	dbf	d7,.p
	; the ball
	tst.b	ball_on
	beq.s	.nb
	move.w	vpos,d2
	lsr.w	#4,d2			; lane step
	move.w	d2,d3
	add.w	d3,d3
	lea	lane_y,a0
	move.w	(a0,d3.w),d1
	lea	lane_hw,a0
	move.w	(a0,d3.w),d0
	move.l	u16,d4
	asr.l	#4,d4
	muls	d4,d0
	asr.l	#8,d0
	add.w	#160,d0
	mulu	#5,d2			; size: big near, small far
	divu	#NV+1,d2
	lsl.w	#2,d2
	lea	bball_tab,a0
	move.l	(a0,d2.w),a0
	subq.w	#7,d0
	sub.w	#12,d1
	jsr	K_BOB(a5)
.nb	; the bowler
	move.l	bw_tabp,a0
	move.w	bfr,d0
	lsl.w	#2,d0
	move.l	(a0,d0.w),a0
	move.w	u0,d0
	muls	#92,d0
	asr.l	#8,d0
	add.w	#160-20,d0
	move.w	#186,d1
	tst.w	bfr
	beq.s	.st
	sub.w	#8,d1			; (forward to the line)
.st	jsr	K_BOB(a5)
	jsr	K_END(a5)
	bsr	read_input
	movem.l	(sp)+,d0-d7/a0-a1
	rts

	include	"evcommon.s"

;==============================================================================
	section	data,data
s_pos		dc.b	'LEFT/RIGHT: WHERE YOU STAND, FIRE',0
s_hook		dc.b	'SPIN:',0
s_power		dc.b	'POWER:',0
s_strike	dc.b	'STRIKE!',0
s_spare		dc.b	'SPARE!',0
s_gutter	dc.b	'GUTTER BALL!',0
s_miss		dc.b	'NO PINS!',0
s_pinsn		dc.b	' PINS',0
s_pins		dc.b	'PINS',0
	even
	include	"bow_data.i"
bg_rle	incbin	"bow_bg.rle"
	even

	section	chip,data_c
bow_chip	incbin	"bow_chip.bin"

	section	bss,bss
vars
bw_tabp		ds.l	1
u16		ds.l	1
uvel		ds.l	1
fr		ds.w	1
nroll		ds.w	1
total		ds.w	1
fscore		ds.w	10
u0		ds.w	1
hook		ds.w	1
hook_d		ds.w	1
power		ds.w	1
pow_d		ds.w	1
vpos		ds.w	1
bfr		ds.w	1
rolls		ds.b	24
pstand		ds.b	10
phit		ds.b	10
pfall		ds.b	10
ball_on		ds.b	1
gutter		ds.b	1
	even
VARS_END
VARS_SIZE	equ	VARS_END-vars
