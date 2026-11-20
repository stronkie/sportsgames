;------------------------------------------------------------------------------
;  fieldcommon.s - the run-up screen of the field events: the colours, the
;  athlete (p_pos, p_fr / running frames, p_up), one frame.
;  The event may set hook_frame (drawn before the athlete) and fx_bob /
;  fx_x / fx_y (one more bob: the javelin, the roll; fx_bob 0 = none).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
fld_setup:
	lea	pm_tab,a0
	tst.w	CX_WOMAN(a4)
	beq.s	.m
	lea	pw_tab,a0
.m	move.l	a0,pl_tab
	clr.l	hook_frame
	clr.l	fx_bob
	clr.w	p_up
	lea	pal_field,a0
	lea	bg_rle,a1
	bra	ev_start

; run_frame: d0.l = position, d1 = moving -> d0 = the frame (0-5 running)
run_frame:
	tst.w	d1
	bne.s	.m
	moveq	#0,d0
	rts
.m	lsr.l	#7,d0
	divu	#6,d0
	swap	d0
	and.l	#$ffff,d0
	rts

fld_frame:
frame:
	movem.l	d0-d3/a0,-(sp)
	jsr	K_BEGIN(a5)
	move.l	hook_frame,d0
	beq.s	.nh
	move.l	d0,a0
	jsr	(a0)
.nh	tst.b	hide_me
	bne.s	.fx
	move.l	p_fr,d0
	bpl.s	.pf
	move.l	p_pos,d0
	move.w	p_spd,d1
	bsr	run_frame
.pf	lsl.w	#2,d0
	move.l	pl_tab,a0
	move.l	(a0,d0.w),a0
	move.l	p_pos,d0
	bsr	race_x
	sub.w	#16,d0
	bpl.s	.p0
	moveq	#0,d0
.p0	move.w	#LANE-47,d1
	sub.w	p_up,d1
	jsr	K_BOB(a5)
.fx	move.l	fx_bob,d0
	beq.s	.nf
	move.l	d0,a0
	move.w	fx_x,d0
	bpl.s	.f0
	moveq	#0,d0
.f0	move.w	fx_y,d1
	jsr	K_BOB(a5)
.nf	jsr	K_END(a5)
	bsr	read_input
	movem.l	(sp)+,d0-d3/a0
	rts

	section	bss,bss
pl_tab		ds.l	1
hook_frame	ds.l	1
fx_bob		ds.l	1
p_fr		ds.l	1		; -1: running frames
fx_x		ds.w	1
fx_y		ds.w	1
p_up		ds.w	1
hide_me		ds.b	1
	even
	section	code,code
