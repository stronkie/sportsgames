;------------------------------------------------------------------------------
;  ev_basket.s - BASKETBALL: the three point shoot-out (5 racks, 60 seconds).
;  An event of Stronkie's Olympics (loaded from Basket.evt; see kernel.i).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"bas_equ.i"

TIME		equ	60*25
METER_X		equ	16
METER_Y		equ	60			; top of the bar (100 pixels: power 100)
FLY		equ	20

	section	code,code
	bra.w	entry
	dc.l	'SOEV'
	dc.w	10,20			; the computer athletes score 10..20 points
	dc.w	0

entry:	movem.l	d1-d7/a0-a6,-(sp)
	move.l	sp,ev_sp
	lea	vars,a0
	move.w	#VARS_SIZE/2-1,d0
.cl	clr.w	(a0)+
	dbf	d0,.cl
	lea	pm_tab,a0
	tst.w	CX_WOMAN(a4)
	beq.s	.m
	lea	pw_tab,a0
.m	move.l	a0,pl_tab
	lea	pal_bas,a0
	lea	bg_rle,a1
	bsr	ev_start
	move.w	#TIME,time
	move.w	spots,px
	move.w	#FLOOR_Y-48,py
	bsr	draw_top
	bsr	draw_zone
	moveq	#1,d0
	bsr	frames
	jsr	K_FADEIN(a5)
	lea	v_basket,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	s_help,a0
	bsr	msg_mid
	moveq	#40,d0
	moveq	#1,d1
	jsr	K_WAIT(a5)
	lea	snd_horn,a0
	moveq	#50,d1
	jsr	K_SFX(a5)
	st	clock_on
	bsr	clear_mid

.ball	; wait for fire
	clr.w	pfr
	clr.w	power
	bsr	draw_meter
.w	bsr	frame
	tst.w	time
	beq	.end
	btst	#J_FIRE,held+1
	beq.s	.w
	move.w	#1,pfr			; hold fire: the power goes up
.ch	move.w	power,d0
	addq.w	#4,d0
	cmp.w	#100,d0
	bls.s	.c1
	moveq	#100,d0
.c1	move.w	d0,power
	bsr	draw_meter
	bsr	frame
	tst.w	time
	beq	.end
	btst	#J_FIRE,held+1
	bne.s	.ch
	; let go: how good?
	bsr	judge
	bsr	throw
	; the next ball
	addq.w	#1,ballno
	cmp.w	#5,ballno
	blo	.ball
	clr.w	ballno
	addq.w	#1,rack
	cmp.w	#5,rack
	bhs.s	.all
	bsr	draw_top
	bsr	draw_zone
	bsr	walk
	bra	.ball
.all	moveq	#CS_GREAT,d0		; all 25 balls before the time
	moveq	#64,d1
	jsr	K_CSFX(a5)
	lea	s_all,a0
	bra.s	.res
.end	lea	snd_horn,a0
	moveq	#50,d1
	jsr	K_SFX(a5)
	moveq	#CS_TIMEUP,d0
	moveq	#64,d1
	jsr	K_CSFX(a5)
	lea	s_timeup,a0
.res	sf	clock_on
	bsr	msg_mid
	moveq	#0,d0
	move.w	score,d0
	bsr	result_pts
	moveq	#CS_CLAP,d0
	moveq	#40,d1
	jsr	K_CSFX(a5)
	bra	ev_done

;------------------------------------------------------------------ the shot
; judge: power against the green zone -> outcome: 0 swish, 1 in off the rim, 2 rim out, 3 short, 4 long
judge:
	bsr	zone			; d0 = middle, d1 = half width
	move.w	power,d2
	sub.w	d0,d2
	move.w	d2,d3			; signed
	bpl.s	.p
	neg.w	d2
.p	move.w	d1,d4
	lsr.w	#1,d4
	cmp.w	d4,d2
	bhi.s	.n0
	clr.w	outcome
	rts
.n0	cmp.w	d1,d2
	bhi.s	.n1
	move.w	#1,outcome
	rts
.n1	add.w	d1,d1
	cmp.w	d1,d2
	bhi.s	.n2
	moveq	#100,d0			; on the rim: in or out
	jsr	K_RAND(a5)
	move.w	#1,outcome
	cmp.w	#35,d0
	blo.s	.x
	move.w	#2,outcome
