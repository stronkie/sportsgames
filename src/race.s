;------------------------------------------------------------------------------
;  race.s - the race engine of Stronkie's Olympics (100m, hurdles, swimming,
;  cycling, root beer sprint): you against a rival from another country.
;  The event sets RACE_LEN (1/16 pixels from the start to the finish), the
;  rival's time range (CPU_LO/CPU_HI in 1/100 s) and has its own 'frame'.
;  Positions are in 1/16 pixels from the start line.
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------

race_init:				; (c_wait: set it after, then call race_speed)
	lea	rvars,a0
	move.w	#RVARS_SIZE/2-1,d0
.c	clr.w	(a0)+
	dbf	d0,.c
	; the rival's time: low..high, faster on hard
	move.w	#CPU_HI-CPU_LO,d1
	move.w	#CPU_LO,d2
	move.w	CX_LEVEL(a4),d3
	bne.s	.n0
	lsr.w	#1,d1			; easy: the slow half
	add.w	d1,d2
	bra.s	.r
.n0	cmp.w	#2,d3
	bne.s	.r
	lsr.w	#1,d1			; hard: the fast half
.r	move.w	d1,d0
	addq.w	#1,d0
	jsr	K_RAND(a5)
	add.w	d2,d0
	move.w	d0,cpu_time
race_speed:				; cpu_time, c_wait -> cpu_step
	; its speed: RACE_LEN*256 / ticks
	move.w	cpu_time,d0
	moveq	#0,d1
	move.w	d0,d1
	lsr.w	#2,d1			; ticks (4/100 s each)
	sub.w	c_wait,d1		; (the part it waits does not count)
	move.l	#RACE_LEN*64,d0
	divu	d1,d0
	and.l	#$ffff,d0
	lsl.l	#2,d0
	move.l	d0,cpu_step
	rts

; race_countdown: on your marks, set, go (a false start: start again) -> when it is GO
race_countdown:
.again	lea	s_r_marks,a0
	bsr	message
	moveq	#30,d0
	bsr	frames
	lea	s_r_set,a0
	bsr	message
	moveq	#30,d0			; (a moment you can't guess)
	jsr	K_RAND(a5)
	add.w	#20,d0
	move.w	d0,d7
.set	bsr	frame
	bsr	waggle
	tst.w	d0
	bne.s	.false
	subq.w	#1,d7
	bne.s	.set
	moveq	#CS_BEEPHI,d0
	moveq	#64,d1
	jsr	K_CSFX(a5)
	moveq	#CS_GO,d0
	moveq	#64,d1
	jsr	K_CSFX(a5)
	lea	s_r_go,a0
	bsr	message
	move.w	#25,go_msg
	st	running
	rts
.false	moveq	#CS_BUZZER,d0
	moveq	#56,d1
	jsr	K_CSFX(a5)
	lea	s_r_false,a0
	bsr	message
	moveq	#40,d0
	bsr	frames
	bra	.again

; race_tick: the clock, the rival, the GO message - once a tick while running
race_tick:
	tst.b	running
	beq	.x
	tst.b	p_done
	bne.s	.c
	addq.l	#4,p_time
.c	tst.b	c_done
	bne.s	.m
	addq.l	#4,c_time
	tst.w	c_wait			; (still waiting / drinking)
	beq.s	.go
	subq.w	#1,c_wait
	bra.s	.m
.go	move.l	cpu_step,d0		; the rival: a little slower in the first second
	cmp.w	#25,ctick
	bhs.s	.full
	addq.w	#1,ctick
	mulu	ctick,d0
	divu	#25,d0
	and.l	#$ffff,d0
.full	add.l	d0,c_pos
	move.l	c_pos,d0
	lsr.l	#8,d0
	cmp.l	#RACE_LEN,d0
	blo.s	.m
	st	c_done
.m	tst.w	go_msg
	beq.s	.x
	subq.w	#1,go_msg
	bne.s	.x
	bsr	clear_msg
.x	rts

; race_run: d1 = what one step adds, d2 = the top speed: your legs (or arms...)
; (p_spd is in 1/16: it loses 1/16 every tick, so it follows how fast you go)
race_run:
	tst.b	running
	beq.s	.x
	tst.b	p_done
	bne.s	.x
	movem.l	d1-d2,-(sp)
	lsl.w	#4,d1
	lsl.w	#4,d2
	bsr	waggle
	move.b	d0,stroked
	tst.w	d0
	beq.s	.n
	add.w	d1,p_spd
.n	cmp.w	p_spd,d2
	bhs.s	.t
	move.w	d2,p_spd
.t	move.w	p_spd,d0		; slowing down
	lsr.w	#4,d0
	bne.s	.s
	tst.w	p_spd
	beq.s	.s
	moveq	#1,d0
.s	sub.w	d0,p_spd
	moveq	#0,d0
	move.w	p_spd,d0
	lsr.w	#4,d0
	add.l	d0,p_pos
	movem.l	(sp)+,d1-d2
	cmp.l	#RACE_LEN,p_pos
	blo.s	.x
	move.l	#RACE_LEN,p_pos
	st	p_done
.x	rts

; race_x: d0.l = position (1/16 px) -> d0.w = screen x
race_x:
	lsr.l	#RACE_SHIFT,d0
	add.w	#START_X,d0
	rts

; race_time: the time in the top bar (x = 8)
race_time:
	movem.l	d0-d3/a0,-(sp)
	move.l	p_time,d0
	bsr	hund_text
	moveq	#8,d0
	moveq	#3,d2
	bsr	top_text
	movem.l	(sp)+,d0-d3/a0
	rts

; race_finish: wait for the rival, the result -> d0 = 1 you won
race_finish:
	moveq	#CS_CHEER,d0
	moveq	#44,d1
	jsr	K_CSFX(a5)
	moveq	#0,d6
.w	tst.b	c_done
	bne.s	.d
	bsr	race_tick
	bsr	frame
	addq.w	#1,d6
	cmp.w	#1500,d6
	blo.s	.w
.d	move.l	p_time,d0
	lea	s_c_secs,a0
	bsr	result_hund
	move.l	p_time,d0
	cmp.l	c_time,d0
	bhi.s	.lost
	lea	s_r_win,a0
	bsr	message
	moveq	#CS_GREAT,d0
	moveq	#64,d1
	jsr	K_CSFX(a5)
	moveq	#1,d0
	rts
.lost	lea	s_r_lose,a0
	bsr	message
	moveq	#0,d0
	rts

	section	data,data
s_r_marks	dc.b	'ON YOUR MARKS',0
s_r_set		dc.b	'SET...',0
s_r_go		dc.b	'GO!',0
s_r_false	dc.b	'FALSE START!',0
s_r_win		dc.b	'YOU WIN THE RACE!',0
s_r_lose	dc.b	'SECOND PLACE',0
	even
	section	bss,bss
rvars
p_pos		ds.l	1
c_pos		ds.l	1
p_time		ds.l	1
c_time		ds.l	1
cpu_step	ds.l	1
p_spd		ds.w	1
cpu_time	ds.w	1
ctick		ds.w	1
c_wait		ds.w	1
go_msg		ds.w	1
running		ds.b	1
p_done		ds.b	1
c_done		ds.b	1
stroked		ds.b	1		; race_run: a step (stroke) this tick
	even
RVARS_END
RVARS_SIZE	equ	RVARS_END-rvars
	section	code,code
