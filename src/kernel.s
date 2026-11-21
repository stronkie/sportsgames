;------------------------------------------------------------------------------
;  STRONKIE'S OLYMPICS  -  the sports game for the Amiga 500.
;
;  Kickstart / Workbench 1.3, 512K chip + 512K trapdoor.  68000 assembly.
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;
;  kernel.s : start-up, display (double buffer + bobs), text, sound, input,
;             loading the events, the records file
;  main.s   : the menus, making your athlete, the competition, the medals
;  Events are separate files (Soccer.evt, ...): see kernel.i
;
;  Build: sh tools/build.sh
;------------------------------------------------------------------------------

	include	"kernel.i"
	include	"main_equ.i"
	include	"build.i"
	include	"events_equ.i"

CUSTOM		equ	$dff000
SCRW		equ	40
PLANES		equ	5
ROWB		equ	SCRW*PLANES		; 200
SCRSIZE		equ	ROWB*256		; 51200
MAXBOBS		equ	48
GRADMAX		equ	64
EV_ANY_SIZE	equ	180000
EV_CHIP_SIZE	equ	150000
MAXHUNKS	equ	8
IOBUFSIZE	equ	4096
MUSIC_VOL	equ	9			; music: quiet, the effects and voices on top

_LVOSupervisor	equ	-30
_LVOForbid	equ	-132
_LVOPermit	equ	-138
_LVOFindTask	equ	-294
_LVOAllocMem	equ	-198
_LVOFreeMem	equ	-210
_LVOGetMsg	equ	-372
_LVOReplyMsg	equ	-378
_LVOWaitPort	equ	-384
_LVOCloseLibrary equ	-414
_LVOOpenLibrary	equ	-552
_LVOLoadView	equ	-222
_LVOWaitBlit	equ	-228
_LVOWaitTOF	equ	-270
_LVOOwnBlitter	equ	-456
_LVODisownBlitter equ	-462
_LVOOpen	equ	-30
_LVOClose	equ	-36
_LVORead	equ	-42
_LVOWrite	equ	-48
_LVODelay	equ	-198

	section	code,code

;==============================================================================
;  start-up and shut-down
;==============================================================================
start:
	move.l	sp,stacksave
	move.l	4.w,a6
	sub.l	a1,a1
	jsr	_LVOFindTask(a6)
	move.l	d0,a4
	move.l	d0,mytask
	cmp.l	#'SOLY',d7		; started by the loader: it owns the WB message
	beq.s	.cli
	cmp.l	#'WHDL',d7		; started by the WHDLoad slave (no OS)
	bne.s	.nwhd
	st	whd_mode
	bra.s	.cli
.nwhd	tst.l	172(a4)
	bne.s	.cli
	lea	92(a4),a0
	jsr	_LVOWaitPort(a6)
	lea	92(a4),a0
	jsr	_LVOGetMsg(a6)
	move.l	d0,wbmsg
.cli	lea	gfxname,a1
	moveq	#0,d0
	jsr	_LVOOpenLibrary(a6)
	move.l	d0,gfxbase
	beq	.exit
	lea	dosname,a1
	moveq	#0,d0
	jsr	_LVOOpenLibrary(a6)
	move.l	d0,dosbase
	move.l	mytask,a0		; no "please insert volume" requesters (pr_WindowPtr = -1)
	move.l	184(a0),old_winptr
	move.l	#-1,184(a0)
	move.l	#$2f1c3a57,seed
	bsr	alloc_chip
	tst.l	d0
	beq	.nomem
	bsr	load_records

	move.l	gfxbase,a6
	move.l	34(a6),oldview
	move.l	50(a6),old_lof
	sub.l	a1,a1
	jsr	_LVOLoadView(a6)
	jsr	_LVOWaitTOF(a6)
	jsr	_LVOWaitTOF(a6)
	bsr	init_display
	bsr	hw_takeover

	bsr	game_main

	bsr	hw_restore
	bsr	free_chip
	move.l	gfxbase,a6
	move.l	old_lof,50(a6)
	move.l	oldview,a1
	jsr	_LVOLoadView(a6)
	jsr	_LVOWaitTOF(a6)
	jsr	_LVOWaitTOF(a6)
	move.l	38(a6),CUSTOM+$80
	move.l	4.w,a6
	move.l	dosbase,d0
	beq.s	.nodos
	move.l	d0,a1
	jsr	_LVOCloseLibrary(a6)
.nodos	move.l	gfxbase,a1
	jsr	_LVOCloseLibrary(a6)
	move.l	mytask,a0
	move.l	old_winptr,184(a0)
	bra.s	.exit
.nomem	bsr	free_chip
	move.l	4.w,a6
	move.l	dosbase,a1
	jsr	_LVOCloseLibrary(a6)
	move.l	gfxbase,a1
	jsr	_LVOCloseLibrary(a6)
.exit	tst.l	wbmsg
	beq.s	.ret
	move.l	4.w,a6
	jsr	_LVOForbid(a6)
	move.l	wbmsg,a1
	jsr	_LVOReplyMsg(a6)
.ret	move.l	stacksave,sp
	moveq	#0,d0
	rts

; alloc_chip: the screens and the event chip memory -> d0 = 0 if there is not enough
alloc_chip:
	movem.l	d1-d2/a0-a2/a6,-(sp)
	move.l	4.w,a6
	lea	chip_sizes,a2
	lea	screen0,a1
.l	move.l	(a2)+,d0
	beq.s	.ok
	move.l	a1,-(sp)
	move.l	#$10002,d1		; chip, cleared
	jsr	_LVOAllocMem(a6)
	move.l	(sp)+,a1
	move.l	d0,(a1)+
	bne.s	.l
	moveq	#0,d0
	bra.s	.x
.ok	moveq	#1,d0
.x	movem.l	(sp)+,d1-d2/a0-a2/a6
	rts

free_chip:
	movem.l	d0-d1/a0-a2/a6,-(sp)
	tst.b	whd_mode
	bne.s	.x
	move.l	4.w,a6
	lea	chip_sizes,a2
	lea	screen0,a0
.l	move.l	(a2)+,d0
	beq.s	.x
	move.l	(a0),d1
	clr.l	(a0)+
	tst.l	d1
	beq.s	.l
	move.l	a0,-(sp)
	move.l	d1,a1
	jsr	_LVOFreeMem(a6)
	move.l	(sp)+,a0
	bra.s	.l
.x	movem.l	(sp)+,d0-d1/a0-a2/a6
	rts

hw_takeover:
	move.l	gfxbase,a6
	jsr	_LVOOwnBlitter(a6)
	jsr	_LVOWaitBlit(a6)
	move.l	4.w,a6
	jsr	_LVOForbid(a6)
	lea	CUSTOM,a5
	tst.b	saved_hw
	bne.s	.sv
	st	saved_hw
	move.w	$1c(a5),old_intena
	move.w	$02(a5),old_dmacon
	move.w	$10(a5),old_adkcon
.sv	move.w	#$7fff,$9a(a5)
	move.w	#$7fff,$9c(a5)
	bsr	wait_vbl
	move.w	#$7fff,$96(a5)
	move.w	#$00ff,$9e(a5)
	moveq	#0,d0
	move.w	d0,$a8(a5)
	move.w	d0,$b8(a5)
	move.w	d0,$c8(a5)
	move.w	d0,$d8(a5)
	lea	$140(a5),a0		; disarm all sprites
	moveq	#7,d1
.spr	move.w	d0,4(a0)
	move.w	d0,6(a0)
	move.w	d0,(a0)
	move.w	d0,2(a0)
	addq.l	#8,a0
	dbf	d1,.spr
	move.w	#$ff00,$34(a5)
	move.l	#copperlist,$80(a5)
	move.w	d0,$88(a5)
	move.w	#$83c0,$96(a5)		; DMA: master, bitplanes, copper, blitter
	bsr	music_init
	bsr	get_vbr
	move.l	d0,a0
	move.l	$6c(a0),old_irq
	move.l	#vbl_irq,$6c(a0)
	move.w	#$0020,$9c(a5)
	move.w	#$c020,$9a(a5)		; master + vertical blank
	sf	os_running
	rts

