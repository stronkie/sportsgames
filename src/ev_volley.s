;------------------------------------------------------------------------------
;  ev_volley.s - VOLLEYBALL: beach volleyball, you against another country,
;  the first to 7 points.
;  An event of Stronkie's Olympics (loaded from Volley.evt; see kernel.i).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"vol_equ.i"

WIN		equ	7
GRAV		equ	6			; the ball: 1/16 pixels per tick per tick
PGRAV		equ	8			; the athletes
TOPY		equ	GROUND-48		; top of an athlete on the sand
P_MIN		equ	4			; the player's left edge (frame x)
P_MAX		equ	NET_X-36
C_MIN		equ	NET_X+4
C_MAX		equ	284

	section	code,code
	bra.w	entry
	dc.l	'SOEV'
	dc.w	7,14			; the computer athletes score 7..14 points
	dc.w	0

entry:	movem.l	d1-d7/a0-a6,-(sp)
	move.l	sp,ev_sp
	lea	vars,a0
	move.w	#VARS_SIZE/2-1,d0
.cl	clr.w	(a0)+
	dbf	d0,.cl
	lea	pm_tab,a0
	lea	cm_tab,a1
	tst.w	CX_WOMAN(a4)
	beq.s	.m
	lea	pw_tab,a0
	lea	cw_tab,a1
.m	move.l	a0,pl_tab
	move.l	a1,cp_tab
	lea	pal_vol,a0		; the palette with the other athlete's colours in 18-24
	lea	palbuf,a1
	moveq	#31,d0
.p	move.w	(a0)+,(a1)+
	dbf	d0,.p
	move.l	CX_OPPCOL(a4),a0
	lea	palbuf+36,a1
	moveq	#6,d0
.o	move.w	(a0)+,(a1)+
	dbf	d0,.o
	lea	palbuf,a0
	lea	bg_rle,a1
	bsr	ev_start
	lea	grad_vol,a0
	jsr	K_GRAD(a5)
	bsr	draw_top
	clr.w	server
	bsr	positions
	moveq	#1,d0
	bsr	frames
	jsr	K_FADEIN(a5)
	lea	v_volley,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#30,d0
	bsr	frames

.rally	bsr	serve
	bsr	play			; -> d0 = 0: your point, 1: theirs
	bsr	point
	cmp.w	#WIN,score_p
	beq.s	.end
	cmp.w	#WIN,score_c
	beq.s	.end
	bsr	positions
	moveq	#10,d0
	bsr	frames
	bra.s	.rally
.end	moveq	#CS_WHISTLE,d0
	moveq	#50,d1
	jsr	K_CSFX(a5)
	moveq	#10,d0			; points: 10 + yours - theirs
	add.w	score_p,d0
	sub.w	score_c,d0
	ext.l	d0
	move.l	d0,CX_SCORE(a4)
	lea	CX_RESULT(a4),a1	; "WON 7-4 = 13 PTS"
	lea	s_won,a0
	move.w	score_p,d0
	cmp.w	score_c,d0
	bhi.s	.w
	lea	s_lost,a0
.w	bsr	cat
	moveq	#0,d0
	move.w	score_p,d0
	bsr	catnum
	move.b	#'-',(a1)+
	moveq	#0,d0
	move.w	score_c,d0
	bsr	catnum
	lea	s_eq,a0
	bsr	cat
	move.l	CX_SCORE(a4),d0
	bsr	catnum
	lea	s_c_pts,a0
	bsr	cat
	move.w	score_p,d0
	cmp.w	score_c,d0
	bhi.s	.won
	moveq	#CS_OHNO,d0
	moveq	#64,d1
	jsr	K_CSFX(a5)
	lea	s_youlose,a0
	bra.s	.msg
.won	moveq	#CS_CHEER,d0
	moveq	#48,d1
	jsr	K_CSFX(a5)
	moveq	#CS_GREAT,d0
	moveq	#64,d1
	jsr	K_CSFX(a5)
	lea	s_youwin,a0
.msg	bsr	message
	bra	ev_done

;------------------------------------------------------------------ a rally
positions:
	move.w	#56,px
	move.w	#TOPY,py
	clr.w	pvy
	move.w	#224,cx
	move.w	#TOPY,cy
	clr.w	cvy
	sf	ball_on
	rts

; serve: the ball over the server's head, then the serve
serve:
	st	ball_on
	clr.w	touches
	move.w	#-1,last_side
	moveq	#0,d7
