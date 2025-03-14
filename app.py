from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import random
import json
import os
import shortuuid
from flask_cors import CORS

app = Flask(__name__)
# Добавляем поддержку CORS для работы с React-приложением
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class GameState(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    deck = db.Column(db.JSON)
    player_cards = db.Column(db.JSON)
    opponent_cards = db.Column(db.JSON)
    discard_pile = db.Column(db.JSON)
    current_turn = db.Column(db.String(10))
    player_name = db.Column(db.String(20))
    opponent_name = db.Column(db.String(20))
    game_type = db.Column(db.String(10))  # 'bot' или 'multiplayer'
    no_valid_moves_count = db.Column(db.Integer)
    game_status = db.Column(db.String(20))  # 'waiting', 'active', 'finished'
    auto_draw_cards = db.Column(db.Boolean, default=False)  # По умолчанию не добирать карты автоматически

def load_verbs():
    with open(os.path.join(app.static_folder, 'data', 'verbs.json'), 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['verbs']

@app.route("/")
def index():
    return render_template('index.html')

class Game:
    def __init__(self, game_id=None):
        self.verbs = load_verbs()
        if game_id:
            game_state = GameState.query.get(game_id)
            if game_state:
                self.deck = game_state.deck
                self.players = {
                    "player": game_state.player_cards,
                    "opponent": game_state.opponent_cards
                }
                self.discard_pile = game_state.discard_pile
                self.current_turn = game_state.current_turn
                self.game_type = game_state.game_type
                self.no_valid_moves_count = game_state.no_valid_moves_count if hasattr(game_state, 'no_valid_moves_count') else 0
                return
        
        self.deck = []
        for verb in self.verbs:
            self.deck.extend([
                (verb['infinitive'], verb['infinitive'], 0, verb['translation']),
                (verb['prasens_3'], verb['infinitive'], 1, verb['translation']),
                (verb['prateritum'], verb['infinitive'], 2, verb['translation']),
                (verb['partizip_2'], verb['infinitive'], 3, verb['translation'])
            ])
        random.shuffle(self.deck)
        self.players = {"player": [], "opponent": []}
        self.discard_pile = []
        self.current_turn = "player"  # Всегда начинает игрок
        self.game_type = "bot"  # по умолчанию игра с ботом
        self.no_valid_moves_count = 0
        self.deal_cards()

    def deal_cards(self):
        for _ in range(10):
            self.players["player"].append(self.deck.pop())
            self.players["opponent"].append(self.deck.pop())
        self.discard_pile.append(self.deck.pop())
        
        # При игре с ботом проверяем, может ли игрок сделать ход с начальными картами
        if self.game_type == "bot":
            if not self.check_if_playable():
                # Если игрок не может сделать ход, берем карту и меняем ход на бота
                self.pull_one_more_card("player")
                # Предотвращаем немедленный ход бота, просто меняя ход обратно на игрока
                self.current_turn = "player"

    def play_card(self, player, card):
        if player != self.current_turn:
            return False, "Не ваш ход!"
        if card not in self.players[player]:
            return False, "У вас нет такой карты!"
        top_form, top_verb, top_index, _ = self.discard_pile[-1]
        card_form, card_verb, card_index, _ = card
        if card_index == top_index or card_verb == top_verb:
            self.players[player].remove(card)
            self.discard_pile.append(card)
            
            # Проверяем, остались ли у игрока карты
            if len(self.players[player]) == 0:
                self.current_turn = "over"  # Игра закончена
                winner = player
                return True, f"Игрок {player} выиграл, избавившись от всех карточек!"
            
            self.current_turn = "opponent" if player == "player" else "player"
            self.no_valid_moves_count = 0
            
            # Если игра с ботом, сразу делаем ход ботом
            if self.game_type == "bot" and self.current_turn == "opponent":
                print("Делаем ход ботом")  # Отладка
                return self.bot_move()
            
            return True, "Карта успешно сыграна."
        return False, "Недопустимый ход!"

    def bot_move(self):
        if self.game_type != "bot" or self.current_turn != "opponent":
            return False, "Не ход бота!"
        
        print("Ход бота, проверяем карты")  # Отладка
        
        top_form, top_verb, top_index, _ = self.discard_pile[-1]
        for card in self.players["opponent"]:
            if card[2] == top_index or card[1] == top_verb:
                self.players["opponent"].remove(card)
                self.discard_pile.append(card)
                
                # Проверяем, остались ли у бота карты
                if len(self.players["opponent"]) == 0:
                    self.current_turn = "over"  # Игра закончена
                    return True, "Бот выиграл, избавившись от всех карточек!"
                
                self.current_turn = "player"
                self.no_valid_moves_count = 0
                print("Бот сделал ход, передаем ход игроку")  # Отладка
                return True, "Бот сделал ход."

        # если у бота нет возможности сходить
        print("У бота нет возможности сходить, берет карту")  # Отладка
        self.pull_one_more_card("opponent")
        self.no_valid_moves_count += 1
        if self.no_valid_moves_count >= 2:
            self.replace_top_card()
            self.no_valid_moves_count = 0
            return True, "После двух ходов без возможности сходить, верхняя карточка заменена"
        return True, "У бота нет возможности сходить. Он берет карту и пропускает ход"

    def pull_one_more_card(self, player_name):
        if len(self.deck) > 0:
            self.players[player_name].append(self.deck.pop())
        self.current_turn = "opponent" if player_name == "player" else "player"

    def replace_top_card(self):
        """Заменяет верхнюю карту в стопке сброса на новую карту из колоды"""
        if len(self.deck) > 0:
            # Если в стопке сброса больше одной карты
            if len(self.discard_pile) > 1:
                # Берем карту, которую собираемся скрыть (предпоследнюю)
                card_to_return = self.discard_pile.pop(-2)
                # Возвращаем её в колоду
                self.deck.append(card_to_return)
                # Перемешиваем колоду
                random.shuffle(self.deck)
            
            # Заменяем верхнюю карту на новую из колоды
            new_card = self.deck.pop()
            self.discard_pile.append(new_card)
            
            return new_card
        return None

    def get_state(self):
        return {
            "player_cards": self.players["player"],
            "opponent_cards_count": len(self.players["opponent"]),
            "discard_pile": self.discard_pile[-1],
            "current_turn": self.current_turn,
            "game_type": self.game_type,
            "is_my_turn": self.current_turn == "player",  # Для игры с ботом игрок всегда "player"
            "game_over": self.current_turn == "over",  # Добавляем флаг для обозначения конца игры
            "winner": "player" if len(self.players["player"]) == 0 else ("opponent" if len(self.players["opponent"]) == 0 else None)
        }

    def check_if_playable(self):
        top_form, top_verb, top_index, _ = self.discard_pile[-1]
        for card in self.players["player"]:
            if card[2] == top_index or card[1] == top_verb:
                return True
        return False

    def save_state(self, game_id, player_name=None, opponent_name=None, game_type="bot", auto_draw_cards=False):
        # Получаем текущее состояние из базы данных, если оно существует
        existing_state = GameState.query.get(game_id)
        
        if existing_state:
            # Обновляем существующую запись
            existing_state.deck = self.deck
            existing_state.player_cards = self.players["player"]
            existing_state.opponent_cards = self.players["opponent"]
            existing_state.discard_pile = self.discard_pile
            existing_state.current_turn = self.current_turn
            existing_state.no_valid_moves_count = self.no_valid_moves_count
            
            # Проверяем, закончилась ли игра
            if len(self.players["player"]) == 0 or len(self.players["opponent"]) == 0:
                existing_state.game_status = 'finished'
            
            # Обновляем имена и тип игры только если они предоставлены
            if player_name:
                existing_state.player_name = player_name
            if opponent_name:
                existing_state.opponent_name = opponent_name
                existing_state.game_status = 'active' if existing_state.game_status != 'finished' else 'finished'
            elif game_type == 'multiplayer' and not existing_state.opponent_name:
                existing_state.game_status = 'waiting' if existing_state.game_status != 'finished' else 'finished'
            
            if game_type:
                existing_state.game_type = game_type
            # Всегда сохраняем значение auto_draw_cards, независимо от того, True оно или False
            existing_state.auto_draw_cards = auto_draw_cards
        else:
            # Создаем новую запись
            game_state = GameState(
                id=game_id,
                deck=self.deck,
                player_cards=self.players["player"],
                opponent_cards=self.players["opponent"],
                discard_pile=self.discard_pile,
                current_turn=self.current_turn,
                player_name=player_name,
                opponent_name=opponent_name,
                game_type=game_type,
                no_valid_moves_count=self.no_valid_moves_count,
                game_status='waiting' if game_type == 'multiplayer' and not opponent_name else 'active',
                auto_draw_cards=auto_draw_cards
            )
            db.session.add(game_state)
        
        # Сохраняем изменения
        db.session.commit()

games = {}

@app.route("/game/new", methods=["POST"])
def create_new_game():
    data = request.json
    player_name = data.get('player_name')
    game_type = data.get('game_type', 'bot')  # по умолчанию игра с ботом
    auto_draw_cards = data.get('auto_draw_cards', False)  # По умолчанию не добирать карты автоматически
    
    if not player_name:
        return jsonify({"success": False, "message": "Имя игрока обязательно"})
    if player_name.lower() == 'bot':
        return jsonify({"success": False, "message": "Имя 'bot' зарезервировано"})
    
    game_id = shortuuid.uuid()[:8]
    games[game_id] = Game()
    games[game_id].game_type = game_type
    
    # Явно гарантируем, что в игре с ботом первый ход за игроком
    if game_type == 'bot':
        games[game_id].current_turn = "player"
    
    games[game_id].save_state(game_id, player_name, game_type=game_type, auto_draw_cards=auto_draw_cards)
    
    return jsonify({
        "success": True, 
        "game_id": game_id,
        "game_type": game_type,
        "auto_draw_cards": auto_draw_cards
    })

@app.route("/game/<game_id>/join", methods=["POST"])
def join_game(game_id):
    data = request.json
    player_name = data.get('player_name')
    
    if not player_name:
        return jsonify({"success": False, "message": "Имя игрока обязательно"})
    if player_name.lower() == 'bot':
        return jsonify({"success": False, "message": "Имя 'bot' зарезервировано"})
    
    game_state = GameState.query.get(game_id)
    if not game_state:
        return jsonify({"success": False, "message": "Игра не найдена"})
    
    if game_state.game_type != 'multiplayer':
        return jsonify({"success": False, "message": "Это не мультиплеерная игра"})
    
    if game_state.opponent_name and game_state.opponent_name != player_name:
        return jsonify({"success": False, "message": "К этой игре уже присоединился другой игрок"})
    
    if game_state.player_name == player_name:
        return jsonify({"success": False, "message": "Вы не можете играть против себя"})
    
    if not game_state.opponent_name:
        game_state.opponent_name = player_name
        game_state.game_status = 'active'
        db.session.commit()
    
    return jsonify({
        "success": True,
        "game_type": game_state.game_type,
        "opponent_name": game_state.player_name,
        "auto_draw_cards": game_state.auto_draw_cards
    })

@app.route("/game/<game_id>/state", methods=["GET"])
def get_game_state(game_id):
    player_name = request.args.get('player_name')
    if not player_name:
        return jsonify({"success": False, "message": "Не указано имя игрока"})

    if game_id not in games:
        games[game_id] = Game(game_id)
    
    game = games[game_id]
    game_state = GameState.query.get(game_id)
    
    # Отладка
    print(f"Получен запрос состояния игры: {game_id}, игрок: {player_name}, текущий ход: {game.current_turn}")
    
    # Для мультиплеерной игры
    if game_state and game_state.game_type == 'multiplayer':
        if game_state.game_status == 'waiting':
            return jsonify({
                "status": "waiting",
                "message": "Ожидание подключения второго игрока..."
            })
        
        # Определяем, является ли текущий игрок первым или вторым игроком
        is_first_player = game_state.player_name == player_name
        
        # Формируем состояние игры с точки зрения текущего игрока
        # Используем глубокие копии для предотвращения случайных изменений
        player_cards = game_state.player_cards.copy() if is_first_player else game_state.opponent_cards.copy()
        opponent_cards = game_state.opponent_cards.copy() if is_first_player else game_state.player_cards.copy()
        discard_pile = game_state.discard_pile.copy() if game_state.discard_pile else []
        
        # Проверка на случай, если сброс пуст
        top_card = discard_pile[-1] if discard_pile else None
        
        state = {
            "player_cards": player_cards,
            "opponent_cards_count": len(opponent_cards),
            "discard_pile": top_card,
            "current_turn": game_state.current_turn,
            "game_type": game_state.game_type,
            "game_status": game_state.game_status,
            "player_name": player_name,
            "opponent_name": game_state.opponent_name if is_first_player else game_state.player_name,
            "is_my_turn": (game_state.current_turn == "player" and is_first_player) or 
                        (game_state.current_turn == "opponent" and not is_first_player),
            "auto_draw_cards": game_state.auto_draw_cards
        }
        
        # Обновляем состояние игры в памяти
        game.players = {
            "player": game_state.player_cards.copy(),
            "opponent": game_state.opponent_cards.copy()
        }
        game.discard_pile = discard_pile
        game.current_turn = game_state.current_turn
        game.no_valid_moves_count = game_state.no_valid_moves_count
        
        return jsonify(state)
    
    # Для игры с ботом
    if game.game_type == 'bot':
        # Отладка
        print(f"Игра с ботом, ход: {game.current_turn}")
        
        # Проверяем возможность хода игрока и настройку автоматического добора карт
        if game.current_turn == "player" and not game.check_if_playable() and game_state.auto_draw_cards:
            print("У игрока нет возможности сделать ход, берет карту автоматически")
            game.pull_one_more_card("player")
            bot_success, bot_message = game.bot_move()
            game.save_state(game_id, auto_draw_cards=game_state.auto_draw_cards)
        
        state = game.get_state()
        state["auto_draw_cards"] = game_state.auto_draw_cards
        print(f"Возвращаемое состояние: {state}")
        return jsonify(state)
        
    # Сохраняем состояние для обычной игры (не с ботом)
    game.save_state(game_id, auto_draw_cards=game_state.auto_draw_cards)
    return jsonify(game.get_state())

@app.route("/game/<game_id>/play", methods=["POST"])
def play_card(game_id):
    if game_id not in games:
        return jsonify({"success": False, "message": "Игра не найдена!"})
    
    data = request.json
    player_name = data.get('player_name')
    if not player_name:
        return jsonify({"success": False, "message": "Не указано имя игрока"})
    
    game = games[game_id]
    game_state = GameState.query.get(game_id)
    
    # Определяем, является ли текущий игрок первым или вторым игроком
    is_first_player = game_state.player_name == player_name
    current_role = "player" if is_first_player else "opponent"
    
    # Проверяем, чей сейчас ход
    if game_state.current_turn != current_role:
        return jsonify({"success": False, "message": "Сейчас не ваш ход!"})
    
    # Для мультиплеерной игры
    if game_state.game_type == 'multiplayer':
        # Получаем карты текущего игрока
        player_cards = game_state.player_cards.copy() if is_first_player else game_state.opponent_cards.copy()
        received_card = data["card"]
        
        # Преобразуем полученную карту в тот же формат, который используется в БД
        received_card = [str(received_card[0]), str(received_card[1]), int(received_card[2]), str(received_card[3])]
        
        # Ищем соответствующую карту в руке игрока
        card_found = False
        card_index = -1
        
        for i, card in enumerate(player_cards):
            # Убедимся, что типы данных в карте совпадают
            card_check = [str(card[0]), str(card[1]), int(card[2]), str(card[3])]
            
            if (card_check[0] == received_card[0] and 
                card_check[1] == received_card[1] and 
                card_check[2] == received_card[2] and 
                card_check[3] == received_card[3]):
                card_found = True
                card_index = i
                break
        
        if not card_found:
            return jsonify({"success": False, "message": "У вас нет такой карты!"})
        
        # Проверяем, можно ли сыграть эту карту
        top_card = game_state.discard_pile[-1]
        top_card_check = [str(top_card[0]), str(top_card[1]), int(top_card[2]), str(top_card[3])]
        
        if received_card[2] == top_card_check[2] or received_card[1] == top_card_check[1]:
            # Удаляем карту из руки игрока
            played_card = player_cards.pop(card_index)
            
            # Обновляем состояние игры в памяти
            if is_first_player:
                game.players["player"] = player_cards
            else:
                game.players["opponent"] = player_cards
            
            # Добавляем карту в сброс
            game.discard_pile.append(played_card)
            
            # Меняем ход
            game.current_turn = "opponent" if game.current_turn == "player" else "player"
            game.no_valid_moves_count = 0
            
            # Сохраняем все изменения в базу данных
            game.save_state(game_id, game_state.player_name, game_state.opponent_name, game_state.game_type, game_state.auto_draw_cards)
            
            return jsonify({"success": True, "message": "Карта успешно сыграна"})
        return jsonify({"success": False, "message": "Недопустимый ход!"})
    
    # Для игры с ботом
    success, message = game.play_card("player", tuple(data["card"]))
    if success:
        # Сохраняем текущее значение auto_draw_cards
        game.save_state(game_id, auto_draw_cards=game_state.auto_draw_cards)
        return jsonify({"success": success, "message": message})
    return jsonify({"success": success, "message": message})

@app.route("/game/<game_id>/draw", methods=["POST"])
def draw_card(game_id):
    """Маршрут для случая, когда игрок не может сделать ход и хочет взять карту"""
    if game_id not in games:
        return jsonify({"success": False, "message": "Игра не найдена!"})
    
    data = request.json
    player_name = data.get('player_name')
    if not player_name:
        return jsonify({"success": False, "message": "Не указано имя игрока"})
    
    game = games[game_id]
    game_state = GameState.query.get(game_id)
    
    # Определяем, является ли текущий игрок первым или вторым игроком
    is_first_player = game_state.player_name == player_name
    current_role = "player" if is_first_player else "opponent"
    
    # Проверяем, чей сейчас ход
    if game_state.current_turn != current_role:
        return jsonify({"success": False, "message": "Сейчас не ваш ход!"})
    
    # Проверяем, действительно ли у игрока нет возможности сделать ход
    player_cards = game_state.player_cards.copy() if is_first_player else game_state.opponent_cards.copy()
    top_card = game_state.discard_pile[-1]
    
    # Проверяем все карты игрока
    has_valid_move = False
    for card in player_cards:
        if card[2] == top_card[2] or card[1] == top_card[1]:
            has_valid_move = True
            break
    
    if has_valid_move:
        return jsonify({"success": False, "message": "У вас есть возможность сделать ход!"})
    
    # Берем карту из колоды
    if len(game.deck) > 0:
        new_card = game.deck.pop()
        if is_first_player:
            game.players["player"].append(new_card)
            game_state.player_cards.append(new_card)
        else:
            game.players["opponent"].append(new_card)
            game_state.opponent_cards.append(new_card)
    
    # Увеличиваем счетчик безвыходных ситуаций
    game.no_valid_moves_count += 1
    game_state.no_valid_moves_count += 1
    
    # Если было 2 хода (вместо 3) без возможности сходить, меняем верхнюю карту
    if game.no_valid_moves_count >= 2:
        new_card = game.replace_top_card()
        if new_card:
            # Обновляем состояние в БД
            game_state.discard_pile = game.discard_pile
        game.no_valid_moves_count = 0
        game_state.no_valid_moves_count = 0
        message = "После двух ходов без возможности сходить, верхняя карточка заменена"
    else:
        # Передаем ход другому игроку
        game.current_turn = "opponent" if current_role == "player" else "player"
        game_state.current_turn = game.current_turn
        message = "Карта взята, ход переходит к другому игроку"
    
    # Сохраняем изменения
    db.session.commit()
    
    # Для игры с ботом
    if game.game_type == "bot" and game.current_turn == "opponent":
        bot_success, bot_message = game.bot_move()
        game.save_state(game_id, auto_draw_cards=game_state.auto_draw_cards)
        return jsonify({"success": True, "message": message, "bot_message": bot_message})
    else:
        # Сохраняем состояние для обычной игры (не с ботом)
        game.save_state(game_id, auto_draw_cards=game_state.auto_draw_cards)
    
    return jsonify({"success": True, "message": message})

@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint для проверки работоспособности сервиса"""
    return jsonify({"status": "healthy"}), 200

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8085, debug=True)

