;------------------------------------------------------------------------------
;  ev_archery.s - ARCHERY: six arrows at the target.  The sight sways: hold
;  it on the gold with the joystick, mind the wind, fire to shoot.
;  An event of Stronkie's Olympics (Archery.evt; see kernel.i).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"arc_equ.i"

CPU_LO		equ	35			; the others: 35 .. 55 points
CPU_HI		equ	55
NARROWS		equ	6
STEER		equ	20			; the joystick: 1/16 pixels a tick
WIND_PX		equ	4			; pixels per wind step

	section	code,code
	bra.w	entry
	dc.l	'SOEV'
	dc.w	CPU_LO,CPU_HI
	dc.w	0

entry:	movem.l	d1-d7/a0-a6,-(sp)
	move.l	sp,ev_sp
	clr.l	fx_bob
	move.w	#-100,sx
	lea	pal_arc,a0
	lea	bg_rle,a1
	bsr	ev_start
	clr.w	score
	move.w	#1,arrow_n
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
	; the sway: easy 6, normal 10, hard 14
	move.w	CX_LEVEL(a4),d0
	lsl.w	#2,d0
	addq.w	#6,d0
	move.w	d0,sway
.arrow	moveq	#7,d0			; the wind: -3 .. +3
	jsr	K_RAND(a5)
	subq.w	#3,d0
	move.w	d0,wind
	moveq	#81,d0			; the sight starts somewhere off the gold
	jsr	K_RAND(a5)
	sub.w	#40,d0
	asl.w	#4,d0
	move.w	d0,ax
	moveq	#61,d0
	jsr	K_RAND(a5)
	sub.w	#30,d0
	asl.w	#4,d0
	move.w	d0,ay
	clr.w	vx
	clr.w	vy
	clr.w	aimt
	bsr	draw_top
	lea	sight,a0
	move.l	a0,fx_bob
.aim	addq.w	#1,aimt
	moveq	#15,d0			; a new sway now and then
	and.w	aimt,d0
	bne.s	.sw
	move.w	sway,d0
	add.w	d0,d0
	addq.w	#1,d0
	jsr	K_RAND(a5)
	sub.w	sway,d0
	move.w	d0,vx
	move.w	sway,d0
	add.w	d0,d0
	addq.w	#1,d0
	jsr	K_RAND(a5)
	sub.w	sway,d0
	move.w	d0,vy
.sw	move.w	vx,d0
	add.w	d0,ax
	move.w	vy,d0
	add.w	d0,ay
	move.w	held,d0			; the joystick
	btst	#J_LEFT,d0
	beq.s	.nl
	sub.w	#STEER,ax
.nl	btst	#J_RIGHT,d0
	beq.s	.nr
	add.w	#STEER,ax
.nr	btst	#J_UP,d0
	beq.s	.nu
	sub.w	#STEER,ay
.nu	btst	#J_DOWN,d0
	beq.s	.nd
	add.w	#STEER,ay
.nd	lea	ax,a0			; keep it near the target
	bsr	clamp
	lea	ay,a0
	bsr	clamp
	bsr	sight_xy
	bsr	frame
	move.w	pressed,d0
	btst	#J_FIRE,d0
	bne.s	.shoot
	cmp.w	#250,aimt		; (10 seconds: it goes by itself)
	blo	.aim
.shoot	; where it lands: the sight + the wind (+- a pixel)
	move.w	ax,d6
	asr.w	#4,d6
	move.w	wind,d0
	muls	#WIND_PX,d0
	add.w	d0,d6
	moveq	#3,d0
	jsr	K_RAND(a5)
	subq.w	#1,d0
	add.w	d0,d6			; d6 = dx
	move.w	ay,d7
	asr.w	#4,d7
	moveq	#3,d0
	jsr	K_RAND(a5)
	subq.w	#1,d0
	add.w	d0,d7			; d7 = dy
	lea	snd_twang,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	; the flight: from the bottom to the target, smaller and smaller
	moveq	#0,d5
.fl	move.w	d6,d0			; x = 160 + dx * t / 8
	muls	d5,d0
	asr.w	#3,d0
	add.w	#CX-8,d0
	move.w	d0,sx
	move.w	d7,d0			; y = 236 + (CY + dy - 236) * t / 8
	add.w	#CY-236,d0
	muls	d5,d0
	asr.w	#3,d0
	add.w	#236-8,d0
	move.w	d0,sy
	move.w	d5,d0
	lsr.w	#1,d0
	cmp.w	#3,d0
	bls.s	.f3
	moveq	#3,d0
.f3	lsl.w	#2,d0
	lea	fly_tab,a0
	move.l	(a0,d0.w),fx_bob
	bsr	frame
	addq.w	#1,d5
	cmp.w	#9,d5
	blo.s	.fl
	clr.l	fx_bob
	lea	arrow,a0		; in the target (the tip at the spot)
	move.w	d6,d0
	add.w	#CX-7,d0
	move.w	d7,d1
	add.w	#CY-7,d1
	jsr	K_STAMP(a5)
	lea	snd_thunk,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	; the points: 10 - (distance / RING), 0 outside
	muls	d6,d6
	muls	d7,d7
	add.l	d7,d6			; d6 = distance^2
	moveq	#0,d1			; n rings out
	moveq	#RING,d2
