/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import { RefObject, useEffect, useState, useRef } from 'react';

import { renderBasicFace } from './basic-face-render';

import useHover from '../../../hooks/demo/use-hover';
import useTilt from '../../../hooks/demo/use-tilt';
import { useLiveAPIContext } from '../../../contexts/LiveAPIContext';
import { useBlink } from '../../../hooks/demo/use-face';
import useNod from '../../../hooks/demo/use-nod';

// Minimum volume level that indicates audio output is occurring
const USER_AUDIO_INPUT_DETECTION_THRESHOLD = 0.02;

type BasicFaceProps = {
  /** The canvas element on which to render the face. */
  canvasRef: RefObject<HTMLCanvasElement | null>;
  /** The radius of the face. */
  radius?: number;
  /** The color of the face. */
  color?: string;
};

export default function BasicFace({
  canvasRef,
  radius = 250,
  color,
}: BasicFaceProps) {
  const userTalkingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Audio output volume
  const { inputVolume, isTalking } = useLiveAPIContext();

  // User talking state
  const [isUserTalking, setIsUserTalking] = useState(false);

  const [scale, setScale] = useState(0.1);

  const hoverPosition = useHover();
  const tiltAngle = useTilt({
    maxAngle: 15,
    speed: 0.075,
    isActive: isTalking,
  });
  const nodAngle = useNod({
    maxAngle: 10,
    isActive: isUserTalking,
  });
  const rotationRef = useRef(0);
  const eyeScale = useBlink({ speed: 0.0125 });

  useEffect(() => {
    function calculateScale() {
      setScale(Math.min(window.innerWidth, window.innerHeight) / 1000);
    }
    window.addEventListener('resize', calculateScale);
    calculateScale();
    return () => window.removeEventListener('resize', calculateScale);
  }, []);

  // Detect when user is talking
  useEffect(() => {
    if (inputVolume > USER_AUDIO_INPUT_DETECTION_THRESHOLD) {
      setIsUserTalking(true);
      if (userTalkingTimeoutRef.current) {
        clearTimeout(userTalkingTimeoutRef.current);
      }
      userTalkingTimeoutRef.current = setTimeout(() => {
        setIsUserTalking(false);
      }, 500); // User is considered "not talking" if no sound for 500ms
    }
  }, [inputVolume]);

  // Render the face on the canvas
  useEffect(() => {
    const ctx = canvasRef.current?.getContext('2d');
    if (!ctx) {
      return;
    }
    let animationFrameId: number;
    const render = () => {
      if (isTalking) {
        rotationRef.current += 0.02; // Rotation speed
      }
      renderBasicFace({
        ctx,
        mouthScale: 0,
        eyeScale: eyeScale,
        color,
        rotation: rotationRef.current,
      });
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [canvasRef, color, isTalking, eyeScale]);

  return (
    <canvas
      className="basic-face"
      ref={canvasRef}
      width={radius * 2 * scale}
      height={radius * 2 * scale}
      style={{
        display: 'block',
        transform: `translateY(${hoverPosition}px) rotateZ(${tiltAngle}deg) rotateX(${nodAngle}deg)`,
      }}
    />
  );
}
