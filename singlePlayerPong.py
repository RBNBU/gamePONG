import pygame
import random
import math
import os

#color config
BLACK, WHITE, RED, GREEN, BLUE = (0,0,0), (255,255,255), (255,0,0), (0,255,0), (0,0,255)
LIGHT_BLUE, GREY, YELLOW = (173, 216, 230), (128,128,128), (255, 255, 0)

#screen config
screenWidth, screenHeight = 1000, 650
gameWidth, gameHeight = 400, 400
game_X_Offset, game_Y_Offset = 50, 50

#game space config
gameLeft = game_X_Offset
gameRight = game_X_Offset + gameWidth
gameTop = game_Y_Offset
gameBottom = game_Y_Offset + gameHeight

#ball & paddle config
ballRadius = 4
ballSpeed = -3
paddleWidth = 10
paddle_X_Pos = gameRight - paddleWidth - 5
paddleSpeed = 6
turnsPerGame = 10

#dificulty config
difficulties = {
    "Easy":   {"speed_multiplier": 1.0, "paddle_height": 60},
    "Medium": {"speed_multiplier": 1.5, "paddle_height": 50},
    "Hard":   {"speed_multiplier": 2.0, "paddle_height": 40}
}
#highscore txt file
highScore = "high_scores.txt"

#infopanel config
infoPanel_X_Start = game_X_Offset + gameWidth + 50
infoPanel_Y_Start = game_Y_Offset

#initialize pygame
pygame.init()
screen = pygame.display.set_mode((screenWidth, screenHeight))
pygame.display.set_caption("Pong")
#start clock
clock = pygame.time.Clock()
#font config
title_font = pygame.font.Font(None, 70)
header_font = pygame.font.Font(None, 50)
game_font = pygame.font.Font(None, 40)
small_font = pygame.font.Font(None, 30)
input_font = pygame.font.Font(None, 36)

#functoins to prevent repetition for drawing text on screen
def drawTextOnScreen(text, font, color, surface, x, y, center_x=True, center_y=False):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center_x and center_y: text_rect.center = (x,y)
    elif center_x: text_rect.centerx = x; text_rect.y = y
    elif center_y: text_rect.centery = y; text_rect.x = x
    else: text_rect.topleft = (x,y)
    surface.blit(text_surface, text_rect)

def fetchHighScores():
    scores = {}
    if not os.path.exists(highScore): return scores
    try:
        with open(highScore, 'r') as f:
            for line in f:
                parts = line.strip().split(':', 2)
                if len(parts) == 3:
                    diff, name, time_str = parts
                    if diff in difficulties and (diff not in scores or float(time_str) > scores[diff][1]):
                        scores[diff] = (name, float(time_str))
    except Exception as e: print(f"Error loading scores: {e}")
    return scores

def updateSaveHighScores(current_scores, difficulty, player_name, player_time):
    if difficulty not in current_scores or player_time > current_scores[difficulty][1]:
        current_scores[difficulty] = (player_name, player_time)
        try:
            with open(highScore, 'w') as f:
                for diff_key in sorted(current_scores.keys()):
                    name, time_val = current_scores[diff_key]
                    f.write(f"{diff_key}:{name}:{time_val:.2f}\n")
        except Exception as e: print(f"Error saving scores: {e}")


#default variables
player_name_str = ""
difficulty_name_str = "Medium"
current_paddle_height = difficulties[difficulty_name_str]["paddle_height"]
paddle_y_pos = (gameTop + gameBottom) / 2 - current_paddle_height / 2
ball_rect_obj = pygame.Rect(0,0, ballRadius*2, ballRadius*2)
ball_speed_vec = [0,0]
turns_count = 0
total_game_time = 0.0
turn_start_time_ticks = 0
current_game_state = "getPlayerName"
high_scores_data = fetchHighScores()


