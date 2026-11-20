;------------------------------------------------------------------------------
;  main.s - Stronkie's Olympics: the menus, making your athlete, the
;  competition, the results, the medals and the world records.
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------

MAXCOMP		equ	7			; 4 players + 3 computer athletes
NAMELEN		equ	10
MENU_N		equ	11
MENU_Y		equ	104
MENU_DY		equ	9
FIELD_N		equ	6
CS_NAME		equ	0			; a competitor
CS_RES		equ	4
CS_SCORE	equ	8
CS_CTRY		equ	12
CS_PL		equ	14
CS_SIZE		equ	16

;==============================================================================
game_main:
	bsr	init_players
	move.l	#players,cur_ctx
	move.w	#1,level
	move.w	#1,nplayers
	move.w	dbg_event,d0		; (test bench: straight into an event)
	beq.s	.cer
	cmp.w	#30,d0
	blo.s	.dbg
	sub.w	#30,d0			; 30 / 31: the ceremonies
	move.w	d0,d7
	bsr	ceremony
	rts
.cer	moveq	#0,d7			; the opening ceremony
	bsr	ceremony
	bra.s	.title
.dbg	subq.w	#1,d0
	move.w	#2,mode
	lea	ev_sel,a0
	st	(a0,d0.w)
	bsr	compete
	rts
.title	tst.b	quit_now
	bne	.x
	bsr	title_screen		; -> d0 = the choice
	tst.b	quit_now
	bne	.x
	cmp.w	#10,d0
	beq	.x
	cmp.w	#7,d0
	bne.s	.n7
	bsr	records_screen
	bra.s	.title
.n7	cmp.w	#8,d0
	bne.s	.n8
	bsr	help_screen
	bra.s	.title
.n8	cmp.w	#4,d0
	bhi.s	.title
	move.w	d0,d7			; 0 all, 1 classic, 2 silly, 3 choose, 4 practice
	moveq	#0,d1
	cmp.w	#3,d7
	blo.s	.md
	moveq	#1,d1
	cmp.w	#4,d7
	bne.s	.md
	moveq	#2,d1
.md	move.w	d1,mode
	bsr	make_players		; -> d0 = 0: back to the title
	tst.w	d0
	beq	.title
	tst.w	mode
	bne.s	.some
	lea	ev_sel,a0		; all / classic / silly
	moveq	#0,d0
.al	moveq	#0,d1
	cmp.w	#1,d7
	bne.s	.a1
	cmp.w	#NCLASSIC,d0
	slo	d1
	bra.s	.a3
.a1	cmp.w	#2,d7
	bne.s	.a2
	cmp.w	#NCLASSIC,d0
	shs	d1
	bra.s	.a3
.a2	st	d1
.a3	move.b	d1,(a0,d0.w)
	addq.w	#1,d0
	cmp.w	#NEV,d0
	blo.s	.al
	tst.b	is_demo			; (the demo: soccer only)
	beq.s	.go
	lea	ev_sel+1,a0
	moveq	#NEV-2,d0
.dm	clr.b	(a0)+
	dbf	d0,.dm
	st	ev_sel
	bra.s	.go
.some	bsr	choose_events		; -> d0 = 0: back
	tst.w	d0
	beq	.title
.go	bsr	compete
	bra	.title
.x	bsr	fade_out
	bsr	song_stop
	rts

init_players:
	lea	players,a0
	moveq	#3,d0
.p	move.l	a0,a1
	moveq	#CX_SIZE/2-1,d1
.c	clr.w	(a1)+
	dbf	d1,.c
	lea	s_player,a1		; "PLAYER 1"
	move.l	a0,a2
.n	move.b	(a1)+,(a2)+
	bne.s	.n
	moveq	#3,d1
	sub.w	d0,d1
	move.w	d1,CX_PLAYER(a0)
	add.b	#'1',d1
	move.b	d1,7(a0)
	moveq	#3,d1
	sub.w	d0,d1
	lea	def_ctry,a1
	add.w	d1,d1
	move.w	(a1,d1.w),CX_CTRY(a0)
	move.w	#1,CX_HAIR(a0)
	lea	CX_SIZE(a0),a0
	dbf	d0,.p
	rts

fade_out:
	tst.w	fade_lvl
	beq.s	.x
	bsr	k_fadeout
.x	rts

menu_screen:
	bsr	fade_out
	move.l	a0,-(sp)
	sub.l	a0,a0
	move.l	a0,grad_ptr
	bsr	write_black
	lea	pal_main,a0
	bsr	k_pal
	move.l	(sp)+,a0
	bsr	k_setbg
	rts

; wait_fire -> d1 = J_ bits pressed (fire or esc)
wait_fire:
	bsr	k_input			; (forget old presses)
.l	bsr	vsync
	tst.b	quit_now
	bne.s	.q
	bsr	k_input
	and.w	#(1<<J_FIRE)|(1<<J_ESC),d1
	beq.s	.l
	rts
.q	moveq	#1<<J_ESC,d1
	rts

copy_str:				; a0 -> a1 (a1 ends on the 0)
	move.b	(a0)+,(a1)+
	bne.s	copy_str
	subq.l	#1,a1
	rts

;==============================================================================
;  the title screen and its menu
;==============================================================================
title_screen:
	lea	title_rle,a0
	bsr	menu_screen
	move.l	#players,cur_ctx
	moveq	#64,d0			; the menu box
	move.w	#MENU_Y-4,d1
	move.w	#192,d2
	move.w	#MENU_N*MENU_DY+6,d3
	moveq	#0,d4
	bsr	k_fill
	lea	s_version,a0
	moveq	#8,d0
	move.w	#246,d1
	moveq	#2,d2
	moveq	#-1,d3
	bsr	k_text
	clr.w	menu_sel
	bsr	draw_menu
	tst.l	mus_ptr
	bne.s	.m
	lea	song_theme_m,a0
	lea	song_theme_b,a1
	bsr	k_song
.m	bsr	k_fadein
	tst.b	said_title
	bne.s	.st
	st	said_title
	lea	v_title,a0
	moveq	#64,d1
	bsr	k_sfx
.st	move.w	#-40,run_x
	bsr	k_input
.loop	bsr	k_begin
	bsr	title_runner
	bsr	k_end
	tst.b	quit_now
	bne	.esc
	bsr	k_input
	btst	#J_UP,d1
	beq.s	.nu
	move.w	menu_sel,d0
	subq.w	#1,d0
	bpl.s	.u
	moveq	#MENU_N-1,d0
.u	bsr	menu_move
.nu	btst	#J_DOWN,d1
	beq.s	.nd
	move.w	menu_sel,d0
	addq.w	#1,d0
	cmp.w	#MENU_N,d0
	blo.s	.d
	moveq	#0,d0
.d	bsr	menu_move
.nd	move.w	d1,d4
	and.w	#(1<<J_LEFT)|(1<<J_RIGHT)|(1<<J_FIRE),d4
	beq	.nf
	move.w	menu_sel,d0
	cmp.w	#5,d0			; players: 1-4
	bne.s	.n3
	moveq	#1,d2
	btst	#J_LEFT,d1
	beq.s	.p
	moveq	#-1,d2
.p	move.w	nplayers,d0
	add.w	d2,d0
	bne.s	.p1
	moveq	#4,d0
.p1	cmp.w	#4,d0
	bls.s	.p2
	moveq	#1,d0
.p2	move.w	d0,nplayers
	bra.s	.redraw
.n3	cmp.w	#6,d0			; level
	bne.s	.n4
	moveq	#1,d2
	btst	#J_LEFT,d1
	beq.s	.l
	moveq	#-1,d2
.l	move.w	level,d0
	add.w	d2,d0
	bpl.s	.l1
	moveq	#2,d0
.l1	cmp.w	#2,d0
	bls.s	.l2
	moveq	#0,d0
.l2	move.w	d0,level
	bra.s	.redraw
.n4	cmp.w	#9,d0			; music
	bne.s	.n7
	not.b	music_off
	bra.s	.redraw
.n7	btst	#J_FIRE,d1
	beq.s	.nf
	moveq	#CS_BEEPHI,d0
	moveq	#40,d1
	bsr	k_csfx
	move.w	menu_sel,d0
	rts
