;------------------------------------------------------------------------------
;  ev_skate.s - SKATEBOARDING: the half pipe, 60 seconds, 3 falls and out.
;  An event of Stronkie's Olympics (loaded from Skate.evt; see kernel.i).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"ska_equ.i"

TIME		equ	60*25
SMAX		equ	(RAMP_N-1)*16
VMAX		equ	150

	section	code,code
	bra.w	entry
	dc.l	'SOEV'
	dc.w	40,110			; the computer athletes score 40..110 points
	dc.w	0

entry:	movem.l	d1-d7/a0-a6,-(sp)
	move.l	sp,ev_sp
	lea	vars,a0
	move.w	#VARS_SIZE/2-1,d0
.cl	clr.w	(a0)+
	dbf	d0,.cl
	lea	km_tab,a0
	lea	crm,a1
	tst.w	CX_WOMAN(a4)
	beq.s	.m
	lea	kw_tab,a0
	lea	crw,a1
.m	move.l	a0,k_tab
	move.l	a1,crash_bob
	lea	pal_ska,a0
	lea	bg_rle,a1
	bsr	ev_start
	lea	grad_ska,a0
	jsr	K_GRAD(a5)
	move.w	#TIME,time
	move.w	#3,lives
	bsr	respawn
	bsr	draw_top
	moveq	#1,d0
	bsr	frames
	jsr	K_FADEIN(a5)
	lea	v_skate,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	s_go,a0
	bsr	message_small
	moveq	#30,d0
	bsr	frames
	bsr	clear_msg
	st	clock_on
.l	bsr	move
	bsr	frame
	tst.w	time
	beq.s	.end
	tst.w	lives
	bne.s	.l
	lea	s_out,a0
	bra.s	.e2
.end	moveq	#CS_TIMEUP,d0
	moveq	#64,d1
	jsr	K_CSFX(a5)
	lea	s_timeup,a0
.e2	sf	clock_on
	bsr	message
	moveq	#CS_CLAP,d0
	moveq	#40,d1
	jsr	K_CSFX(a5)
	moveq	#0,d0
	move.w	score,d0
	bsr	result_pts
	bra	ev_done

respawn:
	move.w	#(RAMP_N/2)*16,s16	; in the middle of the bottom, rolling
	move.w	#40,v16
	sf	air
	clr.w	crash_t
	rts

;------------------------------------------------------------------ moving
move:
	tst.w	crash_t
	beq.s	.go
	subq.w	#1,crash_t
	bne.s	.x
	tst.w	lives
	beq.s	.x
	bsr	respawn
.x	rts
.go	tst.b	air
	bne	in_air
	bsr	here			; a0 = the ramp point
	move.w	4(a0),d0		; slope: gravity along the ramp
	asr.w	#4,d0
	add.w	d0,v16
	; pump: push down while rolling through the bottom
	move.w	4(a0),d0
	bpl.s	.ab
	neg.w	d0
.ab	cmp.w	#14,d0
	bhi.s	.np
	btst	#J_DOWN,held+1
	beq.s	.np
	move.w	#3,d0
	tst.w	v16
	bpl.s	.pu
	neg.w	d0
.pu	add.w	d0,v16
	move.w	#4,pump_t
.np	; a little friction
	move.w	v16,d0
	beq.s	.f
	move.w	time,d1
	and.w	#3,d1
	bne.s	.f
	bmi.s	.fm
	subq.w	#1,d0
	bra.s	.f
.fm	addq.w	#1,d0
.f	cmp.w	#VMAX,d0
	ble.s	.f1
	move.w	#VMAX,d0
.f1	cmp.w	#-VMAX,d0
	bge.s	.f2
	move.w	#-VMAX,d0
.f2	move.w	d0,v16
	add.w	d0,s16
	; off the top: into the air
	tst.w	s16
	bmi.s	.offl
	cmp.w	#SMAX,s16
	bgt.s	.offr
	rts
.offl	clr.w	s16
	moveq	#-1,d1			; left wall, going up
	bra.s	.fly
.offr	move.w	#SMAX,s16
	moveq	#1,d1
.fly	move.w	d1,side
	move.w	v16,d0
	bpl.s	.av
	neg.w	d0
