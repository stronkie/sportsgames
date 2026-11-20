;------------------------------------------------------------------------------
;  ev_pies.s - PIE DODGE: cross the arena from one green side to the other
;  and back (10 points a crossing) while the clowns throw pies at you
;  (a pie in the face: 3 points off and a moment to wipe it).  60 seconds.
;  An event of Stronkie's Olympics (PieDodge.evt; see kernel.i).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"pie_equ.i"

CPU_LO		equ	30			; the others: 30 .. 70 points
CPU_HI		equ	70
NPIES		equ	8
TIME		equ	60*25
SPEED		equ	2
WIPE		equ	25			; ticks with a pie in the face

	section	code,code
	bra.w	entry
	dc.l	'SOEV'
	dc.w	CPU_LO,CPU_HI
	dc.w	0

; a pie: x.w, y.w, dy.w (0 = none)
P_X		equ	0
P_Y		equ	2
P_DY		equ	4
P_SIZE		equ	6

entry:	movem.l	d1-d7/a0-a6,-(sp)
	move.l	sp,ev_sp
	lea	pal_pie,a0
	lea	bg_rle,a1
	bsr	ev_start
	lea	pies,a0
	moveq	#NPIES*P_SIZE/2-1,d0
.c	clr.w	(a0)+
	dbf	d0,.c
	move.w	#X0+4,px
	move.w	#(Y0+Y1)/2,py
	clr.w	score
	clr.w	wipe
	clr.w	walk
	move.w	#1,goal			; 1: to the right, 0: to the left
	move.w	#TIME,timer
	; the throwing: a pie every 22 (easy), 15, 10 (hard) ticks
	moveq	#22,d0
	move.w	CX_LEVEL(a4),d1
	beq.s	.l
	moveq	#15,d0
	subq.w	#1,d1
	beq.s	.l
	moveq	#10,d0
.l	move.w	d0,every
	clr.w	next
	bsr	draw_top
	moveq	#1,d0
	bsr	frames
	jsr	K_FADEIN(a5)
	lea	v_title,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	s_help,a0
	bsr	message_small
	moveq	#40,d0
	bsr	frames
	moveq	#CS_GO,d0
	moveq	#64,d1
	jsr	K_CSFX(a5)
	bsr	clear_msg
.loop	bsr	move_me
	bsr	throw
	bsr	move_pies
	subq.w	#1,timer
	moveq	#24,d0			; the clock once a second
	and.w	timer,d0
	bne.s	.f
	bsr	draw_top
.f	bsr	frame
	tst.w	timer
	bne.s	.loop
	moveq	#CS_TIMEUP,d0
	moveq	#64,d1
	jsr	K_CSFX(a5)
	moveq	#0,d0
	move.w	score,d0
	bsr	result_pts
	lea	CX_RESULT(a4),a0
	bsr	message
	bra	ev_done

; you: the joystick (not while wiping), the crossings
move_me:
	tst.w	wipe
	beq.s	.go
	subq.w	#1,wipe
	rts
.go	move.w	held,d0
	moveq	#0,d1			; moved?
	btst	#J_LEFT,d0
	beq.s	.nl
	subq.w	#SPEED,px
	moveq	#1,d1
.nl	btst	#J_RIGHT,d0
	beq.s	.nr
	addq.w	#SPEED,px
	moveq	#1,d1
.nr	btst	#J_UP,d0
	beq.s	.nu
	subq.w	#SPEED,py
	moveq	#1,d1
.nu	btst	#J_DOWN,d0
	beq.s	.nd
	addq.w	#SPEED,py
	moveq	#1,d1
.nd	add.w	d1,walk
	cmp.w	#X0,px			; the walls
	bge.s	.a
	move.w	#X0,px
.a	cmp.w	#X1,px
	ble.s	.b
	move.w	#X1,px
.b	cmp.w	#Y0,py
	bge.s	.c
	move.w	#Y0,py
.c	cmp.w	#Y1,py
	ble.s	.d
	move.w	#Y1,py
.d	tst.w	goal			; across?
	beq.s	.left
	cmp.w	#ZR,px
	blt.s	.x
	clr.w	goal
	bra.s	.got
.left	cmp.w	#ZL,px
	bgt.s	.x
	move.w	#1,goal
.got	add.w	#10,score
	lea	snd_ding,a0
	moveq	#56,d1
	jsr	K_SFX(a5)
	bsr	draw_top
.x	rts

; throw: a new pie now and then, from the top or the bottom
throw:	subq.w	#1,next
	bpl.s	.x
	move.w	every,d0		; next: every/2 .. every*3/2
	jsr	K_RAND(a5)
	move.w	every,d1
	lsr.w	#1,d1
	add.w	d1,d0
	move.w	d0,next
	lea	pies,a0
	moveq	#NPIES-1,d7
