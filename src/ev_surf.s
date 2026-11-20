;------------------------------------------------------------------------------
;  ev_surf.s - SURFING: ride the wave for 60 seconds, 3 wipe-outs and out.
;  An event of Stronkie's Olympics (loaded from Surfing.evt; see kernel.i).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"sur_equ.i"

TIME		equ	60*25
HMAX		equ	(TROUGH_Y-LIP_Y)*16	; the lip (h in 1/16 pixels)
XMAX		equ	292*16
SPMIN		equ	28
SPMAX		equ	150

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
	lea	sm_tab,a0
	tst.w	CX_WOMAN(a4)
	beq.s	.m
	lea	sw_tab,a0
.m	move.l	a0,s_tab
	lea	pal_sur,a0
	lea	bg_rle,a1
	bsr	ev_start
	lea	grad_sur,a0
	jsr	K_GRAD(a5)
	move.w	#TIME,time
	move.w	#3,lives
	bsr	respawn
	bsr	draw_top
	moveq	#1,d0
	bsr	frames
	jsr	K_FADEIN(a5)
	lea	v_surf,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	s_go,a0
	bsr	message_small
	moveq	#30,d0
	bsr	frames
	bsr	clear_msg
	st	clock_on
.l	bsr	ride
	bsr	frame
	tst.w	time
	beq.s	.end
	tst.w	lives
	bne.s	.l
	lea	s_out,a0		; 3 wipe-outs
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
	move.w	#170*16,sx
	move.w	#40*16,sh
	clr.w	ang
	move.w	#60,spd
	sf	air
	clr.w	wipe_t
	rts

;------------------------------------------------------------------ the ride
ride:
	tst.w	wipe_t			; a wipe-out: the splash, then a new ride
	beq.s	.go
	subq.w	#1,wipe_t
	bne.s	.x
	tst.w	lives
	beq.s	.x
	bsr	respawn
.x	rts
.go	tst.w	cut_t
	beq.s	.c
	subq.w	#1,cut_t
.c	tst.b	air
	bne	in_air
	; the joystick turns the board (one step every 2 ticks) towards its direction
	addq.w	#1,turn_t
	btst	#0,turn_t+1
	bne	.nt
	move.w	held,d0
	and.w	#$1e,d0
	beq	.nt
	lsr.w	#1,d0			; 1 left 2 right 4 up 8 down
	lea	joy_ang,a0
	move.b	(a0,d0.w),d1
	bmi	.nt
	ext.w	d1
	sub.w	ang,d1			; shortest way round
	and.w	#15,d1
	beq.s	.nt
	move.w	ang,d2
	cmp.w	#8,d1
	bhi.s	.ccw
	addq.w	#1,d2
	bra.s	.set
.ccw	subq.w	#1,d2
.set	and.w	#15,d2
	move.w	d2,ang
	bsr	dir_lr			; a cutback: from right to left (or back) high on the wave
	tst.w	d0
	beq.s	.nt
	move.w	last_lr,d1
	move.w	d0,last_lr
	tst.w	d1
	beq.s	.nt
	cmp.w	d0,d1
	beq.s	.nt
	cmp.w	#HMAX/2,sh
	blt.s	.nt
	tst.w	cut_t
	bne.s	.nt
	move.w	#40,cut_t
	moveq	#5,d0
	lea	s_cut,a0
	bsr	points
.nt	; speed: faster going down, slower going up
	move.w	ang,d0
	add.w	d0,d0
	lea	sin_t,a0
	move.w	(a0,d0.w),d1		; sin: + up
	neg.w	d1
	bmi.s	.up
	asr.w	#3,d1			; down the wave: faster
	bra.s	.ad
.up	asr.w	#5,d1			; up: slower
	subq.w	#1,d1			; (the water slows you)
.ad	add.w	d1,spd
	cmp.w	#SPMIN,spd
	bge.s	.s1
	move.w	#SPMIN,spd
.s1	cmp.w	#SPMAX,spd
	ble.s	.s2
	move.w	#SPMAX,spd
.s2	; move
	lea	cos_t,a0
	move.w	(a0,d0.w),d1
	muls	spd,d1
	asr.l	#6,d1
	add.w	d1,sx
	lea	sin_t,a0
	move.w	(a0,d0.w),d1
	muls	spd,d1
	asr.l	#6,d1
	add.w	d1,sh
	sub.w	#10,sx			; the wave peels: the curl comes for you
	bsr	limits
	; the bottom: turn flat
	tst.w	sh
	bpl.s	.nb
	clr.w	sh
	bsr	flatten