.redraw	moveq	#CS_BEEP,d0
	moveq	#40,d1
	bsr	k_csfx
	move.w	menu_sel,d0
	bsr	draw_item
	bra	.loop
.nf	btst	#J_ESC,d1
	beq	.loop
.esc	moveq	#10,d0
	rts

menu_move:				; d0 = the new selection
	move.w	d1,-(sp)
	move.w	menu_sel,-(sp)
	move.w	d0,menu_sel
	bsr	draw_item
	move.w	(sp)+,d0
	bsr	draw_item
	moveq	#CS_BEEP,d0
	moveq	#30,d1
	bsr	k_csfx
	move.w	(sp)+,d1
	rts

draw_menu:
	moveq	#0,d0
.l	bsr	draw_item
	addq.w	#1,d0
	cmp.w	#MENU_N,d0
	blo.s	.l
	rts

; draw_item: d0 = item
draw_item:
	movem.l	d0-d4/a0-a1,-(sp)
	move.w	d0,d4
	lea	s_mplay,a1		; the changing items
	move.w	nplayers,d1
	add.b	#'0',d1
	move.b	d1,9(a1)
	lea	s_mlevel+7,a1
	move.w	level,d1
	lsl.w	#2,d1
	lea	level_names,a0
	move.l	(a0,d1.w),a0
	bsr	copy_str
	lea	s_mmus+7,a1
	lea	s_on,a0
	tst.b	music_off
	beq.s	.mo
	lea	s_off,a0
.mo	bsr	copy_str
	moveq	#64,d0			; clear the line
	move.w	d4,d1
	mulu	#MENU_DY,d1
	add.w	#MENU_Y-1,d1
	move.w	#192,d2
	moveq	#MENU_DY,d3
	move.w	d4,d0
	moveq	#0,d4
	move.w	d0,-(sp)
	moveq	#64,d0
	bsr	k_fill
	move.w	(sp)+,d4
	move.w	d4,d0
	lsl.w	#2,d0
	lea	menu_items,a0
	move.l	(a0,d0.w),a0
	move.w	d4,d1
	mulu	#MENU_DY,d1
	add.w	#MENU_Y,d1
	moveq	#2,d2
	cmp.w	menu_sel,d4
	bne.s	.c
	moveq	#3,d2
.c	moveq	#-1,d3
	bsr	k_ctext
	movem.l	(sp)+,d0-d4/a0-a1
	rts

; a runner crosses the bottom of the title screen
title_runner:
	addq.w	#3,run_x
	cmp.w	#330,run_x
	blt.s	.in
	move.w	#-200,run_x
.in	move.w	run_x,d0
	bmi.s	.x
	cmp.w	#272,d0
	bhi.s	.x
	move.w	d0,d1
	lsr.w	#2,d1
	moveq	#0,d2
	move.w	d1,d2
	divu	#6,d2
	swap	d2
	lsl.w	#2,d2
	lea	runner_tab,a0
	move.l	(a0,d2.w),a0
	move.w	#208,d1
	bsr	k_bob
.x	rts

;==============================================================================
;  making the athletes
;==============================================================================
; make_players -> d0 = 1 go on, 0 back to the title
make_players:
	clr.w	cur_pl
.p	move.w	cur_pl,d0
	cmp.w	nplayers,d0
	bhs.s	.ok
	bsr	player_screen
	tst.w	d0
	bne.s	.next
	tst.w	cur_pl			; back: to the previous athlete or the title
	beq.s	.back
	subq.w	#1,cur_pl
	bra.s	.p
.next	addq.w	#1,cur_pl
	bra.s	.p
.ok	moveq	#1,d0
	rts
.back	moveq	#0,d0
	rts

player_ctx:				; d0 = player -> a0
	move.w	d0,-(sp)
	mulu	#CX_SIZE,d0
	lea	players,a0
	add.l	d0,a0
	move.w	(sp)+,d0
	rts

; player_screen: cur_pl -> d0 = 1 done, 0 back
player_screen:
	lea	menu_rle,a0
	bsr	menu_screen
	move.w	cur_pl,d0
	bsr	player_ctx
	move.l	a0,cur_ctx
	bsr	player_colours
	bsr	write_colours
	lea	s_create,a0		; "CREATE YOUR ATHLETE"
	moveq	#16,d1
	moveq	#3,d2
	moveq	#-1,d3
	bsr	k_ctext2
	lea	s_athn,a1		; "ATHLETE 1 OF 2"
	move.w	cur_pl,d0
	add.b	#'1',d0
	move.b	d0,8(a1)
	move.w	nplayers,d0
	add.b	#'0',d0
	move.b	d0,13(a1)
	move.l	a1,a0
	moveq	#50,d1
	moveq	#2,d2
	moveq	#-1,d3
	bsr	k_ctext
	lea	s_cr_help,a0
	move.w	#228,d1
	moveq	#11,d2
	moveq	#-1,d3
	bsr	k_ctext
	clr.w	field
	moveq	#0,d0
.d	bsr	draw_field
	addq.w	#1,d0
	cmp.w	#FIELD_N,d0
	blo.s	.d
	bsr	draw_flag
	bsr	k_fadein
	bsr	k_input
.loop	bsr	k_begin
	move.l	cur_ctx,a1		; the athlete
	lea	ath_man,a0
	tst.w	CX_WOMAN(a1)
	beq.s	.m
	lea	ath_woman,a0
.m	move.w	#256,d0
	move.w	#150,d1
	bsr	k_bob
	bsr	k_end
	tst.b	quit_now
	bne	.back
	bsr	k_input
	move.l	cur_ctx,a1
	sf	typing
	tst.w	field			; the name: typing
	bne.s	.nt
	st	typing
	tst.b	d2
	beq.s	.nt
	cmp.b	#' ',d2			; (space is a letter here, not fire)
	bne.s	.ns
	bclr	#J_FIRE,d1
.ns	bsr	name_key
.nt	btst	#J_UP,d1
	beq.s	.nu
	move.w	field,d0
	subq.w	#1,d0
	bmi.s	.nu
	bsr	field_move
.nu	btst	#J_DOWN,d1
	beq.s	.nd
	move.w	field,d0
	addq.w	#1,d0
	cmp.w	#FIELD_N,d0
	bhs.s	.nd
	bsr	field_move
.nd	moveq	#0,d3			; left / right: change
	btst	#J_LEFT,d1
	beq.s	.nl
	moveq	#-1,d3
.nl	btst	#J_RIGHT,d1
	beq.s	.nr
	moveq	#1,d3
.nr	tst.w	d3
	beq.s	.nch
	bsr	field_change
.nch	btst	#J_FIRE,d1
	beq.s	.nf
	move.w	field,d0
	cmp.w	#FIELD_N-1,d0
	beq.s	.done
	addq.w	#1,d0
	bsr	field_move
	bra	.loop
.nf	btst	#J_ESC,d1
	beq	.loop
.back	sf	typing
	moveq	#0,d0
	rts
.done	sf	typing
	moveq	#CS_READY,d0
	moveq	#64,d1
	bsr	k_csfx
	move.l	cur_ctx,a0		; an empty name: PLAYER n
	tst.b	(a0)
	bne.s	.nm
	lea	s_player,a1
.cp	move.b	(a1)+,(a0)+
	bne.s	.cp
	move.l	cur_ctx,a0
	move.w	cur_pl,d0
	add.b	#'1',d0
	move.b	d0,7(a0)
.nm	moveq	#20,d0
	moveq	#0,d1
	bsr	k_wait
	moveq	#1,d0
	rts

field_move:				; d0 = the new field
	move.w	d1,-(sp)
	move.w	field,-(sp)
	move.w	d0,field
	bsr	draw_field
	move.w	(sp)+,d0
	bsr	draw_field
	moveq	#CS_BEEP,d0
	moveq	#30,d1
	bsr	k_csfx
	move.w	(sp)+,d1
	rts

; name_key: d2 = character
name_key:
	movem.l	d0-d2/a0,-(sp)
	move.l	cur_ctx,a0
	moveq	#0,d0			; length
.l	tst.b	(a0,d0.w)
	beq.s	.e
	addq.w	#1,d0
	bra.s	.l
