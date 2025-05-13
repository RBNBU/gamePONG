import pygame
import random
import math
from time import sleep

BLACK = (0,0,0)
WHITE = (255,255,255)
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)

pygame.init()

size = (1000,650)
width = 1000
height = 650
screen = pygame.display.set_mode(size)
currentGame = 0

pygame.display.set_caption("Singleplayer Pong")

paddle_x = 600
paddle_y = (screen.get_height() / 2) - 45
paddle_h = 90
paddle_w = 10

borderH_h = 20
borderH_w = 650
borderV_h = 650
borderV_w = 20
borderO_y = 0
borderO_x = 650
margin = 20

ball_centre_y = random.randint(borderH_h + margin, height + margin - borderH_h - margin)
ball_centre_x = random.randint(borderV_w + margin, borderO_x + margin - borderV_w - margin)
ball_radius = 20
ball_direction = 'UP_LEFT'
ball_speed = [-10,random.randint(-7,7)]
while ball_speed[1] == 0:
        ball_speed[1] = random.randint(-7, 7)
ball_obj = pygame.draw.circle(screen,"GREEN", (ball_centre_x, ball_centre_y), ball_radius)

pygame.display.flip()


dt = 0

running = True
clock = pygame.time.Clock()

def resetball():
    global paddle_y, ball_centre_x, ball_centre_y, ball_speed, ball_obj

    paddle_y = (height / 2) - (paddle_h / 2)

    ball_centre_y = random.randint(borderH_h + margin, height + margin - borderH_h - margin)

    ball_centre_x = random.randint(borderV_w + margin, borderO_x + margin - borderV_w - margin)

    ball_speed[0] = -10 
    ball_speed[1] = random.randint(-7, 7)
    while ball_speed[1] == 0:
        ball_speed[1] = random.randint(-7, 7)
    ball_obj.center = (ball_centre_x, ball_centre_y)
    
    return


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill("WHITE")
    wall1 = pygame.Rect(0,0, borderH_w, borderH_h)
    wall2 = pygame.Rect(0,0,borderV_w,borderV_h)
    wall3 = pygame.Rect(0,height - borderH_h, borderH_w, borderH_h)
    wall4 = pygame.Rect(borderO_x,borderO_y,borderV_w,borderV_h)
    pallet = pygame.Rect(paddle_x, paddle_y, paddle_w, paddle_h)


    pygame.draw.rect(screen, "BLUE", wall1)
    pygame.draw.rect(screen, "BLUE", wall2)
    pygame.draw.rect(screen, "BLUE", wall3)
    pygame.draw.rect(screen, "BLACK", wall4)
    pygame.draw.rect(screen, "RED", pallet)


    ball_obj = ball_obj.move(ball_speed)

    if ball_obj.left <= borderV_w or ball_obj.right >= borderO_x:
        ball_speed[0] = -ball_speed[0]
    if ball_obj.top <= borderH_h or ball_obj.bottom >= (screen.get_height())-borderH_h:
        ball_speed[1] = -ball_speed[1]

    pygame.draw.circle(screen, "GREEN", ball_obj.center, ball_radius)


    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP] and paddle_y>margin:
       paddle_y -= 5

    if keys[pygame.K_DOWN] and paddle_y<height-paddle_h - margin:
        paddle_y += 5

    pygame.draw.rect(screen, "RED", (paddle_x, paddle_y, paddle_w, paddle_h)) 

    if ball_obj.colliderect(pallet):
        relative_intersect_y = (pallet.y + (paddle_h / 2)) - ball_obj.centery
        normalized_relative_intersect_y = relative_intersect_y / (paddle_h / 2)
        bounce_angle = normalized_relative_intersect_y * 75 
        ball_speed[0] = -ball_speed[0]
        ball_speed[1] = ball_speed[0] * math.sin(math.radians(bounce_angle))

    if ball_obj.right >= borderO_x:
        #running = False
        font = pygame.font.Font(None, 74)
        text = font.render("GAME OVER", 1, RED)
        textpos = text.get_rect(centerx=screen.get_width()/2, centery=screen.get_height()/2)
        screen.blit(text, textpos)
        currentGame = currentGame + 1
        pygame.display.flip()
        waiting = True
        while waiting:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                waiting = False
        if currentGame == 10:
            running = False
            currentGame = 0
            resetball()

    pygame.display.flip()


    dt = clock.tick(60) / 1000

pygame.quit()