.l	tst.w	server
	bne.s	.cpu
	move.w	px,d0			; you: the ball goes with you, fire serves
	add.w	#24,d0
	lsl.w	#4,d0
	move.w	d0,bx
	move.w	#(TOPY-14)*16,by
	lea	s_serve,a0
	tst.w	d7
	bne.s	.nm
	bsr	message_small
.nm	bsr	move_player
	bsr	frame
	addq.w	#1,d7
	btst	#J_FIRE,pressed+1
	beq.s	.l
	move.w	#60,bvx
	move.w	#-132,bvy
	clr.w	last_side
	move.w	#1,touches
	bra.s	.go
.cpu	move.w	cx,d0			; the computer serves after a moment
	add.w	#8,d0
	lsl.w	#4,d0
	move.w	d0,bx
	move.w	#(TOPY-14)*16,by
	bsr	frame
	addq.w	#1,d7
	cmp.w	#30,d7
	blo.s	.cpu
	moveq	#16,d0
	jsr	K_RAND(a5)
	neg.w	d0
	sub.w	#52,d0
	move.w	d0,bvx
	move.w	#-132,bvy
	move.w	#1,last_side
	move.w	#1,touches
.go	bsr	clear_msg
	lea	snd_hit,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	move.w	#6,hit_p		; (no hit back at once)
	move.w	#6,hit_c
	rts

; play: until the ball is on the sand -> d0 = 0 your point, 1 theirs
play:
.l	bsr	move_player
	bsr	move_cpu
	bsr	move_ball		; -> d0 = -1 on, 0/1 a point
	tst.w	d0
	bpl.s	.x
	bsr	hits
	tst.w	d0
	bpl.s	.x
	bsr	frame
	bra.s	.l
.x	move.w	d0,-(sp)
	bsr	frame
	move.w	(sp)+,d0
	rts

; point: d0 = 0 yours, 1 theirs
point:
	move.w	d0,server
	tst.w	d0
	bne.s	.c
	addq.w	#1,score_p
	moveq	#CS_CHEER,d0
	moveq	#36,d1
	jsr	K_CSFX(a5)
	lea	v_point,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	s_yourpt,a0
	bra.s	.m
.c	addq.w	#1,score_c
	moveq	#CS_OOH,d0
	moveq	#30,d1
	jsr	K_CSFX(a5)
	lea	s_theirpt,a0
	tst.b	was_out
	beq.s	.m
	lea	v_out,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	s_out,a0
.m	tst.b	was_out
	beq.s	.n
	tst.w	server
	bne.s	.n
	lea	s_out2,a0		; they hit it out
.n	bsr	message
	bsr	draw_top
	moveq	#40,d0
	bsr	frames
	bsr	clear_msg
	rts

;------------------------------------------------------------------ moving
move_player:
	move.w	held,d1
	moveq	#0,d2			; dx
	btst	#J_LEFT,d1
	beq.s	.nl
	moveq	#-4,d2
.nl	btst	#J_RIGHT,d1
	beq.s	.nr
	moveq	#4,d2
.nr	move.w	px,d0
	add.w	d2,d0
	cmp.w	#P_MIN,d0
	bge.s	.a
	moveq	#P_MIN,d0
.a	cmp.w	#P_MAX,d0
	ble.s	.b
	move.w	#P_MAX,d0
.b	move.w	d0,px
	move.w	d2,pmov
	; jump
	move.w	py,d0
	cmp.w	#TOPY,d0
	blt.s	.air
	tst.w	pvy
	bmi.s	.air
	btst	#J_FIRE,pressed+1
	beq.s	.x
	tst.b	ball_on
	beq.s	.x
	move.w	#-104,pvy		; up!
.air	move.w	pvy,d0
	asr.w	#4,d0
	add.w	d0,py
	add.w	#PGRAV,pvy
	cmp.w	#TOPY,py
	blt.s	.x
	move.w	#TOPY,py
	clr.w	pvy
.x	rts

; the computer: runs to where the ball comes down, jumps to spike
move_cpu:
	tst.w	hit_c
	beq.s	.h
	subq.w	#1,hit_c
.h	move.w	#240,d5			; home
	move.w	bx,d0
	asr.w	#4,d0
	cmp.w	#NET_X-40,d0
	blt.s	.go			; (far on your side: go home)
	tst.w	bvx
	bmi.s	.pr
	cmp.w	#NET_X,d0
	blt.s	.go
.pr	bsr	predict			; -> d0 = x where it comes down
	add.w	miss_c,d0
	sub.w	#10,d0			; (the ball a little on the net side)
	move.w	d0,d5
