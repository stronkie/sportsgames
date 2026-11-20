; strings.s - the texts of Stronkie's Olympics (data)
is_demo		dc.b	DEMO
s_version	include	"version.i"
s_player	dc.b	'PLAYER 1',0,0,0,0
	even
def_ctry	dc.w	0,1,3,5

menu_items	dc.l	s_m0,s_ma,s_mb,s_m1,s_m2,s_mplay,s_mlevel,s_m5,s_m6,s_mmus,s_m8
s_m0		dc.b	'ALL 18 EVENTS',0
s_ma		dc.b	'THE CLASSIC EVENTS (14)',0
s_mb		dc.b	'THE SILLY GAMES (4)',0
s_m1		dc.b	'CHOOSE YOUR EVENTS',0
s_m2		dc.b	'PRACTICE ONE EVENT',0
s_mplay		dc.b	'PLAYERS: 1',0
s_mlevel	dc.b	'LEVEL: NORMAL',0,0,0,0,0
s_m5		dc.b	'WORLD RECORDS',0
s_m6		dc.b	'HOW TO PLAY',0
s_mmus		dc.b	'MUSIC: ON',0,0,0,0
s_m8		dc.b	'QUIT',0
s_on		dc.b	'ON',0
s_off		dc.b	'OFF',0
	even
level_names	dc.l	s_easy,s_normal,s_hard
s_easy		dc.b	'EASY',0
s_normal	dc.b	'NORMAL',0
s_hard		dc.b	'HARD',0

s_create	dc.b	'CREATE YOUR ATHLETE',0
s_athn		dc.b	'ATHLETE 1 OF 1',0
s_cr_help	dc.b	'TYPE A NAME  -  LEFT/RIGHT: CHANGE',0
	even
field_names	dc.l	s_f0,s_f1,s_f2,s_f3,s_f4,s_f5
s_f0		dc.b	'NAME',0
s_f1		dc.b	'COUNTRY',0
s_f2		dc.b	'ATHLETE',0
s_f3		dc.b	'SKIN',0
s_f4		dc.b	'HAIR',0
s_f5		dc.b	'READY! PRESS FIRE',0
s_man		dc.b	'MAN',0
s_woman		dc.b	'WOMAN',0
	even
skin_names	dc.l	s_sk0,s_sk1,s_sk2
hair_names	dc.l	s_h0,s_h1,s_h2,s_h3
s_sk0		dc.b	'LIGHT',0
s_sk1		dc.b	'TANNED',0
s_sk2		dc.b	'DARK',0
s_h0		dc.b	'BLACK',0
s_h1		dc.b	'BROWN',0
s_h2		dc.b	'BLOND',0
s_h3		dc.b	'RED',0

s_choose	dc.b	'CHOOSE EVENTS',0
s_choose1	dc.b	'PRACTICE',0
s_ch_help	dc.b	'FIRE: CHOOSE, THEN START!',0
s_ch_help1	dc.b	'FIRE: PRACTICE THIS EVENT',0
s_start		dc.b	'START!',0
s_full		dc.b	' *',0
s_fullonly	dc.b	'ONLY IN THE FULL VERSION OF THE GAME!',0
s_event		dc.b	'EVENT ',0
s_of		dc.b	' OF ',0
s_practice	dc.b	'PRACTICE',0
s_loading	dc.b	'LOADING...',0
s_noload	dc.b	'CANNOT LOAD THE EVENT FILE!',0
s_skipped	dc.b	'DID NOT START',0
s_gaveup	dc.b	'GAVE UP',0
s_pressfire	dc.b	'PRESS FIRE',0
s_escskip	dc.b	'ESC: SKIP THIS ATHLETE',0
s_yourres	dc.b	'YOUR RESULT',0
s_again		dc.b	'FIRE: TRY AGAIN     ESC: MENU',0
s_newrec	dc.b	' NEW WORLD RECORD! ',0
s_results	dc.b	'RESULTS',0
s_ceremony	dc.b	'MEDAL CEREMONY',0
s_anthem	dc.b	'THE ANTHEM OF ',0
s_medtab	dc.b	'MEDAL TABLE',0
s_nomedals	dc.b	'NO MEDALS FOR ANYBODY...',0
s_champion	dc.b	'THE CHAMPION OF STRONKIE',39,'S OLYMPICS:',0
s_nextime	dc.b	'NO MEDALS FOR YOU THIS TIME!',0
s_records	dc.b	'WORLD RECORDS',0
s_howto		dc.b	'HOW TO PLAY',0
s_help		dc.b	'JOYSTICK IN PORT 2 (OR THE CURSOR KEYS',10
		dc.b	'AND RETURN).  ESC GIVES UP AN EVENT.',10
		dc.b	'M: MUSIC ON/OFF',10
		dc.b	'MAKE YOUR OWN ATHLETE: A NAME, YOUR',10
		dc.b	'COUNTRY (YOUR KIT HAS ITS COLOURS),',10
		dc.b	'MAN OR WOMAN, SKIN AND HAIR.',10,10
		dc.b	'UP TO 4 PLAYERS TAKE TURNS. IN EVERY',10
		dc.b	'EVENT THEY MEET 3 ATHLETES FROM OTHER',10
		dc.b	'COUNTRIES: THE BEST 3 GET GOLD, SILVER',10
		dc.b	'AND BRONZE.  BEAT A WORLD RECORD AND',10
		dc.b	'YOUR NAME IS SAVED ON THE DISK.',10,10
		dc.b	'18 EVENTS: 14 CLASSIC ONES AND 4 SILLY',10
		dc.b	'GAMES. EACH ONE IS LOADED FROM THE',10
		dc.b	'DISK WHEN IT STARTS (THE GAME ASKS',10
		dc.b	'FOR THE NEXT DISK). HOW TO PLAY EACH',10
		dc.b	'EVENT IS SHOWN BEFORE IT.',10,10
		dc.b	'CREATED BY MARK STRONKS, STRONKIE SOFT',0
	even

f_cer	dc.b	'Ceremony.evt',0
vol_name	dc.b	'Olympics',0
s_insert	dc.b	'PLEASE INSERT DISK 1 AND PRESS FIRE',0
s_title		dc.b	'STRONKIE',39,'S OLYMPICS',0
s_dnf		dc.b	'DNF',0
s_disk		dc.b	'DISK 1',0
	even
	include	"events.i"
medal_tab	dc.l	medal_g,medal_s,medal_b
medal_voice	dc.l	v_gold,v_silver,v_bronze
pod_xy		dc.w	160,176,80,196,240,208
title_rle	incbin	"title.rle"
	even
menu_rle	incbin	"menu.rle"
	even
podium_rle	incbin	"podium.rle"
	even