; get_vbr -> d0 = the vector base (0 on a 68000)
get_vbr:
	movem.l	d1/a5-a6,-(sp)
	moveq	#0,d0
	tst.b	whd_mode
	bne.s	.x
	move.l	4.w,a6
	btst	#0,297(a6)		; AttnFlags: 68010 or better?
	beq.s	.x
	lea	.super,a5
	jsr	_LVOSupervisor(a6)
.x	move.l	d0,vbr
	movem.l	(sp)+,d1/a5-a6
	rts
.super	dc.w	$4e7a,$0801		; movec vbr,d0
	rte

; hw_restore: the OS gets the machine back (and its own screen)
hw_restore:
	bsr	os_back
	lea	CUSTOM,a5
	tst.b	whd_mode
	bne.s	.x
	move.l	gfxbase,a6
	move.l	38(a6),$80(a5)
	move.w	d0,$88(a5)
.x	rts

; os_back: the OS runs again (for the disk) but our screen stays on
os_back:
	movem.l	d0-d1/a0/a5-a6,-(sp)
	bsr	wait_blit
	lea	CUSTOM,a5
	move.w	#$000f,$96(a5)		; sound off
	tst.b	whd_mode
	beq.s	.os
	movem.l	(sp)+,d0-d1/a0/a5-a6	; (WHDLoad: nothing to give back)
	rts
.os	move.w	#$7fff,$9a(a5)
	move.l	vbr,a0
	move.l	old_irq,$6c(a0)
	move.w	#$7fff,$9c(a5)
	move.l	gfxbase,a6		; graphics puts its copper list back at every frame:
	move.l	#copperlist,50(a6)	; let it be ours while the disk runs
	move.w	#$7fff,$9e(a5)
	move.w	old_adkcon,d0
	or.w	#$8000,d0
	move.w	d0,$9e(a5)
	move.w	old_dmacon,d0
	or.w	#$8380,d0		; (+ our bitplanes and copper)
	move.w	d0,$96(a5)
	move.w	old_intena,d0
	or.w	#$c000,d0
	move.w	d0,$9a(a5)
	jsr	_LVODisownBlitter(a6)
	move.l	4.w,a6
	jsr	_LVOPermit(a6)
	st	os_running
	movem.l	(sp)+,d0-d1/a0/a5-a6
	rts

; os_away: after the disk, the machine is ours again
os_away:
	tst.b	whd_mode
	bne.s	.x
	movem.l	d0-d7/a0-a6,-(sp)
	move.l	gfxbase,a6
	move.l	old_lof,50(a6)
	bsr	hw_takeover
	movem.l	(sp)+,d0-d7/a0-a6
.x	rts

wait_vbl:
.w1	move.l	CUSTOM+4,d0
	and.l	#$1ff00,d0
	cmp.l	#303<<8,d0
	bne.s	.w1
.w2	move.l	CUSTOM+4,d0
	and.l	#$1ff00,d0
	cmp.l	#303<<8,d0
	beq.s	.w2
	rts

wait_lines:				; d3 = raster lines
	movem.l	d0/d3,-(sp)
	subq.w	#1,d3
.l	move.b	CUSTOM+6,d0
.w	cmp.b	CUSTOM+6,d0
	beq.s	.w
	dbf	d3,.l
	movem.l	(sp)+,d0/d3
	rts

wait_blit:
	tst.b	CUSTOM+2		; (early Agnus: read twice)
.w	btst	#6,CUSTOM+2
	bne.s	.w
	rts

;==============================================================================
;  the jump table for the events
;==============================================================================
ktable:	jmp	k_begin
	jmp	k_end
	jmp	k_bob
	jmp	k_text
	jmp	k_text2
	jmp	k_ctext
	jmp	k_ctext2
	jmp	k_fill
	jmp	k_setbg
	jmp	k_pal
	jmp	k_grad
	jmp	k_sfx
	jmp	k_song
	jmp	k_rand
	jmp	k_input
	jmp	k_num
	jmp	k_wait
	jmp	k_stamp
	jmp	k_csfx
	jmp	k_fadein
	jmp	k_fadeout
	jmp	k_frames
	jmp	k_playerpal

;==============================================================================
;  display: two screens to draw on (double buffer) and a clean background
;==============================================================================
init_display:
	movem.l	d0-d2/a0,-(sp)
	lea	cop_spr,a0		; all sprites to the empty one
	move.w	#$120,d0
	moveq	#7,d1
.s	move.l	#spr_null,d2
	move.w	d0,(a0)+
	swap	d2
	move.w	d2,(a0)+
	addq.w	#2,d0
	move.w	d0,(a0)+
	swap	d2
	move.w	d2,(a0)+
	addq.w	#2,d0
	dbf	d1,.s
	move.l	screen0,scr_tab
	move.l	screen1,scr_tab+4
	clr.w	front
	move.l	screen0,d0
	bsr	set_bpl
	move.l	screen1,back_ptr
	clr.w	nrect
	clr.w	nrect+2
	clr.w	fade_lvl
	clr.l	grad_ptr
	lea	cop_grad,a0
	move.l	#$fffffffe,(a0)
	movem.l	(sp)+,d0-d2/a0
	rts

; set_bpl: d0 = screen -> the copper list shows it
set_bpl:
	movem.l	d0-d1/a0,-(sp)
	lea	cop_bpl+2,a0
	moveq	#PLANES-1,d1
.p	swap	d0
	move.w	d0,(a0)
	swap	d0
	move.w	d0,4(a0)
	addq.l	#8,a0
	add.l	#SCRW,d0
	dbf	d1,.p
	movem.l	(sp)+,d0-d1/a0
	rts

; k_begin: the back screen gets the background back where bobs were
k_begin:
	movem.l	d0-d3/a0-a2,-(sp)
	move.w	front,d0
	eor.w	#1,d0			; the back screen
	add.w	d0,d0
	lea	nrect,a2
	move.w	(a2,d0.w),d1
	clr.w	(a2,d0.w)
	add.w	d0,d0
	move.l	back_ptr,a1
	lea	rects0,a2
	tst.w	d0
	beq.s	.r
	lea	rects1,a2
.r	subq.w	#1,d1
	bmi.s	.x
	lea	CUSTOM,a0
.l	bsr	wait_blit
	move.l	(a2)+,d2		; offset
	move.w	(a2)+,d3		; words
	move.w	#$09f0,$40(a0)
	clr.w	$42(a0)
	move.l	#-1,$44(a0)
	move.l	background,d0
	add.l	d2,d0
	move.l	d0,$50(a0)
	move.l	a1,d0
	add.l	d2,d0
	move.l	d0,$54(a0)
	moveq	#SCRW,d0
	sub.w	d3,d0
	sub.w	d3,d0
	move.w	d0,$64(a0)
	move.w	d0,$66(a0)
	move.w	(a2)+,d0		; rows (all planes)
	lsl.w	#6,d0
	or.w	d3,d0
	move.w	d0,$58(a0)
	dbf	d1,.l
.x	movem.l	(sp)+,d0-d3/a0-a2
	rts

; k_end: the back screen is finished: show it (25 frames a second)
k_end:
	movem.l	d0/a0,-(sp)
	bsr	wait_blit
	move.l	back_ptr,swap_ptr
	st	swap_req
.w	tst.b	swap_req
	bne.s	.w
	eor.w	#1,front
	move.w	front,d0
	eor.w	#1,d0
	lsl.w	#2,d0
	lea	scr_tab,a0
	move.l	(a0,d0.w),back_ptr
	movem.l	(sp)+,d0/a0
	rts

