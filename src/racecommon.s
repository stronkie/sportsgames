;------------------------------------------------------------------------------
;  racecommon.s - the screen of the races on the track (100m, hurdles,
;  root beer sprint): the colours, the runners, one frame.
;  The event may set hook_frame (drawn before the runners) to its own routine.
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
race_setup:
	lea	pm_tab,a0
	lea	cm_tab,a1
	tst.w	CX_WOMAN(a4)
	beq.s	.m
	lea	pw_tab,a0
	lea	cw_tab,a1
.m	move.l	a0,pl_tab
	move.l	a1,cp_tab
	lea	pal_race,a0		; the rival's colours in 18-24
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
	; the top bar: TIME, you and the rival
	lea	s_rc_vs,a0
	move.w	#152,d0
	moveq	#2,d2
	bsr	top_text
	lea	strbuf,a1		; your name - their country (10 letters)
	move.l	a4,a0
	bsr	cat
	lea	strbuf,a0
	move.w	#88,d0
	moveq	#3,d2
	bsr	top_text
	lea	strbuf,a1
	move.l	CX_OPPNAME(a4),a0
	moveq	#9,d0
.c	move.b	(a0)+,(a1)+
	dbeq	d0,.c
	clr.b	(a1)
	lea	strbuf,a0
	move.w	#184,d0
	moveq	#2,d2
	bsr	top_text
	rts

; run_frame: d0.l = position (1/16 px), d1 = moving -> d0 = the frame (0-5 running, 6 crouch)
run_frame:
	tst.b	running
	bne.s	.r
	moveq	#6,d0
	rts
.r	tst.w	d1
	bne.s	.m
	moveq	#0,d0
	rts
.m	lsr.l	#7,d0
	divu	#6,d0
	swap	d0
	and.l	#$ffff,d0
	rts

frame:
	movem.l	d0-d3/a0,-(sp)
	jsr	K_BEGIN(a5)
	move.l	hook_frame,d0
	beq.s	.nh
	move.l	d0,a0
	jsr	(a0)
.nh	move.l	c_fr,d0		; the rival: a frame set by the event, or running
	bmi.s	.cr
	move.l	c_pos,d2
	lsr.l	#8,d2
	bra.s	.cd
.cr	move.l	c_pos,d0
	lsr.l	#8,d0
	moveq	#1,d1
	tst.b	c_done
	beq.s	.cm
	moveq	#0,d1
.cm	move.l	d0,d2
	bsr	run_frame
.cd	lsl.w	#2,d0
	move.l	cp_tab,a0
	move.l	(a0,d0.w),a0
	move.l	d2,d0
	bsr	race_x
	sub.w	#16,d0
	bpl.s	.c0
	moveq	#0,d0
.c0	move.w	#LANE_C-47,d1
	sub.w	c_up,d1
	jsr	K_BOB(a5)
	move.l	p_fr,d0			; you: a frame set by the event, or running
	bpl.s	.pf
	move.l	p_pos,d0
	move.w	p_spd,d1
	move.l	d0,-(sp)
	bsr	run_frame
	move.l	(sp)+,d2
	bra.s	.pd
.pf	move.l	p_pos,d2
.pd	lsl.w	#2,d0
	move.l	pl_tab,a0
	move.l	(a0,d0.w),a0
	move.l	d2,d0
	bsr	race_x
	sub.w	#16,d0
	bpl.s	.p0
	moveq	#0,d0
.p0	move.w	#LANE_P-47,d1
	sub.w	p_up,d1
	jsr	K_BOB(a5)
	jsr	K_END(a5)
	bsr	race_time
	bsr	read_input
	movem.l	(sp)+,d0-d3/a0
	rts

	section	data,data
s_rc_vs	dc.b	'-',0
	even
	section	bss,bss
pl_tab		ds.l	1
cp_tab		ds.l	1
hook_frame	ds.l	1
p_fr		ds.l	1		; -1: running frames
c_fr		ds.l	1
p_up		ds.w	1
c_up		ds.w	1
palbuf		ds.w	32
	section	code,code
