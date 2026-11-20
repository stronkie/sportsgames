;------------------------------------------------------------------------------
;  ev_soccer.s - SOCCER: a penalty shoot-out against another country.
;  An event of Stronkie's Olympics (loaded from Soccer.evt; see kernel.i).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"soc_equ.i"

AIM_Y		equ	104
FLY_MAX		equ	16
MAXROUND	equ	10

	section	code,code
	bra.w	entry
	dc.l	'SOEV'
	dc.w	4,9			; the computer athletes score 4..9 points
	dc.w	0

entry:	movem.l	d1-d7/a0-a6,-(sp)
	move.l	sp,ev_sp
	lea	vars,a0			; all variables 0
	move.w	#VARS_SIZE/2-1,d0
.cl	clr.w	(a0)+
	dbf	d0,.cl
	lea	pal_a,a0
	jsr	K_PAL(a5)
	lea	bg_rle,a0
	jsr	K_SETBG(a5)
	bsr	draw_board
	bsr	reset_scene
	moveq	#1,d0
	bsr	frames
	jsr	K_FADEIN(a5)
	lea	v_soccer,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#CS_CHEER,d0
	moveq	#32,d1
	jsr	K_CSFX(a5)
	moveq	#25,d0
	bsr	frames
	moveq	#CS_WHISTLE,d0
	moveq	#50,d1
	jsr	K_CSFX(a5)
	; the shoot-out
	clr.w	round
.round	bsr	player_shoots
	bsr	decided
	bne.s	.over
	bsr	cpu_shoots
	bsr	decided
	bne.s	.over
	addq.w	#1,round
	cmp.w	#MAXROUND,round
	blo.s	.round
.over	; the result
	moveq	#CS_WHISTLE,d0
	moveq	#50,d1
	jsr	K_CSFX(a5)
	moveq	#12,d0
	bsr	frames
	moveq	#0,d6			; points: goals + saves (+3 win)
	move.w	goals_p,d6
	add.w	saves,d6
	lea	s_draw,a2
	move.w	goals_p,d0
	cmp.w	goals_c,d0
	beq.s	.res
	lea	s_lost,a2
	blo.s	.res
	lea	s_won,a2
	addq.w	#3,d6
.res	move.l	d6,CX_SCORE(a4)
	lea	CX_RESULT(a4),a1	; "WON 5-4 = 9 PTS"
	move.l	a2,a0
	bsr	cat
	moveq	#0,d0
	move.w	goals_p,d0
	moveq	#1,d1
	jsr	K_NUM(a5)
	bsr	cat
	move.b	#'-',(a1)+
	moveq	#0,d0
	move.w	goals_c,d0
	moveq	#1,d1
	jsr	K_NUM(a5)
	bsr	cat
	lea	s_eq,a0
	bsr	cat
	move.l	d6,d0
	moveq	#1,d1
	jsr	K_NUM(a5)
	bsr	cat
	lea	s_pts,a0
	bsr	cat
	clr.b	(a1)
	; on the screen
	move.l	a2,d0
	cmp.l	#s_won,d0
	bne.s	.n1
	lea	v_youwin,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#CS_CHEER,d0
	moveq	#48,d1
	jsr	K_CSFX(a5)
	lea	s_youwin,a0
	bra.s	.msg
.n1	cmp.l	#s_lost,d0
	bne.s	.n2
	moveq	#CS_OHNO,d0
	moveq	#64,d1
	jsr	K_CSFX(a5)
	lea	s_youlose,a0
	bra.s	.msg
.n2	lea	s_itsdraw,a0
.msg	bsr	message
	lea	CX_RESULT(a4),a0	; and the result under it in the top bar
	moveq	#0,d0
	moveq	#0,d1
	move.w	#320,d2
	moveq	#23,d3
	moveq	#0,d4
	jsr	K_FILL(a5)
	moveq	#8,d1
	moveq	#3,d2
	moveq	#-1,d3
	jsr	K_CTEXT(a5)
	moveq	#100,d0
	moveq	#1,d1
	jsr	K_WAIT(a5)
	jsr	K_FADEOUT(a5)
	moveq	#0,d0
	bra.s	leave
give_up	jsr	K_FADEOUT(a5)
	moveq	#-1,d0
leave	move.l	ev_sp,sp
	movem.l	(sp)+,d1-d7/a0-a6
	rts

