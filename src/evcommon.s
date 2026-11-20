;------------------------------------------------------------------------------
;  evcommon.s - small things every event of Stronkie's Olympics uses.
;  The event has its own 'frame' routine (draws, shows, reads the input into
;  held / pressed and jumps to give_up on ESC).
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------

; ev_start: a0 = palette, a1 = packed background (the screen stays dark)
ev_start:
	move.l	a1,-(sp)
	jsr	K_PAL(a5)
	move.l	(sp)+,a0
	jsr	K_SETBG(a5)
	rts

give_up	jsr	K_FADEOUT(a5)
	moveq	#-1,d0
leave	move.l	ev_sp,sp
	movem.l	(sp)+,d1-d7/a0-a6
	rts

; ev_done: the result is in CX_SCORE / CX_RESULT: wait, fade, back
ev_done:
	moveq	#90,d0
	moveq	#1,d1
	jsr	K_WAIT(a5)
	jsr	K_FADEOUT(a5)
	moveq	#0,d0
	bra.s	leave

cat:					; a0 -> a1 (a1 stays on the 0)
	move.b	(a0)+,(a1)+
	bne.s	cat
	subq.l	#1,a1
	rts

catnum:					; d0.l -> a1
	movem.l	d1/a0,-(sp)
	moveq	#1,d1
	jsr	K_NUM(a5)
	bsr.s	cat
	movem.l	(sp)+,d1/a0
	rts

; result_pts: d0.l = points -> CX_SCORE and CX_RESULT = "<n> PTS", a1 = after it
result_pts:
	move.l	d0,CX_SCORE(a4)
	lea	CX_RESULT(a4),a1
	bsr.s	catnum
	lea	s_c_pts,a0
	bsr.s	cat
	rts

frames:					; d0 = frames to show
	move.w	d0,-(sp)
.l	bsr	frame
	subq.w	#1,(sp)
	bgt.s	.l
	addq.l	#2,sp
	rts

message:				; a0: big, in the bottom bar (y 240)
	movem.l	d0-d4/a0,-(sp)
	bsr.s	clear_msg
	move.l	20(sp),a0
	move.w	#240,d1
	moveq	#3,d2
	moveq	#-1,d3
	jsr	K_CTEXT2(a5)
	movem.l	(sp)+,d0-d4/a0
	rts
message_small:
	movem.l	d0-d4/a0,-(sp)
	bsr.s	clear_msg
	move.l	20(sp),a0
	move.w	#244,d1
	moveq	#2,d2
	moveq	#-1,d3
	jsr	K_CTEXT(a5)
	movem.l	(sp)+,d0-d4/a0
	rts
clear_msg:
	movem.l	d0-d4,-(sp)
	moveq	#0,d0
	move.w	#241,d1
	move.w	#320,d2
	moveq	#15,d3
	moveq	#0,d4
	jsr	K_FILL(a5)
	movem.l	(sp)+,d0-d4
	rts

; top_text: a0 = text at x d0 in the top bar (y 8), d2 = colour (paper 0)
top_text:
	movem.l	d1/d3,-(sp)
	moveq	#8,d1
	moveq	#0,d3
	jsr	K_TEXT(a5)
	movem.l	(sp)+,d1/d3
	rts

; top_num: d0.l = number, d1 = x, d2 = colour, d3 = digits (with zeros)
top_num:
	movem.l	d0-d3/a0,-(sp)
	move.w	d1,-(sp)
	move.w	d3,d1
	jsr	K_NUM(a5)
	move.w	(sp)+,d0
	bsr.s	top_text
	movem.l	(sp)+,d0-d3/a0
	rts

; read_input: the end of every frame
read_input:
	jsr	K_INPUT(a5)
	move.w	d0,held
	move.w	d1,pressed
	btst	#J_ESC,d1
	bne	give_up
	rts

; time_text: d0 = ticks (25 a second) -> a0 = "0:59"
time_text:
	movem.l	d0-d1/a1,-(sp)
	lea	timebuf,a1
	ext.l	d0
	add.l	#24,d0
	divu	#25,d0			; seconds (rounded up)
	and.l	#$ffff,d0
	divu	#60,d0
	add.b	#'0',d0
	move.b	d0,(a1)+
	move.b	#':',(a1)+
	swap	d0
	and.l	#$ffff,d0
	divu	#10,d0
	add.b	#'0',d0
	move.b	d0,(a1)+
	swap	d0
	add.b	#'0',d0
	move.b	d0,(a1)+
	clr.b	(a1)
	lea	timebuf,a0
	movem.l	(sp)+,d0-d1/a1
	rts

; waggle -> d0 = 1 for a new step: left after right or right after left (the joystick or the keys)
waggle:
	move.w	pressed,d0
	btst	#J_LEFT,d0
	beq.s	.r
	cmp.b	#1,wag_last
	beq.s	.r
	move.b	#1,wag_last
	moveq	#1,d0
	rts
.r	btst	#J_RIGHT,d0
	beq.s	.no
	cmp.b	#2,wag_last
	beq.s	.no
	move.b	#2,wag_last
	moveq	#1,d0
	rts
.no	moveq	#0,d0
	rts

; hund_text: d0.l = 1/100 seconds (or cm) -> a0 = "10.24"
hund_text:
	movem.l	d0-d1/a1,-(sp)
	lea	timebuf,a1
	divu	#100,d0
	move.l	d0,-(sp)
	and.l	#$ffff,d0
	moveq	#1,d1
	jsr	K_NUM(a5)
	bsr	cat
	move.b	#'.',(a1)+
	move.l	(sp)+,d0
	clr.w	d0
	swap	d0
	moveq	#2,d1
	jsr	K_NUM(a5)
	bsr	cat
	clr.b	(a1)
	lea	timebuf,a0
	movem.l	(sp)+,d0-d1/a1
	rts

; result_hund: d0.l = 1/100 s or cm, a0 = unit (" S" / " M") -> CX_SCORE, CX_RESULT
result_hund:
	move.l	d0,CX_SCORE(a4)
	move.l	a0,-(sp)
	bsr	hund_text
	lea	CX_RESULT(a4),a1
	bsr	cat
	move.l	(sp)+,a0
	bsr	cat
	rts

	section	data,data
s_c_secs	dc.b	' S',0
s_c_m	dc.b	' M',0
s_c_pts	dc.b	' PTS',0
	even
	section	bss,bss
ev_sp		ds.l	1
held		ds.w	1
pressed		ds.w	1
timebuf		ds.b	16
wag_last	ds.b	1
	even
strbuf		ds.b	40
	section	code,code
