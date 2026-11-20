; strings.s - the texts of Stronkie's Olympics (data)
is_demo		dc.b	DEMO
s_version	include	"version.i"
s_player	dc.b	'PLAYER 1',0,0,0,0
	even
def_ctry	dc.w	0,1,3,5

menu_items	dc.l	s_m0,s_m1,s_m2,s_mplay,s_mlevel,s_m5,s_m6,s_mmus,s_m8
s_m0		dc.b	'COMPETE IN ALL EVENTS',0
s_m1		dc.b	'COMPETE IN SOME EVENTS',0
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
s_ch_help	dc.b	'FIRE: CHOOSE THE EVENTS, THEN START!',0
s_ch_help1	dc.b	'FIRE: PRACTICE THIS EVENT',0
s_start		dc.b	'START!',0
s_full		dc.b	' (FULL GAME)',0
s_fullonly	dc.b	'ONLY IN THE FULL VERSION OF THE GAME!',0
s_event		dc.b	'EVENT 1 OF 6',0
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
s_medtab	dc.b	'MEDAL TABLE',0
s_nomedals	dc.b	'NO MEDALS FOR ANYBODY...',0
s_champion	dc.b	'THE CHAMPION OF STRONKIE',39,'S OLYMPICS:',0
s_nextime	dc.b	'NO MEDALS FOR YOU THIS TIME!',0
s_records	dc.b	'WORLD RECORDS',0
s_howto		dc.b	'HOW TO PLAY',0
s_help		dc.b	'JOYSTICK IN PORT 2 (OR THE CURSOR KEYS',10
		dc.b	'AND RETURN).  ESC GIVES UP AN EVENT.',10
		dc.b	'M: MUSIC ON/OFF',10,10
		dc.b	'MAKE YOUR OWN ATHLETE: A NAME, YOUR',10
		dc.b	'COUNTRY (YOUR KIT HAS ITS COLOURS),',10
		dc.b	'MAN OR WOMAN, SKIN AND HAIR.',10,10
		dc.b	'UP TO 4 PLAYERS TAKE TURNS. IN EVERY',10
		dc.b	'EVENT THEY MEET 3 ATHLETES FROM OTHER',10
		dc.b	'COUNTRIES: THE BEST 3 GET GOLD, SILVER',10
		dc.b	'AND BRONZE.  BEAT A WORLD RECORD AND',10
		dc.b	'YOUR NAME IS SAVED ON THE DISK.',10,10
		dc.b	'THE EVENTS: SOCCER, BASKETBALL,',10
		dc.b	'VOLLEYBALL, BOWLING, SURFING AND',10
		dc.b	'SKATEBOARDING.  EACH ONE IS LOADED',10
		dc.b	'FROM THE DISK WHEN IT STARTS.  HOW TO',10
		dc.b	'PLAY EACH EVENT IS SHOWN BEFORE IT.',10,10
		dc.b	'CREATED BY MARK STRONKS, STRONKIE SOFT',0
	even

; the events: name, file, unit, how to play
ev_tab	dc.l	n_soc,f_soc,u_pts,h_soc
	dc.l	n_bas,f_bas,u_pts,h_bas
	dc.l	n_vol,f_vol,u_pts,h_vol
	dc.l	n_bow,f_bow,u_pins,h_bow
	dc.l	n_sur,f_sur,u_pts,h_sur
	dc.l	n_ska,f_ska,u_pts,h_ska
n_soc	dc.b	'SOCCER',0
n_bas	dc.b	'BASKETBALL',0
n_vol	dc.b	'VOLLEYBALL',0
n_bow	dc.b	'BOWLING',0
n_sur	dc.b	'SURFING',0
n_ska	dc.b	'SKATEBOARDING',0
f_soc	dc.b	'Soccer.evt',0
f_bas	dc.b	'Basket.evt',0
f_vol	dc.b	'Volley.evt',0
f_bow	dc.b	'Bowling.evt',0
f_sur	dc.b	'Surfing.evt',0
f_ska	dc.b	'Skate.evt',0
f_cer	dc.b	'Ceremony.evt',0
vol_name	dc.b	'Olympics',0
s_insert	dc.b	'PLEASE INSERT DISK 1 AND PRESS FIRE',0
s_title		dc.b	'STRONKIE',39,'S OLYMPICS',0
	even
