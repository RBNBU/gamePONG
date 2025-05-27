import pygame
import random
import math
import os
import paho.mqtt.client as mqtt

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
"Easy":   {"speedMultiplier": 1.0, "paddleHeight": 60},
"Medium": {"speedMultiplier": 1.5, "paddleHeight": 50},
"Hard":   {"speedMultiplier": 2.0, "paddleHeight": 40}
}

#highscore txt file
highScore = "high_scores.txt"

#infopanel config
infoPanel_X_Start = game_X_Offset + gameWidth + 50
infoPanel_Y_Start = game_Y_Offset

# MQTT config
MQTT_BROKER = "192.168.0.157"
MQTT_PORT = 1883
MQTT_TOPIC_GAME = "game/Ruben"
mqttPaddleDirection = None

#initialize pygame
pygame.init()
screen = pygame.display.set_mode((screenWidth, screenHeight))
pygame.display.set_caption("Pong")

#start clock
clock = pygame.time.Clock()

#font config
titleFont = pygame.font.Font(None, 70)
headerFont = pygame.font.Font(None, 50)
gameFont = pygame.font.Font(None, 40)
smallFont = pygame.font.Font(None, 30)
inputFont = pygame.font.Font(None, 36)

#play music
try:
    pygame.mixer.music.load("song.mp3")
    pygame.mixer.music.play(-1)
except pygame.error as e:
    print(f"Cannot load music file song.mp3: {e}")

def on_connect_mqtt(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(MQTT_TOPIC_GAME)
    else:
        print(f"Failed to connect to MQTT broker, return code {rc}")

#define mqtt messages
def on_message_mqtt(client, userdata, msg):
    global mqttPaddleDirection
    payload = msg.payload.decode()
    if payload == "up":
        mqttPaddleDirection = "up"
    elif payload == "down":
        mqttPaddleDirection = "down"
    elif payload == "hold":
        mqttPaddleDirection = None

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect_mqtt
mqtt_client.on_message = on_message_mqtt

try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"MQTT connection error: {e}")


#functions to prevent repetition for drawing text on screen
def drawTextOnScreen(text, font, color, surface, x, y, center_x=True, center_y=False):
    textSurface = font.render(text, True, color)
    textRect = textSurface.get_rect()
    if center_x and center_y: textRect.center = (x,y)
    elif center_x: textRect.centerx = x; textRect.y = y
    elif center_y: textRect.centery = y; textRect.x = x
    else: textRect.topleft = (x,y)
    surface.blit(textSurface, textRect)

#function to get high scores from file
def fetchHighScores():
    scores = {diff: [] for diff in difficulties.keys()}
    if not os.path.exists(highScore): return scores
    try:
        with open(highScore, 'r') as f:
            for line in f:
                parts = line.strip().split(':', 2)
                if len(parts) == 3:
                    diff, name, time_str = parts
                    if diff in scores:
                        try:
                            timeVal = float(time_str)
                            scores[diff].append((name, timeVal))
                        except ValueError:
                            pass 
    except Exception as e: print(f"Error loading scores: {e}")
    
    for diffKey in scores:
        scores[diffKey].sort(key=lambda item: item[1], reverse=True)
        scores[diffKey] = scores[diffKey][:3]
    return scores

#function to update the high score file
def updateSaveHighScores(currentScores, difficulty, playerName, playerTime):
    if difficulty not in currentScores:
        currentScores[difficulty] = []
    
    currentScores[difficulty].append((playerName, playerTime))
    currentScores[difficulty].sort(key=lambda item: item[1], reverse=True)
    currentScores[difficulty] = currentScores[difficulty][:3]
    
    try:
        with open(highScore, 'w') as f:
            for diffOrderedKey in difficulties.keys(): # Use defined order of difficulties
                if diffOrderedKey in currentScores and currentScores[diffOrderedKey]:
                    for name, timeVal in currentScores[diffOrderedKey]:
                        f.write(f"{diffOrderedKey}:{name}:{timeVal:.2f}\n")
    except Exception as e: print(f"Error saving scores: {e}")

#default variables
playerNameStr = ""
difficultyNameStr = "Medium"
currentPaddleHeight = difficulties[difficultyNameStr]["paddleHeight"]
paddle_Y_Pos = (gameTop + gameBottom) / 2 - currentPaddleHeight / 2
ballRectObj = pygame.Rect(0,0, ballRadius * 2, ballRadius * 2)
ballSpeedVec = [0,0]
turnsCount = 0
totalGameTime = 0.0
turnStartTimeTicks = 0
currentGameState = "getPlayerName"
highScoresData = fetchHighScores()