.nb	cmp.w	#HMAX-16*16,sh		; the lip: fly off with speed, or turn flat
	blt.s	.nl
	move.w	ang,d0
	add.w	d0,d0
	lea	sin_t,a0
	move.w	(a0,d0.w),d1
	ble.s	.flat
	cmp.w	#56,spd
	blt.s	.nf
	muls	spd,d1			; take off!
	asr.l	#6,d1
	move.w	d1,avh
	lea	cos_t,a0
	move.w	(a0,d0.w),d1
	muls	spd,d1
	asr.l	#6,d1
	move.w	d1,avx
	st	air
	clr.w	spin
	lea	snd_whoosh,a0
	moveq	#50,d1
	jsr	K_SFX(a5)
	bra.s	.nl
.nf	cmp.w	#HMAX,sh
	blt.s	.nl
.flat	move.w	#HMAX,sh
	bsr	flatten
.nl	; close to the curl: in the tube, points
	cmp.w	#(CURL_X+56)*16,sx
	bge.s	.nt2
	addq.w	#1,tube_t
	cmp.w	#10,tube_t
	blo.s	.x2
	clr.w	tube_t
	moveq	#1,d0
	sub.l	a0,a0
	bsr	points
	bra.s	.x2
.nt2	clr.w	tube_t
.x2	rts

; in the air: up and down again; fire spins
in_air:
	move.w	avx,d0
	add.w	d0,sx
	move.w	avh,d0
	add.w	d0,sh
	sub.w	#7,avh
	sub.w	#8,sx
	bsr	limits
	btst	#J_FIRE,held+1
	beq.s	.ns
	addq.w	#1,turn_t
	btst	#0,turn_t+1
	bne.s	.ns
	move.w	ang,d0
	addq.w	#1,d0
	and.w	#15,d0
	move.w	d0,ang
	addq.w	#1,spin
.ns	tst.w	avh			; coming down to the lip?
	bpl.s	.x
	cmp.w	#HMAX-16*16,sh
	bgt.s	.x
	move.w	#HMAX-17*16,sh
	sf	air
	move.w	ang,d0			; land pointing down the wave (9..15), or wipe out
	cmp.w	#9,d0
	blo	wipeout
	move.w	#80,spd
	moveq	#10,d0			; an air: 10, every half spin 20 more
	move.w	spin,d1
	lsr.w	#3,d1
	beq.s	.p
	mulu	#20,d1
	add.w	d1,d0
	lea	v_rad,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	s_spin,a0
	bra.s	.pp
.p	lea	s_air,a0
.pp	bsr	points
	moveq	#CS_CHEER,d0
	moveq	#30,d1
	jsr	K_CSFX(a5)
.x	rts

limits:
	cmp.w	#XMAX,sx
	ble.s	.a
	move.w	#XMAX,sx
.a	cmp.w	#(CURL_X+6)*16,sx	; caught by the curl
	bge.s	.x
	addq.l	#4,sp			; (no return to the caller)
	bra	wipeout
.x	rts

flatten:				; the board flat: right or left
	bsr	dir_lr
	clr.w	ang
	tst.w	d0
	bpl.s	.x
	move.w	#8,ang
.x	rts

; dir_lr -> d0 = 1 right, -1 left, 0 straight up/down (from ang)
dir_lr:
	move.w	ang,d0
	add.w	d0,d0
	move.l	a0,-(sp)
	lea	cos_t,a0
	move.w	(a0,d0.w),d0
	move.l	(sp)+,a0
	cmp.w	#10,d0
	bgt.s	.r
	cmp.w	#-10,d0
	blt.s	.l
	moveq	#0,d0
	rts
.r	moveq	#1,d0
	rts
.l	moveq	#-1,d0
	rts

wipeout:
	sf	air
	subq.w	#1,lives
	move.w	#50,wipe_t
	move.w	sx,wx
	move.w	sh,wh
	lea	snd_splash,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	v_wipe,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	s_wipe,a0
	bsr	message
	bsr	draw_top
	rts

; points: d0 = points, a0 = what (or 0)
points:
	add.w	d0,score
	move.l	a0,d0
	beq.s	.n
	bsr	message
	move.w	#30,msg_t