; k_bob: a0 = bob (W.w, H.w, image.l, mask.l), d0 = x, d1 = y: on the back screen
k_bob:
	movem.l	d0-d7/a0-a3,-(sp)
	move.l	back_ptr,a3
	bsr	draw_bob
	tst.l	d7
	bmi.s	.x
	move.w	front,d0		; remember where (to restore it)
	eor.w	#1,d0
	add.w	d0,d0
	lea	nrect,a1
	move.w	(a1,d0.w),d1
	cmp.w	#MAXBOBS,d1
	bhs.s	.x
	addq.w	#1,(a1,d0.w)
	lea	rects0,a1
	tst.w	d0
	beq.s	.r
	lea	rects1,a1
.r	lsl.w	#3,d1
	add.w	d1,a1
	move.l	d7,(a1)+		; offset
	move.w	d6,(a1)+		; words
	move.w	d5,d0
	mulu	#5,d0
	move.w	d0,(a1)+		; rows
.x	movem.l	(sp)+,d0-d7/a0-a3
	rts

; k_stamp: a0 = bob, d0 = x, d1 = y: into the background and both screens
k_stamp:
	movem.l	d0-d7/a0-a3,-(sp)
	move.w	d0,d2
	move.w	d1,d3
	move.l	background,a3
	bsr	draw_bob
	move.w	d2,d0
	move.w	d3,d1
	move.l	screen0,a3
	bsr	draw_bob
	move.w	d2,d0
	move.w	d3,d1
	move.l	screen1,a3
	bsr	draw_bob
	movem.l	(sp)+,d0-d7/a0-a3
	rts

; draw_bob: a0 = bob, d0 = x, d1 = y, a3 = screen
;  -> d7 = offset in the screen (-1 = nothing drawn), d6 = words, d5 = rows
;  (keeps d2-d3)
draw_bob:
	movem.l	d2-d3/a0,-(sp)
	moveq	#-1,d7
	tst.w	d0
	bmi	.x
	move.w	(a0),d4			; W
	move.w	2(a0),d5		; H
	move.l	4(a0),a1		; image
	move.l	8(a0),a2		; mask
	tst.w	d1
	bpl.s	.y0
	neg.w	d1			; rows off the top
	sub.w	d1,d5
	ble	.x
	moveq	#0,d6
	move.w	d1,d6
	mulu	d4,d6
	add.l	d6,d6			; skip * W * 2
	add.l	d6,a2
	move.l	d6,d2
	lsl.l	#2,d2
	add.l	d6,d2
	add.l	d2,a1
	moveq	#0,d1
.y0	cmp.w	#256,d1
	bge	.x
	move.w	d1,d6
	add.w	d5,d6
	cmp.w	#256,d6
	bls.s	.y1
	move.w	#256,d5
	sub.w	d1,d5
.y1	moveq	#0,d6
	move.w	d0,d6
	lsr.w	#4,d6			; word column
	cmp.w	#20,d6
	bhs	.x
	moveq	#20,d2
	sub.w	d6,d2			; words left on the line
	move.w	d4,d3
	addq.w	#1,d3			; W+1 words
	cmp.w	d2,d3
	bls.s	.full
	move.w	d2,d3			; clipped at the right
	move.w	d4,a_mod
	sub.w	d3,a_mod
	move.w	a_mod,d2
	add.w	d2,d2
	move.w	d2,a_mod		; (W - n) * 2
	move.w	d4,d2
	mulu	#5,d2
	sub.w	d3,d2
	add.w	d2,d2
	move.w	d2,b_mod		; (5W - n) * 2
	move.w	d0,d2
	and.w	#15,d2
	move.w	#$ffff,d7
	lsl.w	d2,d7
	move.w	d7,l_mask
	bra.s	.go
.full	move.w	#-2,a_mod
	move.w	d4,d2
	lsl.w	#2,d2
	subq.w	#1,d2
	add.w	d2,d2
	move.w	d2,b_mod		; (4W - 1) * 2
	clr.w	l_mask
.go	move.w	d1,d7			; offset = y * 200 + column * 2
	mulu	#ROWB,d7
	add.w	d6,d6
	add.l	d6,d7
	move.w	d3,d6			; d6 = words
	move.w	d0,d2
	and.w	#15,d2
	ror.w	#4,d2			; shift << 12
	move.w	d4,d1
	add.w	d1,d1			; W * 2 (next plane in the image)
	lea	CUSTOM,a0
	move.l	a3,d0
	add.l	d7,d0			; destination
	moveq	#PLANES-1,d3
.pl	bsr	wait_blit
	move.w	d2,d4
	or.w	#$0fca,d4
	move.w	d4,$40(a0)
	move.w	d2,$42(a0)
	move.w	#$ffff,$44(a0)
	move.w	l_mask,$46(a0)
	move.w	a_mod,$64(a0)
	move.w	b_mod,$62(a0)
	move.w	#ROWB,d4
	sub.w	d6,d4
	sub.w	d6,d4
	move.w	d4,$60(a0)
	move.w	d4,$66(a0)
	move.l	a2,$50(a0)
	move.l	a1,$4c(a0)
	move.l	d0,$48(a0)
	move.l	d0,$54(a0)
	move.w	d5,d4
	lsl.w	#6,d4
	or.w	d6,d4
	move.w	d4,$58(a0)
	add.w	d1,a1			; next plane
	add.l	#SCRW,d0
	dbf	d3,.pl
.x	movem.l	(sp)+,d2-d3/a0
	rts

; k_setbg: a0 = packed screen -> background, both screens; all bobs forgotten
k_setbg:
	movem.l	d0-d2/a0-a2,-(sp)
	bsr	wait_blit
	move.l	background,a1
	move.l	#SCRSIZE,d0
	bsr	unrle
	bsr	copy_bg
	movem.l	(sp)+,d0-d2/a0-a2
	rts

copy_bg:				; background -> both screens
	movem.l	d0/a0-a2,-(sp)
	bsr	wait_blit
	move.l	background,a0
	move.l	screen0,a1
	move.l	screen1,a2
	move.w	#SCRSIZE/16-1,d0
.c	move.l	(a0),(a1)+
	move.l	(a0)+,(a2)+
	move.l	(a0),(a1)+
	move.l	(a0)+,(a2)+
	move.l	(a0),(a1)+
	move.l	(a0)+,(a2)+
	move.l	(a0),(a1)+
	move.l	(a0)+,(a2)+
	dbf	d0,.c
	clr.l	nrect
	movem.l	(sp)+,d0/a0-a2
	rts

clear_bg:				; background colour 0 everywhere
	movem.l	d0/a0,-(sp)
	bsr	wait_blit
	move.l	background,a0
	move.w	#SCRSIZE/4-1,d0
.c	clr.l	(a0)+
	dbf	d0,.c
	bsr	copy_bg
	movem.l	(sp)+,d0/a0
	rts

unrle:					; a0 = packed, a1 = out, d0 = bytes out
	movem.l	d0-d2/a0-a2,-(sp)
	move.l	a1,a2
	add.l	d0,a2
.loop	moveq	#0,d1
	move.b	(a0)+,d1
	bmi.s	.run
.lit	move.b	(a0)+,(a1)+
	dbf	d1,.lit
	bra.s	.chk
.run	and.w	#$7f,d1
	addq.w	#2,d1
	move.b	(a0)+,d2
.rep	move.b	d2,(a1)+
	dbf	d1,.rep
.chk	cmp.l	a2,a1
	blo.s	.loop
	movem.l	(sp)+,d0-d2/a0-a2
	rts

;------------------------------------------------------------------ text
; k_text: a0 = text, d0 = x, d1 = y, d2 = colour, d3 = paper (-1: none) - all three screens
k_text:
	movem.l	d0-d7/a0-a4,-(sp)
	sf	big
	bra.s	text_all
k_text2:
	movem.l	d0-d7/a0-a4,-(sp)
	st	big
