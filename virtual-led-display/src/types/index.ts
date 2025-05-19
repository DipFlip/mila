export interface Led {
    id: number;
    state: 'on' | 'off';
}

export interface LedDisplayProps {
    leds: Led[];
    width: number;
    height: number;
    onLedClick?: (id: number) => void;
}