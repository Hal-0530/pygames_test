
import pygame
import random
import sys
import os
import json

# -------------------------
# 初期設定
# -------------------------

pygame.init()

SCREEN_WIDTH = 480
SCREEN_HEIGHT = 640

screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT)
)

pygame.display.set_caption("Pixel Dodge Game")

clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 32)
title_font = pygame.font.SysFont(None, 64)
subtitle_font = pygame.font.SysFont(None, 28)
start_font = pygame.font.SysFont(None, 32)
lanking_font = pygame.font.SysFont(None, 24)

# 色
BLACK = (20, 20, 30)
WHITE = (240, 240, 240)
BLUE = (50, 150, 255)
RED = (230, 70, 70)
YELLOW = (255, 220, 80)

# 本ファイルのディレクトリを取得
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# -------------------------
# ランキング関連機能
# -------------------------

# ランキング保村ファイル
SCORE_FILE = os.path.join(BASE_DIR, "high_scores.json")

# ランキング読み込み機能
def load_high_scores():

    try:
        with open(SCORE_FILE, "r", encoding="utf-8") as f:
            scores = json.load(f)

        return sorted(
            scores,
            key=lambda item: item["score"],
            reverse=True
        )[:5]
    
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# ランキングデータを読み込む
high_scores = load_high_scores()

# ランキング保存機能
def save_high_scores():

    with open(SCORE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            high_scores,
            f,
            ensure_ascii=False,
            indent=2
        )

# 5位以内に入るか判定する機能
def qualifies_for_ranking(new_score):

    if len(high_scores) < 5:
        return True

    return new_score > high_scores[-1]["score"]

# -------------------------
# BGM
# -------------------------

# BGMの読み込みと再生
pygame.mixer.music.load(
    os.path.join(BASE_DIR, "assets", "space_shooter_famicom_bgm.wav")
)

pygame.mixer.music.set_volume(0.35)

# -1 は無限ループ
pygame.mixer.music.play(-1)

# -------------------------
# 効果音
# -------------------------

# 爆発効果音の読み込み
explosion_sound = pygame.mixer.Sound(
    os.path.join(BASE_DIR, "assets", "sfx_explosion.wav")
)

# 音量（0.0～1.0）
explosion_sound.set_volume(0.8)

# -------------------------
# 背景
# -------------------------

# 背景画像読み込み
background_image = pygame.image.load(
    os.path.join(BASE_DIR, "assets", "background.png")
).convert()

# ゲーム画面サイズに合わせる
background_image = pygame.transform.scale(
    background_image,
    (SCREEN_WIDTH, SCREEN_HEIGHT)
)

# -------------------------
# プレイヤー
# -------------------------

# プレイヤー画像の読み込み
player_image = pygame.image.load(
    os.path.join(BASE_DIR, "assets", "player_ship.png")
).convert_alpha()

# 画像サイズを48×48に変更
PLAYER_SIZE = 48
player_image = pygame.transform.scale(
    player_image, (PLAYER_SIZE, PLAYER_SIZE)
)