cat:					; a0 -> a1
	move.b	(a0)+,(a1)+
	bne.s	cat
	subq.l	#1,a1
	rts

; decided -> ne when the shoot-out is over
decided:
	movem.l	d0-d3,-(sp)
	move.w	kicks_p,d0
	move.w	kicks_c,d1
	cmp.w	#5,d0			; after 5 each: sudden death
	blo.s	.reg
	cmp.w	d0,d1
	bne.s	.no			; (the computer still has to kick)
	move.w	goals_p,d2
	cmp.w	goals_c,d2
	bne.s	.yes
	bra.s	.no
.reg	moveq	#5,d2			; can one side still catch up?
	sub.w	d0,d2
	add.w	goals_p,d2		; the most the player can get
	cmp.w	goals_c,d2
	blo.s	.yes
	moveq	#5,d2
	sub.w	d1,d2
	add.w	goals_c,d2
	cmp.w	goals_p,d2
	blo.s	.yes
.no	moveq	#0,d0
	bra.s	.x
.yes	moveq	#1,d0
.x	movem.l	(sp)+,d0-d3
	tst.w	d0
	rts

;------------------------------------------------------------------ the player shoots
player_shoots:
	lea	pal_a,a0
	jsr	K_PAL(a5)
	bsr	reset_scene
	lea	shm_tab,a0
	tst.w	CX_WOMAN(a4)
	beq.s	.m
	lea	shw_tab,a0
.m	move.l	a0,sh_tab
	lea	s_aim,a0
	bsr	message_small
	; aim: the cross moves over the goal
	move.w	#160,cur_x
	moveq	#4,d0
	add.w	CX_LEVEL(a4),d0
	move.w	d0,cur_dx
	st	cur_on
.aim	bsr	frame
	move.w	cur_x,d0
	add.w	cur_dx,d0
	cmp.w	#GOAL_L-22,d0
	bgt.s	.a1
	neg.w	cur_dx
.a1	cmp.w	#GOAL_R+22,d0
	blt.s	.a2
	neg.w	cur_dx
.a2	move.w	d0,cur_x
	btst	#J_FIRE,pressed+1
	beq.s	.aim
	moveq	#CS_BEEP,d0
	moveq	#40,d1
	jsr	K_CSFX(a5)
	; power: the bar goes up and down
	lea	s_power,a0
	bsr	message_small
	clr.w	power
	move.w	#5,pow_d
.pow	bsr	frame
	move.w	power,d0
	add.w	pow_d,d0
	bpl.s	.p1
	moveq	#0,d0
	neg.w	pow_d
.p1	cmp.w	#100,d0
	blt.s	.p2
	moveq	#100,d0
	neg.w	pow_d
.p2	move.w	d0,power
	bsr	draw_meter
	btst	#J_FIRE,pressed+1
	beq.s	.pow
	sf	cur_on
	bsr	clear_small
	; the shot: where it goes
	move.w	cur_x,d0
	move.w	d0,shot_x
	move.w	power,d1
	mulu	#56,d1
	divu	#85,d1
	move.w	#LINE_Y-6,d2
	sub.w	d1,d2
	move.w	d2,shot_y
	clr.w	outcome			; 0 goal, 1 saved, 2 wide/over, 3 post
	cmp.w	#86,power
	blo.s	.nov
	move.w	#2,outcome		; over the bar
	move.w	#BAR_Y-14,shot_y
.nov	cmp.w	#GOAL_L+2,d0
	blt.s	.wide
	cmp.w	#GOAL_R-2,d0
	ble.s	.inside
.wide	move.w	#2,outcome
	bra.s	.kp
.inside	cmp.w	#GOAL_L+6,d0		; just inside the post: it hits the post (sometimes)
	blt.s	.post
	cmp.w	#GOAL_R-6,d0
	ble.s	.kp
.post	moveq	#2,d0
	jsr	K_RAND(a5)
	tst.w	d0
	bne.s	.kp
	tst.w	outcome
	bne.s	.kp
	move.w	#3,outcome
	; the computer keeper guesses
.kp	move.w	shot_x,d0
	bsr	zone_of
	move.w	d0,d4			; the ball's zone
	moveq	#100,d0
	jsr	K_RAND(a5)
	move.w	CX_LEVEL(a4),d1
	add.w	d1,d1
	lea	kp_read,a0
	cmp.w	(a0,d1.w),d0
	blo.s	.right
	moveq	#3,d0
	jsr	K_RAND(a5)
	bra.s	.dz
