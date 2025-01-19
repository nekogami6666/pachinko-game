import pygame
import random
import math

# 初期化
pygame.init()

# 画面サイズとFPS
SCREEN_WIDTH, SCREEN_HEIGHT = 400, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("脳汁ドバドバ-パチンコゲーム")
clock = pygame.time.Clock()

# 色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (50, 50, 50)

# フォント
FONT = pygame.font.Font(None, 48)  # 大きめのフォント
FONT_SMALL = pygame.font.Font(None, 32)  # 右上のスコア表示などに使う少し小さめのフォント

# ボールクラス
class Ball:
    def __init__(self, x, y, radius, color, velocity):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.vx, self.vy = velocity
        self.is_scored = False

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.5  # 重力

        # 画面端の反射
        if self.x - self.radius < 0 or self.x + self.radius > SCREEN_WIDTH:
            self.vx *= -0.9
        if self.y - self.radius < 0:
            self.vy *= -0.9

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

# ピン（障害物）クラス
class Pin:
    def __init__(self, x, y, radius, color=WHITE):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

# スロットエリア（箱）クラス
class Slot:
    def __init__(self, x, points, width):
        self.points = points
        self.width = width
        self.x = x
        self.y = SCREEN_HEIGHT - 50
        self.height = 50
        # ▼▼▼【変更1】オリジナルの点数を記録しておくための属性を追加 ▼▼▼
        self.original_points = points

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height), 2)
        points_text = FONT_SMALL.render(f"{self.points}", True, WHITE)
        text_rect = points_text.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        screen.blit(points_text, text_rect)

    def is_ball_in_slot(self, ball):
        if self.x < ball.x < self.x + self.width and ball.y + ball.radius >= self.y:
            return True
        return False