text_all:
	bsr	wait_blit
	lsr.w	#3,d0
	move.w	d0,d6			; byte column
	move.l	a0,a4
	move.l	background,a3
	bsr.s	text_on
	move.l	a4,a0
	move.l	screen0,a3
	bsr.s	text_on
	move.l	a4,a0
	move.l	screen1,a3
	bsr.s	text_on
	movem.l	(sp)+,d0-d7/a0-a4
	rts

; text_on: a0 = text, d6 = column, d1 = y, d2 = colour, d3 = paper, a3 = screen
text_on:
	movem.l	d1/d6/a0,-(sp)
.ch	moveq	#0,d0
	move.b	(a0)+,d0
	beq.s	.x
	cmp.b	#10,d0			; (new line)
	bne.s	.nl
	move.l	4(sp),d6
	add.w	#10,d1
	tst.b	big
	beq.s	.ch
	addq.w	#8,d1
	bra.s	.ch
.nl	sub.b	#32,d0
	bcs.s	.sk
	cmp.b	#96,d0
	bhs.s	.sk
	lsl.w	#3,d0
	lea	font8,a1
	add.w	d0,a1
	tst.b	big
	bne.s	.big
	bsr	glyph8
	addq.w	#1,d6
	bra.s	.ch
.big	bsr	glyph16
	addq.w	#2,d6
	bra.s	.ch
.sk	addq.w	#1,d6
	tst.b	big
	beq.s	.ch
	addq.w	#1,d6
	bra.s	.ch
.x	movem.l	(sp)+,d1/d6/a0
	rts

; glyph8: a1 = 8 bytes, d6 = column, d1 = y, d2 = colour, d3 = paper, a3 = screen
glyph8:
	movem.l	d0-d7/a1-a2,-(sp)
	cmp.w	#40,d6
	bhs.s	.x
	move.w	d1,d0
	mulu	#ROWB,d0
	add.w	d6,d0
	lea	(a3,d0.l),a2
	moveq	#7,d7
.row	cmp.w	#256,d1
	bhs.s	.x
	move.b	(a1)+,d4
	bsr	put_byte
	lea	ROWB(a2),a2
	addq.w	#1,d1
	dbf	d7,.row
.x	movem.l	(sp)+,d0-d7/a1-a2
	rts

; put_byte: d4 = pixels at a2 (5 planes, 40 apart), d2 = colour, d3 = paper (-1: none)
put_byte:
	movem.l	d0-d1/d5-d6/a2,-(sp)
	move.b	d4,d6
	not.b	d6
	moveq	#0,d0			; plane
.p	moveq	#0,d5
	btst	d0,d2
	beq.s	.f
	move.b	d4,d5
.f	tst.w	d3
	bmi.s	.tr
	btst	d0,d3
	beq.s	.w
	or.b	d6,d5
	bra.s	.w
.tr	move.b	(a2),d1			; (no paper: keep what is under it)
	and.b	d6,d1
	or.b	d1,d5
.w	move.b	d5,(a2)
	lea	SCRW(a2),a2
	addq.w	#1,d0
	cmp.w	#PLANES,d0
	blo.s	.p
	movem.l	(sp)+,d0-d1/d5-d6/a2
	rts

; glyph16: twice as big
glyph16:
	movem.l	d0-d7/a0-a2,-(sp)
	move.w	d6,d0
	addq.w	#1,d0
	cmp.w	#40,d0
	bhs.s	.x
	move.w	d1,d0
	mulu	#ROWB,d0
	add.w	d6,d0
	lea	(a3,d0.l),a2
	moveq	#7,d7
.row	moveq	#0,d0
	move.b	(a1)+,d0
	add.w	d0,d0
	lea	dbl_tab,a0
	move.w	(a0,d0.w),d0		; the 16 pixels
	moveq	#1,d5			; two lines
.ln	cmp.w	#256,d1
	bhs.s	.x
	move.w	d0,d4
	lsr.w	#8,d4
	bsr	put_byte
	addq.l	#1,a2
	move.b	d0,d4
	bsr	put_byte
	subq.l	#1,a2
	lea	ROWB(a2),a2
	addq.w	#1,d1
	dbf	d5,.ln
	dbf	d7,.row
.x	movem.l	(sp)+,d0-d7/a0-a2
	rts

strlen:					; a0 -> d0 (up to a 0 or a new line)
	move.l	a0,-(sp)
	moveq	#0,d0
.l	tst.b	(a0)
	beq.s	.x
	cmp.b	#10,(a0)+
	beq.s	.x
	addq.w	#1,d0
	bra.s	.l
.x	move.l	(sp)+,a0
	rts

k_ctext:
	move.l	d0,-(sp)
	bsr	strlen
	neg.w	d0
	add.w	#40,d0
	asr.w	#1,d0
	bpl.s	.p
	moveq	#0,d0
.p	lsl.w	#3,d0
	bsr	k_text
	move.l	(sp)+,d0
	rts

k_ctext2:
	move.l	d0,-(sp)
	bsr	strlen
	add.w	d0,d0
	neg.w	d0
	add.w	#40,d0
	asr.w	#1,d0
	bpl.s	.p
	moveq	#0,d0
.p	lsl.w	#3,d0
	bsr	k_text2
	move.l	(sp)+,d0
	rts

; k_fill: d0 = x, d1 = y, d2 = width, d3 = height, d4 = colour (all three screens)
k_fill:
	movem.l	d0-d7/a0-a3,-(sp)
	bsr	wait_blit
	lsr.w	#3,d0
	lsr.w	#3,d2
	subq.w	#1,d2
	bmi.s	.x
	subq.w	#1,d3
	bmi.s	.x
	move.l	background,a3
	bsr.s	.one
	move.l	screen0,a3
	bsr.s	.one
	move.l	screen1,a3
	bsr.s	.one
.x	movem.l	(sp)+,d0-d7/a0-a3
	rts
.one	move.w	d1,-(sp)
	move.w	d1,d5
	move.w	d3,d6
.row	cmp.w	#256,d5
	bhs.s	.n
	move.w	d5,d7
	mulu	#ROWB,d7
	add.w	d0,d7
	lea	(a3,d7.l),a0
	moveq	#0,d7			; plane
.p	move.l	a0,a1
	moveq	#0,d1
	btst	d7,d4
	beq.s	.z
	moveq	#-1,d1
.z	move.w	d2,-(sp)
.b	move.b	d1,(a1)+
	dbf	d2,.b
	move.w	(sp)+,d2
	lea	SCRW(a0),a0
	addq.w	#1,d7
	cmp.w	#PLANES,d7
	blo.s	.p
.n	addq.w	#1,d5
	dbf	d6,.row
	move.w	(sp)+,d1
	rts

