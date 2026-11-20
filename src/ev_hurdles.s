;------------------------------------------------------------------------------
;  ev_hurdles.s - HURDLES: 110 metres, 10 hurdles, against a rival.
;  An event of Stronkie's Olympics (Hurdles.evt; see kernel.i, race.s).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"hur_equ.i"

RACE_LEN	equ	(FINISH_X-START_X)*16
RACE_SHIFT	equ	4
CPU_LO		equ	1350			; the rival: 13.50 .. 17.00 s
CPU_HI		equ	1700
NH		equ	10
JUMP_T		equ	14

	section	code,code
	bra.w	entry
	dc.l	'SOEV'
	dc.w	CPU_LO,CPU_HI
	dc.w	1

entry:	movem.l	d1-d7/a0-a6,-(sp)
	move.l	sp,ev_sp
	move.l	#-1,p_fr
	move.l	#-1,c_fr
	clr.w	p_up
	clr.w	c_up
	clr.w	jt
	lea	hdown,a0
	moveq	#NH-1,d0
.c	clr.b	(a0)+
	dbf	d0,.c
	move.l	#draw_hurdles,hook_frame
	bsr	race_setup
	moveq	#0,d7			; the rival's hurdles: in the background
.s	lea	hx,a0
	move.w	d7,d0
	add.w	d0,d0
	move.w	(a0,d0.w),d0
	subq.w	#8,d0
	move.w	#LANE_C-25,d1
	lea	hurdle_up,a0
	jsr	K_STAMP(a5)
	addq.w	#1,d7
	cmp.w	#NH,d7
	blo.s	.s
	bsr	race_init
	moveq	#1,d0
	bsr	frames
	jsr	K_FADEIN(a5)
	lea	v_title,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#20,d0
	bsr	frames
	bsr	race_countdown
	lea	snd_gun,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
.run	moveq	#5,d1
	moveq	#22,d2
	bsr	race_run
	bsr	jumps
	bsr	race_tick
	bsr	rival_jumps
	bsr	frame
	tst.b	p_done
	beq.s	.run
	clr.w	p_up
	move.l	#-1,p_fr
	bsr	race_finish
	bra	ev_done

; jumps: fire jumps; a hurdle you don't clear falls and slows you down
jumps:
	tst.w	jt
	bne.s	.air
	btst	#J_FIRE,pressed+1
	beq.s	.hit
	tst.b	p_done
	bne.s	.hit
	move.w	#1,jt
.air	move.w	jt,d0			; up: 4 * 20 * t (T-t) / T^2
	moveq	#JUMP_T,d1
	sub.w	d0,d1
	mulu	d1,d0
	mulu	#80,d0
	divu	#JUMP_T*JUMP_T,d0
	move.w	d0,p_up
	move.l	#7,p_fr
	addq.w	#1,jt
	cmp.w	#JUMP_T,jt
	bls.s	.hit
	clr.w	jt
	clr.w	p_up
	move.l	#-1,p_fr
.hit	move.l	p_pos,d0		; at a hurdle, too low?
	bsr	race_x
	moveq	#0,d7
.l	lea	hdown,a0
	tst.b	(a0,d7.w)
	bne.s	.n
	lea	hx,a0
	move.w	d7,d1
	add.w	d1,d1
	move.w	(a0,d1.w),d1
	sub.w	d0,d1
	cmp.w	#-2,d1
	blt.s	.n
	cmp.w	#3,d1
	bgt.s	.n
	cmp.w	#10,p_up
	bhs.s	.n
	lea	hdown,a0		; knocked over
	st	(a0,d7.w)
	move.w	p_spd,d1
	lsr.w	#1,d1
	move.w	d1,p_spd
	lea	snd_clatter,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
.n	addq.w	#1,d7
	cmp.w	#NH,d7
	blo.s	.l
	rts

; rival_jumps: the rival flies over its hurdles
rival_jumps:
	clr.w	c_up
	move.l	#-1,c_fr
	move.l	c_pos,d0
	lsr.l	#8,d0
	bsr	race_x
	moveq	#NH-1,d7
	lea	hx,a0
.l	move.w	(a0)+,d1
	sub.w	d0,d1			; distance to it
	cmp.w	#-12,d1
	blt.s	.n
	cmp.w	#12,d1
	bgt.s	.n
	muls	d1,d1			; 20 - d^2 * 20 / 144
	mulu	#20,d1
	divu	#144,d1
	moveq	#20,d2
	sub.w	d1,d2
	move.w	d2,c_up
	move.l	#7,c_fr
	rts
.n	dbf	d7,.l
	rts

draw_hurdles:
	movem.l	d4/a1,-(sp)
	moveq	#0,d4
.l	lea	hurdle_up,a0
	lea	hdown,a1
	tst.b	(a1,d4.w)
	beq.s	.u
	lea	hurdle_down,a0
.u	lea	hx,a1
	move.w	d4,d0
	add.w	d0,d0
	move.w	(a1,d0.w),d0
	subq.w	#8,d0
	move.w	#LANE_P-25,d1
	jsr	K_BOB(a5)
	addq.w	#1,d4
	cmp.w	#NH,d4
	blo.s	.l
	movem.l	(sp)+,d4/a1
	rts

	include	"racecommon.s"
	include	"evcommon.s"
	include	"race.s"

	section	data,data
hx	dc.w	51,74,97,121,144,167,191,214,237,260
	include	"hur_data.i"
bg_rle	incbin	"hur_bg.rle"
	even
	section	chip,data_c
hur_chip	incbin	"hur_chip.bin"
	section	bss,bss
jt	ds.w	1
hdown	ds.b	NH
	even