ev_disk		dc.w	1,1,1,2,2,2
u_pts	dc.b	'PTS',0
u_pins	dc.b	'PINS',0
h_soc	dc.b	'PENALTY SHOOT-OUT AGAINST ANOTHER',10
	dc.b	'COUNTRY: 5 SHOTS EACH, THEN SUDDEN',10
	dc.b	'DEATH.',10,10
	dc.b	'SHOOTING: FIRE STOPS THE AIM, FIRE',10
	dc.b	'AGAIN STOPS THE POWER (TOO MUCH AND',10
	dc.b	'THE BALL FLIES OVER THE BAR!)',10,10
	dc.b	'KEEPING: PUSH LEFT, RIGHT OR UP JUST',10
	dc.b	'BEFORE THE KICK TO DIVE.',10,10
	dc.b	'POINTS: YOUR GOALS + YOUR SAVES',10
	dc.b	'(+3 FOR A WIN).',0
h_bas	dc.b	'THREE POINT SHOOT-OUT: 5 RACKS OF 5',10
	dc.b	'BALLS AND 60 SECONDS ON THE CLOCK.',10,10
	dc.b	'HOLD FIRE: THE POWER BAR GOES UP.',10
	dc.b	'LET GO IN THE GREEN ZONE TO SCORE.',10
	dc.b	'THE GREEN ZONE IS SMALLER FAR AWAY.',10,10
	dc.b	'THE LAST BALL OF A RACK (THE STRIPED',10
	dc.b	'MONEY BALL) COUNTS 2 POINTS.',0
h_vol	dc.b	'BEACH VOLLEYBALL AGAINST ANOTHER',10
	dc.b	'COUNTRY: THE FIRST TO 7 POINTS WINS.',10,10
	dc.b	'LEFT/RIGHT: RUN.  FIRE: JUMP.',10
	dc.b	'THE BALL BOUNCES OFF YOUR HANDS AND',10
	dc.b	'HEAD. HIT IT HIGH IN A JUMP TO SPIKE.',10
	dc.b	'DON',39,'T LET IT TOUCH THE SAND!',10,10
	dc.b	'POINTS: 10 + YOUR POINTS - THEIRS.',0
h_bow	dc.b	'TEN PIN BOWLING: 10 FRAMES.',10,10
	dc.b	'1. LEFT/RIGHT: WHERE YOU STAND, FIRE.',10
	dc.b	'2. FIRE STOPS THE ARROW: THE SPIN.',10
	dc.b	'3. FIRE STOPS THE POWER BAR.',10,10
	dc.b	'A STRIKE: ALL 10 PINS WITH ONE BALL.',10
	dc.b	'A SPARE: ALL 10 WITH TWO BALLS.',10
	dc.b	'THE BEST GAME IS 300.',0
h_sur	dc.b	'RIDE THE WAVE FOR 60 SECONDS.',10,10
	dc.b	'LEFT/RIGHT: TURN THE BOARD.',10
	dc.b	'RIDE UP THE WAVE AND DOWN AGAIN FOR',10
	dc.b	'SPEED. RACE UP OFF THE TOP TO FLY:',10
	dc.b	'HOLD FIRE IN THE AIR TO SPIN, LAND',10
	dc.b	'POINTING DOWN THE WAVE.',10
	dc.b	'POINTS FOR TURNS, AIRS AND SPINS AND',10
	dc.b	'FOR RIDING CLOSE TO THE CURL.',10
	dc.b	'3 WIPE-OUTS AND YOU ARE OUT!',0
h_ska	dc.b	'THE HALF PIPE: 60 SECONDS.',10,10
	dc.b	'PUSH DOWN WHEN YOU ROLL THROUGH THE',10
	dc.b	'BOTTOM TO GO FASTER AND HIGHER.',10
	dc.b	'IN THE AIR: PRESS FIRE TO TURN',10
	dc.b	'AROUND (OR YOU FALL!).',10
	dc.b	'UP IN THE AIR: A GRAB.  LEFT OR',10
	dc.b	'RIGHT: A SPIN.  HIGHER = MORE POINTS.',10
	dc.b	'3 FALLS AND YOU ARE OUT!',0
	even
medal_tab	dc.l	medal_g,medal_s,medal_b
medal_voice	dc.l	v_gold,v_silver,v_bronze
pod_xy		dc.w	160,176,80,196,240,208
title_rle	incbin	"title.rle"
	even
menu_rle	incbin	"menu.rle"
	even
podium_rle	incbin	"podium.rle"
	even