.f	tst.w	P_DY(a0)
	beq.s	.new
	addq.l	#P_SIZE,a0
	dbf	d7,.f
.x	rts
.new	move.w	#ZR-ZL-8,d0		; x: somewhere over the sand
	jsr	K_RAND(a5)
	add.w	#ZL+12,d0
	move.w	d0,P_X(a0)
	moveq	#3,d0			; the speed: 2 .. 4 (5 on hard)
	add.w	CX_LEVEL(a4),d0
	jsr	K_RAND(a5)
	addq.w	#2,d0
	move.w	d0,d6
	moveq	#2,d0
	jsr	K_RAND(a5)
	tst.w	d0
	beq.s	.top
	move.w	#228,P_Y(a0)		; from the bottom: up
	neg.w	d6
	bra.s	.s
.top	move.w	#28,P_Y(a0)
.s	move.w	d6,P_DY(a0)
	lea	snd_honk,a0
	moveq	#20,d1
	jsr	K_SFX(a5)
	rts

; the pies fly; one in the face?
move_pies:
	lea	pies,a2
	moveq	#NPIES-1,d7
.l	move.w	P_DY(a2),d0
	beq.s	.n
	add.w	d0,P_Y(a2)
	move.w	P_Y(a2),d1
	cmp.w	#24,d1			; gone
	blt.s	.gone
	cmp.w	#232,d1
	bgt.s	.gone
	tst.w	wipe			; (not twice)
	bne.s	.n
	move.w	P_X(a2),d0		; |pie x - you x| < 10, |pie y + 6 - you y - 8| < 8
	sub.w	px,d0
	bpl.s	.ax
	neg.w	d0
.ax	cmp.w	#10,d0
	bge.s	.n
	move.w	P_Y(a2),d0
	subq.w	#2,d0
	sub.w	py,d0
	bpl.s	.ay
	neg.w	d0
.ay	cmp.w	#8,d0
	bge.s	.n
	move.w	#WIPE,wipe		; splat!
	sub.w	#3,score
	bpl.s	.s
	clr.w	score
.s	lea	snd_splat,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	bsr	draw_top
.gone	clr.w	P_DY(a2)
.n	addq.l	#P_SIZE,a2
	dbf	d7,.l
	rts

draw_top:
	movem.l	d0-d3/a0-a1,-(sp)
	lea	strbuf,a1
	lea	s_time,a0
	bsr	cat
	move.w	timer,d0
	bsr	time_text
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
	move.b	#' ',(a1)+
	move.b	#' ',(a1)+
	clr.b	(a1)
	lea	strbuf,a0
	move.w	#200,d0
	moveq	#3,d2
	bsr	top_text
	movem.l	(sp)+,d0-d3/a0-a1
	rts

frame:
	movem.l	d0-d3/d7/a0/a2,-(sp)
	jsr	K_BEGIN(a5)
	lea	pies,a2			; the pies
	moveq	#NPIES-1,d7
.p	tst.w	P_DY(a2)
	beq.s	.np
	lea	pi_tab,a0
	moveq	#4,d0
	and.w	P_Y(a2),d0
	move.l	(a0,d0.w),a0
	move.w	P_X(a2),d0
	move.w	P_Y(a2),d1
	jsr	K_BOB(a5)
.np	addq.l	#P_SIZE,a2
	dbf	d7,.p
	moveq	#4,d0			; you: walking, or the pie in the face
	tst.w	wipe
	bne.s	.w
	move.w	walk,d0
	lsr.w	#2,d0
	and.w	#3,d0
.w	lsl.w	#2,d0
	lea	pw_tab,a0
	move.l	(a0,d0.w),a0
	move.w	px,d0
	move.w	py,d1
	jsr	K_BOB(a5)
	jsr	K_END(a5)
	bsr	read_input
	movem.l	(sp)+,d0-d3/d7/a0/a2
	rts

	include	"evcommon.s"

	section	data,data
s_help		dc.b	'CROSS TO THE OTHER SIDE AND BACK!',0
s_time		dc.b	'TIME ',0
s_score		dc.b	'SCORE ',0
	even
	include	"pie_data.i"
bg_rle	incbin	"pie_bg.rle"
	even
	section	bss,bss
pies		ds.b	NPIES*P_SIZE
px		ds.w	1
py		ds.w	1
score		ds.w	1
wipe		ds.w	1
walk		ds.w	1
goal		ds.w	1
timer		ds.w	1
every		ds.w	1
next		ds.w	1
	even
	section	chip,data_c
pie_chip	incbin	"pie_chip.bin"