.e	cmp.b	#8,d2			; backspace
	bne.s	.nb
	tst.w	d0
	beq.s	.x
	clr.b	-1(a0,d0.w)
	bra.s	.draw
.nb	cmp.w	#NAMELEN,d0
	bhs.s	.x
	cmp.b	#' ',d2
	beq.s	.ok
	cmp.b	#'-',d2
	beq.s	.ok
	cmp.b	#'.',d2
	beq.s	.ok
	cmp.b	#'0',d2
	blo.s	.x
	cmp.b	#'9',d2
	bls.s	.ok
	cmp.b	#'A',d2
	blo.s	.x
	cmp.b	#'Z',d2
	bhi.s	.x
.ok	move.b	d2,(a0,d0.w)
	clr.b	1(a0,d0.w)
.draw	moveq	#0,d0
	bsr	draw_field
	moveq	#CS_BEEP,d0
	moveq	#20,d1
	bsr	k_csfx
.x	movem.l	(sp)+,d0-d2/a0
	rts

; field_change: d3 = -1 / +1
field_change:
	movem.l	d0-d3/a0-a1,-(sp)
	move.l	cur_ctx,a1
	move.w	field,d0
	cmp.w	#1,d0
	bne.s	.n1
	lea	CX_CTRY(a1),a0
	moveq	#NCTRY,d2
	bra.s	.ch
.n1	cmp.w	#2,d0
	bne.s	.n2
	lea	CX_WOMAN(a1),a0
	moveq	#2,d2
	bra.s	.ch
.n2	cmp.w	#3,d0
	bne.s	.n3
	lea	CX_SKIN(a1),a0
	moveq	#3,d2
	bra.s	.ch
.n3	cmp.w	#4,d0
	bne.s	.x
	lea	CX_HAIR(a1),a0
	moveq	#4,d2
.ch	move.w	(a0),d1
	add.w	d3,d1
	bpl.s	.c1
	move.w	d2,d1
	subq.w	#1,d1
.c1	cmp.w	d2,d1
	blo.s	.c2
	moveq	#0,d1
.c2	move.w	d1,(a0)
	move.w	field,d0
	bsr	draw_field
	cmp.w	#1,d0
	bne.s	.nf
	bsr	draw_flag
.nf	bsr	player_colours
	bsr	write_colours
	moveq	#CS_BEEP,d0
	moveq	#30,d1
	bsr	k_csfx
.x	movem.l	(sp)+,d0-d3/a0-a1
	rts

draw_flag:
	movem.l	d0-d1/a0-a1,-(sp)
	move.l	cur_ctx,a1
	move.w	CX_CTRY(a1),d0
	lsl.w	#2,d0
	lea	flag_tab,a0
	move.l	(a0,d0.w),a0
	move.w	#260,d0
	move.w	#122,d1
	bsr	k_stamp
	movem.l	(sp)+,d0-d1/a0-a1
	rts

; draw_field: d0 = field
draw_field:
	movem.l	d0-d4/a0-a2,-(sp)
	move.w	d0,d4
	move.l	cur_ctx,a2
	moveq	#8,d0			; clear the line
	move.w	d4,d1
	mulu	#18,d1
	add.w	#76,d1
	move.w	#232,d2
	moveq	#12,d3
	move.w	d4,-(sp)
	moveq	#0,d4
	bsr	k_fill
	move.w	(sp)+,d4
	moveq	#2,d2			; colour: yellow when selected
	cmp.w	field,d4
	bne.s	.c
	moveq	#3,d2
.c	moveq	#-1,d3
	move.w	d4,d1
	mulu	#18,d1
	add.w	#78,d1
	move.w	d4,d0
	lsl.w	#2,d0
	lea	field_names,a0
	move.l	(a0,d0.w),a0
	moveq	#16,d0
	bsr	k_text
	lea	strbuf,a1		; the value
	cmp.w	#0,d4
	bne.s	.v1
	move.l	a2,a0
	bsr	copy_str
	cmp.w	field,d4
	bne.s	.show
	move.b	#'_',(a1)+
	clr.b	(a1)
	bra.s	.show
.v1	cmp.w	#5,d4
	beq.s	.x
	move.b	#'<',(a1)+
	move.b	#' ',(a1)+
	cmp.w	#1,d4
	bne.s	.v2
	move.w	CX_CTRY(a2),d0
	lsl.w	#2,d0
	lea	ctry_names,a0
	move.l	(a0,d0.w),a0
	bra.s	.cp
.v2	cmp.w	#2,d4
	bne.s	.v3
	lea	s_man,a0
	tst.w	CX_WOMAN(a2)
	beq.s	.cp
	lea	s_woman,a0
	bra.s	.cp
.v3	cmp.w	#3,d4
	bne.s	.v4
	move.w	CX_SKIN(a2),d0
	lsl.w	#2,d0
	lea	skin_names,a0
	move.l	(a0,d0.w),a0
	bra.s	.cp
.v4	move.w	CX_HAIR(a2),d0
	lsl.w	#2,d0
	lea	hair_names,a0
	move.l	(a0,d0.w),a0
.cp	bsr	copy_str
	move.b	#' ',(a1)+
	move.b	#'>',(a1)+
	clr.b	(a1)
.show	lea	strbuf,a0
	moveq	#96,d0
	bsr	k_text
.x	movem.l	(sp)+,d0-d4/a0-a2
	rts

;==============================================================================
;  choosing the events (some / practice)
;==============================================================================
; choose_events -> d0 = 1 go, 0 back.  mode 1: any number, mode 2: one (practice)
; 18 events in two columns of 9 (field 0-17), field 18 = START
choose_events:
	lea	menu_rle,a0
	bsr	menu_screen
	move.l	#players,cur_ctx
	lea	s_choose,a0
	cmp.w	#2,mode
	bne.s	.t
	lea	s_choose1,a0
.t	moveq	#16,d1
	moveq	#3,d2
	moveq	#-1,d3
	bsr	k_ctext2
	lea	s_ch_help,a0
	cmp.w	#2,mode
	bne.s	.h
	lea	s_ch_help1,a0
.h	move.w	#232,d1
	moveq	#11,d2
	moveq	#-1,d3
	bsr	k_ctext
	lea	ev_sel,a0
	moveq	#NEV-1,d0
.cl	clr.b	(a0)+
	dbf	d0,.cl
	clr.w	field
	moveq	#0,d0
.d	bsr	draw_ev
	addq.w	#1,d0
	cmp.w	#NEV+1,d0
	blo.s	.d
	bsr	k_fadein
	bsr	k_input
.loop	bsr	vsync
	bsr	vsync
	tst.b	quit_now
	bne	.back
	bsr	k_input
	move.w	field,d0
	btst	#J_UP,d1
	beq.s	.nu
	subq.w	#1,d0
	bmi.s	.nu
	bsr	ev_move
.nu	move.w	field,d0
	btst	#J_DOWN,d1
	beq.s	.nd
	addq.w	#1,d0
	cmp.w	#NEV,d0
	bhi.s	.nd
	bne.s	.dd
	cmp.w	#2,mode			; (practice: no START)
	beq.s	.nd
.dd	bsr	ev_move
.nd	move.w	field,d0
	btst	#J_RIGHT,d1
	beq.s	.nr
	add.w	#9,d0
	cmp.w	#NEV,d0
	bhs.s	.nr
	bsr	ev_move
.nr	move.w	field,d0
	btst	#J_LEFT,d1
	beq.s	.nl
	sub.w	#9,d0
	bmi.s	.nl
	bsr	ev_move
.nl	btst	#J_ESC,d1
	bne	.back
	btst	#J_FIRE,d1
	beq	.loop
	move.w	field,d0
	cmp.w	#NEV,d0
	beq.s	.start
	tst.b	is_demo			; (the demo: soccer only)
	beq.s	.ok
	tst.w	d0
	beq.s	.ok
	bsr	full_only
	bra	.loop
.ok	lea	ev_sel,a0
	not.b	(a0,d0.w)
	bsr	draw_ev
	moveq	#CS_BEEPHI,d0
	moveq	#40,d1
	bsr	k_csfx
	cmp.w	#2,mode			; practice: this one, go
	bne	.loop
.go	moveq	#1,d0
	rts
