/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
type BasicFaceProps = {
  ctx: CanvasRenderingContext2D;
  mouthScale: number;
  eyeScale: number;
  color?: string;
  rotation: number;
};

export function renderBasicFace(props: BasicFaceProps) {
  const { ctx, color, rotation, eyeScale } = props;
  const { width, height } = ctx.canvas;

  // Clear the canvas
  ctx.clearRect(0, 0, width, height);

  const centerX = width / 2;
  const centerY = height / 2;
  const size = Math.min(width, height) * 0.8;
  const triangleHeight = (size * Math.sqrt(3)) / 2;

  ctx.save();
  ctx.translate(centerX, centerY);
  ctx.rotate(rotation);

  // Draw the triangle
  ctx.fillStyle = color || 'white';
  ctx.beginPath();
  ctx.moveTo(0, -triangleHeight / 2);
  ctx.lineTo(-size / 2, triangleHeight / 2);
  ctx.lineTo(size / 2, triangleHeight / 2);
  ctx.closePath();
  ctx.fill();

  // Draw the eye
  const eyeCenterY = triangleHeight / 6;
  const eyeRadiusX = size * 0.1;
  const eyeRadiusY = eyeRadiusX * eyeScale;

  // Sclera (white part)
  ctx.fillStyle = 'white';
  ctx.beginPath();
  ctx.ellipse(0, eyeCenterY, eyeRadiusX, eyeRadiusY, 0, 0, 2 * Math.PI);
  ctx.fill();

  // Pupil (black part)
  if (eyeScale > 0.1) {
    ctx.fillStyle = 'black';
    ctx.beginPath();
    const pupilRadiusX = eyeRadiusX * 0.6;
    const pupilRadiusY = eyeRadiusY * 0.6;
    ctx.ellipse(0, eyeCenterY, pupilRadiusX, pupilRadiusY, 0, 0, 2 * Math.PI);
    ctx.fill();
  }

  ctx.restore();
}
