import React, { memo } from 'react';
import Card from './Card';
import OpponentCard from './OpponentCard';

// Используем React.memo для предотвращения ненужных перерисовок
const GameTable = memo(({ gameState, onPlayCard, onDrawCard, hasValidMove }) => {
  const { 
    currentGameId, 
    playerName, 
    playerCards, 
    opponentCardsCount, 
    discardPile, 
    opponentName, 
    isMyTurn, 
    gameOver, 
    winner,
    waiting,
    autoDrawCards
  } = gameState;

  // Отображение карт игрока
  const renderPlayerCards = () => {
    if (!playerCards || !Array.isArray(playerCards)) return null;
    
    return playerCards.map((card, index) => (
      <Card 
        key={`player-card-${index}-${card[0]}`}
        card={card} 
        disabled={!isMyTurn || gameOver}
        onClick={() => onPlayCard(card)}
      />
    ));
  };

  // Отображение карт противника
  const renderOpponentCards = () => {
    const cards = [];
    for (let i = 0; i < opponentCardsCount; i++) {
      cards.push(<OpponentCard key={`opponent-card-${i}`} />);
    }
    return cards;
  };

  // Определение текста для индикатора хода
  const getTurnText = () => {
    if (gameOver) {
      return `Игра окончена. ${winner === 'player' ? 'Вы выиграли!' : 'Противник выиграл!'}`;
    } else {
      return `Ход: ${isMyTurn ? 'Ваш' : 'Противника'}`;
    }
  };

  // Проверяем, должна ли быть показана кнопка взятия карты
  const shouldShowDrawButton = !gameOver && !autoDrawCards;

  return (
    <div className="game-table">
      {/* Область противника */}
      <div className="player-area opponent-area">
        <div className="player-info">
          <span className="player-name">{opponentName}</span>
          <span className="card-count">{opponentCardsCount}</span>
        </div>
        <div className="opponent-hand" style={{ display: waiting ? 'none' : 'flex' }}>
          {renderOpponentCards()}
        </div>
      </div>

      {/* Центральная область */}
      <div className="play-area">
        <div className="discard-pile">
          {discardPile && (
            <Card card={discardPile} isDiscard={true} />
          )}
        </div>
        <div className="turn-indicator">{getTurnText()}</div>
        <div className="game-id-display">ID игры: <span>{currentGameId}</span></div>
        {waiting && (
          <div className="waiting-message">
            Ожидание подключения второго игрока...
          </div>
        )}
      </div>

      {/* Область игрока */}
      <div className="player-area">
        <div className="player-info">
          <span className="player-name">{playerName}</span>
          {shouldShowDrawButton && (
            <button className="draw-button" onClick={onDrawCard}>
              Взять карту
            </button>
          )}
          <span className="card-count">{playerCards ? playerCards.length : 0}</span>
        </div>
        <div className="player-hand" id="player-cards">
          {renderPlayerCards()}
        </div>
      </div>
    </div>
  );
});

export default GameTable; 