.start	lea	ev_sel,a0		; at least one
	moveq	#NEV-1,d0
.s	tst.b	(a0)+
	bne.s	.go
	dbf	d0,.s
	moveq	#CS_BUZZER,d0
	moveq	#40,d1
	bsr	k_csfx
	bra	.loop
.back	moveq	#0,d0
	rts

full_only:				; (demo)
	movem.l	d0-d4/a0,-(sp)
	moveq	#CS_BUZZER,d0
	moveq	#40,d1
	bsr	k_csfx
	lea	s_fullonly,a0
	move.w	#220,d1
	moveq	#3,d2
	moveq	#0,d3
	bsr	k_ctext
	moveq	#50,d0
	moveq	#1,d1
	bsr	k_wait
	moveq	#0,d0
	move.w	#220,d1
	move.w	#320,d2
	moveq	#8,d3
	moveq	#0,d4
	bsr	k_fill
	movem.l	(sp)+,d0-d4/a0
	rts

ev_move:
	move.w	d1,-(sp)
	move.w	field,-(sp)
	move.w	d0,field
	bsr	draw_ev
	move.w	(sp)+,d0
	bsr	draw_ev
	moveq	#CS_BEEP,d0
	moveq	#30,d1
	bsr	k_csfx
	move.w	(sp)+,d1
	rts

; ev_xy: d0 = line (0-17, 18 = START) -> d5 = x, d6 = y
ev_xy:
	cmp.w	#NEV,d0
	bne.s	.e
	move.w	#128,d5
	move.w	#204,d6
	rts
.e	moveq	#8,d5
	move.w	d0,d6
	cmp.w	#9,d6
	blo.s	.c
	sub.w	#9,d6
	move.w	#164,d5
.c	mulu	#16,d6
	add.w	#54,d6
	rts

; draw_ev: d0 = line
draw_ev:
	movem.l	d0-d6/a0-a1,-(sp)
	move.w	d0,d4
	bsr	ev_xy
	move.w	d5,d0			; clear it
	move.w	d6,d1
	subq.w	#2,d1
	move.w	#152,d2
	moveq	#12,d3
	move.w	d4,-(sp)
	moveq	#0,d4
	bsr	k_fill
	move.w	(sp)+,d4
	moveq	#2,d2
	cmp.w	#NCLASSIC,d4
	blo.s	.cl
	moveq	#7,d2			; (the silly games in light blue)
.cl	cmp.w	field,d4
	bne.s	.c
	moveq	#3,d2
.c	moveq	#-1,d3
	cmp.w	#NEV,d4
	bne.s	.ev
	cmp.w	#2,mode
	beq.s	.x
	lea	s_start,a0
	move.w	d5,d0
	move.w	d6,d1
	bsr	k_text2
	bra.s	.x
.ev	lea	strbuf,a1
	lea	ev_sel,a0
	move.b	#' ',(a1)
	tst.b	(a0,d4.w)
	beq.s	.ns
	move.b	#'~',(a1)		; (a dot: chosen)
.ns	addq.l	#1,a1
	move.b	#' ',(a1)+
	move.w	d4,d0
	bsr	ev_ptr
	move.l	(a0),a0
	bsr	copy_str
	tst.b	is_demo
	beq.s	.nd
	tst.w	d4
	beq.s	.nd
	moveq	#11,d2			; (not in the demo: grey)
.nd	lea	strbuf,a0
	move.w	d5,d0
	move.w	d6,d1
	bsr	k_text
.x	movem.l	(sp)+,d0-d6/a0-a1
	rts

; ev_ptr: d0 = event -> a0 = its line in ev_tab (24 bytes)
ev_ptr:
	move.l	d0,-(sp)
	and.l	#$ffff,d0
	mulu	#24,d0
	lea	ev_tab,a0
	add.l	d0,a0
	move.l	(sp)+,d0
	rts

; cur_low -> d0 = 1 when a lower score is better in cur_ev (times)
cur_low:
	move.l	a0,-(sp)
	move.w	cur_ev,d0
	bsr	ev_ptr
	move.w	20(a0),d0
	move.l	(sp)+,a0
	rts

; fmt_score: d0.l = score of cur_ev, a1 = text -> the score with its unit (a1 after it)
fmt_score:
	movem.l	d0-d4/a0,-(sp)
	move.l	d0,d3
	move.w	cur_ev,d0
	bsr	ev_ptr
	move.w	18(a0),d4		; format
	move.l	8(a0),-(sp)		; unit
	move.l	d3,d0
	tst.w	d4
	beq.s	.n
	cmp.l	#99999,d0		; (did not finish)
	blo.s	.ok
	lea	s_dnf,a0
	bsr	copy_str
	addq.l	#4,sp
	bra.s	.x
.ok	divu	#100,d0			; 1/100 s or cm: whole . two digits
	move.l	d0,d3
	and.l	#$ffff,d0
	moveq	#1,d1
	bsr	k_num
	bsr	copy_str
	move.b	#'.',(a1)+
	swap	d3
	moveq	#0,d0
	move.w	d3,d0
	moveq	#2,d1
	bsr	k_num
	bsr	copy_str
	bra.s	.u
.n	moveq	#1,d1
	bsr	k_num
	bsr	copy_str
.u	move.b	#' ',(a1)+
	move.l	(sp)+,a0
	bsr	copy_str
.x	movem.l	(sp)+,d0-d4/a0
	rts

;==============================================================================
;  the competition
;==============================================================================
compete:
	lea	tally,a0		; no medals yet
	move.w	#NCTRY*3-1,d0
.t	clr.w	(a0)+
	dbf	d0,.t
	lea	pmedals,a0
	moveq	#4*3-1,d0
.p	clr.w	(a0)+
	dbf	d0,.p
	clr.w	ev_done
	clr.w	ev_count
	lea	ev_sel,a0		; how many
	moveq	#NEV-1,d0
.c	tst.b	(a0)+
	beq.s	.c1
	addq.w	#1,ev_count
.c1	dbf	d0,.c
	clr.w	cur_ev
.e	move.w	cur_ev,d0
	cmp.w	#NEV,d0
	bhs.s	.end
	lea	ev_sel,a0
	tst.b	(a0,d0.w)
	beq.s	.n
	addq.w	#1,ev_done
	bsr	run_event
	tst.w	d0			; -1: stopped
	bmi.s	.stop
	tst.b	quit_now
	bne.s	.stop
.n	addq.w	#1,cur_ev
	bra.s	.e
.end	cmp.w	#2,mode
	beq.s	.stop
	bsr	final_screen
	moveq	#1,d7			; all done: the closing ceremony
	bsr	ceremony
.stop	bsr	save_records
	bsr	song_stop
	rts

; run_event: cur_ev -> d0 = 0 (on), -1 (stop the competition)
run_event:
	; the loading screen
	lea	menu_rle,a0
	bsr	menu_screen
	move.l	#players,cur_ctx
	lea	strbuf,a1		; "EVENT 1 OF 18"
	lea	s_event,a0
	bsr	copy_str
	moveq	#0,d0
	move.w	ev_done,d0
	moveq	#1,d1
	bsr	k_num
	bsr	copy_str
	lea	s_of,a0
	bsr	copy_str
	moveq	#0,d0
	move.w	ev_count,d0
	moveq	#1,d1
	bsr	k_num
	bsr	copy_str
	lea	strbuf,a0
	cmp.w	#2,mode
	bne.s	.np
	lea	s_practice,a0
.np	moveq	#60,d1
	moveq	#2,d2
	moveq	#-1,d3
	bsr	k_ctext
	bsr	ev_name_ptr
	moveq	#80,d1
	moveq	#3,d2
	moveq	#-1,d3
	bsr	k_ctext2
	move.w	cur_ev,d0
	lsl.w	#2,d0
	lea	icon_tab,a0
	move.l	(a0,d0.w),a0
	move.w	#144,d0
	move.w	#110,d1
	bsr	k_stamp
	move.w	cur_ev,d0		; (which disk)
	bsr	ev_ptr
	move.w	16(a0),d0
	lea	s_disk,a0
	add.b	#'0',d0
	move.b	d0,5(a0)
	move.w	#164,d1
	moveq	#12,d2
	moveq	#-1,d3
	bsr	k_ctext
	lea	s_loading,a0
	move.w	#150,d1
	moveq	#11,d2
	moveq	#-1,d3
	bsr	k_ctext
	bsr	k_fadein
	move.w	cur_ev,d0
	bsr	ev_ptr
	move.w	16(a0),d1		; its disk
	move.l	4(a0),a0		; its file
	bsr	load_file
	move.l	d0,ev_entry
	beq.s	.fail
	move.l	d0,a0
	cmp.l	#'SOEV',4(a0)
	beq.s	.ok