;------------------------------------------------------------------ colours
; k_pal: a0 = 32 colours (25-31: the player's)
k_pal:
	movem.l	d0/a0-a1,-(sp)
	lea	cur_pal,a1
	moveq	#24,d0
.c	move.w	(a0)+,(a1)+
	dbf	d0,.c
	bsr	player_colours
	bsr	write_colours
	movem.l	(sp)+,d0/a0-a1
	rts

; k_playerpal: a0 = 7 colours for 25-31, or 0 = the player's own
k_playerpal:
	movem.l	d0/a0-a1,-(sp)
	move.l	a0,d0
	bne.s	.o
	bsr	player_colours
	bra.s	.w
.o	lea	cur_pal+50,a1
	moveq	#6,d0
.c	move.w	(a0)+,(a1)+
	dbf	d0,.c
.w	bsr	write_colours
	movem.l	(sp)+,d0/a0-a1
	rts

; player_colours: colours 25-31 from the current player (cur_ctx)
player_colours:
	movem.l	d0-d1/a0-a2,-(sp)
	move.l	cur_ctx,a2
	lea	cur_pal+50,a1
	move.w	CX_HAIR(a2),d0
	add.w	d0,d0
	lea	hair_cols,a0
	move.w	(a0,d0.w),(a1)+		; 25 hair
	move.w	CX_SKIN(a2),d0
	add.w	d0,d0
	add.w	d0,d0
	lea	skin_cols,a0
	move.w	(a0,d0.w),(a1)+		; 26 skin
	move.w	2(a0,d0.w),(a1)+	; 27 skin shade
	move.w	CX_CTRY(a2),d0
	lsl.w	#3,d0
	lea	kit_cols,a0
	add.w	d0,a0
	move.w	(a0)+,(a1)+		; 28 shirt
	move.w	(a0)+,(a1)+		; 29 shirt shade
	move.w	(a0)+,(a1)+		; 30 shorts
	move.w	(a0)+,(a1)+		; 31 shoes
	movem.l	(sp)+,d0-d1/a0-a2
	rts

; kit of a country (d0) -> a0 = 7 colours (as for K_PLAYERPAL; hair, skin from the table)
ctry_kit:
	movem.l	d0-d1/a1,-(sp)
	lea	opp_cols,a0
	move.w	#$321,(a0)
	move.w	#$c96,2(a0)
	move.w	#$a74,4(a0)
	lsl.w	#3,d0
	lea	kit_cols,a1
	add.w	d0,a1
	move.l	(a1)+,6(a0)
	move.l	(a1)+,10(a0)
	movem.l	(sp)+,d0-d1/a1
	rts

; write_colours: cur_pal and the gradient into the copper list, at the fade level
write_colours:
	movem.l	d0-d4/a0-a2,-(sp)
	lea	cur_pal,a0
	lea	cop_col,a1
	move.w	#$180,d1
	moveq	#31,d2
.c	move.w	d1,(a1)+
	move.w	(a0)+,d0
	bsr	fade_col
	move.w	d0,(a1)+
	addq.w	#2,d1
	dbf	d2,.c
	lea	cop_grad,a1
	move.l	grad_ptr,d0
	beq.s	.end
	move.l	d0,a0
	moveq	#GRADMAX-1,d2
.g	move.w	(a0)+,d3		; line
	bmi.s	.end
	add.w	#$2c,d3
	cmp.w	#$ff,d3
	bhi.s	.end
	lsl.w	#8,d3
	or.w	#$07,d3
	move.w	d3,(a1)+
	move.w	#$fffe,(a1)+
	move.w	#$0180,(a1)+
	move.w	(a0)+,d0
	bsr	fade_col
	move.w	d0,(a1)+
	dbf	d2,.g
.end	move.l	#$fffffffe,(a1)
	movem.l	(sp)+,d0-d4/a0-a2
	rts

fade_col:				; d0 = colour -> at fade level
	movem.l	d1-d3,-(sp)
	move.w	fade_lvl,d3
	cmp.w	#16,d3
	bhs.s	.x
	move.w	d0,d1
	lsr.w	#8,d1
	and.w	#15,d1
	mulu	d3,d1
	lsr.w	#4,d1
	lsl.w	#8,d1
	move.w	d0,d2
	lsr.w	#4,d2
	and.w	#15,d2
	mulu	d3,d2
	lsr.w	#4,d2
	lsl.w	#4,d2
	or.w	d2,d1
	and.w	#15,d0
	mulu	d3,d0
	lsr.w	#4,d0
	or.w	d1,d0
.x	movem.l	(sp)+,d1-d3
	rts

; k_grad: a0 = gradient list or 0
k_grad:
	move.l	a0,grad_ptr
	bra	write_colours

k_fadein:
	movem.l	d0-d1,-(sp)
	moveq	#0,d1
.l	move.w	d1,fade_lvl
	bsr	write_colours
	bsr	vsync
	addq.w	#2,d1
	cmp.w	#16,d1
	bls.s	.l
	movem.l	(sp)+,d0-d1
	rts

k_fadeout:
	movem.l	d0-d1,-(sp)
	moveq	#16,d1
.l	move.w	d1,fade_lvl
	bsr	write_colours
	bsr	vsync
	subq.w	#2,d1
	bpl.s	.l
	clr.w	fade_lvl
	bsr	write_black
	movem.l	(sp)+,d0-d1
	rts

write_black:				; level 0 (dark) until the next fade in
	clr.w	fade_lvl
	bra	write_colours

vsync:					; wait for the next frame
	move.l	d0,-(sp)
	move.l	framecount,d0
.w	cmp.l	framecount,d0
	beq.s	.w
	move.l	(sp)+,d0
	rts

;==============================================================================
;  small things
;==============================================================================
k_frames:
	move.l	framecount,d0
	rts

random:
	movem.l	d1-d2,-(sp)
	move.l	seed,d0
	move.l	d0,d1
	moveq	#13,d2
	lsl.l	d2,d1
	eor.l	d1,d0
	move.l	d0,d1
	moveq	#17,d2
	lsr.l	d2,d1
	eor.l	d1,d0
	move.l	d0,d1
	lsl.l	#5,d1
	eor.l	d1,d0
	move.l	d0,seed
	movem.l	(sp)+,d1-d2
	rts

k_rand:					; d0.w = n -> d0.l = 0..n-1
	move.l	d3,-(sp)
	move.w	d0,d3
	bsr	random
	swap	d0
	mulu	d3,d0
	clr.w	d0
	swap	d0
	move.l	(sp)+,d3
	rts

; k_num: d0.l = number, d1.w = minimum digits -> a0 = text
k_num:
	movem.l	d0-d4/a1,-(sp)
	lea	numbuf+12,a0
	clr.b	(a0)
	moveq	#0,d3			; digits
	tst.l	d0
	bpl.s	.d
	moveq	#0,d0
.d	move.l	d0,d2			; d0 / 10 in two steps (any 32 bit number)
	clr.w	d2
	swap	d2
	divu	#10,d2
	move.w	d2,d4			; high quotient
	move.w	d0,d2
	divu	#10,d2			; (remainder << 16 | low) / 10
	move.l	d2,d0
	swap	d0			; the digit
	add.b	#'0',d0
	move.b	d0,-(a0)
	addq.w	#1,d3
	moveq	#0,d0
	move.w	d4,d0
	swap	d0
	move.w	d2,d0
	tst.l	d0
	bne.s	.d
	cmp.w	d1,d3
	bge.s	.x
	moveq	#0,d0
	bra.s	.d
.x	movem.l	(sp)+,d0-d4/a1
	rts

; k_wait: d0 = frames (25 a second), d1 = 1: fire / return ends it -> d0 = 1 if so
k_wait:
	movem.l	d1-d4,-(sp)
	move.w	d0,d3
	move.w	d1,d4
	bsr	k_input			; (forget old presses)
.l	bsr	vsync
	bsr	vsync
	tst.w	d4
	beq.s	.n
	bsr	k_input
	and.w	#(1<<J_FIRE)|(1<<J_ESC),d1
	bne.s	.fire
.n	subq.w	#1,d3
	bgt.s	.l
	moveq	#0,d0
	bra.s	.x
.fire	moveq	#1,d0
.x	movem.l	(sp)+,d1-d4
	rts

;==============================================================================
;  input: joystick in port 2, keyboard
;==============================================================================
k_input:
	move.l	d3,-(sp)
	bsr.s	.in
	move.l	(sp)+,d3
	rts
.in	move.w	#$4000,CUSTOM+$9a
	move.w	joy_now,d0
	move.w	acc_act,d1
	clr.w	acc_act
	moveq	#0,d2
	move.w	kq_r,d3			; one key from the queue
	cmp.w	kq_w,d3
	beq.s	.nk
	move.l	a0,-(sp)
	lea	kqueue,a0
	move.b	(a0,d3.w),d2
	addq.w	#1,d3
	and.w	#15,d3
	move.w	d3,kq_r
	move.l	(sp)+,a0
.nk	move.w	#$c000,CUSTOM+$9a
	rts

read_input:
	moveq	#0,d0
	move.w	CUSTOM+$00c,d1		; joystick in port 2
	btst	#1,d1
	beq.s	.nr
	bset	#J_RIGHT,d0
.nr	btst	#9,d1
	beq.s	.nl
	bset	#J_LEFT,d0
.nl	move.w	d1,d2
	lsr.w	#1,d2
	eor.w	d1,d2
	btst	#0,d2
	beq.s	.nd
	bset	#J_DOWN,d0
.nd	btst	#8,d2
	beq.s	.nu
	bset	#J_UP,d0
.nu	btst	#7,$bfe001
	bne.s	.nf
	bset	#J_FIRE,d0
.nf	btst	#6,$bfe001		; (the left mouse button fires too)
	bne.s	.nm
	bset	#J_FIRE,d0
.nm	or.w	keys_held,d0
	move.w	d0,joy_now
	move.w	joy_prev,d1
	move.w	d0,joy_prev
	not.w	d1
	and.w	d1,d0
	or.w	d0,acc_act
	moveq	#3,d6
.kb	move.b	$bfed01,d1
	btst	#3,d1
	beq	.kdone
	move.b	$bfec01,d2
	bset	#6,$bfee01
	moveq	#3,d3
	bsr	wait_lines
	bclr	#6,$bfee01
	not.b	d2
	ror.b	#1,d2
	and.w	#$ff,d2
	moveq	#0,d1			; released: bit 7
	bclr	#7,d2
	beq.s	.down
	moveq	#1,d1
.down	lea	keymap,a0		; keys that act as the joystick
.km	move.b	(a0)+,d3
	bmi.s	.asc
	move.b	(a0)+,d4
	cmp.b	d2,d3
	bne.s	.km
	tst.w	d1
	bne.s	.rel
	move.w	keys_held,d5
	bset	d4,d5
	move.w	d5,keys_held
	move.w	acc_act,d5
	bset	d4,d5
	move.w	d5,acc_act
	bra.s	.km
.rel	move.w	keys_held,d5
	bclr	d4,d5
	move.w	d5,keys_held
	bra.s	.km
.asc	tst.w	d1
	bne.s	.knext
	cmp.b	#$59,d2			; WHDLoad: F10 quits to Workbench
	bne.s	.nq
	tst.b	whd_mode
	beq.s	.nq
	st	quit_now
.nq	cmp.b	#$37,d2			; M: music on / off
	bne.s	.nmu
	tst.b	typing
	bne.s	.nmu
	not.b	music_off
.nmu	cmp.b	#$68,d2
	bhs.s	.knext
	lea	asciimap,a0
	move.b	(a0,d2.w),d3
	beq.s	.knext
	move.w	kq_w,d4
	lea	kqueue,a0
	move.b	d3,(a0,d4.w)
	addq.w	#1,d4
	and.w	#15,d4
	cmp.w	kq_r,d4
	beq.s	.knext			; (full)
	move.w	d4,kq_w
.knext	dbf	d6,.kb
.kdone	rts

;==============================================================================
;  sound: music on channels 0 and 1 (quiet), effects on 2 and 3
;==============================================================================
music_init:
	movem.l	d0/a5,-(sp)
	lea	CUSTOM,a5
	move.l	#inst_square,$a0(a5)
	move.w	#16,$a4(a5)
	move.w	#400,$a6(a5)
	clr.w	$a8(a5)
	move.l	#inst_tri,$b0(a5)
	move.w	#16,$b4(a5)
	move.w	#400,$b6(a5)
	clr.w	$b8(a5)
	move.l	#snd_null,$c0(a5)
	move.w	#2,$c4(a5)
	move.l	#snd_null,$d0(a5)
	move.w	#2,$d4(a5)
	move.w	#$820f,$96(a5)		; all four channels run for ever
	clr.l	mus_ptr
	clr.l	mus_ptr+4
	clr.l	sfx_st
	movem.l	(sp)+,d0/a5
	rts

; k_song: a0 = melody, a1 = bass (a0 = 0: stop)
k_song:
	move.l	a0,d0
	beq.s	song_stop
	move.w	#$4000,CUSTOM+$9a
	move.l	a0,mus_ptr
	move.l	a1,mus_ptr+4
	move.l	a0,mus_start
	move.l	a1,mus_start+4
	move.w	#1,mus_left
	move.w	#1,mus_left+2
	move.w	#$c000,CUSTOM+$9a
	rts
song_stop:
	move.w	#$4000,CUSTOM+$9a
	clr.l	mus_ptr
	clr.l	mus_ptr+4
	clr.w	CUSTOM+$a8
	clr.w	CUSTOM+$b8
	move.w	#$c000,CUSTOM+$9a
	rts

; k_sfx: a0 = sound, d1 = volume
k_sfx:
	movem.l	d0-d2/a0-a1,-(sp)
	moveq	#0,d2			; channel 2 or 3 in turn
	not.b	sfx_next
	beq.s	.c
	moveq	#1,d2
.c	move.w	#$4000,CUSTOM+$9a
	lea	sfx_st,a1
	move.b	#1,(a1,d2.w)
	add.w	d2,d2
	lea	sfx_reqv,a1
	move.w	d1,(a1,d2.w)
	add.w	d2,d2
	lea	sfx_reqp,a1
	move.l	a0,(a1,d2.w)
	move.w	#$c000,CUSTOM+$9a
	movem.l	(sp)+,d0-d2/a0-a1
	rts

; k_csfx: d0 = common sound, d1 = volume
k_csfx:
	movem.l	d0/a0,-(sp)
	lea	csnd_tab,a0
	lsl.w	#2,d0
	move.l	(a0,d0.w),a0
	bsr	k_sfx
	movem.l	(sp)+,d0/a0
	rts

sound_tick:
	movem.l	d0-d3/a0-a1/a5,-(sp)
	lea	CUSTOM+$a0,a5
	moveq	#0,d1			; effects on channels 2 and 3
.p	lea	sfx_st,a0
	move.b	(a0,d1.w),d2
	beq.s	.pn
	move.w	d1,d0
	addq.w	#2,d0
	moveq	#1,d3
	lsl.w	d0,d3
	lsl.w	#4,d0
	cmp.b	#1,d2
	bne.s	.p2
	move.w	d3,CUSTOM+$96		; 1: channel off, new sample in
	move.w	d1,d2
	lsl.w	#2,d2
	lea	sfx_reqp,a1
	move.l	(a1,d2.w),a1
	move.l	(a1)+,0(a5,d0.w)
	move.w	(a1)+,4(a5,d0.w)
	move.w	(a1)+,6(a5,d0.w)
	move.w	d1,d2
	add.w	d2,d2
	lea	sfx_reqv,a1
	move.w	(a1,d2.w),8(a5,d0.w)
	move.b	#2,(a0,d1.w)
	bra.s	.pn
.p2	cmp.b	#2,d2
	bne.s	.p3
	or.w	#$8200,d3		; 2: channel on
	move.w	d3,CUSTOM+$96
	move.b	#3,(a0,d1.w)
	bra.s	.pn
.p3	move.l	#snd_null,0(a5,d0.w)	; 3: after the sample, loop silence
	move.w	#2,4(a5,d0.w)
	clr.b	(a0,d1.w)
.pn	addq.w	#1,d1
	cmp.w	#2,d1
	blo	.p
	moveq	#0,d1			; music channels
.ch	move.w	d1,d0
	lsl.w	#2,d0
	lea	mus_ptr,a0
	move.l	(a0,d0.w),d2
	beq	.next
	move.l	d2,a1
	move.w	d1,d3
	add.w	d3,d3
	lea	mus_left,a0
	subq.w	#1,(a0,d3.w)
	bne.s	.decay
.note	move.w	(a1)+,d2		; period
	cmp.w	#$fffe,d2
	blo.s	.play
	beq.s	.end			; $fffe: the end (an anthem: played once)
	lea	mus_start,a0		; $ffff: again from the start
	move.l	(a0,d0.w),a1
	bra.s	.note
.end	lea	mus_ptr,a0
	clr.l	(a0,d0.w)
	move.w	d1,d3
	lsl.w	#4,d3
	clr.w	8(a5,d3.w)		; (silent)
	bra	.next
.play	move.w	(a1)+,d3
	lea	mus_ptr,a0
	move.l	a1,(a0,d0.w)
	move.w	d1,d0
	add.w	d0,d0
	lea	mus_left,a0
	move.w	d3,(a0,d0.w)
	lea	mus_vol,a0
	move.w	#MUSIC_VOL,(a0,d0.w)
	tst.w	d2
	bne.s	.per
	clr.w	(a0,d0.w)		; rest
	bra.s	.setv
.per	move.w	d1,d3
	lsl.w	#4,d3
	move.w	d2,6(a5,d3.w)
	bra.s	.setv
.decay	lea	mus_vol,a0
	moveq	#MUSIC_VOL/3,d2
	cmp.w	(a0,d3.w),d2
	bhs.s	.setv
	subq.w	#1,(a0,d3.w)
.setv	move.w	d1,d3
	add.w	d3,d3
	lea	mus_vol,a0
	move.w	(a0,d3.w),d2
	tst.b	music_off
	beq.s	.on
	moveq	#0,d2
.on	lsl.w	#3,d3
	move.w	d2,8(a5,d3.w)
.next	addq.w	#1,d1
	cmp.w	#2,d1
	blo	.ch
	movem.l	(sp)+,d0-d3/a0-a1/a5
	rts

;==============================================================================
;  the vertical blank interrupt: the screen swap, sound, input
;==============================================================================
vbl_irq:
	movem.l	d0-d7/a0-a6,-(sp)
	lea	CUSTOM,a5
	move.w	#$0020,$9c(a5)
	move.w	#$0020,$9c(a5)
	addq.l	#1,framecount
	tst.b	swap_req
	beq.s	.ns
	move.l	framecount,d0
	sub.l	last_swap,d0
	cmp.l	#2,d0
	blo.s	.ns
	move.l	swap_ptr,d0
	bsr	set_bpl
	move.l	framecount,last_swap
	sf	swap_req
.ns	bsr	sound_tick
	bsr	read_input
	movem.l	(sp)+,d0-d7/a0-a6
	rte

;==============================================================================
;  loading an event: a hunk file into the event memory (no AllocMem)
;==============================================================================
; load_event: a0 = file name -> d0 = the first hunk (0 = failed)
load_event:
	movem.l	d1-d7/a0-a6,-(sp)
	move.l	a0,ev_name
	bsr	song_stop
	bsr	os_back
	move.l	#ev_any,any_ptr
	move.l	ev_chip,chip_ptr
	clr.l	buf_left
	move.l	dosbase,a6
	move.l	ev_name,d1
	move.l	#1005,d2
	jsr	_LVOOpen(a6)
	move.l	d0,fh
	beq	.fail
	bsr	get_long
	cmp.l	#$3f3,d0
	bne	.bad
	bsr	get_long		; no resident library names
	tst.l	d0
	bne	.bad
	bsr	get_long
	cmp.l	#MAXHUNKS,d0
	bhi	.bad
	move.w	d0,nhunks
	bsr	get_long		; first
	bsr	get_long		; last
	moveq	#0,d7
.alloc	cmp.w	nhunks,d7
	bhs.s	.hunks
	bsr	get_long
	move.l	d0,d2
	and.l	#$3fffffff,d0
	lsl.l	#2,d0			; bytes
	addq.l	#7,d0
	and.w	#$fff8,d0
	lea	any_ptr,a1
	move.l	#ev_any+EV_ANY_SIZE,d3
	btst	#30,d2
	beq.s	.nc
	lea	chip_ptr,a1
	move.l	ev_chip,d3
	add.l	#EV_CHIP_SIZE,d3
.nc	move.l	(a1),a0
	add.l	d0,(a1)
	cmp.l	(a1),d3
	blo	.bad			; (does not fit)
	move.w	d7,d3
	lsl.w	#2,d3
	lea	hunk_base,a2
	move.l	a0,(a2,d3.w)
	lea	hunk_size,a2
	move.l	d0,(a2,d3.w)
	lsr.l	#2,d0			; clear it
	subq.l	#1,d0
.clr	clr.l	(a0)+
	subq.l	#1,d0
	bpl.s	.clr
	addq.w	#1,d7
	bra.s	.alloc
.hunks	moveq	#0,d7			; current hunk
.type	cmp.w	nhunks,d7
	bhs	.done
	bsr	get_long
	and.l	#$3fffffff,d0
	cmp.l	#$3e9,d0
	beq.s	.data
	cmp.l	#$3ea,d0
	beq.s	.data
	cmp.l	#$3eb,d0
	beq.s	.bss
	cmp.l	#$3ec,d0
	beq.s	.reloc
	cmp.l	#$3f2,d0
	beq.s	.end
	cmp.l	#HUNK_PACKED,d0
	beq.s	.pack
	bra	.bad
.pack	lea	hunk_base,a0		; a crunched hunk (the floppy version)
	move.w	d7,d3
	lsl.w	#2,d3
	move.l	(a0,d3.w),a1
	lea	hunk_size,a0
	move.l	(a0,d3.w),d2
	bsr	unpack_hunk
	tst.l	d0
	beq	.bad
	bra	.type
.data	bsr	get_long
	lsl.l	#2,d0
	move.l	d0,d1
	lea	hunk_base,a0
	move.w	d7,d3
	lsl.w	#2,d3
	move.l	(a0,d3.w),a0
	bsr	read_block
	tst.l	d0
	beq	.bad
	bra	.type
.bss	bsr	get_long
	bra	.type
.end	addq.w	#1,d7
	bra	.type
.reloc	lea	hunk_base,a0
	move.w	d7,d3
	lsl.w	#2,d3
	move.l	(a0,d3.w),a2		; this hunk
.rl	bsr	get_long
	tst.l	d0
	beq	.type
	move.l	d0,d6			; count
	bsr	get_long
	cmp.w	nhunks,d0
	bhs	.bad
	lsl.w	#2,d0
	lea	hunk_base,a0
	move.l	(a0,d0.w),d5		; target base
.ro	bsr	get_long
	add.l	d5,(a2,d0.l)
	subq.l	#1,d6
	bne.s	.ro
	bra.s	.rl
.done	move.l	fh,d1
	move.l	dosbase,a6
	jsr	_LVOClose(a6)
	bsr	os_away
	move.l	hunk_base,d0
	movem.l	(sp)+,d1-d7/a0-a6
	rts
.bad	move.l	fh,d1
	move.l	dosbase,a6
	jsr	_LVOClose(a6)
.fail	bsr	os_away
	moveq	#0,d0
	movem.l	(sp)+,d1-d7/a0-a6
	rts

refill:
	movem.l	d1-d3/a0-a1/a6,-(sp)
	move.l	dosbase,a6
	move.l	fh,d1
	move.l	#iobuf,d2
	move.l	#IOBUFSIZE,d3
	jsr	_LVORead(a6)
	tst.l	d0
	bpl.s	.ok
	moveq	#0,d0
.ok	move.l	d0,buf_left
	move.l	#iobuf,buf_ptr
	movem.l	(sp)+,d1-d3/a0-a1/a6
	rts

get_byte:
	tst.l	buf_left
	bne.s	.have
	bsr	refill
	tst.l	buf_left
	bne.s	.have
	moveq	#0,d0
	rts
.have	move.l	a0,-(sp)
	move.l	buf_ptr,a0
	moveq	#0,d0
	move.b	(a0)+,d0
	move.l	a0,buf_ptr
	subq.l	#1,buf_left
	move.l	(sp)+,a0
	rts

get_long:
	move.l	d1,-(sp)
	bsr	get_byte
	move.l	d0,d1
	bsr	get_byte
	lsl.l	#8,d1
	or.b	d0,d1
	bsr	get_byte
	lsl.l	#8,d1
	or.b	d0,d1
	bsr	get_byte
	lsl.l	#8,d1
	or.b	d0,d1
	move.l	d1,d0
	move.l	(sp)+,d1
	rts

; read_block: a0 = destination, d1 = bytes -> d0 = 1 ok
read_block:
	movem.l	d1-d3/a0-a1/a6,-(sp)
.drain	tst.l	d1
	beq.s	.ok
	tst.l	buf_left
	beq.s	.direct
	bsr	get_byte
	move.b	d0,(a0)+
	subq.l	#1,d1
	bra.s	.drain
.direct	move.l	d1,d3
	move.l	d1,-(sp)
	move.l	a0,-(sp)
	move.l	dosbase,a6
	move.l	fh,d1
	move.l	a0,d2
	jsr	_LVORead(a6)
	move.l	(sp)+,a0
	move.l	(sp)+,d1
	tst.l	d0
	ble.s	.err
	add.l	d0,a0
	sub.l	d0,d1
	bne.s	.direct
.ok	moveq	#1,d0
	bra.s	.x
.err	moveq	#0,d0
.x	movem.l	(sp)+,d1-d3/a0-a1/a6
	rts

	include	"depack.s"

;==============================================================================
;  the records file
;==============================================================================
load_records:
	movem.l	d0-d4/a0-a1/a6,-(sp)
	move.l	dosbase,d0
	beq.s	.def
	move.l	d0,a6
	move.l	#recname,d1
	move.l	#1005,d2
	jsr	_LVOOpen(a6)
	move.l	d0,d4
	beq.s	.def
	move.l	d4,d1
	move.l	#records,d2
	move.l	#REC_SIZE,d3
	jsr	_LVORead(a6)
	move.l	d0,-(sp)
	move.l	d4,d1
	jsr	_LVOClose(a6)
	move.l	(sp)+,d0
	cmp.l	#REC_SIZE,d0
	bne.s	.def
	cmp.l	#'SOR2',records
	beq.s	.x
.def	lea	def_records,a0		; the starting world records
	lea	records,a1
	move.w	#REC_SIZE-1,d0
.c	move.b	(a0)+,(a1)+
	dbf	d0,.c
.x	movem.l	(sp)+,d0-d4/a0-a1/a6
	rts

save_records:
	movem.l	d0-d7/a0-a6,-(sp)
	move.l	#'SOR2',records
	bsr	os_back
	move.l	dosbase,d0
	beq.s	.fail
	move.l	d0,a6
	move.l	#recname,d1
	move.l	#1006,d2
	jsr	_LVOOpen(a6)
	move.l	d0,d4
	beq.s	.fail
	move.l	d4,d1
	move.l	#records,d2
	move.l	#REC_SIZE,d3
	jsr	_LVOWrite(a6)
	move.l	d4,d1
	jsr	_LVOClose(a6)
	tst.b	whd_mode
	bne.s	.fail
	moveq	#50,d1			; let the disk finish
	jsr	_LVODelay(a6)
.fail	bsr	os_away
	movem.l	(sp)+,d0-d7/a0-a6
	rts

	include	"main.s"

;==============================================================================
;  data
;==============================================================================
	section	data,data

gfxname		dc.b	'graphics.library',0
dosname		dc.b	'dos.library',0
recname		dc.b	'Olympics.dat',0
	even
chip_sizes	dc.l	SCRSIZE,SCRSIZE,SCRSIZE,EV_CHIP_SIZE,0
; keys that work as the joystick: raw key, J_ bit
keymap		dc.b	$4c,J_UP,$4d,J_DOWN,$4f,J_LEFT,$4e,J_RIGHT
		dc.b	$40,J_FIRE,$44,J_FIRE,$43,J_FIRE,$45,J_ESC,$5f,J_HELP
		dc.b	-1
	even
; raw key -> character (0 = none); 8 = backspace, 13 = return
asciimap	dc.b	'`1234567890-=\',0,'0'
		dc.b	'QWERTYUIOP[]',0,'123'
		dc.b	'ASDFGHJKL;',39,0,0,'456'
		dc.b	0,'ZXCVBNM,./',0,'.789'
		dc.b	' ',8,0,13,13,27,8,0,0,0,'-',0,0,0,0,0
		dc.b	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
		dc.b	0,0,0,0,0,0,0,0
	even

	include	"main_data.i"

font8		incbin	"font8.bin"
	even

;==============================================================================
	section	chip,data_c
copperlist
	dc.w	$008e,$2c81,$0090,$2cc1,$0092,$0038,$0094,$00d0
	dc.w	$0100,$5200,$0102,$0000,$0104,$0024
	dc.w	$0108,ROWB-SCRW,$010a,ROWB-SCRW
cop_spr	ds.w	8*4
	dc.w	$1001,$fffe
cop_bpl	dc.w	$00e0,0,$00e2,0,$00e4,0,$00e6,0,$00e8,0,$00ea,0
	dc.w	$00ec,0,$00ee,0,$00f0,0,$00f2,0
cop_col	ds.w	32*2
cop_grad
	ds.w	GRADMAX*4+2
spr_null	dc.l	0,0
snd_null	dc.w	0,0
inst_square	dc.b	50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50
		dc.b	-50,-50,-50,-50,-50,-50,-50,-50,-50,-50,-50,-50,-50,-50,-50,-50
inst_tri	dc.b	0,15,30,45,60,75,90,105,120,105,90,75,60,45,30,15
		dc.b	0,-15,-30,-45,-60,-75,-90,-105,-120,-105,-90,-75,-60,-45,-30,-15
main_chip	incbin	"main_chip.bin"
	even

;==============================================================================
	section	vars,bss
stacksave	ds.l	1
wbmsg		ds.l	1
mytask		ds.l	1
gfxbase		ds.l	1
dosbase		ds.l	1
oldview		ds.l	1
old_lof		ds.l	1
old_winptr	ds.l	1
vbr		ds.l	1
old_irq		ds.l	1
framecount	ds.l	1
last_swap	ds.l	1
swap_ptr	ds.l	1
back_ptr	ds.l	1
scr_tab		ds.l	2
grad_ptr	ds.l	1
seed		ds.l	1
cur_ctx		ds.l	1
ev_name		ds.l	1
fh		ds.l	1
buf_left	ds.l	1
buf_ptr		ds.l	1
any_ptr		ds.l	1
chip_ptr	ds.l	1
hunk_base	ds.l	MAXHUNKS
hunk_size	ds.l	MAXHUNKS
mus_ptr		ds.l	2
mus_start	ds.l	2
mus_left	ds.w	2
mus_vol		ds.w	2
sfx_reqp	ds.l	2
sfx_reqv	ds.w	2
sfx_st		ds.b	4
sfx_next	ds.b	1
music_off	ds.b	1
whd_mode	ds.b	1
saved_hw	ds.b	1
os_running	ds.b	1
swap_req	ds.b	1
big		ds.b	1
quit_now	ds.b	1
acc_key		ds.b	1
typing		ds.b	1
	even
kq_r		ds.w	1
kq_w		ds.w	1
kqueue		ds.b	16
nhunks		ds.w	1
front		ds.w	1
nrect		ds.w	2
fade_lvl	ds.w	1
a_mod		ds.w	1
b_mod		ds.w	1
l_mask		ds.w	1
old_intena	ds.w	1
old_dmacon	ds.w	1
old_adkcon	ds.w	1
joy_now		ds.w	1
joy_prev	ds.w	1
acc_act		ds.w	1
keys_held	ds.w	1
cur_pal		ds.w	32
opp_cols	ds.w	8
numbuf		ds.b	16
records		ds.b	REC_SIZE
rects0		ds.b	MAXBOBS*8
rects1		ds.b	MAXBOBS*8
iobuf		ds.b	IOBUFSIZE
	include	"main_vars.s"
screen0		ds.l	1		; chip memory, from AllocMem
screen1		ds.l	1
background	ds.l	1
ev_chip		ds.l	1
ev_any		ds.b	EV_ANY_SIZE

