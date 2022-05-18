import random
import pygame
import pygame.image, pygame.display, pygame.time, pygame.event, pygame.sprite, pygame.mask, pygame.draw
import socket
import threading


def chop(img:pygame.Surface, lefttop, widthheight):
    return img.subsurface(lefttop, widthheight).copy()

def make_mask(img:pygame.Surface, minc, mina = 200):
    masks = pygame.mask.Mask((img.get_width(), img.get_height()))
    for i in range(img.get_width()):
        for j in range(img.get_height()):
            at = img.get_at((i, j))
            if (at[0] >= minc and at[1] >= minc and at[2] >= minc) or at[3] <= mina:
                masks.set_at((i, j))
    masks.invert()
    return masks.copy()

class Trex(pygame.sprite.Sprite):
    def __init__(self, xpos, ypos, image):
        pygame.sprite.Sprite.__init__(self)
        self.imgPos = (1678, 2)
        self.imgPos1 = (1854, 2)
        self.imgPos2 = (1942, 2)
        self.imgPos3 = (2118, 2)
        self.imgSize = (44 * 2, 47 * 2)
        self.imgSize2 = (42 * 2, 47 * 2)
        self.jumpimg = chop(image, self.imgPos, self.imgSize)
        self.img0 = self.jumpimg.copy()
        self.img1 = chop(image, self.imgPos1, self.imgSize)
        self.img2 = chop(image, self.imgPos2, self.imgSize)
        self.imgDied = chop(image, self.imgPos3, self.imgSize2)

        self.img = self.img0
        self.flag = 0 # 0: img1; 1: img2;
        self.startSpeed = -11
        self.ySpeed = 0
        self.g = 0.3
        self.jumping = False
        self.ground = ypos
        self.stepCnt = 0
        self.rect = self.img.get_rect()
        self.rect.topleft = (xpos, ypos)
        self.mask = make_mask(self.img, 200)
        # self.mask = pygame.mask.from_surface(self.img)
    def changeStep(self):
        self.stepCnt += 1
        if self.stepCnt >= 12:
            self.stepCnt = 0
            self.img = self.img1 if self.flag == 1 else self.img2
            self.flag = 1 - self.flag
    def startJump(self):
        if not self.jumping:
            self.ySpeed = self.startSpeed
            self.jumping = True
            self.img = self.jumpimg
    def updateJump(self):
        if self.jumping:
            self.rect.top += self.ySpeed
            self.ySpeed += self.g
            if self.rect.top >= self.ground:
                self.rect.top = self.ground
                self.ySpeed = 0
                self.jumping = False


class Horizon:
    def __init__(self, xpos, ypos, image):
        self.imgPos = (2, 104)
        self.imgSize = (600 * 4, 12 * 2)
        self.xpos1 = xpos
        self.xpos2 = xpos + self.imgSize[0]
        self.ypos = ypos
        self.img = chop(image, self.imgPos, self.imgSize)
    def update(self):
        self.xpos1 -= 5
        self.xpos2 -= 5
        if self.xpos1 < -self.imgSize[0]:
            self.xpos1 = 0
            self.xpos2 = self.imgSize[0]


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, xpos, ypos, image, type):
        pygame.sprite.Sprite.__init__(self)
        self.imgPos = [(446, 2), (480, 2), (548, 2), (652, 2), (702, 2), (802, 2)]
        self.imgSize = [(34, 70), (68, 70), (102, 70), (50, 100), (100, 100), (150, 100)]
        self.img = chop(image, self.imgPos[type], self.imgSize[type])
        self.rect = self.img.get_rect()
        self.rect.topleft = (xpos, ypos)
        self.mask = make_mask(self.img, 200)
        # self.mask = pygame.mask.from_surface(self.img)
    def update(self):
        self.rect.left -= 5

class Score:
    def __init__(self, image):
        self.imgPos = (1294, 2)
        self.imgSize = (20, 24)
        self.imgs = []
        for i in range(10):
            self.imgs.append(chop(image, (self.imgPos[0] + i * self.imgSize[0], self.imgPos[1]), self.imgSize))

# Net Part
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("", 4210))
s.settimeout(1)