.fail	moveq	#0,d0			; the file is not there
	move.w	#150,d1
	move.w	#320,d2
	moveq	#8,d3
	moveq	#0,d4
	bsr	k_fill
	lea	s_noload,a0
	move.w	#150,d1
	moveq	#4,d2
	moveq	#-1,d3
	bsr	k_ctext
	moveq	#CS_BUZZER,d0
	moveq	#50,d1
	bsr	k_csfx
	bsr	wait_fire
	moveq	#0,d0
	rts
.ok	move.l	ev_entry,a0
	move.w	8(a0),cpu_lo
	move.w	10(a0),cpu_hi
	; the players and the computer athletes
	clr.w	ncomp
	moveq	#0,d7
.pl	cmp.w	nplayers,d7
	bhs.s	.cpu
	move.w	d7,d0
	bsr	player_ctx
	bsr	add_player
	addq.w	#1,d7
	bra.s	.pl
.cpu	cmp.w	#2,mode
	beq.s	.turns
	moveq	#2,d7
.cl	bsr	add_cpu
	dbf	d7,.cl
.turns	clr.w	cur_pl
.turn	move.w	cur_pl,d0
	cmp.w	nplayers,d0
	bhs	.results
	bsr	player_ctx
	move.l	a0,cur_ctx
	bsr	ready_screen		; -> d0 = 0 play, 1 skip, -1 stop
	tst.w	d0
	bmi	.stop
	bne.s	.skip
	bsr	play_turn
	bsr	fade_out
	tst.b	quit_now
	bne	.stop
	cmp.w	#2,mode			; practice: again?
	bne.s	.nextp
	bsr	practice_result		; -> d0 = 1 again
	tst.w	d0
	bne.s	.turn
	moveq	#0,d0
	rts
.skip	move.l	cur_ctx,a0
	bsr	no_score
	lea	s_skipped,a1
	exg	a0,a1
	lea	CX_RESULT(a1),a1
	bsr	copy_str
.nextp	move.w	cur_pl,d0		; the result into the list
	mulu	#CS_SIZE,d0
	lea	comps,a1
	add.l	d0,a1
	move.l	cur_ctx,a0
	move.l	CX_SCORE(a0),CS_SCORE(a1)
	lea	CX_RESULT(a0),a0
	move.l	a0,CS_RES(a1)
	addq.w	#1,cur_pl
	bra	.turn
.results
	bsr	results_screen
	bsr	medals
	moveq	#0,d0
	rts
.stop	moveq	#-1,d0
	rts

no_score:				; a0 = context: no result (0, or the slowest time)
	clr.l	CX_SCORE(a0)
	move.l	d0,-(sp)
	bsr	cur_low
	tst.w	d0
	beq.s	.x
	move.l	#999999,CX_SCORE(a0)
.x	move.l	(sp)+,d0
	rts

ev_name_ptr:				; -> a0 = the name of cur_ev
	move.w	cur_ev,d0
	bsr	ev_ptr
	move.l	(a0),a0
	rts

; play_turn: run the event for cur_ctx
play_turn:
	bsr	fade_out
	bsr	song_stop
	move.l	cur_ctx,a4
	move.w	level,CX_LEVEL(a4)
	clr.w	CX_PRACT(a4)
	cmp.w	#2,mode
	bne.s	.np
	move.w	#1,CX_PRACT(a4)
.np	clr.l	CX_SCORE(a4)
	clr.b	CX_RESULT(a4)
	moveq	#NCTRY,d0		; an opponent from another country
	bsr	k_rand
	cmp.w	CX_CTRY(a4),d0
	bne.s	.o
	addq.w	#1,d0
	cmp.w	#NCTRY,d0
	blo.s	.o
	moveq	#0,d0
.o	move.w	d0,opp_ctry
	lsl.w	#2,d0
	lea	ctry_names,a0
	move.l	(a0,d0.w),CX_OPPNAME(a4)
	move.w	opp_ctry,d0
	bsr	ctry_kit
	move.l	a0,CX_OPPCOL(a4)
	lea	ktable,a5
	move.l	ev_entry,a0
	movem.l	d0-d7/a0-a6,-(sp)
	jsr	(a0)
	move.l	d0,(sp)
	movem.l	(sp)+,d0-d7/a0-a6
	bsr	wait_blit
	tst.l	d0
	bpl.s	.x
	move.l	cur_ctx,a1		; given up
	move.l	a1,a0
	bsr	no_score
	lea	CX_RESULT(a1),a1
	lea	s_gaveup,a0
	bsr	copy_str
.x	clr.l	grad_ptr		; (the events change the colours)
	rts

; add_player: a0 = context
add_player:
	movem.l	d0/a0-a1,-(sp)
	move.w	ncomp,d0
	mulu	#CS_SIZE,d0
	lea	comps,a1
	add.l	d0,a1
	move.l	a0,CS_NAME(a1)
	move.w	CX_CTRY(a0),CS_CTRY(a1)
	move.w	CX_PLAYER(a0),CS_PL(a1)
	clr.l	CS_SCORE(a1)
	lea	CX_RESULT(a0),a0
	move.l	a0,CS_RES(a1)
	addq.w	#1,ncomp
	movem.l	(sp)+,d0/a0-a1
	rts

; add_cpu: a computer athlete from a country no player has
add_cpu:
	movem.l	d0-d4/a0-a2,-(sp)
	move.w	ncomp,d4
	mulu	#CS_SIZE,d4
	lea	comps,a2
	add.l	d4,a2
	moveq	#20,d3			; tries
.try	moveq	#NCTRY,d0
	bsr	k_rand
	move.w	d0,d2
	lea	comps,a0		; used already?
	move.w	ncomp,d1
	subq.w	#1,d1
.u	cmp.w	CS_CTRY(a0),d2
	beq.s	.used
	lea	CS_SIZE(a0),a0
	dbf	d1,.u
	bra.s	.free
.used	dbf	d3,.try
.free	move.w	d2,CS_CTRY(a2)
	move.w	#-1,CS_PL(a2)
	moveq	#2,d0
	bsr	k_rand
	move.w	d2,d1
	add.w	d1,d1
	add.w	d0,d1
	lsl.w	#2,d1
	lea	cpu_names,a0
	move.l	(a0,d1.w),CS_NAME(a2)
	; the score: low..high, by the level
	move.w	cpu_hi,d1
	sub.w	cpu_lo,d1		; range
	move.w	cpu_lo,d2
	move.w	level,d3
	bne.s	.n0
	move.w	d1,d0			; easy: lower
	lsr.w	#2,d0
	sub.w	d0,d2
	move.w	d1,d0
	mulu	#3,d0
	lsr.w	#2,d0
	addq.w	#1,d0
	bra.s	.r
.n0	cmp.w	#2,d3
	bne.s	.n1
	move.w	d1,d0			; hard: higher
	lsr.w	#2,d0
	add.w	d0,d2
	move.w	d1,d0
	addq.w	#1,d0
	bra.s	.r
.n1	move.w	d1,d0
	addq.w	#1,d0
.r	bsr	k_rand
	add.w	d2,d0
	bpl.s	.pos
	moveq	#0,d0
.pos	and.l	#$ffff,d0
	move.l	d0,d1
	bsr	cur_low			; times: lower is better, so turn the range round
	tst.w	d0
	beq.s	.hi
	moveq	#0,d0
	move.w	cpu_lo,d0
	add.w	cpu_hi,d0
	sub.l	d1,d0
	bpl.s	.hp
	moveq	#1,d0