def resetBall():
    global turn_start_time_ticks, ball_speed_vec
    ball_rect_obj.center = (
        random.randint(gameLeft + ballRadius + 5, gameLeft + gameWidth // 2),
        random.randint(gameTop + ballRadius + 5, gameBottom - ballRadius - 5)
    )
    angle_rad = math.radians(random.uniform(-45, 45))
    speed_mult = difficulties[difficulty_name_str]["speed_multiplier"]
    base_s = ballSpeed * speed_mult
    ball_speed_vec = [base_s * math.cos(angle_rad), base_s * math.sin(angle_rad)]
    turn_start_time_ticks = pygame.time.get_ticks()


#main loop
running_main_loop = True
while running_main_loop:
    for event in pygame.event.get(): 
        if event.type == pygame.QUIT:
            running_main_loop = False

    #get player name screen
    if current_game_state == "getPlayerName":
        input_box = pygame.Rect(screenWidth/2 - 150, screenHeight/2 - 20, 300, 40)
        done_button = pygame.Rect(screenWidth/2 - 75, screenHeight/2 + 50, 150, 40)
        is_input_active = False
        name_typed = ""
        
        sub_loop_running = True
        while sub_loop_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running_main_loop = False; sub_loop_running = False; break
                if event.type == pygame.MOUSEBUTTONDOWN:
                    is_input_active = input_box.collidepoint(event.pos)
                    if done_button.collidepoint(event.pos) and name_typed.strip():
                        player_name_str = name_typed.strip()
                        current_game_state = "difficultySelect"
                        sub_loop_running = False
                if event.type == pygame.KEYDOWN and is_input_active:
                    if event.key == pygame.K_RETURN and name_typed.strip():
                        player_name_str = name_typed.strip()
                        current_game_state = "difficultySelect"
                        sub_loop_running = False
                    elif event.key == pygame.K_BACKSPACE: name_typed = name_typed[:-1]
                    elif len(name_typed) < 20: name_typed += event.unicode
            if not running_main_loop: break
            
            screen.fill(BLACK)
            drawTextOnScreen("Voer je naam in:", header_font, WHITE, screen, screenWidth/2, screenHeight/3, True, True)
            box_color = LIGHT_BLUE if is_input_active else GREY
            pygame.draw.rect(screen, box_color, input_box, 0 if is_input_active else 2)
            name_surface = input_font.render(name_typed, True, BLACK if is_input_active else WHITE)
            input_box.w = max(200, name_surface.get_width() + 20); input_box.x = screenWidth/2 - input_box.w/2
            screen.blit(name_surface, (input_box.x + 10, input_box.y + 5))
            pygame.draw.rect(screen, LIGHT_BLUE, done_button)
            drawTextOnScreen("Klaar", game_font, BLACK, screen, done_button.centerx, done_button.centery, True, True)
            pygame.display.flip()
            clock.tick(30)
        if not running_main_loop: break

    #difficulty select screen
    elif current_game_state == "difficultySelect":
        buttons_list = []
        btn_w, btn_h, btn_spacing = 200, 60, 20
        total_btn_height = (btn_h + btn_spacing) * len(difficulties) - btn_spacing
        btns_start_y = screenHeight/2 - total_btn_height/2 + 30
        for i, diff_name in enumerate(difficulties.keys()):
            rect = pygame.Rect(screenWidth/2 - btn_w/2, btns_start_y + i * (btn_h + btn_spacing), btn_w, btn_h)
            buttons_list.append({'rect': rect, 'name': diff_name})

        sub_loop_running = True
        while sub_loop_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running_main_loop = False; sub_loop_running = False; break
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for btn_item in buttons_list:
                        if btn_item['rect'].collidepoint(event.pos):
                            difficulty_name_str = btn_item['name']
                            current_paddle_height = difficulties[difficulty_name_str]['paddle_height']
                            paddle_y_pos = (gameTop + gameBottom)/2 - current_paddle_height/2
                            turns_count = 0
                            total_game_time = 0.0
                            resetBall() 
                            turns_count = 1 
                            current_game_state = "playing"
                            sub_loop_running = False; break
            if not running_main_loop: break

            screen.fill(BLACK)
            drawTextOnScreen("Kies Moeilijkheidsgraad", header_font, WHITE, screen, screenWidth/2, screenHeight/4, True, True)
            for btn_item in buttons_list:
                pygame.draw.rect(screen, LIGHT_BLUE, btn_item['rect'])
                pygame.draw.rect(screen, BLUE, btn_item['rect'], 3)
                drawTextOnScreen(btn_item['name'], game_font, BLACK, screen, btn_item['rect'].centerx, btn_item['rect'].centery, True, True)
            pygame.display.flip()
            clock.tick(30)
        if not running_main_loop: break

    #while playing the game
    elif current_game_state == "playing":
        keys_pressed = pygame.key.get_pressed()
        if keys_pressed[pygame.K_UP] and paddle_y_pos > gameTop:
            paddle_y_pos -= paddleSpeed
        if keys_pressed[pygame.K_DOWN] and paddle_y_pos < gameBottom - current_paddle_height:
            paddle_y_pos += paddleSpeed
        paddle_y_pos = max(gameTop, min(paddle_y_pos, gameBottom - current_paddle_height))

        ball_rect_obj.x += ball_speed_vec[0]
        ball_rect_obj.y += ball_speed_vec[1]

        #ball bounce on paddle
        current_paddle_rect = pygame.Rect(paddle_X_Pos, paddle_y_pos, paddleWidth, current_paddle_height)
        if ball_rect_obj.colliderect(current_paddle_rect) and ball_speed_vec[0] > 0:
            y_intersect = (current_paddle_rect.centery) - ball_rect_obj.centery
            norm_y_intersect = y_intersect / (current_paddle_height / 2.0)
            angle = math.radians(-norm_y_intersect * 75.0)

            #to prevent vertical bounces on the paddle
            while angle == 90 or angle == 180:
                if angle == 90:
                    angle = 105
                elif angle == 180:
                    angle == 165

            speed = math.hypot(*ball_speed_vec)
            ball_speed_vec = [-speed * math.cos(angle), speed * math.sin(angle)]
            ball_rect_obj.right = current_paddle_rect.left - 1

        if ball_rect_obj.top <= gameTop or ball_rect_obj.bottom >= gameBottom:
            ball_speed_vec[1] *= -1
            ball_rect_obj.top = max(gameTop + 1, ball_rect_obj.top)
            ball_rect_obj.bottom = min(gameBottom - 1, ball_rect_obj.bottom)
        if ball_rect_obj.left <= gameLeft:
            ball_speed_vec[0] *= -1; ball_rect_obj.left = gameLeft + 1
        if ball_rect_obj.right >= gameRight:
            current_game_state = "turnOver"

        #info panel / highscore panel
        screen.fill(GREY)
        pygame.draw.rect(screen, BLACK, (game_X_Offset, game_Y_Offset, gameWidth, gameHeight))
        info_y_pos = infoPanel_Y_Start
        drawTextOnScreen(f"Speler: {player_name_str}", game_font, BLACK, screen, infoPanel_X_Start, info_y_pos, False)
        info_y_pos += 35; drawTextOnScreen(f"Level: {difficulty_name_str}", game_font, BLACK, screen, infoPanel_X_Start, info_y_pos, False)
        info_y_pos += 35; drawTextOnScreen(f"Beurt: {turns_count}/{turnsPerGame}", game_font, BLACK, screen, infoPanel_X_Start, info_y_pos, False)
        live_time_now = (pygame.time.get_ticks() - turn_start_time_ticks) / 1000.0
        current_total_time = total_game_time + live_time_now
        info_y_pos += 35; drawTextOnScreen(f"Tijd: {current_total_time:.2f}s", game_font, BLACK, screen, infoPanel_X_Start, info_y_pos, False)
        
        info_y_pos += 60; drawTextOnScreen("Beste Scores:", header_font, BLACK, screen, infoPanel_X_Start, info_y_pos, False)
        info_y_pos += 45
        if not high_scores_data:
            drawTextOnScreen("Nog geen scores!", small_font, BLACK, screen, infoPanel_X_Start + 10, info_y_pos, False)
        else:
            for diff_hs_key in sorted(difficulties.keys()):
                hs_text = f"{diff_hs_key}: "
                if diff_hs_key in high_scores_data: hs_text += f"{high_scores_data[diff_hs_key][0]} - {high_scores_data[diff_hs_key][1]:.2f}s"
                else: hs_text += "Nog geen score"
                drawTextOnScreen(hs_text, small_font, BLACK, screen, infoPanel_X_Start + 10, info_y_pos, False)
                info_y_pos += 25

        pygame.draw.rect(screen, RED, current_paddle_rect)
        pygame.draw.circle(screen, GREEN, ball_rect_obj.center, ballRadius)
        pygame.display.flip()

    #when turn over, "died but have lives left"
    elif current_game_state == "turnOver":
        turn_duration = (pygame.time.get_ticks() - turn_start_time_ticks) / 1000.0
        total_game_time += turn_duration
        
        screen.fill(GREY)
        drawTextOnScreen("BEURT VOORBIJ!", header_font, RED, screen, screenWidth/2, screenHeight/2 - 80, True, True)
        drawTextOnScreen(f"Beurten over: {turnsPerGame - turns_count}", game_font, WHITE, screen, screenWidth/2, screenHeight/2, True, True)
        drawTextOnScreen("Druk op een toets", small_font, WHITE, screen, screenWidth/2, screenHeight/2 + 50, True, True)
        pygame.display.flip()

        key_pressed_flag = False
        wait_timeout_start = pygame.time.get_ticks()
        while not key_pressed_flag and (pygame.time.get_ticks() - wait_timeout_start < 2500): 
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running_main_loop = False; break
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN: key_pressed_flag = True; break
            if not running_main_loop:
                break
            clock.tick(30) 
        if not running_main_loop:
            break

        if turns_count < turnsPerGame:
            turns_count += 1
            resetBall()
            current_game_state = "playing"
        else:
            current_game_state = "gameOver"
    
    #no lives left, game over
    elif current_game_state == "gameOver":
        updateSaveHighScores(high_scores_data, difficulty_name_str, player_name_str, total_game_time)
        
        play_again_button_rect = pygame.Rect(screenWidth/2 - 150, screenHeight*2/3, 300, 50)
        quit_button_rect = pygame.Rect(screenWidth/2 - 150, screenHeight*2/3 + 70, 300, 50)
        
        sub_loop_running = True
        while sub_loop_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running_main_loop = False; sub_loop_running = False; break
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if play_again_button_rect.collidepoint(event.pos): 
                        current_game_state = "getPlayerName"; sub_loop_running = False
                    if quit_button_rect.collidepoint(event.pos): 
                        running_main_loop = False; sub_loop_running = False
            if not running_main_loop:
                break

            screen.fill(BLACK)
            drawTextOnScreen("SPEL VOORBIJ!", title_font, YELLOW, screen, screenWidth/2, screenHeight/3, True, True)
            drawTextOnScreen(f"{player_name_str} ({difficulty_name_str})", game_font, LIGHT_BLUE, screen, screenWidth/2, screenHeight/3 + 60, True, True)
            drawTextOnScreen(f"Totale Tijd: {total_game_time:.2f}s", header_font, WHITE, screen, screenWidth/2, screenHeight/2 + 20, True, True)
            pygame.draw.rect(screen, LIGHT_BLUE, play_again_button_rect)
            drawTextOnScreen("Nieuw Spel", game_font, BLACK, screen, play_again_button_rect.centerx, play_again_button_rect.centery, True, True)
            pygame.draw.rect(screen, LIGHT_BLUE, quit_button_rect)
            drawTextOnScreen("Afsluiten", game_font, BLACK, screen, quit_button_rect.centerx, quit_button_rect.centery, True, True)
            pygame.display.flip()
            clock.tick(30)
        if not running_main_loop:
            break

    clock.tick(60)

pygame.quit()