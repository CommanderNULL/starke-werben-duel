import React, { useState } from 'react';

const GameSetup = ({ onCreateGame, onJoinGame }) => {
  const [playerName, setPlayerName] = useState('');
  const [gameId, setGameId] = useState('');
  const [gameType, setGameType] = useState('bot');
  const [autoDrawCards, setAutoDrawCards] = useState(false);

  const handleCreateGame = () => {
    onCreateGame(playerName, gameType, autoDrawCards);
  };

  const handleJoinGame = () => {
    onJoinGame(gameId, playerName);
  };

  return (
    <div className="game-setup">
      <h1>Starke Verben Duell</h1>
      <div className="setup-buttons">
        <div className="setup-form">
          <input 
            type="text" 
            id="player-name" 
            placeholder="Ваше имя" 
            maxLength="20"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
          />
          <div className="game-type-selector">
            <label>
              <input 
                type="radio" 
                name="game-type" 
                value="bot" 
                checked={gameType === 'bot'}
                onChange={() => setGameType('bot')}
              />
              Игра с ботом
            </label>
            <label>
              <input 
                type="radio" 
                name="game-type" 
                value="multiplayer"
                checked={gameType === 'multiplayer'}
                onChange={() => setGameType('multiplayer')}
              />
              Игра с человеком
            </label>
          </div>
          <div className="game-options">
            <label className="auto-draw-option">
              <input 
                type="checkbox" 
                name="auto-draw-cards"
                checked={autoDrawCards}
                onChange={() => setAutoDrawCards(!autoDrawCards)}
              />
              Добирать карты автоматически
            </label>
          </div>
          <div className="setup-actions">
            <button onClick={handleCreateGame}>Создать новую игру</button>
            <div className="separator">или</div>
            <div className="join-section">
              <div className="input-hint">Введите ID игры, чтобы присоединиться:</div>
              <div className="join-game">
                <input 
                  type="text" 
                  id="game-id" 
                  placeholder="Например: 94wqjh6A" 
                  maxLength="8"
                  value={gameId}
                  onChange={(e) => setGameId(e.target.value)}
                />
                <button onClick={handleJoinGame}>Присоединиться</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GameSetup; 