.hp	move.l	d0,d1
.hi	move.l	d1,CS_SCORE(a2)
	move.w	ncomp,d1		; the result text: number + unit
	mulu	#20,d1
	lea	cpu_res,a1
	add.l	d1,a1
	move.l	a1,CS_RES(a2)
	move.l	CS_SCORE(a2),d0
	bsr	fmt_score
	addq.w	#1,ncomp
	movem.l	(sp)+,d0-d4/a0-a2
	rts

; ready_screen: cur_ctx -> d0 = 0 play, 1 skip (esc), -1 stop the competition
ready_screen:
	tst.w	dbg_event
	beq.s	.nd
	moveq	#0,d0
	rts
.nd	lea	menu_rle,a0
	bsr	menu_screen
	bsr	ev_name_ptr
	moveq	#12,d1
	moveq	#3,d2
	moveq	#-1,d3
	bsr	k_ctext2
	move.l	cur_ctx,a1		; flag, name, country
	move.w	CX_CTRY(a1),d0
	lsl.w	#2,d0
	lea	flag_tab,a0
	move.l	(a0,d0.w),a0
	moveq	#24,d0
	moveq	#56,d1
	bsr	k_stamp
	move.l	cur_ctx,a0
	moveq	#56,d0
	moveq	#56,d1
	moveq	#2,d2
	moveq	#-1,d3
	bsr	k_text2
	move.l	cur_ctx,a1
	move.w	CX_CTRY(a1),d0
	lsl.w	#2,d0
	lea	ctry_names,a0
	move.l	(a0,d0.w),a0
	moveq	#56,d0
	moveq	#76,d1
	moveq	#7,d2
	bsr	k_text
	move.w	cur_ev,d0		; how to play
	bsr	ev_ptr
	move.l	12(a0),a0
	moveq	#16,d0
	moveq	#96,d1
	moveq	#2,d2
	moveq	#-1,d3
	bsr	k_text
	lea	s_pressfire,a0
	move.w	#214,d1
	moveq	#3,d2
	bsr	k_ctext
	lea	s_escskip,a0
	move.w	#228,d1
	moveq	#11,d2
	bsr	k_ctext
	bsr	player_colours
	bsr	write_colours
	bsr	k_fadein
	moveq	#CS_READY,d0
	moveq	#64,d1
	bsr	k_csfx
	bsr	k_input
.l	bsr	k_begin
	move.l	cur_ctx,a1
	lea	ath_man,a0
	tst.w	CX_WOMAN(a1)
	beq.s	.m
	lea	ath_woman,a0
.m	move.w	#264,d0
	moveq	#48,d1
	bsr	k_bob
	bsr	k_end
	tst.b	quit_now
	bne.s	.stop
	bsr	k_input
	btst	#J_FIRE,d1
	bne.s	.go
	btst	#J_ESC,d1
	beq.s	.l
	moveq	#1,d0
	rts
.go	moveq	#0,d0
	rts
.stop	moveq	#-1,d0
	rts

; practice_result -> d0 = 1 again, 0 back to the title
practice_result:
	lea	menu_rle,a0
	bsr	menu_screen
	move.l	#players,cur_ctx
	bsr	ev_name_ptr
	moveq	#30,d1
	moveq	#3,d2
	moveq	#-1,d3
	bsr	k_ctext2
	lea	s_yourres,a0
	moveq	#80,d1
	moveq	#2,d2
	bsr	k_ctext
	move.l	cur_ctx,a0
	lea	CX_RESULT(a0),a0
	moveq	#100,d1
	moveq	#3,d2
	bsr	k_ctext2
	lea	s_again,a0
	move.w	#180,d1
	moveq	#2,d2
	bsr	k_ctext
	bsr	k_fadein
	bsr	check_record
	bsr	wait_fire
	btst	#J_ESC,d1
	bne.s	.no
	moveq	#1,d0
	rts
.no	moveq	#0,d0
	rts

; check_record: cur_ctx's score against the world record of cur_ev
check_record:
	movem.l	d0-d2/a0-a2,-(sp)
	move.l	cur_ctx,a2
	move.w	cur_ev,d0
	mulu	#20,d0
	lea	records+4,a1
	add.l	d0,a1
	move.l	CX_SCORE(a2),d1
	beq.s	.x			; (nothing)
	bsr	cur_low
	tst.w	d0
	bne.s	.low
	cmp.l	(a1),d1
	ble.s	.x
	bra.s	.rec
.low	cmp.l	#99999,d1		; (did not finish)
	bhs.s	.x
	cmp.l	(a1),d1
	bge.s	.x
.rec	move.l	d1,(a1)+		; a new world record!
	move.l	a2,a0
	moveq	#11,d0
.c	move.b	(a0)+,(a1)+
	dbf	d0,.c
	move.w	CX_CTRY(a2),(a1)
	lea	v_record,a0
	moveq	#64,d1
	bsr	k_sfx
	moveq	#CS_CHEER,d0
	moveq	#40,d1
	bsr	k_csfx
	lea	s_newrec,a0
	move.w	#220,d1
	moveq	#3,d2
	moveq	#4,d3
	bsr	k_ctext
	moveq	#60,d0
	moveq	#1,d1
	bsr	k_wait
.x	movem.l	(sp)+,d0-d2/a0-a2
	rts

;==============================================================================
;  results and medals
;==============================================================================
; sort the competitors: comp_ord = indexes, best first (players first when equal)
sort_comps:
	movem.l	d0-d7/a0-a1,-(sp)
	lea	comp_ord,a0
	moveq	#0,d0
.i	move.w	d0,(a0)+
	addq.w	#1,d0
	cmp.w	#MAXCOMP,d0
	blo.s	.i
	move.w	ncomp,d7
	subq.w	#1,d7
	ble.s	.x
.pass	moveq	#0,d6			; bubble sort: few athletes
	lea	comp_ord,a0
	move.w	d7,d5
	subq.w	#1,d5
.b	move.w	(a0),d0
	move.w	2(a0),d1
	bsr	score_of
	move.l	d2,d3
	move.w	d1,d0
	bsr	score_of
	cmp.l	d3,d2
	ble.s	.k
	move.w	(a0),d0			; swap
	move.w	2(a0),(a0)
	move.w	d0,2(a0)
	moveq	#1,d6
.k	addq.l	#2,a0
	dbf	d5,.b
	tst.w	d6
	bne.s	.pass
.x	movem.l	(sp)+,d0-d7/a0-a1
	rts
score_of:				; d0 = competitor -> d2 = score (times: turned round, higher is better)
	move.l	a1,-(sp)
	mulu	#CS_SIZE,d0
	lea	comps,a1
	move.l	CS_SCORE(a1,d0.l),d2
	bsr	cur_low
	tst.w	d0
	beq.s	.x
	neg.l	d2
.x	move.l	(sp)+,a1
	rts

results_screen:
	bsr	sort_comps
	lea	menu_rle,a0
	bsr	menu_screen
	move.l	#players,cur_ctx
	bsr	ev_name_ptr
	moveq	#8,d1
	moveq	#3,d2
	moveq	#-1,d3
	bsr	k_ctext2
	lea	s_results,a0
	moveq	#26,d1
	moveq	#2,d2
	bsr	k_ctext
	moveq	#0,d7			; place
.r	cmp.w	ncomp,d7
	bhs	.done
	lea	comp_ord,a0
	move.w	d7,d0
	add.w	d0,d0
	move.w	(a0,d0.w),d0
	mulu	#CS_SIZE,d0
	lea	comps,a2
	add.l	d0,a2
	move.w	d7,d6			; y
	mulu	#26,d6
	add.w	#52,d6
	move.w	d7,d0			; place number
	addq.w	#1,d0
	ext.l	d0
	moveq	#1,d1
	bsr	k_num
	moveq	#8,d0
	move.w	d6,d1
	moveq	#2,d2
	moveq	#-1,d3
	bsr	k_text2
	cmp.w	#3,d7			; medal
	bhs.s	.nm
	lea	medal_tab,a0
	move.w	d7,d0
	lsl.w	#2,d0
	move.l	(a0,d0.w),a0
	moveq	#28,d0
	move.w	d6,d1
	bsr	k_stamp
	; the tally
	move.w	CS_CTRY(a2),d0
	mulu	#6,d0
	lea	tally,a0
	add.l	d0,a0
	move.w	d7,d0
	add.w	d0,d0
	addq.w	#1,(a0,d0.w)
	move.w	CS_PL(a2),d0
	bmi.s	.nm
	mulu	#6,d0
	lea	pmedals,a0
	add.l	d0,a0
	move.w	d7,d0
	add.w	d0,d0
	addq.w	#1,(a0,d0.w)
