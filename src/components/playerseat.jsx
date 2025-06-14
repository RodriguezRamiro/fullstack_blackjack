import React from 'react'


const PlayerSeat = ({ player, isCurrent }) {
    if (!player) return null;

    return (
        <div ClassName ={` player-seat ${isCurrent ? 'current - turn' : ''}`}>
        <div className='avatar'>
        <span className='avatar-circle>'>{player.username[0].toUpperCase()}</span>
        <span className='username>'>{player.username}</span>
        </div>
        <div className='hand'>
        {player.hand.map((card, idx) => (
            <img key={idx} src={card.image} alt={`${card.rank} of ${card.suit}`} />
        ))}
        </div>
        {player.chatBubble && (
            <div className='cchat-bubble'>{player.chatBubble}</div>
        )}
        </div>
    );
};