# Virtual LED Display

This project is a single-page application built with TypeScript, React, and D3.js that simulates a virtual LED display. The application allows users to visualize LED states and configurations dynamically.

## Project Structure

```
virtual-led-display
├── public
│   └── index.html          # Main HTML file serving the React app
├── src
│   ├── components
│   │   └── LedDisplay.tsx  # React component for rendering the LED display
│   ├── d3
│   │   └── ledUtils.ts     # Utility functions for D3.js LED rendering
│   ├── App.tsx             # Main App component
│   ├── index.tsx           # Entry point for the React application
│   └── types
│       └── index.ts        # TypeScript interfaces and types
├── package.json            # npm configuration file
├── tsconfig.json           # TypeScript configuration file
└── README.md               # Project documentation
```

## Installation

To get started with the project, follow these steps:

1. Clone the repository:
   ```
   git clone <repository-url>
   cd virtual-led-display
   ```

2. Install the dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```

4. Open your browser and navigate to `http://localhost:3000` to view the application.

## Usage

The application features a virtual LED display that can be configured to show different states. You can modify the number of LEDs and their states through the `LedDisplay` component.

## Technologies Used

- TypeScript
- React
- D3.js

## Contributing

If you would like to contribute to this project, please fork the repository and submit a pull request with your changes.