.x	rts
.n2	move.w	#3,outcome
	tst.w	d3
	bmi.s	.x
	move.w	#4,outcome
	rts

; zone -> d0 = the middle of the green zone, d1 = half its width
zone:
	move.w	rack,d0
	add.w	d0,d0
	lea	zone_mid,a0
	move.w	(a0,d0.w),d0
	move.w	CX_LEVEL(a4),d1
	add.w	d1,d1
	lea	zone_w,a0
	move.w	(a0,d1.w),d1
	cmp.w	#2,rack			; the far one: smaller
	bne.s	.x
	subq.w	#1,d1
.x	rts

; throw: the ball flies, then what happens
throw:
	move.w	#2,pfr
	sub.w	#6,py			; (a little jump)
	move.w	px,d0
	add.w	#20,d0
	move.w	d0,bx0
	move.w	#FLOOR_Y-52,by0
	; where the arc ends
	move.w	outcome,d0
	lea	end_xy,a0
	lsl.w	#2,d0
	move.w	(a0,d0.w),bx1
	move.w	2(a0,d0.w),by1
	st	ball_on
	moveq	#0,d7
.f	move.w	bx1,d0			; x = x0 + (x1-x0) t/n
	sub.w	bx0,d0
	muls	d7,d0
	divs	#FLY,d0
	add.w	bx0,d0
	move.w	by1,d1
	sub.w	by0,d1
	muls	d7,d1
	divs	#FLY,d1
	add.w	by0,d1
	moveq	#FLY,d2			; - 4 h t (n-t) / n^2, h = 64
	sub.w	d7,d2
	mulu	d7,d2
	lsl.l	#8,d2
	divu	#FLY*FLY,d2
	sub.w	d2,d1
	move.w	d0,bx
	move.w	d1,by
	cmp.w	#8,d7
	bne.s	.nf
	move.w	#3,pfr
	add.w	#6,py
.nf	bsr	frame
	addq.w	#1,d7
	cmp.w	#FLY,d7
	bls.s	.f
	; after the arc
	move.w	outcome,d0
	cmp.w	#2,d0
	bhs	.miss
	tst.w	d0
	bne.s	.rimin
	lea	snd_swish,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	bra.s	.drop
.rimin	lea	snd_rim,a0
	moveq	#50,d1
	jsr	K_SFX(a5)
	moveq	#3,d7			; a little hop on the rim
.h	subq.w	#2,by
	addq.w	#2,bx
	bsr	frame
	dbf	d7,.h
	moveq	#3,d7
.h2	addq.w	#2,by
	addq.w	#1,bx
	bsr	frame
	dbf	d7,.h2
.drop	moveq	#5,d7			; through the net
.d	addq.w	#4,by
	bsr	frame
	dbf	d7,.d
	moveq	#1,d0			; points
	cmp.w	#4,ballno
	bne.s	.pt
	moveq	#2,d0
.pt	add.w	d0,score
	bsr	draw_top
	moveq	#CS_CHEER,d0
	moveq	#28,d1
	jsr	K_CSFX(a5)
	lea	s_score,a0
	cmp.w	#4,ballno
	bne.s	.sm
	lea	v_money,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	s_money,a0
	bra.s	.say
.sm	tst.w	outcome
	bne.s	.say
	lea	s_swish,a0
.say	bsr	msg_mid
	bra.s	.fall
.miss	cmp.w	#3,d0
	beq.s	.short
	lea	snd_rim,a0
	cmp.w	#2,d0
	beq.s	.mz
	lea	snd_board,a0
.mz	moveq	#50,d1
	jsr	K_SFX(a5)
.short	lea	s_miss,a0
	bsr	msg_mid
	; the ball falls to the floor
.fall	move.w	#-3,bvx
	move.w	#-3,bvy
	cmp.w	#2,outcome
	bhs.s	.fl
	move.w	#-1,bvx
	move.w	#2,bvy
.fl	moveq	#0,d6			; bounces
.fa	move.w	bvx,d0
	add.w	d0,bx
	move.w	bvy,d0
	add.w	d0,by
	addq.w	#1,bvy
	move.w	by,d0
	cmp.w	#FLOOR_Y-10,d0
	blt.s	.nb
	move.w	#FLOOR_Y-10,by
	move.w	bvy,d0
	asr.w	#1,d0
	neg.w	d0
	move.w	d0,bvy
	lea	snd_bounce,a0
	moveq	#40,d1
	jsr	K_SFX(a5)
	addq.w	#1,d6