def resetBall():
    global turnStartTimeTicks, ballSpeedVec
    ballRectObj.center = (
        random.randint(gameLeft + ballRadius + 5, gameLeft + gameWidth // 2),
        random.randint(gameTop + ballRadius + 5, gameBottom - ballRadius - 5)
    )
    angle_rad = math.radians(random.uniform(-45, 45))
    speed_mult = difficulties[difficultyNameStr]["speedMultiplier"]
    base_s = ballSpeed * speed_mult
    ballSpeedVec = [base_s * math.cos(angle_rad), base_s * math.sin(angle_rad)]
    turnStartTimeTicks = pygame.time.get_ticks()

#main loop
runningMainLoop = True
while runningMainLoop:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            runningMainLoop = False

    #get player name screen
    if currentGameState == "getPlayerName":
        inputBox = pygame.Rect(screenWidth/2 - 150, screenHeight/2 - 20, 300, 40)
        dontButton = pygame.Rect(screenWidth/2 - 75, screenHeight/2 + 50, 150, 40)
        isInputActive = False
        nameTyped = ""
        
        subLoopRunning = True
        while subLoopRunning:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: runningMainLoop = False; subLoopRunning = False; break
                if event.type == pygame.MOUSEBUTTONDOWN:
                    isInputActive = inputBox.collidepoint(event.pos)
                    if dontButton.collidepoint(event.pos) and nameTyped.strip():
                        playerNameStr = nameTyped.strip()
                        currentGameState = "difficultySelect"
                        subLoopRunning = False
                if event.type == pygame.KEYDOWN and isInputActive:
                    if event.key == pygame.K_RETURN and nameTyped.strip():
                        playerNameStr = nameTyped.strip()
                        currentGameState = "difficultySelect"
                        subLoopRunning = False
                    elif event.key == pygame.K_BACKSPACE: nameTyped = nameTyped[:-1]
                    elif len(nameTyped) < 20: nameTyped += event.unicode
            if not runningMainLoop: break
            
            screen.fill(BLACK)
            drawTextOnScreen("Voer je naam in:", headerFont, WHITE, screen, screenWidth/2, screenHeight/3, True, True)
            box_color = LIGHT_BLUE if isInputActive else GREY
            pygame.draw.rect(screen, box_color, inputBox, 0 if isInputActive else 2)
            nameSurface = inputFont.render(nameTyped, True, BLACK if isInputActive else WHITE)
            inputBox.w = max(200, nameSurface.get_width() + 20); inputBox.x = screenWidth/2 - inputBox.w/2
            screen.blit(nameSurface, (inputBox.x + 10, inputBox.y + 5))
            pygame.draw.rect(screen, LIGHT_BLUE, dontButton)
            drawTextOnScreen("Klaar", gameFont, BLACK, screen, dontButton.centerx, dontButton.centery, True, True)
            pygame.display.flip()
            clock.tick(30)
        if not runningMainLoop: break

    #difficulty select screen
    elif currentGameState == "difficultySelect":
        buttonsList = []
        btnW, btnH, btnSpacing = 200, 60, 20
        totalBtnHeight = (btnH + btnSpacing) * len(difficulties) - btnSpacing
        btnsStart_Y = screenHeight/2 - totalBtnHeight/2 + 30
        for i, diffName in enumerate(difficulties.keys()):
            rect = pygame.Rect(screenWidth/2 - btnW/2, btnsStart_Y + i * (btnH + btnSpacing), btnW, btnH)
            buttonsList.append({'rect': rect, 'name': diffName})

        subLoopRunning = True
        while subLoopRunning:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: runningMainLoop = False; subLoopRunning = False; break
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for btnItem in buttonsList:
                        if btnItem['rect'].collidepoint(event.pos):
                            difficultyNameStr = btnItem['name']
                            currentPaddleHeight = difficulties[difficultyNameStr]['paddleHeight']
                            paddle_Y_Pos = (gameTop + gameBottom)/2 - currentPaddleHeight/2
                            turnsCount = 0
                            totalGameTime = 0.0
                            resetBall() 
                            turnsCount = 1 
                            currentGameState = "playing"
                            subLoopRunning = False; break
            if not runningMainLoop: break

            screen.fill(BLACK)
            drawTextOnScreen("Kies Moeilijkheidsgraad", headerFont, WHITE, screen, screenWidth/2, screenHeight/4, True, True)
            for btnItem in buttonsList:
                pygame.draw.rect(screen, LIGHT_BLUE, btnItem['rect'])
                pygame.draw.rect(screen, BLUE, btnItem['rect'], 3)
                drawTextOnScreen(btnItem['name'], gameFont, BLACK, screen, btnItem['rect'].centerx, btnItem['rect'].centery, True, True)
            pygame.display.flip()
            clock.tick(30)
        if not runningMainLoop: break

    #while playing the game
    elif currentGameState == "playing":
        #MQTT controls        
        if mqttPaddleDirection == "up":
            if paddle_Y_Pos > gameTop:
                paddle_Y_Pos -= paddleSpeed
        elif mqttPaddleDirection == "down":
            if paddle_Y_Pos < gameBottom - currentPaddleHeight:
                paddle_Y_Pos += paddleSpeed

        #Keyboard controls
        keysPressed = pygame.key.get_pressed()
        if keysPressed[pygame.K_UP] and paddle_Y_Pos > gameTop:
            paddle_Y_Pos -= paddleSpeed
        if keysPressed[pygame.K_DOWN] and paddle_Y_Pos < gameBottom - currentPaddleHeight:
            paddle_Y_Pos += paddleSpeed
        paddle_Y_Pos = max(gameTop, min(paddle_Y_Pos, gameBottom - currentPaddleHeight))

        ballRectObj.x += ballSpeedVec[0]
        ballRectObj.y += ballSpeedVec[1]

        #when the ball intersects with the walls & paddle
        currentPaddleRect = pygame.Rect(paddle_X_Pos, paddle_Y_Pos, paddleWidth, currentPaddleHeight)
        if ballRectObj.colliderect(currentPaddleRect) and ballSpeedVec[0] > 0:
            yIntersect = (currentPaddleRect.centery) - ballRectObj.centery
            norm_yIntersect = max(-1.0, min(1.0, yIntersect / (currentPaddleHeight / 2.0)))
            angle = math.radians(-norm_yIntersect * 75.0)
            speed = math.hypot(*ballSpeedVec)
            ballSpeedVec = [-speed * math.cos(angle), speed * math.sin(angle)]
            ballRectObj.right = currentPaddleRect.left - 1

        if ballRectObj.top <= gameTop or ballRectObj.bottom >= gameBottom:
            ballSpeedVec[1] *= -1
            ballRectObj.top = max(gameTop + 1, ballRectObj.top)
            ballRectObj.bottom = min(gameBottom - 1, ballRectObj.bottom)
        if ballRectObj.left <= gameLeft:
            ballSpeedVec[0] *= -1; ballRectObj.left = gameLeft + 1
        if ballRectObj.right >= gameRight:
            currentGameState = "turnOver"

        #draw everything
        screen.fill(GREY)
        pygame.draw.rect(screen, BLACK, (game_X_Offset, game_Y_Offset, gameWidth, gameHeight))
        info_Y_pos = infoPanel_Y_Start
        drawTextOnScreen(f"Speler: {playerNameStr}", gameFont, BLACK, screen, infoPanel_X_Start, info_Y_pos, False)
        info_Y_pos += 35; drawTextOnScreen(f"Level: {difficultyNameStr}", gameFont, BLACK, screen, infoPanel_X_Start, info_Y_pos, False)
        info_Y_pos += 35; drawTextOnScreen(f"Beurt: {turnsCount}/{turnsPerGame}", gameFont, BLACK, screen, infoPanel_X_Start, info_Y_pos, False)
        liveTime = (pygame.time.get_ticks() - turnStartTimeTicks) / 1000.0
        current_total_time = totalGameTime + liveTime
        info_Y_pos += 35; drawTextOnScreen(f"Tijd: {current_total_time:.2f}s", gameFont, BLACK, screen, infoPanel_X_Start, info_Y_pos, False)
        
        info_Y_pos += 60; drawTextOnScreen("Beste Scores:", headerFont, BLACK, screen, infoPanel_X_Start, info_Y_pos, False)
        info_Y_pos += 45
        
        has_any_scores_overall = any(highScoresData.get(diffKey) for diffKey in difficulties.keys())

        if not has_any_scores_overall:
            drawTextOnScreen("Nog geen scores!", smallFont, BLACK, screen, infoPanel_X_Start + 10, info_Y_pos, False)
            info_Y_pos += 25 
        else:
            for diffKey_ordered in difficulties.keys():
                drawTextOnScreen(f"{diffKey_ordered}:", smallFont, BLACK, screen, infoPanel_X_Start + 10, info_Y_pos, False)
                info_Y_pos += 20 

                scores_list_for_diff = highScoresData.get(diffKey_ordered, [])
                if scores_list_for_diff:
                    for rank, (name, score_val) in enumerate(scores_list_for_diff):
                        display_text = f"  {rank + 1}. {name} - {score_val:.2f}s"
                        drawTextOnScreen(display_text, smallFont, BLACK, screen, infoPanel_X_Start + 15, info_Y_pos, False)
                        info_Y_pos += 20
                else:
                    drawTextOnScreen("  Nog geen score", smallFont, BLACK, screen, infoPanel_X_Start + 15, info_Y_pos, False)
                    info_Y_pos += 20
                
                info_Y_pos += 5 

        pygame.draw.rect(screen, RED, currentPaddleRect)
        pygame.draw.circle(screen, GREEN, ballRectObj.center, ballRadius)
        pygame.display.flip()

    #when turn over, "died but have lives left"
    elif currentGameState == "turnOver":
        turnDuration = (pygame.time.get_ticks() - turnStartTimeTicks) / 1000.0
        totalGameTime += turnDuration
        
        screen.fill(GREY)
        drawTextOnScreen("BEURT VOORBIJ!", headerFont, RED, screen, screenWidth/2, screenHeight/2 - 80, True, True)
        drawTextOnScreen(f"Beurten over: {turnsPerGame - turnsCount}", gameFont, WHITE, screen, screenWidth/2, screenHeight/2, True, True)
        drawTextOnScreen("Druk op een toets", smallFont, WHITE, screen, screenWidth/2, screenHeight/2 + 50, True, True)
        pygame.display.flip()

        keyPressedFlag = False
        waitTimeoutStart = pygame.time.get_ticks()
        while not keyPressedFlag and (pygame.time.get_ticks() - waitTimeoutStart < 2500): 
            for event in pygame.event.get():
                if event.type == pygame.QUIT: runningMainLoop = False; break
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN: keyPressedFlag = True; break
            if not runningMainLoop:
                break
            clock.tick(30) 
        if not runningMainLoop:
            break

        if turnsCount < turnsPerGame:
            turnsCount += 1
            resetBall()
            currentGameState = "playing"
        else:
            currentGameState = "gameOver"

    #no lives left, game over
    elif currentGameState == "gameOver":
        updateSaveHighScores(highScoresData, difficultyNameStr, playerNameStr, totalGameTime)
        
        playAgainButtonRect = pygame.Rect(screenWidth/2 - 150, screenHeight*2/3, 300, 50)
        quitButtonRect = pygame.Rect(screenWidth/2 - 150, screenHeight*2/3 + 70, 300, 50)
        
        subLoopRunning = True
        while subLoopRunning:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    runningMainLoop = False; subLoopRunning = False; break
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if playAgainButtonRect.collidepoint(event.pos): 
                        currentGameState = "getPlayerName"; subLoopRunning = False
                    if quitButtonRect.collidepoint(event.pos): 
                        runningMainLoop = False; subLoopRunning = False
            if not runningMainLoop:
                break

            #print spel voorbij scherm
            screen.fill(BLACK)
            drawTextOnScreen("SPEL VOORBIJ!", titleFont, YELLOW, screen, screenWidth/2, screenHeight/3, True, True)
            drawTextOnScreen(f"{playerNameStr} ({difficultyNameStr})", gameFont, LIGHT_BLUE, screen, screenWidth/2, screenHeight/3 + 60, True, True)
            drawTextOnScreen(f"Totale Tijd: {totalGameTime:.2f}s", headerFont, WHITE, screen, screenWidth/2, screenHeight/2 + 20, True, True)
            pygame.draw.rect(screen, LIGHT_BLUE, playAgainButtonRect)
            drawTextOnScreen("Nieuw Spel", gameFont, BLACK, screen, playAgainButtonRect.centerx, playAgainButtonRect.centery, True, True)
            pygame.draw.rect(screen, LIGHT_BLUE, quitButtonRect)
            drawTextOnScreen("Afsluiten", gameFont, BLACK, screen, quitButtonRect.centerx, quitButtonRect.centery, True, True)
            pygame.display.flip()
            clock.tick(30)
        if not runningMainLoop:
            break

    clock.tick(60)

mqtt_client.loop_stop()
mqtt_client.disconnect()
pygame.quit()