.right	move.w	d4,d0
.dz	move.w	d0,dive			; 0 left, 1 middle, 2 right
	tst.w	outcome
	bne.s	.go
	cmp.w	d4,d0			; the right way?
	bne.s	.go
	bsr	save_chance		; -> d0 = % for this shot
	sub.w	#10,d0			; (a shooter's ball is hard to hold)
	cmp.w	#25,power
	bhs.s	.hard
	add.w	#25,d0
.hard	move.w	d0,d3
	moveq	#100,d0
	jsr	K_RAND(a5)
	cmp.w	d3,d0
	bhs.s	.go
	move.w	#1,outcome
.go	bsr	run_up
	bsr	fly
	; the result
	addq.w	#1,kicks_p
	move.w	kicks_p,d0
	subq.w	#1,d0
	lea	res_p,a0
	move.b	#'X',(a0,d0.w)
	tst.w	outcome
	bne.s	.ng
	move.b	#'~',(a0,d0.w)
	addq.w	#1,goals_p
.ng	bsr	draw_board
	bsr	say_outcome
	rts

; zone_of: d0 = x -> d0 = 0 left, 1 middle, 2 right
zone_of:
	cmp.w	#138,d0
	blt.s	.l
	cmp.w	#182,d0
	bgt.s	.r
	moveq	#1,d0
	rts
.l	moveq	#0,d0
	rts
.r	moveq	#2,d0
	rts

; save_chance -> d0 = % that a keeper who went the right way holds shot_x/shot_y
save_chance:
	move.w	shot_x,d0
	bsr	zone_of
	cmp.w	#1,d0
	bne.s	.corner
	moveq	#88,d0
	rts
.corner	cmp.w	#BAR_Y+20,shot_y
	bge.s	.low
	moveq	#40,d0			; top corner
	rts
.low	moveq	#75,d0
	rts

;------------------------------------------------------------------ the computer shoots, you keep
cpu_shoots:
	lea	pal_b,a0
	jsr	K_PAL(a5)
	move.l	CX_OPPCOL(a4),a0
	jsr	K_PLAYERPAL(a5)
	bsr	reset_scene
	lea	shm_tab,a0
	tst.w	CX_WOMAN(a4)
	beq.s	.m
	lea	shw_tab,a0
.m	move.l	a0,sh_tab
	lea	s_keep,a0
	bsr	message_small
	moveq	#20,d0
	bsr	frames
	; where it goes
	moveq	#3,d0
	jsr	K_RAND(a5)
	move.w	d0,d4
	lea	zone_x,a0
	add.w	d0,d0
	move.w	(a0,d0.w),d5
	moveq	#13,d0
	jsr	K_RAND(a5)
	subq.w	#6,d0
	add.w	d0,d5
	move.w	d5,shot_x
	moveq	#2,d0
	jsr	K_RAND(a5)
	move.w	#LINE_Y-12,d1
	tst.w	d0
	beq.s	.lo
	move.w	#BAR_Y+12,d1
.lo	move.w	d1,shot_y
	clr.w	outcome
	moveq	#100,d0			; the computer misses sometimes
	jsr	K_RAND(a5)
	moveq	#12,d1
	sub.w	CX_LEVEL(a4),d1
	sub.w	CX_LEVEL(a4),d1
	cmp.w	d1,d0
	bhs.s	.nm
	move.w	#2,outcome
	move.w	#BAR_Y-14,shot_y	; over the bar
	moveq	#2,d0
	jsr	K_RAND(a5)
	tst.w	d0
	beq.s	.nm
	move.w	#LINE_Y-10,shot_y	; wide
	move.w	#GOAL_L-14,shot_x
	tst.w	d4
	beq.s	.nm
	move.w	#GOAL_R+14,shot_x
.nm	move.w	#60,power
	move.w	#1,dive			; you stand still if you do nothing
	sf	dived
	st	you_keep
	bsr	run_up			; (reads your dive)
	sf	you_keep
	tst.w	outcome
	bne.s	.go
	move.w	shot_x,d0
	bsr	zone_of
	cmp.w	dive,d0
	bne.s	.go
	bsr	save_chance
	move.w	d0,d3
	cmp.w	#1,dive			; in the middle: only if you jumped or stayed
	bne.s	.c
	add.w	#5,d3