.r	move.l	d2,d0
	mulu	d0,d0
	cmp.l	d0,d6
	blo.s	.in
	add.w	#RING,d2
	addq.w	#1,d1
	cmp.w	#10,d1
	blo.s	.r
.in	moveq	#10,d0
	sub.w	d1,d0
	add.w	d0,score
	lea	strbuf,a1		; "+8"
	move.b	#'+',(a1)+
	ext.l	d0
	bsr	catnum
	lea	strbuf,a0
	bsr	message
	cmp.w	#10,d0
	bne.s	.n10
	moveq	#CS_CHEER,d0
	moveq	#48,d1
	jsr	K_CSFX(a5)
.n10	bsr	draw_top
	moveq	#40,d0
	bsr	frames
	bsr	clear_msg
	addq.w	#1,arrow_n
	cmp.w	#NARROWS,arrow_n
	bls	.arrow
	moveq	#0,d0
	move.w	score,d0
	bsr	result_pts
	lea	CX_RESULT(a4),a0
	bsr	message
	moveq	#CS_GREAT,d0
	moveq	#64,d1
	jsr	K_CSFX(a5)
	bra	ev_done

; clamp: (a0).w to -90 .. 90 pixels (1/16)
clamp:	cmp.w	#-90*16,(a0)
	bge.s	.a
	move.w	#-90*16,(a0)
.a	cmp.w	#90*16,(a0)
	ble.s	.b
	move.w	#90*16,(a0)
.b	rts

sight_xy:
	move.w	ax,d0
	asr.w	#4,d0
	add.w	#CX-7,d0
	move.w	d0,sx
	move.w	ay,d0
	asr.w	#4,d0
	add.w	#CY-7,d0
	move.w	d0,sy
	rts

; the top bar: ARROW n, the wind, the score
draw_top:
	movem.l	d0-d3/a0-a1,-(sp)
	lea	strbuf,a1
	lea	s_arrow,a0
	bsr	cat
	moveq	#0,d0
	move.w	arrow_n,d0
	bsr	catnum
	lea	s_of6,a0
	bsr	cat
	lea	strbuf,a0
	moveq	#8,d0
	moveq	#3,d2
	bsr	top_text
	lea	s_wind,a0		; WIND: <<< or >>> or 0
	lea	strbuf,a1
	bsr	cat
	move.w	wind,d0
	bne.s	.w
	move.b	#'0',(a1)+
	bra.s	.we
.w	moveq	#'>',d1
	tst.w	d0
	bpl.s	.wl
	moveq	#'<',d1
	neg.w	d0
.wl	move.b	d1,(a1)+
	subq.w	#1,d0
	bne.s	.wl
.we	move.b	#' ',(a1)+
	move.b	#' ',(a1)+
	move.b	#' ',(a1)+
	clr.b	(a1)
	lea	strbuf,a0
	moveq	#112,d0
	moveq	#2,d2
	bsr	top_text
	lea	strbuf,a1
	lea	s_score,a0
	bsr	cat
	moveq	#0,d0
	move.w	score,d0
	bsr	catnum
	lea	strbuf,a0
	move.w	#216,d0
	moveq	#3,d2
	bsr	top_text
	movem.l	(sp)+,d0-d3/a0-a1
	rts

frame:
	movem.l	d0-d3/a0,-(sp)
	jsr	K_BEGIN(a5)
	move.l	fx_bob,d0
	beq.s	.n
	move.l	d0,a0
	move.w	sx,d0
	bpl.s	.x
	moveq	#0,d0
.x	move.w	sy,d1
	jsr	K_BOB(a5)
.n	jsr	K_END(a5)
	bsr	read_input
	movem.l	(sp)+,d0-d3/a0
	rts

	include	"evcommon.s"

	section	data,data
s_help		dc.b	'STEER THE SIGHT TO THE GOLD, FIRE!',0
s_arrow		dc.b	'ARROW ',0
s_of6		dc.b	'/6',0
s_wind		dc.b	'WIND ',0
s_score		dc.b	'SCORE ',0
	even
	include	"arc_data.i"
bg_rle	incbin	"arc_bg.rle"
	even
	section	bss,bss
fx_bob		ds.l	1
sx		ds.w	1
sy		ds.w	1
ax		ds.w	1
ay		ds.w	1
vx		ds.w	1
vy		ds.w	1
aimt		ds.w	1
sway		ds.w	1
wind		ds.w	1
score		ds.w	1
arrow_n		ds.w	1
	even
	section	chip,data_c
arc_chip	incbin	"arc_chip.bin"
