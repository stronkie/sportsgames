;------------------------------------------------------------------------------
;  ev_ceremony.s - the OPENING and the CLOSING CEREMONY of Stronkie's Olympics
;  (loaded from Ceremony.evt).  Called like an event, with d7 = 0 for the
;  opening (the athletes march in, the flame is lit, the doves fly off) or
;  d7 = 1 for the closing (at night: fireworks, the athletes leave, the flame
;  goes out).  Fire or ESC skips it.
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------
	include	"kernel.i"
	include	"cer_equ.i"

NMARCH		equ	8
NBIRD		equ	12
NFW		equ	3
CLIMB		equ	64			; ticks up the stairs

	section	code,code
	bra.w	entry
	dc.l	'SOEV'
	dc.w	0,0
	dc.w	0

entry:	movem.l	d1-d7/a0-a6,-(sp)
	move.l	sp,ev_sp
	lea	vars,a0
	move.w	#VARS_SIZE/2-1,d0
.cl	clr.w	(a0)+
	dbf	d0,.cl
	move.w	d7,closing
	lea	lead_m_tab,a0
	tst.w	CX_WOMAN(a4)
	beq.s	.m
	lea	lead_w_tab,a0
.m	move.l	a0,lead_tab
	lea	pal_day,a0
	lea	grad_day,a1
	tst.w	closing
	beq.s	.p
	lea	pal_night,a0
	lea	grad_night,a1
.p	move.l	a1,-(sp)
	lea	bg_rle,a1
	bsr	ev_start
	move.l	(sp)+,a0
	jsr	K_GRAD(a5)
	tst.w	closing
	bne	closing_show

;------------------------------------------------------------------ the opening
	moveq	#0,d0			; the athletes: in a line, off the screen at the left
	lea	mx,a0			; (the first one walks in first and stops the furthest right)
	lea	mtarget,a1
.mi	move.w	d0,d1
	mulu	#30,d1
	add.w	#80,d1
	neg.w	d1
	lsl.w	#4,d1
	move.w	d1,(a0)+
	move.w	d0,d1
	mulu	#22,d1
	neg.w	d1
	add.w	#174,d1
	lsl.w	#4,d1
	move.w	d1,(a1)+
	addq.w	#1,d0
	cmp.w	#NMARCH,d0
	blo.s	.mi
	move.w	#-40*16,lx
	move.w	#TRACK_Y,ly
	lea	song_anthem_m,a0
	lea	song_anthem_b,a1
	jsr	K_SONG(a5)
	moveq	#1,d0
	bsr	frames
	jsr	K_FADEIN(a5)
	moveq	#CS_CHEER,d0
	moveq	#40,d1
	jsr	K_CSFX(a5)
	lea	s_open,a0
	bsr	banner
	lea	v_welcome,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
.loop	addq.w	#1,clock
	bsr	march
	bsr	leader
	bsr	birds
	cmp.w	#40,lit_t		; after the flame: the doves
	bne.s	.nb
	bsr	free_birds
	lea	snd_flap,a0
	moveq	#50,d1
	jsr	K_SFX(a5)
.nb	cmp.w	#190,lit_t
	bne.s	.nt
	lea	s_begin,a0
	bsr	banner
	lea	v_begin,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#CS_CHEER,d0
	moveq	#48,d1
	jsr	K_CSFX(a5)
.nt	bsr	frame
	tst.b	skip
	bne.s	.end
	cmp.w	#290,lit_t
	blo.s	.loop
.end	jsr	K_FADEOUT(a5)
	sub.l	a0,a0
	jsr	K_SONG(a5)
	moveq	#0,d0
	bra	leave

; march: walk to your place
march:
	lea	mx,a0
	lea	mtarget,a1
	moveq	#NMARCH-1,d0
.l	move.w	(a0),d1
	cmp.w	(a1)+,d1
	bge.s	.st
	add.w	#22,d1
	move.w	d1,(a0)
.st	addq.l	#2,a0
	dbf	d0,.l
	rts

; leader: the torch runs in, up the stairs, and lights the flame
leader:
	tst.w	lit_t
	beq.s	.go
	addq.w	#1,lit_t
	rts