.c	moveq	#100,d0
	jsr	K_RAND(a5)
	cmp.w	d3,d0
	bhs.s	.go
	move.w	#1,outcome
.go	bsr	fly
	addq.w	#1,kicks_c
	move.w	kicks_c,d0
	subq.w	#1,d0
	lea	res_c,a0
	move.b	#'~',(a0,d0.w)
	cmp.w	#1,outcome
	bne.s	.ns
	addq.w	#1,saves
.ns	tst.w	outcome
	beq.s	.g
	move.b	#'X',(a0,d0.w)
	bra.s	.b
.g	addq.w	#1,goals_c
.b	bsr	draw_board
	bsr	say_outcome_keep
	rts

;------------------------------------------------------------------ the run-up and the ball
reset_scene:
	lea	kp_stand,a0
	move.l	a0,kp_bob
	move.w	#160-16,kp_x
	move.w	#LINE_Y-46,kp_y
	lea	ball0,a0
	move.l	a0,ball_bob
	move.w	#SPOT_X-6,ball_x
	move.w	#SPOT_Y-6,ball_y
	move.w	#108,sh_x
	move.w	#196,sh_y
	clr.w	sh_fr
	sf	cur_on
	clr.w	power
	bsr	draw_meter
	rts

run_up:
	moveq	#0,d7
.l	move.w	d7,d0			; run frames 1, 2, 1, 2 ...
	lsr.w	#1,d0
	and.w	#1,d0
	addq.w	#1,d0
	move.w	d0,sh_fr
	addq.w	#2,sh_x
	subq.w	#3,sh_y
	tst.b	you_keep
	beq.s	.nk
	bsr	read_dive
.nk	bsr	frame
	addq.w	#1,d7
	cmp.w	#12,d7
	blo.s	.l
	move.w	#3,sh_fr		; the kick
	lea	snd_kick,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	tst.b	you_keep
	beq.s	.x
	bsr	read_dive
.x	rts

read_dive:				; your joystick: the way you dive
	move.w	held,d0
	or.w	pressed,d0
	btst	#J_LEFT,d0
	beq.s	.n1
	clr.w	dive
	st	dived
.n1	btst	#J_RIGHT,d0
	beq.s	.n2
	move.w	#2,dive
	st	dived
.n2	btst	#J_UP,d0
	beq.s	.n3
	move.w	#1,dive
	st	dived
.n3	rts

; fly: the ball from the spot to shot_x/shot_y (or saved, or over / wide / post)
fly:
	move.w	#18,d6			; ticks to the goal: faster with more power
	move.w	power,d0
	divu	#11,d0
	sub.w	d0,d6
	moveq	#0,d7			; tick
.l	; the keeper moves from tick 2
	cmp.w	#2,d7
	bne.s	.nk
	bsr	keeper_dive
.nk	cmp.w	#3,d7
	blo.s	.nk2
	bsr	keeper_move
.nk2	; ball position: x = x0 + (xt-x0)*t/n, y the same, minus an arc
	move.w	shot_x,d0
	sub.w	#SPOT_X,d0
	muls	d7,d0
	divs	d6,d0
	add.w	#SPOT_X,d0
	move.w	shot_y,d1
	sub.w	#SPOT_Y,d1
	muls	d7,d1
	divs	d6,d1
	add.w	#SPOT_Y,d1
	move.w	d7,d2			; arc: t*(n-t)*24/n^2
	move.w	d6,d3
	sub.w	d7,d3
	mulu	d3,d2
	mulu	#24,d2
	move.w	d6,d3
	mulu	d6,d3
	divu	d3,d2
	sub.w	d2,d1
	subq.w	#6,d0
	subq.w	#6,d1
	move.w	d0,ball_x
	move.w	d1,ball_y
	move.w	d7,d0			; size: smaller further away
	lsl.w	#2,d0
	ext.l	d0
	divu	d6,d0
	cmp.w	#3,d0
	bls.s	.s
	moveq	#3,d0
.s	lsl.w	#2,d0
	lea	ball_tab,a0
	move.l	(a0,d0.w),ball_bob
	cmp.w	#3,d7
	bhs.s	.st
	move.w	#3,sh_fr
	bra.s	.f
