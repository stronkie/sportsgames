;------------------------------------------------------------------------------
;  ev_rootbeer.s - ROOT BEER SPRINT: drink, run, don't hiccup.
;  Hold fire to drink the mug empty (let go now and then: drink too fast and
;  you get the hiccups), then left/right in turn to run to the finish.
;  An event of Stronkie's Olympics (RootBeer.evt; see kernel.i, race.s).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"rbr_equ.i"

RACE_LEN	equ	(FINISH_X-START_X)*16
RACE_SHIFT	equ	4
CPU_LO		equ	1400			; the rival: 14.00 .. 22.00 s (with the drinking)
CPU_HI		equ	2200
MUG_FULL	equ	80			; ticks of drinking
FIZZ_MAX	equ	100
HIC_TIME	equ	40

	section	code,code
	bra.w	entry
	dc.l	'SOEV'
	dc.w	CPU_LO,CPU_HI
	dc.w	1			; (lower is better)

entry:	movem.l	d1-d7/a0-a6,-(sp)
	move.l	sp,ev_sp
	move.l	#-1,p_fr
	move.l	#-1,c_fr
	clr.w	c_up
	clr.w	p_up
	clr.l	hook_frame
	move.w	#MUG_FULL,mug
	clr.w	fizz
	clr.w	hic_t
	clr.b	drunk
	move.l	#-1,shown
	bsr	race_setup
	bsr	race_init
	moveq	#0,d0			; the rival drinks about a third of its time
	move.w	cpu_time,d0
	lsr.w	#2,d0
	mulu	#5,d0
	lsr.l	#4,d0
	move.w	d0,c_wait
	bsr	race_speed
	bsr	draw_meters
	moveq	#1,d0
	bsr	frames
	jsr	K_FADEIN(a5)
	lea	v_title,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	s_hold,a0
	bsr	message_small
	moveq	#50,d0
	bsr	frames
	bsr	race_countdown
	lea	snd_gun,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#6,d0
	move.l	d0,p_fr
.loop	bsr	rival_frame
	tst.b	drunk
	bne	.run
	tst.w	hic_t			; the hiccups: wait
	beq.s	.nh
	subq.w	#1,hic_t
	bne	.tick
	moveq	#6,d0
	move.l	d0,p_fr
	bra	.tick
.nh	move.w	held,d0
	btst	#J_FIRE,d0
	beq	.rest
	moveq	#7,d0			; drinking
	move.l	d0,p_fr
	subq.w	#1,mug
	moveq	#7,d0
	and.w	mug,d0
	bne.s	.ng
	lea	snd_gulp,a0
	moveq	#48,d1
	jsr	K_SFX(a5)
.ng	addq.w	#2,fizz
	cmp.w	#FIZZ_MAX,fizz
	blo.s	.nf
	move.w	#HIC_TIME,hic_t		; hic!
	move.w	#60,fizz
	moveq	#8,d0
	move.l	d0,p_fr
	lea	snd_hic,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	lea	s_hic,a0
	bsr	message
	move.w	#25,go_msg
.nf	tst.w	mug
	bne	.tick
	st	drunk			; empty: burp and run
	clr.w	fizz
	lea	snd_burp,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	move.l	#-1,p_fr
	lea	s_run,a0
	bsr	message
	move.w	#25,go_msg
	bra.s	.tick
.rest	moveq	#6,d0			; not drinking: the fizz goes down
	move.l	d0,p_fr
	subq.w	#4,fizz
	bpl.s	.tick
	clr.w	fizz
	bra.s	.tick
.run	moveq	#5,d1			; a step adds 5, the top speed is 22
	moveq	#22,d2
	bsr	race_run
.tick	bsr	race_tick
	bsr	frame
	bsr	draw_meters
	tst.b	p_done
	beq	.loop
	moveq	#-1,d0
	move.l	d0,c_fr
	bsr	race_finish
	bra	ev_done

; the rival: drinking (a hiccup now and then), then running
rival_frame:
	moveq	#-1,d0
	tst.b	running
	beq.s	.s
	tst.w	c_wait
	beq.s	.s
	moveq	#7,d0
	moveq	#63,d1
	and.w	c_wait,d1
	cmp.w	#50,d1
	blo.s	.s
	moveq	#8,d0
.s	move.l	d0,c_fr
	rts

; the MUG and HIC meters in the strip (8 blocks each, only when they change)
draw_meters:
	movem.l	d0-d5,-(sp)
	moveq	#0,d0
	move.w	mug,d0
	lsl.w	#3,d0
	add.w	#MUG_FULL-1,d0
	divu	#MUG_FULL,d0
	move.w	d0,d5
	swap	d5
	moveq	#0,d0
	move.w	fizz,d0
	lsl.w	#3,d0
	divu	#FIZZ_MAX,d0
	cmp.w	#8,d0
	bls.s	.f8
	moveq	#8,d0
.f8	move.w	d0,d5
	cmp.l	shown,d5
	beq.s	.x
	move.l	d5,shown
	swap	d5
	move.w	#MUG_X,d0		; the mug: brown
	move.w	d5,d1
	moveq	#14,d2
	bsr.s	bar
	swap	d5
	move.w	#HIC_X,d0		; the fizz: yellow, red when close
	move.w	d5,d1
	moveq	#3,d2
	cmp.w	#6,d1
	blo.s	.y
	moveq	#4,d2
.y	bsr.s	bar
.x	movem.l	(sp)+,d0-d5
	rts
; bar: d0 = x, d1 = blocks full (0-8), d2 = colour
bar:	movem.l	d0-d4,-(sp)
	move.w	d2,d4
	move.w	d1,d2
	lsl.w	#3,d2
	beq.s	.e
	move.w	#BAR_Y,d1
	moveq	#6,d3
	jsr	K_FILL(a5)
.e	movem.l	(sp),d0-d4
	move.w	d1,d2
	lsl.w	#3,d2
	add.w	d2,d0
	neg.w	d2
	add.w	#64,d2
	beq.s	.x
	move.w	#BAR_Y,d1
	moveq	#6,d3
	moveq	#16,d4
	jsr	K_FILL(a5)
.x	movem.l	(sp)+,d0-d4
	rts

	include	"racecommon.s"
	include	"evcommon.s"
	include	"race.s"

	section	data,data
s_hold		dc.b	'HOLD FIRE TO DRINK - NOT TOO FAST!',0
s_hic		dc.b	'HIC!',0
s_run		dc.b	'BURP! RUN!',0
	even
	include	"rbr_data.i"
bg_rle	incbin	"rbr_bg.rle"
	even
	section	bss,bss
shown		ds.l	1
mug		ds.w	1
fizz		ds.w	1
hic_t		ds.w	1
drunk		ds.b	1
	even
	section	chip,data_c
rbr_chip	incbin	"rbr_chip.bin"