# パチンコゲームクラス
class PachinkoGame:
    def __init__(self):
        self.balls = []
        self.pins = self.create_pins()
        self.slots = self.create_slots()
        self.score = 0  # スコアの初期値
        self.remaining_balls = 10  # 残り玉数
        self.red_pin = Pin(SCREEN_WIDTH // 2, 50, 25, RED)  # 赤いピンを上部に移動
        self.dragging_ball = None
        self.is_dragging = False
        self.drag_line_start = None
        self.drag_line_end = None
        self.game_over = False

        # ▼▼▼【変更2】前回ボールが入ったスロットを記憶するための変数を追加 ▼▼▼
        self.last_triggered_slot = None

    def create_pins(self):
        pins = []
        rows = 5
        cols = 9
        spacing_x = SCREEN_WIDTH // cols
        spacing_y = 100
        for row in range(rows):
            for col in range(cols):
                offset = (row % 2) * (spacing_x // 2)
                x = col * spacing_x + offset + spacing_x // 2
                y = row * spacing_y + 100
                pins.append(Pin(x, y, 5))
        return pins

    def create_slots(self):
        slots = []
        # スコア設定と対応する箱の幅計算
        slot_points = [1000, 300, 100, 30, 10]
        total_width = SCREEN_WIDTH
        inverse_points = [1 / p for p in slot_points]
        total_inverse = sum(inverse_points)
        x_offset = 0

        for i, (points, inverse) in enumerate(zip(slot_points, inverse_points)):
            width = max(50, int((inverse / total_inverse) * total_width))
            if i == len(slot_points) - 1:
                width = SCREEN_WIDTH - x_offset
            slots.append(Slot(x_offset, points, width))
            x_offset += width
        return slots

    def add_ball(self, x, y, velocity):
        if self.remaining_balls > 0:
            self.balls.append(Ball(x, y, 10, WHITE, velocity))

    def update(self):
        if self.remaining_balls == 0:
            self.game_over = True

        for ball in self.balls:
            ball.update()

            # ピンとの衝突
            for pin in self.pins:
                dx = ball.x - pin.x
                dy = ball.y - pin.y
                distance = math.hypot(dx, dy)
                if distance < ball.radius + pin.radius:
                    angle = math.atan2(dy, dx)
                    ball.vx += math.cos(angle) * 2
                    ball.vy += math.sin(angle) * 2

            # スロットへの加点処理
            if not ball.is_scored:
                for slot in self.slots:
                    if slot.is_ball_in_slot(ball):
                        # ▼▼▼【変更3】連続ボーナスのロジック ▼▼▼
                        if self.last_triggered_slot == slot:
                            # 同じスロットに連続で入った場合 → スロットの得点を倍にして加算
                            slot.points *= 2
                            self.score += slot.points
                        else:
                            # 違うスロットに入った場合
                            # 前回スロットを元の点数に戻し、今回スロットの点数を加算
                            if self.last_triggered_slot is not None:
                                self.last_triggered_slot.points = self.last_triggered_slot.original_points
                            self.score += slot.points

                        # ボールのスコア取得完了フラグ
                        ball.is_scored = True
                        # 今回入ったスロットを last_triggered_slot に更新
                        self.last_triggered_slot = slot
                        break  # 1つのスロットで得点したら抜ける

    # ▼▼▼ 右上スコア表示 ▼▼▼
    def draw_score_in_top_right(self, screen):
        score_text = FONT_SMALL.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (SCREEN_WIDTH - score_text.get_width() - 20, 20))

    # ▼▼▼ ゲームオーバー時の中央表示 ▼▼▼
    def draw_score_board(self, screen):
        pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 50, 300, 100))
        score_text = FONT.render(f"Your Score: {self.score}", True, BLACK)
        screen.blit(
            score_text,
            (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2 - score_text.get_height() // 2)
        )

    # ▼▼▼ 左上の残り玉数表示 ▼▼▼
    def draw_remaining_balls_board(self, screen):
        remaining_text = FONT_SMALL.render(f"Remaining: {self.remaining_balls}", True, WHITE)
        screen.blit(remaining_text, (20, 20))

    def draw(self, screen):
        screen.fill(BLACK)

        for slot in self.slots:
            slot.draw(screen)

        for pin in self.pins:
            pin.draw(screen)

        self.red_pin.draw(screen)

        for ball in self.balls:
            ball.draw(screen)

        self.draw_remaining_balls_board(screen)

        # プレイ中スコアを右上に表示
        self.draw_score_in_top_right(screen)

        # ゲームオーバー時は中央に大きくスコア表示
        if self.game_over:
            self.draw_score_board(screen)

        # ドラッグ中のボール
        if self.is_dragging and self.dragging_ball:
            pygame.draw.circle(
                screen, WHITE,
                (int(self.dragging_ball[0]), int(self.dragging_ball[1])),
                10
            )

        # ドラッグ中の線
        if self.is_dragging and self.drag_line_start and self.drag_line_end:
            pygame.draw.line(screen, WHITE, self.drag_line_start, self.drag_line_end, 2)

    def handle_drag(self, x, y):
        if self.is_dragging:
            self.dragging_ball = (x, y)
            self.drag_line_end = (x, y)

    def start_drag(self, x, y):
        if (self.red_pin.x - 15 < x < self.red_pin.x + 15 and
            self.red_pin.y - 15 < y < self.red_pin.y + 15):
            self.is_dragging = True
            self.drag_line_start = (x, y)

    def stop_drag(self):
        if self.is_dragging:
            if self.remaining_balls > 0:
                if self.dragging_ball:
                    ball_velocity = (
                        (self.drag_line_start[0] - self.dragging_ball[0]) * 0.2,
                        (self.drag_line_start[1] - self.dragging_ball[1]) * 0.2
                    )
                    self.add_ball(self.red_pin.x, self.red_pin.y, ball_velocity)
                    self.remaining_balls -= 1

            self.is_dragging = False
            self.dragging_ball = None
            self.drag_line_start = None
            self.drag_line_end = None

# ゲームループ
game = PachinkoGame()
running = True

while running:
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            game.start_drag(event.pos[0], event.pos[1])
        elif event.type == pygame.MOUSEBUTTONUP:
            game.stop_drag()
        elif event.type == pygame.MOUSEMOTION:
            game.handle_drag(event.pos[0], event.pos[1])

    game.update()
    game.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