.st	clr.w	sh_fr
.f	bsr	frame
	addq.w	#1,d7
	cmp.w	d6,d7
	bls	.l
	; at the goal
	move.w	outcome,d0
	cmp.w	#1,d0
	beq.s	.saved
	cmp.w	#3,d0
	beq.s	.post
	cmp.w	#2,d0
	beq.s	.miss
	lea	snd_net,a0		; goal: the ball in the net
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#8,d0
	bsr	frames
	rts
.post	lea	snd_post,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	move.w	#-3,d4			; the ball comes back out
	moveq	#3,d5
	bra.s	.away
.saved	moveq	#CS_OOH,d0
	moveq	#30,d1
	jsr	K_CSFX(a5)
	moveq	#4,d4			; pushed away to the side
	cmp.w	#160,shot_x
	bge.s	.sv
	moveq	#-4,d4
.sv	moveq	#-2,d5
	bra.s	.away
.miss	move.w	#0,d4			; on over the bar / past the post
	moveq	#-2,d5
	move.l	#ball3,ball_bob
.away	moveq	#9,d7
.a	add.w	d4,ball_x
	add.w	d5,ball_y
	bsr	frame
	dbf	d7,.a
	move.l	#0,ball_bob
	moveq	#4,d0
	bsr	frames
	rts

keeper_dive:
	move.w	dive,d0
	lea	kp_stand,a0
	cmp.w	#1,d0
	bne.s	.lr
	cmp.w	#BAR_Y+24,shot_y	; a high ball in the middle: jump
	bge.s	.set
	tst.b	you_keep
	beq.s	.j
	tst.b	dived
	beq.s	.set
.j	lea	kp_jump,a0
	bra.s	.set
.lr	tst.w	d0
	bne.s	.r
	lea	kp_divel,a0
	move.w	#160-24,kp_x
	move.w	#LINE_Y-44,kp_y
	bra.s	.set
.r	lea	kp_diver,a0
	move.w	#160-24,kp_x
	move.w	#LINE_Y-44,kp_y
.set	move.l	a0,kp_bob
	rts

keeper_move:
	move.w	dive,d0
	cmp.w	#1,d0
	beq.s	.mid
	move.w	#94,d1			; left target (top left of the 48 wide frame)
	tst.w	d0
	beq.s	.t
	move.w	#178,d1
.t	move.w	kp_x,d0
	cmp.w	d1,d0
	beq.s	.y
	blt.s	.rt
	subq.w	#7,d0
	cmp.w	d1,d0
	bge.s	.st
	move.w	d1,d0
	bra.s	.st
.rt	addq.w	#7,d0
	cmp.w	d1,d0
	ble.s	.st
	move.w	d1,d0
.st	move.w	d0,kp_x
.y	move.w	#LINE_Y-40,d1		; a little up, higher for a high ball
	cmp.w	#BAR_Y+24,shot_y
	bge.s	.lo
	move.w	#LINE_Y-52,d1
.lo	move.w	d1,kp_y
	rts
.mid	cmp.l	#kp_jump,kp_bob
	bne.s	.x
	move.w	#LINE_Y-54,kp_y
.x	rts

;------------------------------------------------------------------ messages
say_outcome:				; after your shot
	move.w	outcome,d0
	bne.s	.n0
	lea	v_goal,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#CS_CHEER,d0
	moveq	#44,d1
	jsr	K_CSFX(a5)
	lea	s_goal,a0
	bra.s	.m
.n0	cmp.w	#1,d0
	bne.s	.n1
	lea	v_saved,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	s_saved,a0
	bra.s	.m
.n1	cmp.w	#3,d0
	bne.s	.n2
	lea	v_missed,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	s_post,a0
	bra.s	.m
.n2	lea	v_missed,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#CS_OOH,d0
	moveq	#30,d1
	jsr	K_CSFX(a5)
	lea	s_missed,a0
.m	bsr	message
	moveq	#40,d0
	moveq	#1,d1
	jsr	K_WAIT(a5)
	bsr	clear_msg
	rts

say_outcome_keep:			; after their shot
	move.w	outcome,d0
	bne.s	.n0
	moveq	#CS_OHNO,d0
	moveq	#64,d1
	jsr	K_CSFX(a5)
	lea	s_theyscore,a0
	bra.s	.m
.n0	cmp.w	#1,d0
	bne.s	.n1
	lea	v_saved,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#CS_CHEER,d0
	moveq	#44,d1
	jsr	K_CSFX(a5)
	lea	s_yousave,a0
	bra.s	.m
