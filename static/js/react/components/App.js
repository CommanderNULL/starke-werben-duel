import React, { useState, useEffect } from 'react';
import GameSetup from './GameSetup';
import GameTable from './GameTable';
import Notification from './Notification';

const App = () => {
  // Состояние игры
  const [gameState, setGameState] = useState({
    currentGameId: null,
    playerName: null,
    gameType: 'bot',
    isMyTurn: false,
    playerCards: [],
    opponentCardsCount: 0,
    discardPile: null,
    opponentName: 'Противник',
    gameOver: false,
    winner: null,
    waiting: false,
    autoDrawCards: false
  });

  // Состояние уведомлений
  const [notification, setNotification] = useState(null);

  // Функция для показа уведомлений
  const showNotification = (message, isConfirmation = false, callback = null) => {
    setNotification({ message, isConfirmation, callback });
    
    // Автоматически скрываем обычные уведомления через 3 секунды
    if (!isConfirmation) {
      setTimeout(() => {
        setNotification(null);
      }, 3000);
    }
  };

  // Обновление состояния игры с сервера
  const updateGameState = async () => {
    if (!gameState.currentGameId || !gameState.playerName) return;

    try {
      const url = `/game/${gameState.currentGameId}/state?player_name=${encodeURIComponent(gameState.playerName)}&t=${Date.now()}`;
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
      
      const state = await response.json();
      
      // Обработка статуса ожидания
      if (state.status === 'waiting') {
        setGameState(prevState => ({
          ...prevState,
          waiting: true,
          opponentName: 'Ожидание противника...'
        }));
        return;
      }

      // Определяем, чей ход
      let isMyTurn = false;
      if (gameState.gameType === 'bot') {
        isMyTurn = state.current_turn === 'player';
      } else {
        isMyTurn = state.is_my_turn;
      }

      // Проверяем, закончена ли игра
      if (state.game_over && !gameState.gameOver) {
        let message = '';
        if (state.winner === 'player') {
          message = 'Поздравляем! Вы выиграли, избавившись от всех карточек!';
        } else if (state.winner === 'opponent') {
          message = 'Противник выиграл, избавившись от всех карточек!';
        }
        
        if (state.game_type === 'bot') {
          showNotification(message, true, () => {
            setGameState(prevState => ({
              ...prevState,
              currentGameId: null,
              gameOver: false
            }));
          });
        } else {
          showNotification(message);
        }
      }

      // Обновляем состояние, только если данные изменились
      // Это предотвращает ненужные перерисовки
      setGameState(prevState => {
        // Проверяем, действительно ли изменилось что-то важное
        const hasChanges = 
          prevState.isMyTurn !== isMyTurn ||
          JSON.stringify(prevState.playerCards) !== JSON.stringify(state.player_cards) ||
          prevState.opponentCardsCount !== state.opponent_cards_count ||
          JSON.stringify(prevState.discardPile) !== JSON.stringify(state.discard_pile) ||
          prevState.gameOver !== state.game_over ||
          prevState.winner !== state.winner ||
          prevState.waiting !== (state.status === 'waiting') ||
          prevState.opponentName !== (state.opponent_name || prevState.opponentName);

        // Возвращаем новое состояние только если есть изменения
        return hasChanges ? {
          ...prevState,
          isMyTurn,
          playerCards: state.player_cards || [],
          opponentCardsCount: state.opponent_cards_count || 0,
          discardPile: state.discard_pile,
          opponentName: state.opponent_name || prevState.opponentName,
          gameOver: state.game_over || false,
          winner: state.winner || null,
          waiting: state.status === 'waiting',
          autoDrawCards: state.auto_draw_cards !== undefined ? state.auto_draw_cards : prevState.autoDrawCards
        } : prevState;
      });
    } catch (error) {
      console.error('Error updating game state:', error);
    }
  };

  // Создание новой игры
  const createNewGame = async (name, type, autoDrawCards = false) => {
    try {
      if (!name) {
        showNotification('Пожалуйста, введите ваше имя');
        return;
      }
      if (name.toLowerCase() === 'bot') {
        showNotification('Имя "bot" зарезервировано');
        return;
      }
      
      const response = await fetch('/game/new', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          player_name: name,
          game_type: type,
          auto_draw_cards: autoDrawCards
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setGameState({
          ...gameState,
          currentGameId: data.game_id,
          playerName: name,
          gameType: type,
          gameOver: false,
          winner: null,
          autoDrawCards: data.auto_draw_cards
        });
        
        if (type === 'multiplayer') {
          showNotification('Игра создана! Поделитесь ID игры с противником: ' + data.game_id);
        }
      } else {
        showNotification(data.message);
      }
    } catch (error) {
      console.error('Error creating new game:', error);
      showNotification('Ошибка при создании новой игры');
    }
  };

  // Присоединение к существующей игре
  const joinGame = async (gameId, name) => {
    try {
      if (!gameId) {
        showNotification('Пожалуйста, введите ID игры');
        return;
      }
      if (!name) {
        showNotification('Пожалуйста, введите ваше имя');
        return;
      }
      if (name.toLowerCase() === 'bot') {
        showNotification('Имя "bot" зарезервировано');
        return;
      }
      
      const response = await fetch(`/game/${gameId}/join`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ player_name: name })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setGameState({
          ...gameState,
          currentGameId: gameId,
          playerName: name,
          gameType: data.game_type,
          opponentName: data.opponent_name,
          gameOver: false,
          winner: null,
          autoDrawCards: data.auto_draw_cards
        });
      } else {
        showNotification(data.message);
      }
    } catch (error) {
      console.error('Error joining game:', error);
      showNotification('Ошибка при подключении к игре');
    }
  };

  // Игровые действия
  const playCard = async (card) => {
    if (!gameState.isMyTurn) {
      showNotification('Сейчас не ваш ход!');
      return;
    }
    
    try {
      const response = await fetch(`/game/${gameState.currentGameId}/play`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          card,
          player_name: gameState.playerName
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        if (data.bot_message) {
          showNotification(data.bot_message);
        }
        // Обновление состояния произойдет через регулярный запрос
      } else {
        showNotification(data.message);
      }
    } catch (error) {
      console.error('Error playing card:', error);
      showNotification('Ошибка при ходе');
    }
  };

  const drawCard = async () => {
    try {
      const response = await fetch(`/game/${gameState.currentGameId}/draw`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          player_name: gameState.playerName
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        if (data.bot_message) {
          showNotification(data.bot_message);
        }
        showNotification(data.message);
        // Обновление состояния произойдет через регулярный запрос
      } else {
        showNotification(data.message);
      }
    } catch (error) {
      console.error('Error drawing card:', error);
      showNotification('Ошибка при взятии карты');
    }
  };

  // Функция для проверки наличия валидного хода
  const hasValidMove = () => {
    if (!gameState.playerCards || !gameState.discardPile) return false;
    
    const topCard = gameState.discardPile;
    const topForm = topCard[0];
    const topVerb = topCard[1];
    const topIndex = topCard[2];
    
    for (const card of gameState.playerCards) {
      if (card[2] === topIndex || card[1] === topVerb) {
        return true;
      }
    }
    
    return false;
  };

  // Регулярное обновление состояния игры
  useEffect(() => {
    if (gameState.currentGameId) {
      updateGameState();
      
      const intervalId = setInterval(updateGameState, 2000);
      
      return () => clearInterval(intervalId);
    }
  }, [gameState.currentGameId, gameState.playerName]);

  return (
    <div className="app">
      {notification && (
        <Notification 
          message={notification.message} 
          isConfirmation={notification.isConfirmation} 
          onConfirm={notification.callback}
          onClose={() => setNotification(null)}
        />
      )}
      
      {!gameState.currentGameId ? (
        <GameSetup 
          onCreateGame={createNewGame} 
          onJoinGame={joinGame} 
        />
      ) : (
        <GameTable 
          gameState={gameState}
          onPlayCard={playCard}
          onDrawCard={drawCard}
          hasValidMove={hasValidMove}
        />
      )}
    </div>
  );
};

export default App; 