.go	tst.w	climb
	bne.s	.up
	add.w	#26,lx
	cmp.w	#(STAIR_X-12)*16,lx
	blt.s	.x
	move.w	#1,climb
	rts
.up	addq.w	#1,climb
	move.w	climb,d0		; x, y on the stairs
	move.w	d0,d1
	mulu	#(CAUL_X-14-STAIR_X+4)*16,d0
	divu	#CLIMB,d0
	add.w	#(STAIR_X-12)*16,d0
	move.w	d0,lx
	mulu	#TRACK_Y-CAUL_Y-8,d1
	divu	#CLIMB,d1
	move.w	#TRACK_Y,d2
	sub.w	d1,d2
	move.w	d2,ly
	cmp.w	#CLIMB,climb
	blo.s	.x
	move.w	#1,lit_t		; light it!
	st	lit
	lea	snd_whoosh,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
	moveq	#CS_CHEER,d0
	moveq	#56,d1
	jsr	K_CSFX(a5)
	lea	s_lit,a0
	bsr	banner
.x	rts

free_birds:
	lea	birdtab,a2
	moveq	#NBIRD-1,d7
.l	moveq	#120,d0
	jsr	K_RAND(a5)
	add.w	#60,d0
	lsl.w	#4,d0
	move.w	d0,(a2)+		; x
	moveq	#20,d0
	jsr	K_RAND(a5)
	add.w	#212,d0
	lsl.w	#4,d0
	move.w	d0,(a2)+		; y
	moveq	#40,d0
	jsr	K_RAND(a5)
	sub.w	#14,d0
	move.w	d0,(a2)+		; vx
	moveq	#24,d0
	jsr	K_RAND(a5)
	add.w	#30,d0
	neg.w	d0
	move.w	d0,(a2)+		; vy
	dbf	d7,.l
	st	birds_on
	rts

birds:
	tst.b	birds_on
	beq.s	.x
	lea	birdtab,a2
	moveq	#NBIRD-1,d7
.l	move.w	4(a2),d0
	add.w	d0,(a2)
	move.w	6(a2),d0
	add.w	d0,2(a2)
	addq.l	#8,a2
	dbf	d7,.l
.x	rts

;------------------------------------------------------------------ the closing
closing_show:
	moveq	#0,d0			; the athletes stand in a line
	lea	mx,a0
.mi	move.w	d0,d1
	mulu	#22,d1
	neg.w	d1
	add.w	#174,d1
	lsl.w	#4,d1
	move.w	d1,(a0)+
	addq.w	#1,d0
	cmp.w	#NMARCH,d0
	blo.s	.mi
	move.w	#(CAUL_X-30)*16,lx	; the torch bearer next to the flame
	move.w	#CAUL_Y+8,ly
	st	lit
	move.w	#1,lit_t
	lea	song_farewell_m,a0
	lea	song_farewell_b,a1
	jsr	K_SONG(a5)
	moveq	#1,d0
	bsr	frames
	jsr	K_FADEIN(a5)
	lea	s_close,a0
	bsr	banner
	moveq	#CS_CLAP,d0
	moveq	#40,d1
	jsr	K_CSFX(a5)
.loop	addq.w	#1,clock
	; fireworks for a while
	cmp.w	#200,clock
	bhs.s	.nf
	move.w	clock,d0
	and.w	#15,d0
	bne.s	.nf
	bsr	firework
.nf	bsr	fw_tick
	; the athletes walk out to the right from tick 60
	cmp.w	#60,clock
	blo.s	.nw
	lea	mx,a0
	moveq	#NMARCH-1,d0
.w	add.w	#20,(a0)+
	dbf	d0,.w
.nw	; the flame goes out from tick 260
	cmp.w	#260,clock
	bne.s	.no
	lea	s_out,a0
	bsr	banner
	lea	snd_whoosh,a0
	moveq	#40,d1
	jsr	K_SFX(a5)
.no	cmp.w	#260,clock
	blo.s	.nd
	addq.w	#1,dying
