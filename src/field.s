;------------------------------------------------------------------------------
;  field.s - the field events of Stronkie's Olympics (long jump, javelin,
;  toilet paper throw): three attempts, the best one counts.
;  Run (left/right in turn), fire at the line to jump / throw, hold fire for
;  the angle, let go.  Over the line: foul.
;  The event sets: MAXD (cm at top speed and 45 degrees), WASTE (cm lost per
;  pixel before the line), LINE_X, WINDY (1: toilet paper), and the routines
;  fly (d0.l = the distance in cm: show it) and fld_frame (one frame).
;  It uses race.s for the run-up (race_run, race_x).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
TOP		equ	22			; the top speed (race_run)

fld_main:
	clr.l	best
	move.w	#1,attempt
.att	bsr	race_init		; (the run-up: the race engine)
	st	running
	clr.w	p_up
	moveq	#6,d0
	move.l	d0,p_fr
	clr.w	angle
	clr.w	wind
	moveq	#WINDY,d0
	beq.s	.nw
	moveq	#11,d0			; the wind: -5 .. +5
	jsr	K_RAND(a5)
	subq.w	#5,d0
	move.w	d0,wind
.nw	bsr	fld_top
	lea	s_f_run,a0
	bsr	message_small
	; the run-up
.run	moveq	#5,d1
	moveq	#TOP,d2
	bsr	race_run
	moveq	#-1,d0
	tst.w	p_spd
	bne.s	.mv
	moveq	#6,d0
.mv	move.l	d0,p_fr
	bsr	fld_frame
	tst.b	p_done			; over the line and on: foul
	bne	.foul
	move.w	pressed,d0
	btst	#J_FIRE,d0
	beq.s	.run
	tst.w	p_spd
	beq.s	.run
	; the jump / the throw: where?
	move.l	p_pos,d0
	bsr	race_x
	cmp.w	#LINE_X,d0
	bhi	.foul
	move.w	#LINE_X,d1
	sub.w	d0,d1
	mulu	#WASTE,d1
	move.l	d1,waste
	; the angle: it rises while fire is held
	moveq	#7,d0
	move.l	d0,p_fr
	move.w	#10,angle
	lea	snd_whoosh,a0
	moveq	#40,d1
	jsr	K_SFX(a5)
.ang	bsr	fld_mid
	bsr	fld_frame
	move.w	held,d0
	btst	#J_FIRE,d0
	beq.s	.go
	addq.w	#2,angle
	cmp.w	#80,angle
	blo.s	.ang
.go	; the distance: MAXD * (speed/top)^2 * sin(2 angle) - waste
	moveq	#0,d0
	move.w	p_spd,d0
	mulu	d0,d0
	divu	#(TOP*16)*(TOP*16)/256,d0	; (speed/top)^2 in 1/256
	and.l	#$ffff,d0
	mulu	#MAXD,d0
	moveq	#0,d1			; sin(2a) in 1/256
	move.w	angle,d1
	lea	sin_tab,a0
	move.b	(a0,d1.w),d1
	bsr	mul32
	clr.w	d0			; (/ 65536)
	swap	d0
	move.w	wind,d1			; the wind: +-5% a metre a second
	beq.s	.nwd
	ext.l	d1
	move.l	d0,-(sp)
	muls	d0,d1
	divs	#20,d1
	ext.l	d1
	move.l	(sp)+,d0
	add.l	d1,d0
.nwd	sub.l	waste,d0
	bpl.s	.pos
	moveq	#0,d0
.pos	move.l	d0,dist
	bsr	fly			; the event shows it
	move.l	dist,d0
	cmp.l	best,d0
	bls.s	.nb
	move.l	d0,best
.nb	lea	strbuf,a1
	move.l	dist,d0
	bsr	hund_text
	bsr	cat
	lea	s_c_m,a0
	bsr	cat
	lea	strbuf,a0
	bsr	message
	moveq	#CS_CLAP,d0
	moveq	#48,d1
	jsr	K_CSFX(a5)
	bra.s	.next
.foul	moveq	#CS_BUZZER,d0
	moveq	#56,d1
	jsr	K_CSFX(a5)
	lea	s_f_foul,a0
	bsr	message
	moveq	#-1,d0
	move.l	d0,p_fr
	clr.w	p_spd
