/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import React from 'react';
import c from 'classnames';

type SpeechBubbleProps = {
  text: string;
  isVisible: boolean;
};

export default function SpeechBubble({ text, isVisible }: SpeechBubbleProps) {
  return (
    <div className={c('speech-bubble', { visible: isVisible })}>
      <p>{text}</p>
    </div>
  );
}