.go	move.w	cx,d0			; frame x -> middle
	add.w	#16,d0
	move.w	CX_LEVEL(a4),d3
	addq.w	#3,d3			; speed 3-5
	moveq	#0,d4
	cmp.w	d5,d0
	beq.s	.st
	blt.s	.r
	neg.w	d3
.r	move.w	d5,d1
	sub.w	d0,d1
	bpl.s	.ab
	neg.w	d1
.ab	cmp.w	#2,d1
	ble.s	.st
	move.w	d3,d4
.st	move.w	cx,d0
	add.w	d4,d0
	cmp.w	#C_MIN,d0
	bge.s	.a
	move.w	#C_MIN,d0
.a	cmp.w	#C_MAX,d0
	ble.s	.b
	move.w	#C_MAX,d0
.b	move.w	d0,cx
	move.w	d4,cmov
	; jump to spike (normal and hard)
	move.w	cy,d0
	cmp.w	#TOPY,d0
	blt.s	.air
	tst.w	CX_LEVEL(a4)
	beq.s	.x
	tst.w	bvy
	bmi.s	.x
	move.w	bx,d0
	asr.w	#4,d0
	cmp.w	#NET_X+8,d0
	blt.s	.x
	sub.w	cx,d0
	sub.w	#16,d0
	bpl.s	.p
	neg.w	d0
.p	cmp.w	#14,d0
	bgt.s	.x
	move.w	by,d0
	asr.w	#4,d0
	cmp.w	#TOPY-50,d0
	blt.s	.x
	cmp.w	#TOPY-26,d0
	bgt.s	.x
	move.w	#-104,cvy
.air	move.w	cvy,d0
	asr.w	#4,d0
	add.w	d0,cy
	add.w	#PGRAV,cvy
	cmp.w	#TOPY,cy
	blt.s	.x
	move.w	#TOPY,cy
	clr.w	cvy
.x	rts

; predict -> d0 = the x (pixels) where the ball comes to head height
predict:
	movem.l	d1-d5,-(sp)
	move.w	bx,d1
	move.w	by,d2
	move.w	bvx,d3
	move.w	bvy,d4
	move.w	#100,d5
.l	add.w	d3,d1
	add.w	d4,d2
	add.w	#GRAV,d4
	tst.w	d4
	bmi.s	.n
	cmp.w	#(TOPY+2)*16,d2
	bge.s	.x
.n	dbf	d5,.l
.x	move.w	d1,d0
	asr.w	#4,d0
	movem.l	(sp)+,d1-d5
	rts

; move_ball -> d0 = -1 still going, 0 your point, 1 theirs
move_ball:
	tst.b	ball_on
	beq	.go
	move.w	bvx,d0
	add.w	d0,bx
	move.w	bvy,d0
	add.w	d0,by
	add.w	#GRAV,bvy
	; the net
	move.w	bx,d0
	asr.w	#4,d0
	move.w	by,d1
	asr.w	#4,d1
	cmp.w	#NET_TOP-6,d1
	blt.s	.nonet
	cmp.w	#NET_X-9,d0
	blt.s	.nonet
	cmp.w	#NET_X+8,d0
	bgt.s	.nonet
	cmp.w	#NET_TOP+2,d1		; on top of the net: up again
	bgt.s	.side
	move.w	bvy,d0
	bmi.s	.nonet
	asr.w	#1,d0
	neg.w	d0
	move.w	d0,bvy
	bra.s	.nsnd
.side	move.w	bvx,d0			; into the net: back
	asr.w	#1,d0
	neg.w	d0
	move.w	d0,bvx
	move.w	#(NET_X-10)*16,bx
	tst.w	d0
	bmi.s	.nsnd
	move.w	#(NET_X+9)*16,bx
.nsnd	lea	snd_net,a0
	moveq	#50,d1
	jsr	K_SFX(a5)
.nonet	; the sand?
	move.w	by,d1
	asr.w	#4,d1
	cmp.w	#GROUND-6,d1
	blt.s	.go
	move.w	#(GROUND-6)*16,by
	lea	snd_sand,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	sf	was_out
	move.w	bx,d0
	asr.w	#4,d0
	cmp.w	#12,d0			; out of the court: the one who hit it last loses it
	blt.s	.out
	cmp.w	#308,d0
	bgt.s	.out
	cmp.w	#NET_X,d0
	blt.s	.mine
	moveq	#0,d0			; on their side: your point
	rts
.mine	moveq	#1,d0
	rts
.out	st	was_out
	moveq	#1,d0
	tst.w	last_side
	beq.s	.o
	moveq	#0,d0
.o	rts
.go	moveq	#-1,d0
	rts