.next	bsr	fld_top
	moveq	#60,d0
	moveq	#1,d1
	jsr	K_WAIT(a5)
	bsr	fld_reset		; (the event: back to the run-up screen)
	addq.w	#1,attempt
	cmp.w	#3,attempt
	bls	.att
	; the result: the best attempt
	move.l	best,d0
	lea	s_c_m,a0
	bsr	result_hund
	lea	CX_RESULT(a4),a0
	bsr	message
	move.l	best,d0
	beq.s	.x
	moveq	#CS_GREAT,d0
	moveq	#64,d1
	jsr	K_CSFX(a5)
.x	rts

; mul32: d0.l * d1.l -> d0.l (unsigned, d1 < 65536)
mul32:	movem.l	d2-d3,-(sp)
	move.l	d0,d2
	swap	d2
	mulu	d1,d2
	swap	d2
	clr.w	d2
	mulu	d1,d0
	add.l	d2,d0
	movem.l	(sp)+,d2-d3
	rts

; the top bar: ATTEMPT n, the angle (or the wind), the best
fld_top:
	movem.l	d0-d3/a0-a1,-(sp)
	lea	strbuf,a1
	lea	s_f_att,a0
	bsr	cat
	moveq	#0,d0
	move.w	attempt,d0
	bsr	catnum
	lea	strbuf,a0
	moveq	#8,d0
	moveq	#3,d2
	bsr	top_text
	bsr.s	fld_mid
	lea	strbuf,a1
	lea	s_f_best,a0
	bsr	cat
	move.l	best,d0
	bsr	hund_text
	bsr	cat
	lea	s_c_m,a0
	bsr	cat
	lea	strbuf,a0
	move.w	#192,d0
	moveq	#3,d2
	bsr	top_text
	movem.l	(sp)+,d0-d3/a0-a1
	rts

; fld_mid: the middle of the top bar: ANGLE n, or WIND +n (toilet paper)
fld_mid:
	movem.l	d0-d3/a0-a1,-(sp)
	lea	strbuf,a1
	move.w	angle,d0
	beq.s	.wnd
	lea	s_f_ang,a0
	bsr	cat
	ext.l	d0
	bsr	catnum
	bra.s	.sh
.wnd	moveq	#WINDY,d0
	beq.s	.sh
	lea	s_f_wind,a0
	bsr	cat
	move.w	wind,d0
	move.b	#'+',(a1)+
	tst.w	d0
	bpl.s	.wp
	move.b	#'-',-1(a1)
	neg.w	d0
.wp	ext.l	d0
	bsr	catnum
.sh	lea	s_f_pad,a0
	bsr	cat
	lea	strbuf,a0		; (padded: the old text goes)
	clr.b	10(a0)
	moveq	#96,d0
	moveq	#2,d2
	bsr	top_text
	movem.l	(sp)+,d0-d3/a0-a1
	rts

	section	data,data
s_f_run		dc.b	'RUN, FIRE AT THE LINE, HOLD FOR ANGLE',0
s_f_foul	dc.b	'FOUL!',0
s_f_att		dc.b	'ATTEMPT ',0
s_f_ang		dc.b	'ANGLE ',0
s_f_wind	dc.b	'WIND ',0
s_f_best	dc.b	'BEST ',0
s_f_pad		dc.b	'          ',0
	even
sin_tab		; sin(2a) * 255 for a = 0..90 (a byte each)
	dc.b	0,9,18,27,35,44,53,62,70,79,87,96,104,112,120,127,135,143,150,157
	dc.b	164,171,177,183,190,195,201,206,211,216,221,225,229,233,236,240,243,245,247,249
	dc.b	251,253,254,254,255,255,255,254,254,253,251,249,247,245,243,240,236,233,229,225
	dc.b	221,216,211,206,201,195,190,183,177,171,164,157,150,143,135,127,120,112,104,96
	dc.b	87,79,70,62,53,44,35,27,18,9,0
	even
	section	bss,bss
best		ds.l	1
dist		ds.l	1
waste		ds.l	1
attempt		ds.w	1
angle		ds.w	1
wind		ds.w	1
	section	code,code
