// src/components/Modal.jsx

import React from 'react'
import '../styles/blackjackgame.css';


export default function Modal({ isOpen, title, message, onConfirm, onCancel }) {
    if (!isOpen) return null;

  return (
    <div className='modal-overlay'>
        <div className='modal-content'>
            {title && <h3>{title}</h3>}
            <p>{message}</p>
            <div className='modal-buttons'>
                <button className='modal-btn modal-confirm' onClick={onConfirm}>Yes</button>
                <button className='modal-btn modal-cancel' onClick={onCancel}>No</button>
            </div>
        </div>
    </div>
  )
}
