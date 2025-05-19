export const createLed = (svg: any, x: number, y: number, isOn: boolean) => {
    const led = svg.append('circle')
        .attr('cx', x)
        .attr('cy', y)
        .attr('r', 10)
        .attr('fill', isOn ? 'green' : 'red')
        .attr('stroke', 'black')
        .attr('stroke-width', 2);
    
    return led;
};

export const updateLedState = (led: any, isOn: boolean) => {
    led.attr('fill', isOn ? 'green' : 'red');
};

export const clearDisplay = (svg: any) => {
    svg.selectAll('*').remove();
};