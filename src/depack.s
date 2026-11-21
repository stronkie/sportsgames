;==============================================================================
;  depack.s - unpacks the hunks that tools/crunch.py packed (the floppy version)
;  Included by loader.s and kernel.s, which both have get_long and read_block.
;
;  A packed hunk is unpacked in place: its packed bytes are read to the END of
;  the hunk's memory, then unpacked forwards from the start (crunch.py made the
;  hunk big enough for that), then the rest of the hunk is cleared again.
;==============================================================================
HUNK_PACKED	equ	$7e9

; unpack_hunk: a1 = the hunk's memory, d2 = its size in bytes -> d0 = 1 ok, 0 failed
;   (the HUNK_PACKED long has been read)
unpack_hunk:
	movem.l	d1-d4/a0-a2,-(sp)
	bsr	get_long		; the original type
	bsr	get_long		; unpacked size (longs)
	lsl.l	#2,d0
	move.l	d0,d4
	bsr	get_long		; the size in the header before the room was added
	bsr	get_long		; packed bytes
	addq.l	#3,d0
	and.b	#$fc,d0
	move.l	d0,d1
	cmp.l	d2,d1
	bhi.s	.err
	lea	(a1,d2.l),a0
	sub.l	d1,a0			; to the end of the hunk
	bsr	read_block		; (a0, d1)
	tst.l	d0
	beq.s	.err
	move.l	d4,d0
	bsr	depack			; a0 -> a1, d0 bytes
	lea	(a1,d4.l),a0		; clear what is left (the packed bytes, the bss part)
	move.l	d2,d0
	sub.l	d4,d0
	lsr.l	#2,d0
	bra.s	.c2
.cl	clr.l	(a0)+
.c2	subq.l	#1,d0
	bpl.s	.cl
	moveq	#1,d0
	bra.s	.x
.err	moveq	#0,d0
.x	movem.l	(sp)+,d1-d4/a0-a2
	rts

; depack: a0 = packed bytes, a1 = destination, d0 = unpacked size (bytes)
;   bits are read MSB first through d1 (a 1 bit marks the end of each byte);
;   literals and offset bytes come straight from (a0)+
depack:
	movem.l	d0-d3/a0-a3,-(sp)
	tst.l	d0
	beq.s	.done
	lea	(a1,d0.l),a3		; the end
	moveq	#-128,d1		; no bits yet
	moveq	#0,d3			; the last offset
	move.b	(a0)+,(a1)+		; it starts with a literal
.loop	cmp.l	a3,a1
	bhs.s	.done
	add.b	d1,d1			; a bit: 0 = literal
	bne.s	.b1
	move.b	(a0)+,d1
	addx.b	d1,d1
.b1	bcs.s	.match
	move.b	(a0)+,(a1)+
	bra.s	.loop
.match	add.b	d1,d1			; 1 = the same offset again
	bne.s	.b2
	move.b	(a0)+,d1
	addx.b	d1,d1
.b2	bcs.s	.rep
	bsr.s	.gamma			; a new offset: high part + 1, the low byte
	subq.l	#1,d2
	lsl.l	#8,d2
	move.b	(a0)+,d2
	addq.l	#1,d2
	move.l	d2,d3
	bsr.s	.gamma			; length - 1
	bra.s	.copy
.rep	bsr.s	.gamma			; length
	subq.l	#1,d2
.copy	move.l	a1,a2
	sub.l	d3,a2
.c	move.b	(a2)+,(a1)+
	dbf	d2,.c
	bra.s	.loop
.done	movem.l	(sp)+,d0-d3/a0-a3
	rts
; gamma -> d2 (1, 2..3, 4..7, ...): (1, bit)* then 0
.gamma	moveq	#1,d2
.g	add.b	d1,d1
	bne.s	.g1
	move.b	(a0)+,d1
	addx.b	d1,d1
.g1	bcc.s	.gx
	add.b	d1,d1
	bne.s	.g2
	move.b	(a0)+,d1
	addx.b	d1,d1
.g2	addx.l	d2,d2
	bra.s	.g
.gx	rts
