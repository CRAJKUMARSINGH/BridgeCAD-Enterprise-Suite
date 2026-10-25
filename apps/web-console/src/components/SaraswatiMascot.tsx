/**
 * SaraswatiMascot — the in-app design assistant mascot.
 *
 * Renders the Saraswati artwork next to an optional caption. Safe to render
 * with no props. `SARASWATI` is a stable named alias kept for the component
 * test's `import { SARASWATI } from './SaraswatiMascot'`.
 */
export interface SaraswatiMascotProps {
  /** Image source; defaults to the bundled asset in `public/`. */
  src?: string
  /** Accessible description of the mascot. */
  alt?: string
  /** Rendered width and height in pixels. */
  size?: number
  /** Optional caption shown beside the mascot. */
  caption?: string
  /** Extra classes for the wrapping element. */
  className?: string
}

export function SaraswatiMascot({
  src = '/saraswati.jpg',
  alt = 'Saraswati — BridgeCAD design assistant',
  size = 96,
  caption,
  className,
}: SaraswatiMascotProps) {
  return (
    <figure className={className}>
      <img
        src={src}
        alt={alt}
        width={size}
        height={size}
        loading="lazy"
        style={{ width: size, height: size }}
        className="rounded-full border border-slate-200 bg-white object-cover shadow-sm"
      />
      {caption ? <figcaption className="text-sm text-slate-500">{caption}</figcaption> : null}
    </figure>
  )
}

/** Named alias retained for the SARASWATI component test. */
export const SARASWATI = SaraswatiMascot

export default SaraswatiMascot