.nb	bsr	frame
	cmp.w	#2,d6
	blo.s	.fa
	sf	ball_on
	clr.w	pfr
	bsr	clear_mid
	rts

; walk: to the next spot
walk:
	move.w	rack,d0
	add.w	d0,d0
	lea	spots,a0
	move.w	(a0,d0.w),d5		; the new x
	moveq	#0,d7
.l	move.w	px,d0
	cmp.w	d5,d0
	beq.s	.x
	blt.s	.r
	subq.w	#4,d0
	cmp.w	d5,d0
	bge.s	.s
	move.w	d5,d0
	bra.s	.s
.r	addq.w	#4,d0
	cmp.w	d5,d0
	ble.s	.s
	move.w	d5,d0
.s	move.w	d0,px
	move.w	d7,d0
	lsr.w	#1,d0
	and.w	#3,d0
	addq.w	#4,d0
	move.w	d0,pfr
	bsr	frame
	addq.w	#1,d7
	bra.s	.l
.x	clr.w	pfr
	rts

;------------------------------------------------------------------ the screen
draw_top:
	movem.l	d0-d3/a0,-(sp)
	moveq	#0,d0
	moveq	#0,d1
	move.w	#320,d2
	moveq	#23,d3
	moveq	#0,d4
	jsr	K_FILL(a5)
	lea	s_score_t,a0
	moveq	#8,d0
	moveq	#2,d2
	bsr	top_text
	moveq	#0,d0
	move.w	score,d0
	moveq	#64,d1
	moveq	#3,d2
	moveq	#1,d3
	bsr	top_num
	lea	s_rack_t,a0
	move.w	#232,d0
	moveq	#2,d2
	bsr	top_text
	moveq	#0,d0
	move.w	rack,d0
	addq.w	#1,d0
	move.w	#280,d1
	moveq	#3,d2
	moveq	#1,d3
	bsr	top_num
	lea	s_time_t,a0
	move.w	#112,d0
	moveq	#2,d2
	bsr	top_text
	bsr	draw_time
	movem.l	(sp)+,d0-d3/a0
	rts

draw_time:
	movem.l	d0-d3/a0,-(sp)
	move.w	time,d0
	bsr	time_text
	move.w	#160,d0
	moveq	#3,d2
	cmp.w	#10*25,time
	bhs.s	.c
	moveq	#4,d2			; (red: the last 10 seconds)
.c	bsr	top_text
	movem.l	(sp)+,d0-d3/a0
	rts

; the power bar
draw_meter:
	movem.l	d0-d6,-(sp)
	moveq	#100,d6
	sub.w	power,d6		; empty
	moveq	#METER_X,d0
	moveq	#METER_Y,d1
	moveq	#16,d2
	move.w	d6,d3
	moveq	#1,d4
	tst.w	d3
	beq.s	.f
	jsr	K_FILL(a5)
.f	moveq	#METER_X,d0
	moveq	#METER_Y,d1
	add.w	d6,d1
	moveq	#16,d2
	move.w	power,d3
	moveq	#3,d4
	tst.w	d3
	beq.s	.x
	jsr	K_FILL(a5)
.x	movem.l	(sp)+,d0-d6
	rts

; the green zone, next to the bar
draw_zone:
	movem.l	d0-d6,-(sp)
	moveq	#40,d0			; clear the column
	moveq	#METER_Y,d1
	moveq	#8,d2
	moveq	#100,d3
	moveq	#13,d4
	jsr	K_FILL(a5)
	bsr	zone
	move.w	d0,d5
	add.w	d1,d5			; top of the zone (power)
	moveq	#100,d6
	sub.w	d5,d6
	add.w	#METER_Y,d6		; y
	add.w	d1,d1
	addq.w	#1,d1
	move.w	d1,d3			; height
	moveq	#40,d0
	move.w	d6,d1
	moveq	#8,d2
	moveq	#10,d4
	jsr	K_FILL(a5)
	movem.l	(sp)+,d0-d6
	rts