.av	neg.w	d0
	move.w	d0,ay_v			; up
	clr.w	ay
	st	air
	clr.w	spin
	clr.w	grab_t
	sf	turned
	move.w	#4,air_ang		; facing up
	lea	snd_clack,a0
	moveq	#40,d1
	jsr	K_SFX(a5)
	rts

in_air:
	move.w	ay_v,d0
	add.w	d0,ay
	addq.w	#4,ay_v			; gravity
	move.w	ay,d0
	cmp.w	top_ay,d0
	bge.s	.nt
	move.w	d0,top_ay
.nt	; fire: turn around (once); left / right: a spin; up: a grab
	addq.w	#1,turn_t
	btst	#0,turn_t+1
	bne.s	.tricks
	tst.b	turning
	bne.s	.turn
	btst	#J_FIRE,held+1
	beq.s	.spin
	tst.b	turned
	bne.s	.spin
	st	turning
.turn	bsr	rot_step
	addq.w	#1,turn_n
	cmp.w	#8,turn_n
	blo.s	.tricks
	sf	turning
	clr.w	turn_n
	st	turned
	bra.s	.tricks
.spin	move.w	held,d0
	and.w	#(1<<J_LEFT)|(1<<J_RIGHT),d0
	beq.s	.tricks
	bsr	rot_step
	addq.w	#1,spin
.tricks	btst	#J_UP,held+1
	beq.s	.ng
	addq.w	#1,grab_t
.ng	; back down on the lip?
	tst.w	ay_v
	bmi	.x
	tst.w	ay
	bmi	.x
	clr.w	ay
	sf	air
	sf	turning
	; a good landing: turned around, and no spin half done
	tst.b	turned
	beq	fall
	move.w	spin,d0
	and.w	#15,d0
	bne	fall
	move.w	ay_v,d0			; back down at the same speed
	tst.w	side
	bmi.s	.lr
	neg.w	d0
.lr	move.w	d0,v16
	lea	snd_clack,a0
	moveq	#50,d1
	jsr	K_SFX(a5)
	; points: 5 + height/8, a grab 10, every full spin 25
	move.w	top_ay,d0
	neg.w	d0
	lsr.w	#7,d0			; (1/16 pixels: /8 per pixel... /128)
	addq.w	#5,d0
	lea	s_air,a0
	cmp.w	#6,grab_t
	blo.s	.nog
	add.w	#10,d0
	lea	s_grab,a0
.nog	move.w	spin,d1
	lsr.w	#4,d1
	beq.s	.nos
	mulu	#25,d1
	add.w	d1,d0
	lea	s_spin,a0
	movem.l	d0/a0,-(sp)
	lea	v_rad,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	movem.l	(sp)+,d0/a0
.nos	add.w	d0,score
	clr.w	top_ay
	bsr	message
	move.w	#30,msg_t
	bsr	draw_top
	moveq	#CS_CHEER,d0
	moveq	#24,d1
	jsr	K_CSFX(a5)
.x	rts

rot_step:				; turn one step (16 a full turn)
	move.w	air_ang,d0
	addq.w	#1,d0
	and.w	#15,d0
	move.w	d0,air_ang
	rts

fall:
	subq.w	#1,lives
	move.w	#50,crash_t
	clr.w	top_ay
	lea	snd_crash,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	v_ouch,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#CS_OOH,d0
	moveq	#30,d1
	jsr	K_CSFX(a5)
	lea	s_fall,a0
	tst.b	turned
	bne.s	.m
	lea	s_noturn,a0
.m	bsr	message
	move.w	#40,msg_t
	bsr	draw_top
	rts

here:					; -> a0 = the ramp point for s16
	move.w	s16,d0
	bpl.s	.p
	moveq	#0,d0
.p	lsr.w	#4,d0
	cmp.w	#RAMP_N-1,d0
	bls.s	.q
	move.w	#RAMP_N-1,d0
.q	lsl.w	#3,d0
	lea	ramp,a0
	add.w	d0,a0
	rts

