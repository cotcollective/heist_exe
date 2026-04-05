/**
 * NavArrow — Grosse flèche directionnelle style Crazy Taxi.
 * Pointe vers le waypoint en calculant le bearing player → cible.
 * Disparaît automatiquement quand le joueur est en portée.
 */
export default function NavArrow({ bearing, inRange }) {
    if (inRange || bearing === null) return null

    return (
        <div
            className="nav-arrow-container"
            aria-label={`Direction : ${bearing}°`}
        >
            {/* Pulsing background ring */}
            <div className="nav-arrow-ring" />

            {/* La flèche SVG qui tourne */}
            <svg
                viewBox="0 0 80 80"
                width="80"
                height="80"
                className="nav-arrow-svg"
                style={{ transform: `rotate(${bearing}deg)` }}
            >
                {/* Corps de la flèche */}
                <polygon
                    points="40,6 58,62 40,50 22,62"
                    fill="#00d4aa"
                    opacity="0.95"
                    filter="url(#glow)"
                />
                {/* Tige */}
                <rect x="35" y="48" width="10" height="20" fill="#00d4aa" opacity="0.7" rx="2" />

                {/* Filtre glow */}
                <defs>
                    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                        <feGaussianBlur stdDeviation="3" result="blur" />
                        <feMerge>
                            <feMergeNode in="blur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                </defs>
            </svg>

            {/* Label degré discret */}
            <div className="nav-arrow-label">{bearing}°</div>
        </div>
    )
}