msg_mid:				; a0: big text in the middle of the bottom bar
	movem.l	d0-d4/a0,-(sp)
	bsr	clear_mid
	move.l	20(sp),a0
	move.w	#241,d1
	moveq	#3,d2
	moveq	#-1,d3
	jsr	K_CTEXT2(a5)
	movem.l	(sp)+,d0-d4/a0
	rts
clear_mid:
	movem.l	d0-d4,-(sp)
	moveq	#0,d0
	move.w	#241,d1
	move.w	#320,d2
	moveq	#15,d3
	moveq	#0,d4
	jsr	K_FILL(a5)
	movem.l	(sp)+,d0-d4
	rts

;------------------------------------------------------------------ one frame
frame:
	movem.l	d0-d3/a0,-(sp)
	jsr	K_BEGIN(a5)
	move.l	pl_tab,a0		; the player
	move.w	pfr,d0
	lsl.w	#2,d0
	move.l	(a0,d0.w),a0
	move.w	px,d0
	move.w	py,d1
	jsr	K_BOB(a5)
	tst.b	ball_on			; the ball, then the front of the rim
	beq.s	.nb
	lea	ball_n,a0
	cmp.w	#4,ballno
	bne.s	.bn
	lea	ball_m,a0
.bn	move.w	bx,d0
	subq.w	#6,d0
	move.w	by,d1
	subq.w	#6,d1
	jsr	K_BOB(a5)
.nb	lea	rimfront,a0
	move.w	#RIM_X-13,d0
	move.w	#RIM_Y-1,d1
	jsr	K_BOB(a5)
	; the balls still in the rack (bottom right)
	tst.b	clock_on
	beq.s	.nr
	move.w	ballno,d3
	tst.b	ball_on
	beq.s	.r
	addq.w	#1,d3
.r	cmp.w	#5,d3
	bhs.s	.nr
	lea	ball_n,a0
	cmp.w	#4,d3
	bne.s	.rb
	lea	ball_m,a0
.rb	move.w	d3,d0
	mulu	#12,d0
	add.w	#252,d0
	move.w	#243,d1
	jsr	K_BOB(a5)
	addq.w	#1,d3
	bra.s	.r
.nr	jsr	K_END(a5)
	tst.b	clock_on		; the clock
	beq.s	.nc
	tst.w	time
	beq.s	.nc
	subq.w	#1,time
	move.w	time,d0
	and.w	#7,d0
	bne.s	.nc
	bsr	draw_time
.nc	bsr	read_input
	movem.l	(sp)+,d0-d3/a0
	rts

	include	"evcommon.s"

;==============================================================================
	section	data,data
zone_mid	dc.w	60,66,72,66,60
zone_w		dc.w	10,8,6
; where the arc ends: swish, in off the rim, rim out, short, long (board)
end_xy		dc.w	RIM_X,RIM_Y,RIM_X-6,RIM_Y-2,RIM_X-8,RIM_Y-2,RIM_X-26,RIM_Y+10,RIM_X+12,RIM_Y-16
s_help		dc.b	'HOLD FIRE!',0
s_score_t	dc.b	'SCORE',0
s_time_t	dc.b	'TIME',0
s_rack_t	dc.b	'RACK',0
s_swish		dc.b	'SWISH!',0
s_score		dc.b	'SCORE!',0
s_money		dc.b	'MONEY BALL!',0
s_miss		dc.b	'MISS',0
s_timeup	dc.b	'TIME UP!',0
s_all		dc.b	'ALL 25 BALLS!',0
	even
	include	"bas_data.i"
bg_rle	incbin	"bas_bg.rle"
	even

	section	chip,data_c
bas_chip	incbin	"bas_chip.bin"

	section	bss,bss
vars
pl_tab		ds.l	1
time		ds.w	1
score		ds.w	1
rack		ds.w	1
ballno		ds.w	1
power		ds.w	1
outcome		ds.w	1
pfr		ds.w	1
px		ds.w	1
py		ds.w	1
bx		ds.w	1
by		ds.w	1
bx0		ds.w	1
by0		ds.w	1
bx1		ds.w	1
by1		ds.w	1
bvx		ds.w	1
bvy		ds.w	1
ball_on		ds.b	1
clock_on	ds.b	1
	even
VARS_END
VARS_SIZE	equ	VARS_END-vars