# プレイヤーの位置
player = player_image.get_rect(
    center=(SCREEN_WIDTH // 2, 566)
)

# 当たり判定設定
player_hitbox = pygame.Rect(0, 0, 24, 32)
player_hitbox.center = player.center

# プレイヤーの移動速度
player_speed = 5

# -------------------------
# 爆発画像
# -------------------------

explosion_image = pygame.image.load(
    os.path.join(BASE_DIR, "assets", "explosion_64x64.png")
).convert_alpha()

# 爆発アニメーションのサイズ
EXPLOSION_SIZES = [64, 40, 64, 32, 16]

# -------------------------
# 敵
# -------------------------

enemies = []

# 敵画像の読み込み
enemy_images = {
    "alien_green": pygame.image.load(
        os.path.join(BASE_DIR, "assets", "alien_green.png")
    ).convert_alpha(),

    "alien_purple": pygame.image.load(
        os.path.join(BASE_DIR, "assets", "alien_purple.png")
    ).convert_alpha(),

    "alien_orange": pygame.image.load(
        os.path.join(BASE_DIR, "assets", "alien_orange.png")
    ).convert_alpha()
}

enemy_timer = 0

# 敵の出現間隔
INITIAL_ENEMY_INTERVAL = 0.8
MIN_ENEMY_INTERVAL = 0.25

# -------------------------
# ゲーム状態
# -------------------------

score = 0
game_over = False

# ゲーム開始状態(False=タイトル画面、True=ゲーム中)
game_started = False

# 爆発状態
explosion_active = False
explosion_timer = 0
explosion_duration = 1.35

# 爆発が発生した位置
explosion_center = player.center

# プレイヤー名入力モード
name_entry_active = False
player_name = ""

# -------------------------
# プレイヤーの描画
# -------------------------

def draw_player():

    screen.blit(player_image, player)

    # 当たり判定を赤枠で表示（確認用）
    pygame.draw.rect(
        screen,
        RED,
        player_hitbox,
        1
    )

# -------------------------
# 爆発の描画
# -------------------------

def draw_explosion():

    # 爆発の進行度に応じて画像サイズを選択
    progress = explosion_timer / explosion_duration

    frame = min(
        int(progress * len(EXPLOSION_SIZES)),
        len(EXPLOSION_SIZES) - 1
    )

    size = EXPLOSION_SIZES[frame]

    # 指定サイズに拡大・縮小
    image = pygame.transform.scale(
        explosion_image,
        (size, size)
    )

    # 爆発の中心に画像を配置
    explosion_rect = image.get_rect(
        center=explosion_center
    )

    screen.blit(image, explosion_rect)

# -------------------------
# 敵の生成
# -------------------------

def create_enemy():

    # 出現するエイリアンの種類をランダムに選ぶ
    enemy_type = random.choice(["alien_green", "alien_purple", "alien_orange"])

    # 種類ごとの大きさと移動速度
    enemy_settings = {
        "alien_green": {"size": 36, "speed": 4},
        "alien_purple": {"size": 28, "speed": 6},
        "alien_orange": {"size": 52, "speed": 2.5}
    }

    settings = enemy_settings[enemy_type]
    size = settings["size"]

    # 選択した画像を指定サイズに変更
    image = pygame.transform.scale(
        enemy_images[enemy_type],
        (size, size)
    )
    
    x = random.randint(0, SCREEN_WIDTH - size)

    # 敵の画像表示用の矩形
    rect = pygame.Rect(x, -size, size, size)

    # 当たり判定は画像サイズ70%にする
    hitbox_size = int(size * 0.7)
    hitbox = pygame.Rect(
        0, 0, 
        hitbox_size, 
        hitbox_size
    )

    # 敵の中央に当たり判定配置
    hitbox.center = rect.center

    enemy = {
        "image" : image,
        "rect": rect,
        "hitbox": hitbox,
        "speed": settings["speed"]
    }

    enemies.append(enemy)


# -------------------------
# 敵の描画
# -------------------------

def draw_enemies():

    for enemy in enemies:

        screen.blit(
            enemy["image"], 
            enemy["rect"]
        )

        # 当たり判定の確認用（赤枠）
        pygame.draw.rect(
            screen,
            RED,
            enemy["hitbox"],
            1
        )

# -------------------------
# ランキングシートの描画
# -------------------------

def draw_lanking_sheets(x, y):
    # x, y は左上の座標

    frame_hight = 25
    frame_width1 = 75
    frame_width2 = 200
    frame_width3 = 100

    box_rect = pygame.Rect(x, y, frame_width1 ,frame_hight)
    pygame.draw.rect(screen, WHITE, box_rect, width=2)
    text_surf = lanking_font.render("RANK", True, WHITE)
    text_rect = text_surf.get_rect(center=box_rect.center)
    screen.blit(text_surf, text_rect)

    box_rect2 = pygame.Rect(x+frame_width1, y, frame_width2 ,frame_hight)
    pygame.draw.rect(screen, WHITE, box_rect2, width=2)
    text_surf2 = lanking_font.render("NAME", True, WHITE)
    text_rect2 = text_surf.get_rect(center=box_rect2.center)
    screen.blit(text_surf2, text_rect2)

    box_rect3 = pygame.Rect(x+frame_width1+frame_width2, y, frame_width3 ,frame_hight)
    pygame.draw.rect(screen, WHITE, box_rect3, width=2)
    text_surf3 = lanking_font.render("SCORE", True, WHITE)
    text_rect3 = text_surf.get_rect(center=box_rect3.center)
    screen.blit(text_surf3, text_rect3)

    for i, score_entry in enumerate(high_scores):
        
        box_rect = pygame.Rect(x, y + (i + 1) * frame_hight, frame_width1 ,frame_hight)
        pygame.draw.rect(screen, WHITE, box_rect, width=2)
        text_surf = lanking_font.render(str(i + 1), True, WHITE)
        text_rect = text_surf.get_rect(center=box_rect.center)
        screen.blit(text_surf, text_rect)

        box_rect2 = pygame.Rect(x+frame_width1, y + (i + 1) * frame_hight, frame_width2 ,frame_hight)
        pygame.draw.rect(screen, WHITE, box_rect2, width=2)
        text_surf2 = lanking_font.render(score_entry["name"], True, WHITE)
        text_rect2 = text_surf2.get_rect(center=box_rect2.center)
        screen.blit(text_surf2, text_rect2)

        box_rect3 = pygame.Rect(x+frame_width1+frame_width2, y + (i + 1) * frame_hight, frame_width3 ,frame_hight)
        pygame.draw.rect(screen, WHITE, box_rect3, width=2)
        text_surf3 = lanking_font.render(str(score_entry["score"]), True, WHITE)
        text_rect3 = text_surf3.get_rect(center=box_rect3.center)
        screen.blit(text_surf3, text_rect3)

# -------------------------
# 背景の星
# -------------------------

stars = []

# 星を70個作成
for _ in range(70):
    stars.append({
        "x": random.randint(0, SCREEN_WIDTH),
        "y": random.randint(0, SCREEN_HEIGHT),
        "speed": random.choice([25, 40, 65]),
        "size": random.choice([1, 1, 2]),
        "color": random.choice([
            (180, 200, 255),
            (220, 220, 255),
            (255, 240, 180)
        ])
    })

# -------------------------
# 流れ星
# -------------------------

shooting_stars = []

# 流れ星の出現タイマー
shooting_star_timer = 0

# 次の流れ星が出現するまでの時間
shooting_star_interval = 4.0

# -------------------------
# メインループ
# -------------------------

running = True

while running:

    # 経過時間（秒）
    delta_time = clock.tick(60) / 1000

    # イベント処理
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # タイトル画面でキー入力を受け付ける
        if not game_started and event.type == pygame.KEYDOWN:

            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                # 色々初期化してからゲームを開始する
                player = player_image.get_rect(
                    center=(SCREEN_WIDTH // 2, 566)
                )
                enemies.clear()
                score = 0
                explosion_active = False
                game_over = False
                name_entry_active = False
                player_name = ""

                game_started = True

        # 名前入力中の処理
        if name_entry_active:

            if event.type == pygame.TEXTINPUT:
                if len(player_name) < 10:
                    player_name += event.text

            elif event.type == pygame.KEYDOWN:

                # 1文字削除
                if event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]

                # Enterでランキング登録
                elif event.key == pygame.K_RETURN:

                    if player_name.strip():

                        high_scores.append({
                            "name": player_name.strip(),
                            "score": int(score)
                        })

                        high_scores.sort(
                            key=lambda item: item["score"],
                            reverse=True
                        )

                        high_scores = high_scores[:5]

                        save_high_scores()

                        #タイトル画面へ戻る
                        game_started = False
                        game_over = False

            continue  # 名前入力中はゲーム処理をスキップ

        # ゲームオーバー時の処理（名前入力中でない場合）
        if not name_entry_active and game_over and event.type == pygame.KEYDOWN:

            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                # タイトル画面へ戻る
                game_started = False
                game_over = False



    # -------------------------
    # ゲーム中の処理
    # -------------------------

    # 星を下方向に移動
    for star in stars:

        star["y"] += star["speed"] * delta_time

        # 画面の下に到達したら上に戻す
        if star["y"] > SCREEN_HEIGHT:
            star["y"] = -star["size"]
            star["x"] = random.randint(0, SCREEN_WIDTH)

    # 流れ星の処理
    shooting_star_timer += delta_time
    
    if shooting_star_timer >= shooting_star_interval:

        # 流れ星の移動方向と速度
        direction = random.choice([-1, 1])

        shooting_stars.append({
            "x": random.randint(0, SCREEN_WIDTH),
            "y": random.randint(0, SCREEN_HEIGHT // 2),
            "vx": direction * random.uniform(220, 320),
            "vy": random.uniform(220, 320)
        })

        # タイマーをリセット
        shooting_star_timer = 0

        # 次の出現までの時間をランダムに設定
        shooting_star_interval = random.uniform(3.0, 6.0)

    # 流れ星を移動
    for star in shooting_stars:

        star["x"] += star["vx"] * delta_time
        star["y"] += star["vy"] * delta_time

    # 画面外に出た流れ星を削除
    shooting_stars = [
        star for star in shooting_stars
        if (
            -50 < star["x"] < SCREEN_WIDTH + 50
            and star["y"] < SCREEN_HEIGHT + 50
        )
    ]
    
    # 通常時（ゲームオーバ前）の処理
    if game_started and not game_over and not explosion_active:

        # キーボード入力
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player.x -= player_speed

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player.x += player_speed

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            player.y -= player_speed

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            player.y += player_speed

        # 画面外に出ないようにする
        player.clamp_ip(screen.get_rect())

        # 当たり判定を宇宙船の中央に合わせる
        player_hitbox.center = player.center

        # 生存時間に応じて敵の出現間隔を短くする
        enemy_interval = max(
            MIN_ENEMY_INTERVAL,
            INITIAL_ENEMY_INTERVAL - score * 0.01
        )
        
        # 敵の生成タイマー
        enemy_timer += delta_time

        if enemy_timer >= enemy_interval:
            create_enemy()
            enemy_timer = 0

        # 敵の移動
        for enemy in enemies:
            enemy["rect"].y += enemy["speed"]
            #当たり判定も追従
            enemy["hitbox"].center = enemy["rect"].center

        # 画面外の敵を削除
        enemies = [
            enemy for enemy in enemies
            if enemy["rect"].top < SCREEN_HEIGHT
        ]

        # 衝突判定
        for enemy in enemies:

            if player_hitbox.colliderect(enemy["hitbox"]):

                # プレイヤー爆発
                explosion_active = True
                explosion_timer = 0
                explosion_center = player.center
                explosion_sound.play()
                
                break #複数の敵に同時に衝突しても一度だけ爆発させるためにループを抜ける

        # スコア（生存時間）
        score += delta_time

    # 爆発中の処理
    if explosion_active:

        explosion_timer += delta_time

        if explosion_timer >= explosion_duration:
            explosion_active = False
            game_over = True

            #ランキング入りするか判定
            if qualifies_for_ranking(int(score)):
                name_entry_active = True
                player_name = ""

    # -------------------------
    # 画面描画
    # -------------------------

    # 背景画像を表示
    screen.blit(background_image, (0, 0))

    # 星を描画
    for star in stars:
        pygame.draw.rect(
            screen,
            star["color"],
            (
                int(star["x"]),
                int(star["y"]),
                star["size"],
                star["size"]
            )
        )

    # 流れ星を描画
    for star in shooting_stars:

        # 流れ星の尾
        tail_x = star["x"] - star["vx"] * 0.07
        tail_y = star["y"] - star["vy"] * 0.07

        pygame.draw.line(
            screen,
            (100, 180, 255),
            (int(tail_x), int(tail_y)),
            (int(star["x"]), int(star["y"])),
            3
        )
        # 流れ星の先端
        pygame.draw.circle(
            screen,
            (240, 250, 255),
            (int(star["x"]), int(star["y"])),
            3
        )

    # -------------------------
    # ゲーム画面・タイトル画面の描画
    # -------------------------

    if game_started and not name_entry_active:

        if not explosion_active and not game_over:
            # プレイヤーと敵の描画
            draw_player()
            draw_enemies()
        else:
            # 爆発の描画
            draw_explosion()

        # スコア表示
        score_text = font.render(
            f"TIME: {int(score)}",
            True,
            YELLOW
        )

        screen.blit(score_text, (15, 15))

    elif game_started and name_entry_active:
        # 名前入力パネル
        panel = pygame.Rect(40, 220, 400, 220)
        pygame.draw.rect(screen, BLACK, panel)
        pygame.draw.rect(screen, YELLOW, panel, 2)

        # 見出し
        title_text = subtitle_font.render(
            "NEW HIGH SCORE!",
            True,
            YELLOW
        )
        screen.blit(title_text, title_text.get_rect(
            center=(SCREEN_WIDTH // 2, 280)
        ))

        # 入力案内
        prompt_text = font.render(
            "ENTER YOUR NAME:",
            True,
            WHITE
        )
        screen.blit(prompt_text, prompt_text.get_rect(
            center=(SCREEN_WIDTH // 2, 305)
        ))

        # 入力中の名前（未入力ならカーソル代わりに "_" を表示）
        name_text = font.render(
            player_name or "_",
            True,
            WHITE
        )
        screen.blit(name_text, name_text.get_rect(
            center=(SCREEN_WIDTH // 2, 350)
        ))

        # 操作案内
        help_text = subtitle_font.render(
            "ENTER: SAVE   BACKSPACE: DELETE",
            True,
            BLUE
        )
        screen.blit(help_text, help_text.get_rect(
            center=(SCREEN_WIDTH // 2, 400)
        ))


    else:

        # タイトル
        title_text = title_font.render(
            "PIXEL DODGE",
            True,
            WHITE
        )
        screen.blit(title_text, title_text.get_rect(
            center=(SCREEN_WIDTH // 2, 160)
        ))

        # サブタイトル
        subtitle_text = subtitle_font.render(
            " SPACE SURVIVAL ",
            True,
            BLUE
        )
        screen.blit(subtitle_text, subtitle_text.get_rect(
            center=(SCREEN_WIDTH // 2, 210)
        ))

        # ランキング表示
        ranking_title = subtitle_font.render(
            "HIGH SCORES",
            True,
            YELLOW
        )
        screen.blit(ranking_title, ranking_title.get_rect(
            center=(SCREEN_WIDTH // 2, 270)
        ))

        draw_lanking_sheets(60, 300)

        # ゲーム開始案内

        if pygame.time.get_ticks() % 1000 < 500:  # 点滅効果
            start_text = start_font.render(
                "PRESS SPACE TO START",
                True,
                YELLOW
            )
            screen.blit(start_text, start_text.get_rect(
                center=(SCREEN_WIDTH // 2, 490)
            ))

    # ゲームオーバー
    if game_over:

        over_text = font.render(
            "GAME OVER",
            True,
            RED
        )
        screen.blit(over_text, over_text.get_rect(
            center=(SCREEN_WIDTH // 2, 255)
        ))

        if not name_entry_active:
            restart_text = font.render(
                "PRESS SPACE OR ENTER TO RETURN",
                True,
                WHITE
            )
            screen.blit(restart_text, restart_text.get_rect(
                center=(SCREEN_WIDTH // 2, 330)
            ))

    pygame.display.flip()

pygame.quit()
sys.exit()
