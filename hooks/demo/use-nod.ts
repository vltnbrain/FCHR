/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import { useEffect, useRef, useState } from 'react';

export type UseNodProps = {
  /** Maximum tilt angle (degrees) in either direction. */
  maxAngle: number;
  /** How quickly the tilt occurs. Lower values create slower, gentler movement. */
  speed?: number;
  /** Whether tilt mode is currently active. */
  isActive: boolean;
};

export default function useNod({
  maxAngle = 10,
  speed = 0.1,
  isActive = false,
}: UseNodProps) {
  const [angle, setAngle] = useState<number>(0);
  const [targetAngle, setTargetAngle] = useState<number>(0);
  const timeoutRef = useRef<NodeJS.Timeout>(undefined);
  const animationFrameRef = useRef<number>(0);

  // Reset to center when not active
  useEffect(() => {
    if (!isActive) {
      setTargetAngle(0);
    }
  }, [isActive]);

  // Schedule next random tilt (only when active)
  useEffect(() => {
    if (!isActive) return;

    const scheduleNextNod = () => {
      // Random delay, sometimes faster, sometimes slower
      const delay = 500 + Math.random() * 1500;
      timeoutRef.current = setTimeout(() => {
        // Nod down then up
        if (targetAngle <= 0) {
          // Nod down
          const newAngle = maxAngle * 0.5 + Math.random() * maxAngle * 0.5;
          setTargetAngle(newAngle);
        } else {
          // Return to center (or slightly up)
          setTargetAngle(0);
        }
        scheduleNextNod();
      }, delay);
    };

    scheduleNextNod();

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [maxAngle, isActive, targetAngle]); // depends on targetAngle to alternate

  // Animate current angle towards target angle
  useEffect(() => {
    const animate = () => {
      setAngle(currentAngle => {
        const diff = targetAngle - currentAngle;
        // Ease towards target angle
        const delta = diff * speed;
        return currentAngle + delta;
      });

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [targetAngle, speed]);

  return angle;
}
