import type { ImageGeometry, Pixel } from '../store/useStore';

/** Konva stage pan/zoom applied on top of fitted display size. */
export type StageTransform = {
  scale: number;
  offsetX: number;
  offsetY: number;
};

export function mapPointBetweenSizes(point: Pixel, from: Pixel, to: Pixel): Pixel {
  return {
    x: from.x === 0 ? point.x : (point.x * to.x) / from.x,
    y: from.y === 0 ? point.y : (point.y * to.y) / from.y,
  };
}

export function displayToNatural(point: Pixel, geometry: ImageGeometry): Pixel {
  return mapPointBetweenSizes(point, geometry.display, geometry.natural);
}

export function naturalToDisplay(point: Pixel, geometry: ImageGeometry): Pixel {
  return mapPointBetweenSizes(point, geometry.natural, geometry.display);
}

/** Pointer position inside stage container -> fitted display coordinates. */
export function containerToDisplay(
  containerX: number,
  containerY: number,
  transform: StageTransform
): Pixel {
  return {
    x: (containerX - transform.offsetX) / transform.scale,
    y: (containerY - transform.offsetY) / transform.scale,
  };
}

/** Fitted display coordinates -> pointer position inside stage container. */
export function displayToContainer(point: Pixel, transform: StageTransform): Pixel {
  return {
    x: point.x * transform.scale + transform.offsetX,
    y: point.y * transform.scale + transform.offsetY,
  };
}

export function clampToDisplay(point: Pixel, display: Pixel): Pixel {
  return {
    x: Math.min(display.x, Math.max(0, point.x)),
    y: Math.min(display.y, Math.max(0, point.y)),
  };
}

export function displayToNaturalClamped(
  point: Pixel,
  geometry: ImageGeometry
): Pixel {
  const clamped = clampToDisplay(point, geometry.display);
  return displayToNatural(clamped, geometry);
}

export function naturalToDisplayClamped(
  point: Pixel,
  geometry: ImageGeometry
): Pixel {
  const display = naturalToDisplay(point, geometry);
  return clampToDisplay(display, geometry.display);
}

/** Round natural pixel to integer image coordinates. */
export function snapNatural(point: Pixel): Pixel {
  return { x: Math.round(point.x), y: Math.round(point.y) };
}

export function nudgeNatural(
  point: Pixel,
  dx: number,
  dy: number,
  geometry: ImageGeometry
): Pixel {
  return snapNatural({
    x: Math.min(geometry.natural.x - 1, Math.max(0, point.x + dx)),
    y: Math.min(geometry.natural.y - 1, Math.max(0, point.y + dy)),
  });
}