.nd	cmp.w	#380,clock
	bne.s	.nb
	lea	s_thanks,a0
	bsr	banner
	lea	v_goodbye,a0
	moveq	#64,d1
	jsr	K_SFX(a5)
.nb	bsr	frame
	tst.b	skip
	bne.s	.end
	cmp.w	#480,clock
	blo	.loop
.end	jsr	K_FADEOUT(a5)
	sub.l	a0,a0
	jsr	K_SONG(a5)
	moveq	#0,d0
	bra	leave

firework:				; a new burst in the sky
	lea	fwtab,a2
	moveq	#NFW-1,d7
.f	tst.w	4(a2)
	beq.s	.free
	addq.l	#8,a2
	dbf	d7,.f
	rts
.free	move.w	#260,d0
	jsr	K_RAND(a5)
	add.w	#10,d0
	move.w	d0,(a2)
	moveq	#24,d0
	jsr	K_RAND(a5)
	addq.w	#4,d0
	move.w	d0,2(a2)
	move.w	#12,4(a2)		; ticks to live
	moveq	#2,d0
	jsr	K_RAND(a5)
	move.w	d0,6(a2)		; colour
	lea	snd_bang,a0
	moveq	#56,d1
	jsr	K_SFX(a5)
	rts
fw_tick:
	lea	fwtab,a2
	moveq	#NFW-1,d7
.l	tst.w	4(a2)
	beq.s	.n
	subq.w	#1,4(a2)
.n	addq.l	#8,a2
	dbf	d7,.l
	rts

;------------------------------------------------------------------ the screen
banner:					; a0 = text, big, on the stands
	movem.l	d0-d4/a0,-(sp)
	moveq	#0,d0
	moveq	#96,d1
	move.w	#320,d2
	moveq	#22,d3
	moveq	#1,d4
	jsr	K_FILL(a5)
	move.l	20(sp),a0
	moveq	#99,d1
	moveq	#3,d2
	moveq	#-1,d3
	jsr	K_CTEXT2(a5)
	movem.l	(sp)+,d0-d4/a0
	rts

frames:
	move.w	d0,-(sp)
.l	bsr	frame
	subq.w	#1,(sp)
	bgt.s	.l
	addq.l	#2,sp
	rts

frame:
	movem.l	d0-d7/a0-a2,-(sp)
	addq.w	#1,tick
	jsr	K_BEGIN(a5)
	; the flame
	tst.b	lit
	beq.s	.nfl
	move.w	dying,d0
	beq.s	.big
	lsr.w	#4,d0			; going out: smaller and smaller
	cmp.w	#4,d0
	bhs.s	.nfl
	lsl.w	#2,d0
	lea	sflame_tab,a0
	move.l	(a0,d0.w),a0
	bra.s	.fd
.big	move.w	tick,d0
	lsr.w	#1,d0
	and.l	#$ffff,d0
	divu	#3,d0
	swap	d0
	lsl.w	#2,d0
	lea	flame_tab,a0
	move.l	(a0,d0.w),a0
.fd	move.w	#CAUL_X-16,d0
	move.w	#CAUL_Y-31,d1
	jsr	K_BOB(a5)
.nfl	; fireworks
	lea	fwtab,a2
	moveq	#NFW-1,d7
.fw	move.w	4(a2),d0
	beq.s	.fn
	moveq	#12,d1
	sub.w	d0,d1
	lsr.w	#2,d1			; frame 0-2
	cmp.w	#2,d1
	bls.s	.f1
	moveq	#2,d1
.f1	lsl.w	#2,d1
	lea	fwa_tab,a0
	tst.w	6(a2)
	beq.s	.f2
	lea	fwb_tab,a0
.f2	move.l	(a0,d1.w),a0
	move.w	(a2),d0
	move.w	2(a2),d1
	jsr	K_BOB(a5)
.fn	addq.l	#8,a2
	dbf	d7,.fw
	; the athletes, last one first
	moveq	#NMARCH-1,d7
