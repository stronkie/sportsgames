;------------------------------------------------------------------------------
;  throwfly.s - the flight of the javelin / the toilet roll on the field
;  screen (javelin, toilet paper throw).  ROLL = 1: a rolling toilet roll
;  that leaves a paper trail, 0: a javelin that turns with its flight.
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------

; fly: d0.l = the distance (cm)
fly:	movem.l	d0-d7/a0,-(sp)
	moveq	#7,d0			; the throw
	move.l	d0,p_fr
	moveq	#10,d0
	bsr	frames
	st	hide_me			; the field
	lea	field_rle,a0
	jsr	K_SETBG(a5)
	bsr	fld_top
	move.l	(sp),d0			; d7 = the distance in pixels
	mulu	#PX_M,d0
	divu	#100,d0
	cmp.w	#304,d0
	bls.s	.d0
	move.w	#304,d0
.d0	move.w	d0,d7
	move.w	d7,d6			; d6 = T: 20 + px / 6 ticks
	ext.l	d6
	divu	#6,d6
	add.w	#20,d6
	move.w	d7,d5			; d5 = the height: px * angle / 120, at most 90
	mulu	angle,d5
	divu	#120,d5
	cmp.w	#90,d5
	bls.s	.h
	moveq	#90,d5
.h	moveq	#0,d4			; t
.t	; x = FIELD0 + px * t / T - 16
	move.w	d7,d0
	mulu	d4,d0
	divu	d6,d0
	add.w	#FIELD0-16,d0
	move.w	d0,fx_x
	; y = FIELD_Y - 16 - 8 (T - t) / T - h * 4 t (T - t) / T^2
	move.w	d6,d1
	sub.w	d4,d1			; T - t
	move.w	d1,d2
	lsl.w	#3,d2
	ext.l	d2
	divu	d6,d2
	move.w	d1,d0
	mulu	d4,d0
	lsl.l	#2,d0
	mulu	d5,d0
	divu	d6,d0
	and.l	#$ffff,d0
	divu	d6,d0
	move.w	#FIELD_Y-16,d1
	sub.w	d2,d1
	sub.w	d0,d1
	move.w	d1,fx_y
	; the bob
	moveq	#ROLL,d0
	beq.s	.jav
	moveq	#3,d0			; the roll turns
	and.w	d4,d0
	bra.s	.bob
.jav	move.w	d6,d0			; the angle now: angle * (T - 2t) / T
	sub.w	d4,d0
	sub.w	d4,d0
	muls	angle,d0
	divs	d6,d0
	neg.w	d0			; frame = (60 - a + 7) / 15
	add.w	#67,d0
	bpl.s	.j0
	moveq	#0,d0
.j0	ext.l	d0
	divu	#15,d0
	cmp.w	#7,d0
	bls.s	.bob
	moveq	#7,d0
.bob	lsl.w	#2,d0
	lea	jv_tab,a0
	move.l	(a0,d0.w),a0
	move.l	a0,fx_bob
	moveq	#ROLL,d0		; the paper trail
	beq.s	.nt
	tst.w	d4
	beq.s	.nt
	lea	paper,a0
	move.w	fx_x,d0
	addq.w	#4,d0
	bmi.s	.nt
	move.w	fx_y,d1
	addq.w	#7,d1
	jsr	K_STAMP(a5)
.nt	bsr	frame
	addq.w	#1,d4
	cmp.w	d6,d4
	bls	.t
	; it lands: it stays there
	move.l	fx_bob,a0
	move.w	fx_x,d0
	bpl.s	.s0
	moveq	#0,d0
.s0	move.w	fx_y,d1
	jsr	K_STAMP(a5)
	clr.l	fx_bob
	lea	snd_thud,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#20,d0
	bsr	frames
	movem.l	(sp)+,d0-d7/a0
	rts

; fld_reset: back to the run-up
fld_reset:
	clr.b	hide_me
	clr.l	fx_bob
	moveq	#-1,d0
	move.l	d0,p_fr
	lea	bg_rle,a0
	jsr	K_SETBG(a5)
	rts