def net():
    global startGame, gameOver, running
    while True:
        try:
            msg, addrInfo = s.recvfrom(1024)
            msg = msg.decode('utf-8')
            print(msg, addrInfo)
            if msg.split(':')[0] == 'J':
                if not gameOver:
                    if not startGame:
                        startGame = True
                    player.startJump()
        except socket.timeout:
            pass
        if not running:
            break
    s.close()

def newObstacle(image):
    tp = random.randint(0, 4)
    return Obstacle(width, (210 + dy) if tp < 3 else (180 + dy), image, tp)

def restart():
    global startGame, gameOver, score, scoreCnt, obstacles, obstaclesList, player, NEW_OBSTACLE
    if gameOver:
        startGame = True
        gameOver = False
        score = 0
        scoreCnt = 0
        obstacles.empty()
        obstaclesList.clear()
        player.jumping = False
        player.rect.top = player.ground
        player.ySpeed = 0
        player.img = player.img0
        pygame.time.set_timer(NEW_OBSTACLE, 3000)


# Main
def main():
    global width, height, running, player, startGame, gameOver, dy, obstacles, obstaclesList, score, scoreCnt, NEW_OBSTACLE
    startGame = False
    gameOver = False
    pygame.init()
    size = width, height = 1600, 400
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("Demo")
    clock = pygame.time.Clock()
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    image = pygame.image.load("200-offline-sprite.png").convert_alpha()

    dy = 100
    horizonYPos = 127 * 2
    trexYPos = (150 - 47 - 10) * 2

    horizon = Horizon(0, horizonYPos + dy, image)
    player = Trex(40, trexYPos + dy, image)
    # horizon2 = Horizon(2400, 127 + dy, image)

    running = True

    obstacles = pygame.sprite.Group()
    obstaclesList = []
    NEW_OBSTACLE = pygame.USEREVENT
    pygame.time.set_timer(NEW_OBSTACLE, 3000)

    score = 0
    scoreCnt = 0

    scoreBoard = Score(image)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    if not gameOver:
                        if not startGame:
                            startGame = True
                        player.startJump()
                elif event.key == pygame.K_F5:
                    pass
            elif event.type == NEW_OBSTACLE and startGame and not gameOver:
                newOb = newObstacle(image)
                obstacles.add(newOb)
                obstaclesList.append(newOb)
                pygame.time.set_timer(NEW_OBSTACLE, random.randint(1000, 2500))
        
        screen.fill(WHITE)

        if startGame and not gameOver:
            if not player.jumping:
                player.changeStep()
            
            horizon.update()
            for each in obstacles:
                each.update()
            while len(obstaclesList) > 0 and obstaclesList[0].rect.left < -width:
                obstacles.remove(obstaclesList[0])
                obstaclesList.pop(0)
            player.updateJump()
        
            if pygame.sprite.spritecollide(player, obstacles, False, pygame.sprite.collide_mask):
                gameOver = True
                player.img = player.imgDied
            
            scoreCnt += 1
            if scoreCnt >= 12:
                scoreCnt = 0
                score += 1
                # print(score)

        screen.blit(horizon.img, (horizon.xpos1, horizon.ypos))
        screen.blit(horizon.img, (horizon.xpos2, horizon.ypos))
        for each in obstacles:
            screen.blit(each.img, each.rect)
        screen.blit(player.img, player.rect)
        if not gameOver:
            pygame.draw.circle(screen, (0, 0, 0), (player.rect.centerx + 200, player.rect.centery), 3, 0)

        temp = score
        for i in range(6):
            screen.blit(scoreBoard.imgs[temp % 10], (width - 10 - (i + 1) * 20, 10))
            temp //= 10

        if gameOver:
            gameOverPos = (1294, 29)
            gameOverSize = (381, 21)
            gameOverImg = chop(image, gameOverPos, gameOverSize)
            gameOverRect = gameOverImg.get_rect()
            gameOverRect.center = (width // 2, height // 2 - 70)
            screen.blit(gameOverImg, gameOverRect)

        pygame.display.flip()
        clock.tick(120)

    pygame.quit()

if __name__ == '__main__':
    t2 = threading.Thread(target=net)
    t2.start()
    main()
    
    # t1 = threading.Thread(target=main)
    # t1.start()