.nm	move.w	CS_CTRY(a2),d0		; flag
	lsl.w	#2,d0
	lea	flag_tab,a0
	move.l	(a0,d0.w),a0
	moveq	#48,d0
	move.w	d6,d1
	bsr	k_stamp
	move.l	CS_NAME(a2),a0
	moveq	#80,d0
	move.w	d6,d1
	moveq	#2,d2
	tst.w	CS_PL(a2)
	bmi.s	.cn
	moveq	#3,d2			; (players in yellow)
.cn	moveq	#-1,d3
	bsr	k_text
	move.w	CS_CTRY(a2),d0
	lsl.w	#2,d0
	lea	ctry_names,a0
	move.l	(a0,d0.w),a0
	moveq	#80,d0
	move.w	d6,d1
	add.w	#9,d1
	moveq	#11,d2
	bsr	k_text
	move.l	CS_RES(a2),a0
	move.w	#184,d0
	move.w	d6,d1
	addq.w	#4,d1
	moveq	#2,d2
	bsr	k_text
	addq.w	#1,d7
	bra	.r
.done	bsr	k_fadein
	moveq	#CS_CLAP,d0
	moveq	#40,d1
	bsr	k_csfx
	cmp.w	#2,mode
	beq.s	.nr
	moveq	#0,d7			; world records
.wr	cmp.w	nplayers,d7
	bhs.s	.nr
	move.w	d7,d0
	bsr	player_ctx
	move.l	a0,cur_ctx
	bsr	check_record
	addq.w	#1,d7
	bra.s	.wr
.nr	move.l	#players,cur_ctx
	lea	s_pressfire,a0
	move.w	#238,d1
	moveq	#3,d2
	moveq	#-1,d3
	bsr	k_ctext
	bsr	wait_fire
	rts

; the medal ceremony: the first three on the podium
medals:
	lea	podium_rle,a0
	bsr	menu_screen
	bsr	ev_name_ptr
	moveq	#8,d1
	moveq	#3,d2
	moveq	#-1,d3
	bsr	k_ctext2
	lea	s_ceremony,a0
	moveq	#28,d1
	moveq	#2,d2
	bsr	k_ctext
	moveq	#0,d7
.p	cmp.w	ncomp,d7
	bhs	.shown
	cmp.w	#3,d7
	bhs	.shown
	lea	comp_ord,a0
	move.w	d7,d0
	add.w	d0,d0
	move.w	(a0,d0.w),d0
	mulu	#CS_SIZE,d0
	lea	comps,a2
	add.l	d0,a2
	lea	pod_xy,a1
	move.w	d7,d0
	lsl.w	#2,d0
	move.w	(a1,d0.w),d4		; x (centre)
	move.w	2(a1,d0.w),d5		; top of the block
	move.w	CS_CTRY(a2),d0
	lsl.w	#2,d0
	lea	flag_tab,a0
	move.l	(a0,d0.w),a0
	move.w	d4,d0
	sub.w	#12,d0
	and.w	#$fff0,d0
	move.w	d5,d1
	sub.w	#20,d1
	bsr	k_stamp
	move.l	CS_NAME(a2),a0		; the name above it
	bsr	strlen
	lsl.w	#2,d0
	neg.w	d0
	add.w	d4,d0
	and.w	#$fff8,d0
	bpl.s	.x0
	moveq	#0,d0
.x0	move.w	d5,d1
	sub.w	#32,d1
	moveq	#2,d2
	tst.w	CS_PL(a2)
	bmi.s	.c
	moveq	#3,d2
.c	moveq	#-1,d3
	bsr	k_text
	addq.w	#1,d7
	bra	.p
.shown	lea	s_pressfire,a0
	move.w	#244,d1
	moveq	#3,d2
	moveq	#-1,d3
	bsr	k_ctext
	lea	song_fanfare_m,a0
	lea	song_fanfare_b,a1
	bsr	k_song
	bsr	k_fadein
	moveq	#CS_CHEER,d0
	moveq	#48,d1
	bsr	k_csfx
	; the best medal of a player: said out loud
	moveq	#0,d7
.b	cmp.w	#3,d7
	bhs.s	.w
	cmp.w	ncomp,d7
	bhs.s	.w
	lea	comp_ord,a0
	move.w	d7,d0
	add.w	d0,d0
	move.w	(a0,d0.w),d0
	mulu	#CS_SIZE,d0
	lea	comps,a2
	tst.w	CS_PL(a2,d0.l)
	bpl.s	.say
	addq.w	#1,d7
	bra.s	.b
.say	moveq	#25,d0
	moveq	#0,d1
	bsr	k_wait
	lea	medal_voice,a0
	move.w	d7,d0
	lsl.w	#2,d0
	move.l	(a0,d0.w),a0
	moveq	#64,d1
	bsr	k_sfx
.w	bsr	wait_fire
	bsr	fade_out
	bsr	song_stop
	rts

; the end: the medal table and the champion
final_screen:
	lea	menu_rle,a0
	bsr	menu_screen
	move.l	#players,cur_ctx
	lea	s_medtab,a0
	moveq	#8,d1
	moveq	#3,d2
	moveq	#-1,d3
	bsr	k_ctext2
	; countries with medals, best first: score = gold*10000 + silver*100 + bronze
	moveq	#0,d7			; lines
	lea	tally_done,a0
	moveq	#NCTRY-1,d0
.cl	clr.b	(a0)+
	dbf	d0,.cl
.pick	cmp.w	#7,d7
	bhs	.champ
	moveq	#-1,d6			; best country
	moveq	#0,d5			; its score
	moveq	#0,d0
.c	lea	tally_done,a0
	tst.b	(a0,d0.w)
	bne.s	.cn
	bsr	ctry_points
	cmp.l	d5,d1
	ble.s	.cn
	move.l	d1,d5
	move.w	d0,d6
.cn	addq.w	#1,d0
	cmp.w	#NCTRY,d0
	blo.s	.c
	tst.w	d6
	bmi	.champ
	lea	tally_done,a0
	st	(a0,d6.w)
	move.w	d7,d4			; y
	mulu	#20,d4
	add.w	#40,d4
	move.w	d6,d0
	lsl.w	#2,d0
	lea	flag_tab,a0
	move.l	(a0,d0.w),a0
	moveq	#16,d0
	move.w	d4,d1
	bsr	k_stamp
	move.w	d6,d0
	lsl.w	#2,d0
	lea	ctry_names,a0
	move.l	(a0,d0.w),a0
	moveq	#48,d0
	move.w	d4,d1
	addq.w	#4,d1
	moveq	#2,d2
	moveq	#-1,d3
	bsr	k_text
	moveq	#0,d3			; gold, silver, bronze
.m	lea	medal_tab,a0
	move.w	d3,d0
	lsl.w	#2,d0
	move.l	(a0,d0.w),a0
	move.w	d3,d0
	mulu	#40,d0
	add.w	#192,d0
	move.w	d4,d1
	move.w	d3,-(sp)
	bsr	k_stamp
	move.w	(sp)+,d3
	move.w	d6,d0
	mulu	#6,d0
	lea	tally,a0
	add.l	d0,a0
	move.w	d3,d0
	add.w	d0,d0
	moveq	#0,d0
	move.w	d3,d1
	add.w	d1,d1
	move.w	(a0,d1.w),d0
	moveq	#1,d1
	bsr	k_num
	move.w	d3,d0
	mulu	#40,d0
	add.w	#208,d0
	move.w	d4,d1
	addq.w	#4,d1
	moveq	#2,d2
	move.w	d3,-(sp)
	moveq	#-1,d3
	bsr	k_text
	move.w	(sp)+,d3
	addq.w	#1,d3
	cmp.w	#3,d3
	blo.s	.m
	addq.w	#1,d7
	bra	.pick
.champ	tst.w	d7
	bne.s	.some
	lea	s_nomedals,a0
	move.w	#100,d1
	moveq	#2,d2
	moveq	#-1,d3
	bsr	k_ctext