;------------------------------------------------------------------ the screen
draw_top:
	movem.l	d0-d4/a0,-(sp)
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
	lea	s_time_t,a0
	move.w	#120,d0
	moveq	#2,d2
	bsr	top_text
	bsr	draw_time
	lea	s_lives_t,a0
	move.w	#224,d0
	moveq	#2,d2
	bsr	top_text
	moveq	#0,d0
	move.w	lives,d0
	move.w	#280,d1
	moveq	#3,d2
	moveq	#1,d3
	bsr	top_num
	movem.l	(sp)+,d0-d4/a0
	rts

draw_time:
	movem.l	d0-d3/a0,-(sp)
	move.w	time,d0
	bsr	time_text
	move.w	#168,d0
	moveq	#3,d2
	bsr	top_text
	movem.l	(sp)+,d0-d3/a0
	rts

frame:
	movem.l	d0-d3/a0,-(sp)
	jsr	K_BEGIN(a5)
	bsr	here
	move.w	(a0),d0			; x, y of the board
	move.w	2(a0),d1
	tst.w	crash_t
	beq.s	.ride
	move.l	crash_bob,a0		; fallen down at the bottom
	move.w	#160-24,d0
	move.w	#FLOOR_Y-30,d1
	jsr	K_BOB(a5)
	bra.s	.done
.ride	tst.b	air
	beq.s	.gr
	move.w	ay,d2
	asr.w	#4,d2
	add.w	d2,d1
	move.w	air_ang,d2
	bra.s	.dr
.gr	move.w	6(a0),d2		; the angle of the ramp, the way you go
	tst.w	v16
	bpl.s	.dr
	addq.w	#8,d2
	and.w	#15,d2
.dr	lsl.w	#2,d2
	move.l	k_tab,a0
	move.l	(a0,d2.w),a0
	sub.w	#24,d0
	bpl.s	.x0
	moveq	#0,d0
.x0	sub.w	#44,d1
	jsr	K_BOB(a5)
.done	jsr	K_END(a5)
	tst.w	msg_t
	beq.s	.nm
	subq.w	#1,msg_t
	bne.s	.nm
	bsr	clear_msg
.nm	tst.b	clock_on
	beq.s	.nc
	tst.w	time
	beq.s	.nc
	subq.w	#1,time
	move.w	time,d0
	and.w	#7,d0
	bne.s	.nc
	bsr	draw_time
	tst.b	air			; the wheels on the ramp
	bne.s	.nc
	tst.w	crash_t
	bne.s	.nc
	move.w	time,d0
	and.w	#31,d0
	bne.s	.nc
	lea	snd_roll,a0
	moveq	#20,d1
	jsr	K_SFX(a5)
.nc	bsr	read_input
	movem.l	(sp)+,d0-d3/a0
	rts

	include	"evcommon.s"

;==============================================================================
	section	data,data
s_go		dc.b	'DOWN AT THE BOTTOM: PUMP!  FIRE: TURN',0
s_air		dc.b	'AIR!',0
s_grab		dc.b	'GRAB!',0
s_spin		dc.b	'360!',0
s_fall		dc.b	'OUCH!',0
s_noturn	dc.b	'NO TURN! OUCH!',0
s_out		dc.b	'3 FALLS!',0
s_timeup	dc.b	'TIME UP!',0
s_score_t	dc.b	'SCORE',0
s_time_t	dc.b	'TIME',0
s_lives_t	dc.b	'LIVES',0
	even
	include	"ska_data.i"
bg_rle	incbin	"ska_bg.rle"
	even

	section	chip,data_c
ska_chip	incbin	"ska_chip.bin"

	section	bss,bss
vars
k_tab		ds.l	1
crash_bob	ds.l	1
time		ds.w	1
lives		ds.w	1
score		ds.w	1
s16		ds.w	1
v16		ds.w	1
side		ds.w	1
ay		ds.w	1
ay_v		ds.w	1
top_ay		ds.w	1
air_ang		ds.w	1
spin		ds.w	1
grab_t		ds.w	1
turn_t		ds.w	1
turn_n		ds.w	1
pump_t		ds.w	1
crash_t		ds.w	1
msg_t		ds.w	1
air		ds.b	1
turned		ds.b	1
turning		ds.b	1
clock_on	ds.b	1
	even
VARS_END
VARS_SIZE	equ	VARS_END-vars
