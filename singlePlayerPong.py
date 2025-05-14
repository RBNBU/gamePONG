import pygame
import random
import math
import os

BLACK, WHITE, RED, GREEN, BLUE = (0,0,0), (255,255,255), (255,0,0), (0,255,0), (0,0,255)
LIGHT_BLUE, GREY, YELLOW = (173, 216, 230), (128,128,128), (255, 255, 0)

SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 650
GAME_AREA_WIDTH, GAME_AREA_HEIGHT = 400, 400
GAME_AREA_X_OFFSET, GAME_AREA_Y_OFFSET = 50, 50

PLAY_AREA_LEFT = GAME_AREA_X_OFFSET
PLAY_AREA_RIGHT = GAME_AREA_X_OFFSET + GAME_AREA_WIDTH
PLAY_AREA_TOP = GAME_AREA_Y_OFFSET
PLAY_AREA_BOTTOM = GAME_AREA_Y_OFFSET + GAME_AREA_HEIGHT

BALL_RADIUS = 4
BASE_BALL_SPEED = 3
PADDLE_WIDTH = 10
PADDLE_X_POS = PLAY_AREA_RIGHT - PADDLE_WIDTH - 5
PADDLE_SPEED = 6
TOTAL_TURNS_PER_GAME = 10

DIFFICULTIES = {
    "Easy":   {"speed_multiplier": 1.0, "paddle_height": 40},
    "Medium": {"speed_multiplier": 1.5, "paddle_height": 30},
    "Hard":   {"speed_multiplier": 2.0, "paddle_height": 20}
}
HIGH_SCORE_FILE = "high_scores.txt"

INFO_PANEL_X_START = GAME_AREA_X_OFFSET + GAME_AREA_WIDTH + 50
INFO_PANEL_Y_START = GAME_AREA_Y_OFFSET

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pong - Simpler")
clock = pygame.time.Clock()
title_font = pygame.font.Font(None, 70)
header_font = pygame.font.Font(None, 50)
game_font = pygame.font.Font(None, 40)
small_font = pygame.font.Font(None, 30)
input_font = pygame.font.Font(None, 36)

def draw_text_on_screen(text, font, color, surface, x, y, center_x=True, center_y=False):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center_x and center_y: text_rect.center = (x,y)
    elif center_x: text_rect.centerx = x; text_rect.y = y
    elif center_y: text_rect.centery = y; text_rect.x = x
    else: text_rect.topleft = (x,y)
    surface.blit(text_surface, text_rect)

