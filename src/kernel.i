;------------------------------------------------------------------------------
;  kernel.i - Stronkie's Olympics: what the main program offers the events.
;
;  An event file (e.g. Soccer.evt) is an AmigaDOS hunk file that the main
;  program loads into its own memory.  The first hunk starts with:
;	bra.w	entry
;	dc.l	'SOEV'
;	dc.w	cpu_low, cpu_high	; scores of the computer athletes
;	dc.w	flags			; bit 0: lower score is better (not used yet)
;  The main program calls entry with  a5 = the kernel jump table,
;  a4 = the player (context, CX_...).  The event writes CX_SCORE and
;  CX_RESULT and returns d0 = 0 (done) or -1 (ESC: given up).
;  Keep a5 and a4 in every routine.  All kernel calls keep d2-d7/a2-a6
;  unless they return something there.
;  Created By Mark Stronks, Stronkie Soft (c) 2026
;------------------------------------------------------------------------------

K_BEGIN		equ	0	; a new frame: the back buffer gets its background back
K_END		equ	6	; show the frame (25 frames a second)
K_BOB		equ	12	; a0 = bob, d0 = x, d1 = y (top left; x >= 0)
K_TEXT		equ	18	; a0 = text, d0 = x (multiple of 8), d1 = y, d2 = colour, d3 = paper (-1 = none)
K_TEXT2		equ	24	; the same, twice as big
K_CTEXT		equ	30	; centred: a0 = text, d1 = y, d2 = colour, d3 = paper
K_CTEXT2	equ	36	; centred, twice as big
K_FILL		equ	42	; d0 = x, d1 = y, d2 = width, d3 = height (x, width: multiples of 8), d4 = colour
K_SETBG		equ	48	; a0 = packed screen: the background (and both screens)
K_PAL		equ	54	; a0 = 32 colours (25-31 become the player's colours)
K_GRAD		equ	60	; a0 = (line.w, colour.w)... -1: colour 0 per line, or a0 = 0
K_SFX		equ	66	; a0 = sound (ptr.l, words.w, period.w), d1 = volume 0-64
K_SONG		equ	72	; a0 = melody, a1 = bass (a0 = 0: silence)
K_RAND		equ	78	; d0.w = n -> d0.l = 0..n-1
K_INPUT		equ	84	; -> d0 = held, d1 = pressed since the last call (J_...), d2 = key (ascii)
K_NUM		equ	90	; d0.l = number, d1 = minimum digits -> a0 = text
K_WAIT		equ	96	; d0 = frames (25 a second), d1 = 1: fire ends it -> d0 = 1 if fire
K_STAMP		equ	102	; a0 = bob, d0 = x, d1 = y: drawn on the background (stays)
K_CSFX		equ	108	; d0 = common sound (CS_...), d1 = volume
K_FADEIN	equ	114	; fade the colours in
K_FADEOUT	equ	120	; fade the colours out
K_FRAMES	equ	126	; -> d0 = frames counted (50 a second)
K_PLAYERPAL	equ	132	; a0 = 7 colours: other athletes' colours into 25-31 (a0 = 0: the player again)

; input bits
J_FIRE		equ	0
J_LEFT		equ	1
J_RIGHT		equ	2
J_UP		equ	3
J_DOWN		equ	4
J_ESC		equ	5
J_HELP		equ	6

; common sounds (K_CSFX)
CS_CHEER	equ	0
CS_CLAP		equ	1
CS_BEEP		equ	2
CS_BUZZER	equ	3
CS_WHISTLE	equ	4
CS_READY	equ	5	; voices
CS_GO		equ	6
CS_TIMEUP	equ	7
CS_GREAT	equ	8
CS_OHNO		equ	9
CS_GAMEOVER	equ	10
CS_BEEPHI	equ	11
CS_OOH		equ	12

; the player (a4)
CX_NAME		equ	0	; 12 bytes: the name
CX_CNAME	equ	12	; long: the country's name
CX_CTRY		equ	16	; word: country number
CX_WOMAN	equ	18	; word: 0 man, 1 woman
CX_SKIN		equ	20	; word: 0-2
CX_PLAYER	equ	22	; word: player 0-3
CX_PRACT	equ	24	; word: 1 = practice
CX_SCORE	equ	26	; long: the score (the event writes it)
CX_RESULT	equ	30	; 20 bytes: the result as text (the event writes it)
CX_OPPNAME	equ	50	; long: the opponent's country (head to head events)
CX_OPPCOL	equ	54	; long: the opponent's 7 colours (for K_PLAYERPAL)
CX_LEVEL	equ	58	; word: 0 easy, 1 normal, 2 hard
CX_HAIR		equ	60	; word: 0-3
CX_SIZE		equ	64

; colours 25-31: the player
C_HAIR		equ	25
C_SKIN		equ	26
C_SKIND		equ	27
C_SHIRT		equ	28
C_SHIRTD	equ	29
C_SHORTS	equ	30
C_SHOES		equ	31
