import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface LedDisplayProps {
    numLeds: number;
    ledStates: boolean[];
    toggleLed: (index: number) => void;
}

const LedDisplay: React.FC<LedDisplayProps> = ({ numLeds, ledStates }) => {
    const svgRef = useRef<SVGSVGElement | null>(null);

    useEffect(() => {
        if (svgRef.current) {
            const svg = d3.select(svgRef.current);
            svg.selectAll('*').remove(); // Clear previous content

            const ledWidth = 20;
            const ledHeight = 40;
            const spacing = 10;

            svg.attr('width', (ledWidth + spacing) * numLeds)
               .attr('height', ledHeight);

            ledStates.forEach((state, index) => {
                const x = index * (ledWidth + spacing);
                svg.append('rect')
                   .attr('x', x)
                   .attr('y', 0)
                   .attr('width', ledWidth)
                   .attr('height', ledHeight)
                   .attr('fill', state ? 'green' : 'red')
                   .attr('stroke', 'black')
                   .attr('stroke-width', 2);
            });
        }
    }, [numLeds, ledStates]);

    return <svg ref={svgRef}></svg>;
};

export default LedDisplay;