.some	; the best player: gold 3, silver 2, bronze 1 points
	moveq	#-1,d6
	moveq	#0,d5
	moveq	#0,d0
.bp	cmp.w	nplayers,d0
	bhs.s	.bpd
	lea	pmedals,a0
	move.w	d0,d1
	mulu	#6,d1
	add.l	d1,a0
	move.w	(a0)+,d1
	mulu	#3,d1
	move.w	(a0)+,d2
	add.w	d2,d2
	add.w	d2,d1
	add.w	(a0)+,d1
	cmp.w	d5,d1
	ble.s	.bn
	move.w	d1,d5
	move.w	d0,d6
.bn	addq.w	#1,d0
	bra.s	.bp
.bpd	tst.w	d6
	bmi.s	.nochamp
	lea	s_champion,a0
	move.w	#190,d1
	moveq	#2,d2
	moveq	#-1,d3
	bsr	k_ctext
	move.w	d6,d0
	bsr	player_ctx
	move.w	#204,d1
	moveq	#3,d2
	bsr	k_ctext2
	moveq	#CS_CHEER,d0
	moveq	#48,d1
	bsr	k_csfx
	lea	song_fanfare_m,a0
	lea	song_fanfare_b,a1
	bsr	k_song
	bra.s	.f
.nochamp
	lea	s_nextime,a0
	move.w	#200,d1
	moveq	#2,d2
	moveq	#-1,d3
	bsr	k_ctext
.f	lea	s_pressfire,a0
	move.w	#232,d1
	moveq	#11,d2
	moveq	#-1,d3
	bsr	k_ctext
	bsr	k_fadein
	tst.w	d6
	bmi.s	.wf
	moveq	#CS_GREAT,d0
	moveq	#64,d1
	bsr	k_csfx
.wf	bsr	wait_fire
	bsr	fade_out
	bsr	song_stop
	rts

ctry_points:				; d0 = country -> d1 = points
	movem.l	d0/a0,-(sp)
	mulu	#6,d0
	lea	tally,a0
	add.l	d0,a0
	moveq	#0,d1
	move.w	(a0)+,d1
	mulu	#10000,d1
	moveq	#0,d0
	move.w	(a0)+,d0
	mulu	#100,d0
	add.l	d0,d1
	moveq	#0,d0
	move.w	(a0)+,d0
	add.l	d0,d1
	movem.l	(sp)+,d0/a0
	rts

;==============================================================================
;  load_file: a0 = file, d1 = its disk (1/2) -> d0 = the first hunk (0: not there)
;  From the game's drawer first (hard drive, WHDLoad), then from OlympicsN:,
;  then it asks for the disk (on the loading screen, line 150).
;==============================================================================
load_file:
	movem.l	d1-d7/a0-a6,-(sp)
	move.l	a0,a2
	move.w	d1,d7
.again	move.l	a2,a0
	bsr	load_event
	tst.l	d0
	bne	.x
	lea	vol_name,a1		; "OlympicsN:file"
	lea	path_buf,a0
.v	move.b	(a1)+,(a0)+
	bne.s	.v
	subq.l	#1,a0
	move.b	d7,d0
	add.b	#'0',d0
	move.b	d0,(a0)+
	move.b	#':',(a0)+
	move.l	a2,a1
.f	move.b	(a1)+,(a0)+
	bne.s	.f
	lea	path_buf,a0
	bsr	load_event
	tst.l	d0
	bne.s	.x
	tst.b	whd_mode
	bne.s	.x
	moveq	#0,d0			; "PLEASE INSERT DISK N AND PRESS FIRE"
	move.w	#150,d1
	move.w	#320,d2
	moveq	#8,d3
	moveq	#0,d4
	bsr	k_fill
	lea	s_insert,a1
	move.b	d7,d0
	add.b	#'0',d0
	move.b	d0,19(a1)
	move.l	a1,a0
	move.w	#150,d1
	moveq	#3,d2
	moveq	#-1,d3
	bsr	k_ctext
	moveq	#CS_BEEPHI,d0
	moveq	#40,d1
	bsr	k_csfx
	bsr	wait_fire
	btst	#J_ESC,d1
	bne.s	.no
	moveq	#0,d0
	move.w	#150,d1
	move.w	#320,d2
	moveq	#8,d3
	moveq	#0,d4
	bsr	k_fill
	lea	s_loading,a0
	move.w	#150,d1
	moveq	#11,d2
	moveq	#-1,d3
	bsr	k_ctext
	bra	.again
.no	moveq	#0,d0
.x	movem.l	(sp)+,d1-d7/a0-a6
	rts

;==============================================================================
;  the ceremonies (Ceremony.evt): d7 = 0 opening, 1 closing
;==============================================================================
ceremony:
	movem.l	d0-d7/a0-a6,-(sp)
	bsr	fade_out
	bsr	song_stop
	lea	menu_rle,a0		; (a screen while it loads)
	bsr	menu_screen
	move.l	#players,cur_ctx
	lea	s_title,a0
	moveq	#80,d1
	moveq	#3,d2
	moveq	#-1,d3
	bsr	k_ctext2
	lea	s_loading,a0
	move.w	#150,d1
	moveq	#11,d2
	bsr	k_ctext
	bsr	k_fadein
	lea	f_cer,a0
	moveq	#1,d1
	bsr	load_file
	move.l	d0,-(sp)
	bsr	fade_out
	move.l	(sp)+,d0
	tst.l	d0
	beq.s	.x
	move.l	d0,a0
	cmp.l	#'SOEV',4(a0)
	bne.s	.x
	move.l	cur_ctx,a4
	lea	ktable,a5
	jsr	(a0)
	bsr	wait_blit
	clr.l	grad_ptr
	bsr	write_black
.x	movem.l	(sp)+,d0-d7/a0-a6
	rts

;==============================================================================
;  world records, how to play
;==============================================================================
records_screen:
	lea	menu_rle,a0
	bsr	menu_screen
	lea	s_records,a0
	moveq	#8,d1
	moveq	#3,d2
	moveq	#-1,d3
	bsr	k_ctext2
	move.w	cur_ev,-(sp)
	moveq	#0,d7
.e	cmp.w	#NEV,d7
	bhs	.done
	move.w	d7,cur_ev
	move.w	d7,d6
	mulu	#11,d6
	add.w	#44,d6			; y
	move.w	d7,d0
	bsr	ev_ptr
	move.l	(a0),a0
	moveq	#0,d0
	move.w	d6,d1
	moveq	#3,d2
	cmp.w	#NCLASSIC,d7
	blo.s	.c
	moveq	#7,d2
.c	moveq	#-1,d3
	bsr	k_text
	move.w	d7,d0
	mulu	#20,d0
	lea	records+4,a2
	add.l	d0,a2
	lea	strbuf,a1		; score + unit
	move.l	(a2),d0
	bsr	fmt_score
	clr.b	(a1)
	lea	strbuf,a0
	move.w	#152,d0
	move.w	d6,d1
	moveq	#2,d2
	bsr	k_text
	lea	4(a2),a0		; the holder (10 letters)
	lea	strbuf,a1
	moveq	#9,d0
.cp	move.b	(a0)+,(a1)+
	dbeq	d0,.cp
	clr.b	(a1)
	lea	strbuf,a0
	move.w	#240,d0
	move.w	d6,d1
	moveq	#11,d2
	bsr	k_text
	addq.w	#1,d7
	bra	.e
.done	move.w	(sp)+,cur_ev
	lea	s_pressfire,a0
	move.w	#244,d1
	moveq	#11,d2
	moveq	#-1,d3
	bsr	k_ctext
	bsr	k_fadein
	bsr	wait_fire
	rts

help_screen:
	lea	menu_rle,a0
	bsr	menu_screen
	lea	s_howto,a0
	moveq	#8,d1
	moveq	#3,d2
	moveq	#-1,d3
	bsr	k_ctext2
	lea	s_help,a0
	moveq	#8,d0
	moveq	#48,d1
	moveq	#2,d2
	bsr	k_text
	bsr	k_fadein
	bsr	wait_fire
	rts

;==============================================================================
	section	data,data
	include	"strings.s"
	section	code,code