; hits: does an athlete touch the ball? -> d0 = -1 on, 0/1 a point (4 touches)
hits:
	tst.w	hit_p
	beq.s	.hp
	subq.w	#1,hit_p
	bra.s	.c
.hp	move.w	px,d2
	move.w	py,d3
	moveq	#0,d4
	bsr	touch			; -> d0 = 1 touched
	tst.w	d0
	beq.s	.c
	moveq	#0,d4
	bsr	do_hit
	tst.w	d0
	bpl.s	.x
.c	tst.w	hit_c
	bne.s	.no
	move.w	cx,d2
	move.w	cy,d3
	bsr	touch
	tst.w	d0
	beq.s	.no
	moveq	#1,d4
	bsr	do_hit
	rts
.no	moveq	#-1,d0
.x	rts

; touch: d2/d3 = the athlete's frame x/y -> d0 = 1 when the ball is at the head or the hands
touch:
	move.w	bx,d0
	asr.w	#4,d0
	sub.w	d2,d0
	sub.w	#16,d0			; dx from the middle
	cmp.w	#-17,d0
	blt.s	.no
	cmp.w	#17,d0
	bgt.s	.no
	move.w	by,d1
	asr.w	#4,d1
	sub.w	d3,d1			; dy from the top of the frame
	cmp.w	#-12,d1
	blt.s	.no
	cmp.w	#18,d1
	bgt.s	.no
	tst.w	bvy			; only a ball on its way down (or a low one)
	bpl.s	.yes
	cmp.w	#6,d1
	blt.s	.no
.yes	moveq	#1,d0
	rts
.no	moveq	#0,d0
	rts

; do_hit: d4 = 0 you, 1 the computer; d2/d3 = its frame -> d0 = -1 on, 0/1 a point (too many touches)
do_hit:
	cmp.w	last_side,d4
	beq.s	.same
	move.w	d4,last_side
	move.w	#1,touches
	bra.s	.t
.same	addq.w	#1,touches
	cmp.w	#4,touches
	blo.s	.t
	moveq	#1,d0			; 4 touches: the other side's point
	sub.w	d4,d0
	rts
.t	move.w	bx,d0			; dx (ball - middle), towards the net is +
	asr.w	#4,d0
	sub.w	d2,d0
	sub.w	#16,d0
	tst.w	d4
	beq.s	.n
	neg.w	d0
.n	move.w	d3,d1			; a spike: high in a jump, in front of the head
	cmp.w	#TOPY-14,d1
	bgt.s	.normal
	cmp.w	#-6,d0
	blt.s	.normal
	move.w	#84,d5			; vx
	move.w	#24,d6			; vy (down)
	lea	snd_spike,a0
	bra.s	.set
.normal	move.w	d0,d5
	mulu	#3,d5
	add.w	#46,d5
	cmp.w	#14,d5
	bge.s	.v1
	moveq	#14,d5
.v1	cmp.w	#86,d5
	ble.s	.v2
	moveq	#86,d5
.v2	move.w	#-118,d6
	lea	snd_hit,a0
.set	moveq	#64,d1
	jsr	K_SFX(a5)
	tst.w	d4
	beq.s	.me
	neg.w	d5			; the computer hits to the left
	move.w	#8,hit_c
	move.w	#5,hit_anim_c
	moveq	#100,d0			; and it misjudges the next ball now and then
	jsr	K_RAND(a5)
	clr.w	miss_c
	move.w	CX_LEVEL(a4),d1
	add.w	d1,d1
	lea	miss_pc,a0
	cmp.w	(a0,d1.w),d0
	bhs.s	.go
	move.w	#24,miss_c
	bra.s	.go
.me	move.w	#8,hit_p
	move.w	#5,hit_anim_p
	cmp.w	#84,d5
	bne.s	.go
	lea	v_spike,a0		; (your spike)
	moveq	#50,d1
	jsr	K_SFX(a5)
.go	move.w	d5,bvx
	move.w	d6,bvy
	moveq	#-1,d0
	rts

;------------------------------------------------------------------ the screen
draw_top:
	movem.l	d0-d4/a0-a1,-(sp)
	moveq	#0,d0
	moveq	#0,d1
	move.w	#320,d2
	moveq	#23,d3
	moveq	#0,d4
	jsr	K_FILL(a5)
	move.l	a4,a0
	moveq	#8,d0
	moveq	#3,d2
	bsr	top_text
	moveq	#0,d0
	move.w	score_p,d0
	moveq	#120,d1
	moveq	#3,d2
	moveq	#1,d3
	bsr	top_num
	lea	strbuf,a1		; their country (11 letters at most)
	move.l	CX_OPPNAME(a4),a0
	moveq	#10,d0