.n1	lea	v_missed,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	s_theymiss,a0
.m	bsr	message
	moveq	#40,d0
	moveq	#1,d1
	jsr	K_WAIT(a5)
	bsr	clear_msg
	rts

message:				; a0: big, in the bottom bar
	movem.l	d0-d4/a0,-(sp)
	bsr	clear_msg
	move.l	20(sp),a0
	move.w	#240,d1
	moveq	#3,d2
	moveq	#-1,d3
	jsr	K_CTEXT2(a5)
	movem.l	(sp)+,d0-d4/a0
	rts
message_small:
	movem.l	d0-d4/a0,-(sp)
	bsr	clear_msg
	move.l	20(sp),a0
	move.w	#244,d1
	moveq	#2,d2
	moveq	#-1,d3
	jsr	K_CTEXT(a5)
	movem.l	(sp)+,d0-d4/a0
	rts
clear_small:
clear_msg:
	movem.l	d0-d4,-(sp)
	moveq	#0,d0
	move.w	#241,d1
	move.w	#320,d2
	moveq	#15,d3
	moveq	#0,d4
	jsr	K_FILL(a5)
	movem.l	(sp)+,d0-d4
	rts

; the top bar: you and them, the kicks, the goals
draw_board:
	movem.l	d0-d7/a0-a2,-(sp)
	moveq	#0,d0
	moveq	#0,d1
	move.w	#320,d2
	moveq	#23,d3
	moveq	#0,d4
	jsr	K_FILL(a5)
	move.l	a4,a0			; your name
	moveq	#8,d0
	moveq	#3,d1
	moveq	#3,d2
	moveq	#-1,d3
	jsr	K_TEXT(a5)
	lea	strbuf,a1		; their country (11 letters at most)
	move.l	CX_OPPNAME(a4),a0
	moveq	#10,d0
.c	move.b	(a0)+,(a1)+
	dbeq	d0,.c
	clr.b	(a1)
	lea	strbuf,a0
	moveq	#8,d0
	moveq	#13,d1
	moveq	#2,d2
	jsr	K_TEXT(a5)
	lea	res_p,a2
	moveq	#3,d1
	bsr	.dots
	lea	res_c,a2
	moveq	#13,d1
	bsr	.dots
	moveq	#0,d0
	move.w	goals_p,d0
	moveq	#1,d1
	jsr	K_NUM(a5)
	move.w	#280,d0
	moveq	#3,d1
	moveq	#3,d2
	jsr	K_TEXT(a5)
	moveq	#0,d0
	move.w	goals_c,d0
	moveq	#1,d1
	jsr	K_NUM(a5)
	move.w	#280,d0
	moveq	#13,d1
	moveq	#2,d2
	jsr	K_TEXT(a5)
	movem.l	(sp)+,d0-d7/a0-a2
	rts
.dots	moveq	#0,d7			; 10 places: ~ goal, X missed, . to come
.d	lea	strbuf,a0
	move.b	(a2,d7.w),d0
	bne.s	.has
	moveq	#'.',d0
	cmp.w	#5,d7
	blo.s	.has
	moveq	#' ',d0
.has	move.b	d0,(a0)
	clr.b	1(a0)
	moveq	#3,d2			; colour: yellow goal, red miss
	cmp.b	#'~',d0
	beq.s	.cc
	moveq	#4,d2
	cmp.b	#'X',d0
	beq.s	.cc
	moveq	#2,d2
.cc	move.w	d7,d0
	lsl.w	#3,d0
	add.w	#120,d0
	moveq	#-1,d3
	movem.l	d1/d7,-(sp)
	jsr	K_TEXT(a5)
	movem.l	(sp)+,d1/d7
	addq.w	#1,d7
	cmp.w	#MAXROUND,d7
	blo.s	.d
	rts

; the power meter: 0-100 -> 0-84 pixels, red at the top
draw_meter:
	movem.l	d0-d6,-(sp)
	move.w	power,d5
	mulu	#84,d5
	divu	#100,d5			; filled height
	moveq	#84,d6
	sub.w	d5,d6			; empty height
	move.w	#296,d0
	move.w	#148,d1
	moveq	#16,d2
	move.w	d6,d3
	moveq	#1,d4
	tst.w	d3
	beq.s	.f
	jsr	K_FILL(a5)
.f	move.w	#296,d0
	move.w	#148,d1
	add.w	d6,d1
	moveq	#16,d2
	move.w	d5,d3
	moveq	#3,d4
	cmp.w	#86,power
	blo.s	.y
	moveq	#4,d4
