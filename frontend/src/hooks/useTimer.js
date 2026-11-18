/**
 * =============================================================================
 * StudyAI — Timer Hook
 * =============================================================================
 * Countdown timer for exams with pause/resume and low-time warning.
 * =============================================================================
 */

import { useState, useEffect, useRef } from 'react';

export function useTimer(initialMinutes = 15, onExpire = null) {
  const [secondsLeft, setSecondsLeft] = useState(initialMinutes * 60);
  const [isRunning, setIsRunning] = useState(true);
  const onExpireRef = useRef(onExpire);
  onExpireRef.current = onExpire;

  useEffect(() => {
    if (!isRunning || secondsLeft <= 0) return;

    const interval = setInterval(() => {
      setSecondsLeft(prev => {
        if (prev <= 1) {
          clearInterval(interval);
          if (onExpireRef.current) onExpireRef.current();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isRunning, secondsLeft]);

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;
  const formatted = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  const isLowTime = secondsLeft > 0 && secondsLeft <= 120; // 2 minutes or less

  const pause = () => setIsRunning(false);
  const resume = () => setIsRunning(true);
  const reset = (newMins = initialMinutes) => {
    setSecondsLeft(newMins * 60);
    setIsRunning(true);
  };

  return {
    secondsLeft,
    formatted,
    isLowTime,
    isRunning,
    pause,
    resume,
    reset
  };
}