.c	move.b	(a0)+,(a1)+
	dbeq	d0,.c
	clr.b	(a1)
	lea	strbuf,a0
	move.w	#176,d0
	moveq	#2,d2
	bsr	top_text
	moveq	#0,d0
	move.w	score_c,d0
	move.w	#296,d1
	moveq	#2,d2
	moveq	#1,d3
	bsr	top_num
	movem.l	(sp)+,d0-d4/a0-a1
	rts

; which frame: 0 ready, 1-4 running, 5 jump, 6 hit
pick_frame:				; d0 = moving, d1 = top y, d2 = hit timer -> d0
	tst.w	d2
	beq.s	.nh
	moveq	#6,d0
	rts
.nh	cmp.w	#TOPY,d1
	bge.s	.g
	moveq	#5,d0
	rts
.g	tst.w	d0
	beq.s	.r
	move.w	tick,d0
	lsr.w	#1,d0
	and.w	#3,d0
	addq.w	#1,d0
	rts
.r	moveq	#0,d0
	rts

frame:
	movem.l	d0-d3/a0,-(sp)
	addq.w	#1,tick
	tst.w	hit_anim_p
	beq.s	.a1
	subq.w	#1,hit_anim_p
.a1	tst.w	hit_anim_c
	beq.s	.a2
	subq.w	#1,hit_anim_c
.a2	jsr	K_BEGIN(a5)
	tst.b	ball_on			; the ball's shadow
	beq.s	.ns
	lea	vshadow,a0
	move.w	bx,d0
	asr.w	#4,d0
	subq.w	#7,d0
	move.w	#GROUND+1,d1
	jsr	K_BOB(a5)
.ns	move.w	cmov,d0			; the computer
	move.w	cy,d1
	move.w	hit_anim_c,d2
	bsr	pick_frame
	lsl.w	#2,d0
	move.l	cp_tab,a0
	move.l	(a0,d0.w),a0
	move.w	cx,d0
	move.w	cy,d1
	jsr	K_BOB(a5)
	move.w	pmov,d0			; you
	move.w	py,d1
	move.w	hit_anim_p,d2
	bsr	pick_frame
	lsl.w	#2,d0
	move.l	pl_tab,a0
	move.l	(a0,d0.w),a0
	move.w	px,d0
	move.w	py,d1
	jsr	K_BOB(a5)
	tst.b	ball_on			; the ball
	beq.s	.nb
	lea	vball,a0
	move.w	bx,d0
	asr.w	#4,d0
	subq.w	#7,d0
	move.w	by,d1
	asr.w	#4,d1
	subq.w	#7,d1
	cmp.w	#24,d1
	blt.s	.nb
	jsr	K_BOB(a5)
.nb	jsr	K_END(a5)
	bsr	read_input
	movem.l	(sp)+,d0-d3/a0
	rts

	include	"evcommon.s"

;==============================================================================
	section	data,data
miss_pc		dc.w	14,8,4			; % the computer misjudges a ball
s_serve		dc.b	'YOUR SERVE: PRESS FIRE',0
s_yourpt	dc.b	'YOUR POINT!',0
s_theirpt	dc.b	'THEIR POINT',0
s_out		dc.b	'OUT!',0
s_out2		dc.b	'THEY HIT IT OUT!',0
s_youwin	dc.b	'YOU WIN!',0
s_youlose	dc.b	'YOU LOSE',0
s_won		dc.b	'WON ',0
s_lost		dc.b	'LOST ',0
s_eq		dc.b	' = ',0
	even
	include	"vol_data.i"
bg_rle	incbin	"vol_bg.rle"
	even

	section	chip,data_c
vol_chip	incbin	"vol_chip.bin"

	section	bss,bss
vars
pl_tab		ds.l	1
cp_tab		ds.l	1
palbuf		ds.w	32
px		ds.w	1
py		ds.w	1
pvy		ds.w	1
pmov		ds.w	1
cx		ds.w	1
cy		ds.w	1
cvy		ds.w	1
cmov		ds.w	1
bx		ds.w	1
by		ds.w	1
bvx		ds.w	1
bvy		ds.w	1
score_p		ds.w	1
score_c		ds.w	1
server		ds.w	1
touches		ds.w	1
last_side	ds.w	1
hit_p		ds.w	1
hit_c		ds.w	1
hit_anim_p	ds.w	1
hit_anim_c	ds.w	1
miss_c		ds.w	1
tick		ds.w	1
ball_on		ds.b	1
was_out		ds.b	1
	even
VARS_END
VARS_SIZE	equ	VARS_END-vars