.y	tst.w	d3
	beq.s	.x
	jsr	K_FILL(a5)
.x	movem.l	(sp)+,d0-d6
	rts

;------------------------------------------------------------------ one frame
frames:					; d0 = frames to show
	move.w	d0,-(sp)
.l	bsr	frame
	subq.w	#1,(sp)
	bgt.s	.l
	addq.l	#2,sp
	rts

frame:
	movem.l	d0-d3/a0,-(sp)
	jsr	K_BEGIN(a5)
	move.l	kp_bob,d2		; the keeper
	beq.s	.nk
	move.l	d2,a0
	move.w	kp_x,d0
	move.w	kp_y,d1
	jsr	K_BOB(a5)
.nk	move.l	ball_bob,d2		; the ball
	beq.s	.nb
	move.l	d2,a0
	move.w	ball_x,d0
	move.w	ball_y,d1
	cmp.w	#24,d1			; (not over the top bar)
	blt.s	.nb
	jsr	K_BOB(a5)
.nb	move.l	sh_tab,d2		; the shooter
	beq.s	.ns
	move.l	d2,a0
	move.w	sh_fr,d0
	lsl.w	#2,d0
	move.l	(a0,d0.w),a0
	move.w	sh_x,d0
	move.w	sh_y,d1
	jsr	K_BOB(a5)
.ns	tst.b	cur_on			; the aim
	beq.s	.nc
	lea	aimcur,a0
	move.w	cur_x,d0
	subq.w	#8,d0
	move.w	#AIM_Y-8,d1
	jsr	K_BOB(a5)
.nc	jsr	K_END(a5)
	jsr	K_INPUT(a5)
	move.w	d0,held
	move.w	d1,pressed
	btst	#J_ESC,d1
	bne	give_up
	movem.l	(sp)+,d0-d3/a0
	rts

;==============================================================================
	section	data,data
kp_read		dc.w	15,25,35		; % the computer keeper reads your shot
zone_x		dc.w	114,160,206
s_aim		dc.b	'AIM: PRESS FIRE',0
s_power		dc.b	'POWER: PRESS FIRE  (NOT TOO HARD!)',0
s_keep		dc.b	'YOU KEEP! DIVE: LEFT, RIGHT OR UP',0
s_goal		dc.b	'GOAL!',0
s_saved		dc.b	'SAVED!',0
s_missed	dc.b	'MISSED!',0
s_post		dc.b	'THE POST!',0
s_theyscore	dc.b	'THEY SCORE',0
s_yousave	dc.b	'GREAT SAVE!',0
s_theymiss	dc.b	'THEY MISS!',0
s_youwin	dc.b	'YOU WIN!',0
s_youlose	dc.b	'YOU LOSE',0
s_itsdraw	dc.b	'A DRAW',0
s_won		dc.b	'WON ',0
s_lost		dc.b	'LOST ',0
s_draw		dc.b	'DRAW ',0
s_eq		dc.b	' = ',0
s_pts		dc.b	' PTS',0
	even
	include	"soc_data.i"
bg_rle	incbin	"soc_bg.rle"
	even

	section	chip,data_c
soc_chip	incbin	"soc_chip.bin"

	section	bss,bss
vars
ev_sp		ds.l	1
kp_bob		ds.l	1
ball_bob	ds.l	1
sh_tab		ds.l	1
held		ds.w	1
pressed		ds.w	1
round		ds.w	1
kicks_p		ds.w	1
kicks_c		ds.w	1
goals_p		ds.w	1
goals_c		ds.w	1
saves		ds.w	1
kp_x		ds.w	1
kp_y		ds.w	1
ball_x		ds.w	1
ball_y		ds.w	1
sh_x		ds.w	1
sh_y		ds.w	1
sh_fr		ds.w	1
cur_x		ds.w	1
cur_dx		ds.w	1
power		ds.w	1
pow_d		ds.w	1
shot_x		ds.w	1
shot_y		ds.w	1
outcome		ds.w	1
dive		ds.w	1
res_p		ds.b	MAXROUND+2
res_c		ds.b	MAXROUND+2
cur_on		ds.b	1
you_keep	ds.b	1
dived		ds.b	1
	even
strbuf		ds.b	32
VARS_END
VARS_SIZE	equ	VARS_END-vars