.m	lea	mx,a0
	move.w	d7,d0
	add.w	d0,d0
	move.w	(a0,d0.w),d0
	asr.w	#4,d0
	bmi.s	.mn
	cmp.w	#300,d0
	bgt.s	.mn
	lea	march_tab,a0
	move.w	d7,d1
	lsl.w	#2,d1
	move.l	(a0,d1.w),a0
	move.w	tick,d1			; walking: frame 0-3 (standing: 0)
	lsr.w	#2,d1
	and.w	#3,d1
	move.w	d7,d2
	add.w	d2,d2
	tst.w	closing
	bne.s	.mc
	lea	mtarget,a1
	move.w	(a1,d2.w),d3
	lea	mx,a1
	cmp.w	(a1,d2.w),d3
	bgt.s	.mw2
	moveq	#0,d1
	bra.s	.mw2
.mc	cmp.w	#60,clock		; (closing: they stand first)
	bhs.s	.mw2
	moveq	#0,d1
.mw2	lsl.w	#2,d1
	move.l	(a0,d1.w),a0
	move.w	#TRACK_Y-63,d1
	jsr	K_BOB(a5)
.mn	dbf	d7,.m
	; the torch bearer
	move.w	lx,d0
	asr.w	#4,d0
	bmi.s	.nl
	move.w	tick,d1
	lsr.w	#1,d1
	and.w	#3,d1
	tst.w	lit_t
	beq.s	.lw
	moveq	#0,d1
.lw	lsl.w	#2,d1
	move.l	lead_tab,a0
	move.l	(a0,d1.w),a0
	move.w	ly,d1
	sub.w	#63,d1
	jsr	K_BOB(a5)
.nl	; the doves
	tst.b	birds_on
	beq.s	.nbd
	lea	birdtab,a2
	moveq	#NBIRD-1,d7
.b	move.w	(a2),d0
	asr.w	#4,d0
	bmi.s	.bn
	cmp.w	#300,d0
	bgt.s	.bn
	move.w	2(a2),d1
	asr.w	#4,d1
	cmp.w	#-8,d1
	blt.s	.bn
	move.w	tick,d2
	add.w	d7,d2
	lsr.w	#1,d2
	and.w	#1,d2
	lsl.w	#2,d2
	lea	bird_tab,a0
	move.l	(a0,d2.w),a0
	jsr	K_BOB(a5)
.bn	addq.l	#8,a2
	dbf	d7,.b
.nbd	jsr	K_END(a5)
	jsr	K_INPUT(a5)
	and.w	#(1<<J_FIRE)|(1<<J_ESC),d1
	beq.s	.x
	st	skip
.x	movem.l	(sp)+,d0-d7/a0-a2
	rts

ev_start:
	move.l	a1,-(sp)
	jsr	K_PAL(a5)
	move.l	(sp)+,a0
	jsr	K_SETBG(a5)
	rts
leave	move.l	ev_sp,sp
	movem.l	(sp)+,d1-d7/a0-a6
	rts

;==============================================================================
	section	data,data
s_open		dc.b	'OPENING CEREMONY',0
s_lit		dc.b	'THE FLAME IS LIT!',0
s_begin		dc.b	'LET THE GAMES BEGIN!',0
s_close		dc.b	'CLOSING CEREMONY',0
s_out		dc.b	'THE FLAME GOES OUT',0
s_thanks	dc.b	'SEE YOU NEXT TIME!',0
	even
	include	"cer_data.i"
bg_rle	incbin	"cer_bg.rle"
	even

	section	chip,data_c
cer_chip	incbin	"cer_chip.bin"

	section	bss,bss
ev_sp		ds.l	1
vars
lead_tab	ds.l	1
closing		ds.w	1
clock		ds.w	1
tick		ds.w	1
lx		ds.w	1
ly		ds.w	1
climb		ds.w	1
lit_t		ds.w	1
dying		ds.w	1
mx		ds.w	NMARCH
mtarget		ds.w	NMARCH
birdtab		ds.w	NBIRD*4
fwtab		ds.w	NFW*4
lit		ds.b	1
skip		ds.b	1
birds_on	ds.b	1
	even
VARS_END
VARS_SIZE	equ	VARS_END-vars