def get_high_scores():
    scores = {}
    if not os.path.exists(HIGH_SCORE_FILE): return scores
    try:
        with open(HIGH_SCORE_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split(':', 2)
                if len(parts) == 3:
                    diff, name, time_str = parts
                    if diff in DIFFICULTIES and (diff not in scores or float(time_str) > scores[diff][1]):
                        scores[diff] = (name, float(time_str))
    except Exception as e: print(f"Error loading scores: {e}")
    return scores

def update_and_save_high_scores(current_scores, difficulty, player_name, player_time):
    if difficulty not in current_scores or player_time > current_scores[difficulty][1]:
        current_scores[difficulty] = (player_name, player_time)
        try:
            with open(HIGH_SCORE_FILE, 'w') as f:
                for diff_key in sorted(current_scores.keys()):
                    name, time_val = current_scores[diff_key]
                    f.write(f"{diff_key}:{name}:{time_val:.2f}\n")
        except Exception as e: print(f"Error saving scores: {e}")


player_name_str = ""
difficulty_name_str = "Medium"
current_paddle_height = DIFFICULTIES[difficulty_name_str]["paddle_height"]
paddle_y_pos = (PLAY_AREA_TOP + PLAY_AREA_BOTTOM) / 2 - current_paddle_height / 2
ball_rect_obj = pygame.Rect(0,0, BALL_RADIUS*2, BALL_RADIUS*2)
ball_speed_vec = [0,0]
turns_count = 0
total_game_time = 0.0
turn_start_time_ticks = 0
current_game_state = "GET_PLAYER_NAME"
high_scores_data = get_high_scores()


def reset_ball_state():
    global turn_start_time_ticks, ball_speed_vec
    ball_rect_obj.center = (
        random.randint(PLAY_AREA_LEFT + BALL_RADIUS + 5, PLAY_AREA_LEFT + GAME_AREA_WIDTH // 2),
        random.randint(PLAY_AREA_TOP + BALL_RADIUS + 5, PLAY_AREA_BOTTOM - BALL_RADIUS - 5)
    )
    angle_rad = math.radians(random.uniform(-45, 45))
    speed_mult = DIFFICULTIES[difficulty_name_str]["speed_multiplier"]
    base_s = BASE_BALL_SPEED * speed_mult
    ball_speed_vec = [base_s * math.cos(angle_rad), base_s * math.sin(angle_rad)]
    turn_start_time_ticks = pygame.time.get_ticks()


running_main_loop = True
while running_main_loop:
    for event in pygame.event.get(): 
        if event.type == pygame.QUIT:
            running_main_loop = False

    if current_game_state == "GET_PLAYER_NAME":
        input_box = pygame.Rect(SCREEN_WIDTH/2 - 150, SCREEN_HEIGHT/2 - 20, 300, 40)
        done_button = pygame.Rect(SCREEN_WIDTH/2 - 75, SCREEN_HEIGHT/2 + 50, 150, 40)
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
                        current_game_state = "DIFFICULTY_SELECT"
                        sub_loop_running = False
                if event.type == pygame.KEYDOWN and is_input_active:
                    if event.key == pygame.K_RETURN and name_typed.strip():
                        player_name_str = name_typed.strip()
                        current_game_state = "DIFFICULTY_SELECT"
                        sub_loop_running = False
                    elif event.key == pygame.K_BACKSPACE: name_typed = name_typed[:-1]
                    elif len(name_typed) < 20: name_typed += event.unicode
            if not running_main_loop: break
            
            screen.fill(BLACK)
            draw_text_on_screen("Voer je naam in:", header_font, WHITE, screen, SCREEN_WIDTH/2, SCREEN_HEIGHT/3, True, True)
            box_color = LIGHT_BLUE if is_input_active else GREY
            pygame.draw.rect(screen, box_color, input_box, 0 if is_input_active else 2)
            name_surface = input_font.render(name_typed, True, BLACK if is_input_active else WHITE)
            input_box.w = max(200, name_surface.get_width() + 20); input_box.x = SCREEN_WIDTH/2 - input_box.w/2
            screen.blit(name_surface, (input_box.x + 10, input_box.y + 5))
            pygame.draw.rect(screen, LIGHT_BLUE, done_button)
            draw_text_on_screen("Klaar", game_font, BLACK, screen, done_button.centerx, done_button.centery, True, True)
            pygame.display.flip()
            clock.tick(30)
        if not running_main_loop: break

    elif current_game_state == "DIFFICULTY_SELECT":
        buttons_list = []
        btn_w, btn_h, btn_spacing = 200, 60, 20
        total_btn_height = (btn_h + btn_spacing) * len(DIFFICULTIES) - btn_spacing
        btns_start_y = SCREEN_HEIGHT/2 - total_btn_height/2 + 30
        for i, diff_name in enumerate(DIFFICULTIES.keys()):
            rect = pygame.Rect(SCREEN_WIDTH/2 - btn_w/2, btns_start_y + i * (btn_h + btn_spacing), btn_w, btn_h)
            buttons_list.append({'rect': rect, 'name': diff_name})

        sub_loop_running = True
        while sub_loop_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running_main_loop = False; sub_loop_running = False; break
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for btn_item in buttons_list:
                        if btn_item['rect'].collidepoint(event.pos):
                            difficulty_name_str = btn_item['name']
                            current_paddle_height = DIFFICULTIES[difficulty_name_str]['paddle_height']
                            paddle_y_pos = (PLAY_AREA_TOP + PLAY_AREA_BOTTOM)/2 - current_paddle_height/2
                            turns_count = 0
                            total_game_time = 0.0
                            reset_ball_state() 
                            turns_count = 1 
                            current_game_state = "PLAYING"
                            sub_loop_running = False; break
            if not running_main_loop: break

            screen.fill(BLACK)
            draw_text_on_screen("Kies Moeilijkheidsgraad", header_font, WHITE, screen, SCREEN_WIDTH/2, SCREEN_HEIGHT/4, True, True)
            for btn_item in buttons_list:
                pygame.draw.rect(screen, LIGHT_BLUE, btn_item['rect'])
                pygame.draw.rect(screen, BLUE, btn_item['rect'], 3)
                draw_text_on_screen(btn_item['name'], game_font, BLACK, screen, btn_item['rect'].centerx, btn_item['rect'].centery, True, True)
            pygame.display.flip()
            clock.tick(30)
        if not running_main_loop: break

    elif current_game_state == "PLAYING":
        keys_pressed = pygame.key.get_pressed()
        if keys_pressed[pygame.K_UP] and paddle_y_pos > PLAY_AREA_TOP:
            paddle_y_pos -= PADDLE_SPEED
        if keys_pressed[pygame.K_DOWN] and paddle_y_pos < PLAY_AREA_BOTTOM - current_paddle_height:
            paddle_y_pos += PADDLE_SPEED
        paddle_y_pos = max(PLAY_AREA_TOP, min(paddle_y_pos, PLAY_AREA_BOTTOM - current_paddle_height))

        ball_rect_obj.x += ball_speed_vec[0]
        ball_rect_obj.y += ball_speed_vec[1]

        current_paddle_rect = pygame.Rect(PADDLE_X_POS, paddle_y_pos, PADDLE_WIDTH, current_paddle_height)
        if ball_rect_obj.colliderect(current_paddle_rect) and ball_speed_vec[0] > 0:
            y_intersect = (current_paddle_rect.centery) - ball_rect_obj.centery
            norm_y_intersect = y_intersect / (current_paddle_height / 2.0)
            angle = math.radians(-norm_y_intersect * 75.0) 
            if angle == 90:
                angle = 105
            elif angle == 180:
                angle == 165
            speed = math.hypot(*ball_speed_vec)
            ball_speed_vec = [-speed * math.cos(angle), speed * math.sin(angle)]
            ball_rect_obj.right = current_paddle_rect.left - 1

        if ball_rect_obj.top <= PLAY_AREA_TOP or ball_rect_obj.bottom >= PLAY_AREA_BOTTOM:
            ball_speed_vec[1] *= -1
            ball_rect_obj.top = max(PLAY_AREA_TOP + 1, ball_rect_obj.top)
            ball_rect_obj.bottom = min(PLAY_AREA_BOTTOM - 1, ball_rect_obj.bottom)
        if ball_rect_obj.left <= PLAY_AREA_LEFT:
            ball_speed_vec[0] *= -1; ball_rect_obj.left = PLAY_AREA_LEFT + 1
        if ball_rect_obj.right >= PLAY_AREA_RIGHT:
            current_game_state = "TURN_OVER"

        screen.fill(GREY)
        pygame.draw.rect(screen, BLACK, (GAME_AREA_X_OFFSET, GAME_AREA_Y_OFFSET, GAME_AREA_WIDTH, GAME_AREA_HEIGHT))
        info_y_pos = INFO_PANEL_Y_START
        draw_text_on_screen(f"Speler: {player_name_str}", game_font, BLACK, screen, INFO_PANEL_X_START, info_y_pos, False)
        info_y_pos += 35; draw_text_on_screen(f"Level: {difficulty_name_str}", game_font, BLACK, screen, INFO_PANEL_X_START, info_y_pos, False)
        info_y_pos += 35; draw_text_on_screen(f"Beurt: {turns_count}/{TOTAL_TURNS_PER_GAME}", game_font, BLACK, screen, INFO_PANEL_X_START, info_y_pos, False)
        live_time_now = (pygame.time.get_ticks() - turn_start_time_ticks) / 1000.0
        current_total_time = total_game_time + live_time_now
        info_y_pos += 35; draw_text_on_screen(f"Tijd: {current_total_time:.2f}s", game_font, BLACK, screen, INFO_PANEL_X_START, info_y_pos, False)
        
        info_y_pos += 60; draw_text_on_screen("Beste Scores:", header_font, BLACK, screen, INFO_PANEL_X_START, info_y_pos, False)
        info_y_pos += 45
        if not high_scores_data: draw_text_on_screen("Nog geen scores!", small_font, BLACK, screen, INFO_PANEL_X_START + 10, info_y_pos, False)
        else:
            for diff_hs_key in sorted(DIFFICULTIES.keys()):
                hs_text = f"{diff_hs_key}: "
                if diff_hs_key in high_scores_data: hs_text += f"{high_scores_data[diff_hs_key][0]} - {high_scores_data[diff_hs_key][1]:.2f}s"
                else: hs_text += "Nog geen score"
                draw_text_on_screen(hs_text, small_font, BLACK, screen, INFO_PANEL_X_START + 10, info_y_pos, False)
                info_y_pos += 25

        pygame.draw.rect(screen, RED, current_paddle_rect)
        pygame.draw.circle(screen, GREEN, ball_rect_obj.center, BALL_RADIUS)
        pygame.display.flip()

    elif current_game_state == "TURN_OVER":
        turn_duration = (pygame.time.get_ticks() - turn_start_time_ticks) / 1000.0
        total_game_time += turn_duration
        
        screen.fill(GREY)
        draw_text_on_screen("BEURT VOORBIJ!", header_font, RED, screen, SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 80, True, True)
        draw_text_on_screen(f"Beurten over: {TOTAL_TURNS_PER_GAME - turns_count}", game_font, WHITE, screen, SCREEN_WIDTH/2, SCREEN_HEIGHT/2, True, True)
        draw_text_on_screen("Druk op een toets", small_font, WHITE, screen, SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 50, True, True)
        pygame.display.flip()

        key_pressed_flag = False
        wait_timeout_start = pygame.time.get_ticks()
        while not key_pressed_flag and (pygame.time.get_ticks() - wait_timeout_start < 2500): 
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running_main_loop = False; break
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN: key_pressed_flag = True; break
            if not running_main_loop: break
            clock.tick(30) 
        if not running_main_loop: break

        if turns_count < TOTAL_TURNS_PER_GAME:
            turns_count += 1
            reset_ball_state()
            current_game_state = "PLAYING"
        else:
            current_game_state = "GAME_OVER"
    
    elif current_game_state == "GAME_OVER":
        update_and_save_high_scores(high_scores_data, difficulty_name_str, player_name_str, total_game_time)
        
        play_again_button_rect = pygame.Rect(SCREEN_WIDTH/2 - 150, SCREEN_HEIGHT*2/3, 300, 50)
        quit_button_rect = pygame.Rect(SCREEN_WIDTH/2 - 150, SCREEN_HEIGHT*2/3 + 70, 300, 50)
        
        sub_loop_running = True
        while sub_loop_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running_main_loop = False; sub_loop_running = False; break
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if play_again_button_rect.collidepoint(event.pos): current_game_state = "GET_PLAYER_NAME"; sub_loop_running = False
                    if quit_button_rect.collidepoint(event.pos): running_main_loop = False; sub_loop_running = False
            if not running_main_loop: break

            screen.fill(BLACK)
            draw_text_on_screen("SPEL VOORBIJ!", title_font, YELLOW, screen, SCREEN_WIDTH/2, SCREEN_HEIGHT/3, True, True)
            draw_text_on_screen(f"{player_name_str} ({difficulty_name_str})", game_font, LIGHT_BLUE, screen, SCREEN_WIDTH/2, SCREEN_HEIGHT/3 + 60, True, True)
            draw_text_on_screen(f"Totale Tijd: {total_game_time:.2f}s", header_font, WHITE, screen, SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 20, True, True)
            pygame.draw.rect(screen, LIGHT_BLUE, play_again_button_rect)
            draw_text_on_screen("Nieuw Spel", game_font, BLACK, screen, play_again_button_rect.centerx, play_again_button_rect.centery, True, True)
            pygame.draw.rect(screen, LIGHT_BLUE, quit_button_rect)
            draw_text_on_screen("Afsluiten", game_font, BLACK, screen, quit_button_rect.centerx, quit_button_rect.centery, True, True)
            pygame.display.flip()
            clock.tick(30)
        if not running_main_loop: break

    clock.tick(60)

pygame.quit()