.n	bsr	draw_top
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
	addq.w	#1,tick
	jsr	K_BEGIN(a5)
	; foam at the curl
	moveq	#3,d3
.f	move.w	tick,d0
	lsr.w	#2,d0
	add.w	d3,d0
	and.l	#$ffff,d0
	divu	#3,d0
	swap	d0
	lsl.w	#2,d0
	lea	foam_tab,a0
	move.l	(a0,d0.w),a0
	moveq	#CURL_X-8,d0
	move.w	d3,d1
	mulu	#30,d1
	add.w	#100,d1
	jsr	K_BOB(a5)
	dbf	d3,.f
	tst.w	wipe_t
	beq.s	.surfer
	move.w	wipe_t,d0		; the splash
	lsr.w	#3,d0
	cmp.w	#2,d0
	bls.s	.s
	moveq	#2,d0
.s	moveq	#2,d1
	sub.w	d0,d1
	lsl.w	#2,d1
	lea	splash_tab,a0
	move.l	(a0,d1.w),a0
	move.w	wx,d0
	asr.w	#4,d0
	sub.w	#24,d0
	bpl.s	.s2
	moveq	#0,d0
.s2	move.w	#TROUGH_Y,d1
	move.w	wh,d2
	asr.w	#4,d2
	sub.w	d2,d1
	sub.w	#28,d1
	jsr	K_BOB(a5)
	bra.s	.done
.surfer	move.l	s_tab,a0
	move.w	ang,d0
	lsl.w	#2,d0
	move.l	(a0,d0.w),a0
	move.w	sx,d0
	asr.w	#4,d0
	sub.w	#24,d0
	bpl.s	.x0
	moveq	#0,d0
.x0	move.w	#TROUGH_Y,d1
	move.w	sh,d2
	asr.w	#4,d2
	sub.w	d2,d1
	sub.w	#42,d1
	jsr	K_BOB(a5)
.done	jsr	K_END(a5)
	tst.w	msg_t
	beq.s	.nm
	subq.w	#1,msg_t
	bne.s	.nm
	bsr	clear_msg
.nm	tst.b	clock_on		; the clock
	beq.s	.nc
	tst.w	time
	beq.s	.nc
	subq.w	#1,time
	move.w	time,d0
	and.w	#7,d0
	bne.s	.nc
	bsr	draw_time
	move.w	time,d0			; the sound of the sea now and then
	and.w	#63,d0
	bne.s	.nc
	lea	snd_wave,a0
	moveq	#24,d1
	jsr	K_SFX(a5)
.nc	bsr	read_input
	movem.l	(sp)+,d0-d3/a0
	rts

	include	"evcommon.s"

;==============================================================================
	section	data,data
; joystick bits (left 1, right 2, up 4, down 8) -> board direction (-1 none)
joy_ang		dc.b	-1,8,0,-1,4,6,2,-1,12,10,14,-1,-1,-1,-1,-1
s_go		dc.b	'RIDE THE WAVE!  UP, DOWN, LEFT, RIGHT',0
s_cut		dc.b	'CUTBACK!',0
s_air		dc.b	'AIR!',0
s_spin		dc.b	'SPIN!',0
s_wipe		dc.b	'WIPE OUT!',0
s_out		dc.b	'3 WIPE-OUTS!',0
s_timeup	dc.b	'TIME UP!',0
s_score_t	dc.b	'SCORE',0
s_time_t	dc.b	'TIME',0
s_lives_t	dc.b	'LIVES',0
	even
	include	"sur_data.i"
bg_rle	incbin	"sur_bg.rle"
	even

	section	chip,data_c
sur_chip	incbin	"sur_chip.bin"

	section	bss,bss
vars
s_tab		ds.l	1
time		ds.w	1
lives		ds.w	1
score		ds.w	1
sx		ds.w	1
sh		ds.w	1
ang		ds.w	1
spd		ds.w	1
avx		ds.w	1
avh		ds.w	1
spin		ds.w	1
turn_t		ds.w	1
cut_t		ds.w	1
tube_t		ds.w	1
wipe_t		ds.w	1
msg_t		ds.w	1
wx		ds.w	1
wh		ds.w	1
tick		ds.w	1
last_lr		ds.w	1
air		ds.b	1
clock_on	ds.b	1
	even
VARS_END
VARS_SIZE	equ	VARS_END-vars
