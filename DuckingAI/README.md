# DuckingAI Edge Extension

A chatbot extension for Stevens Institute of Technology websites that provides instant assistance and information.

## Features

- Appears on Stevens-related websites (Canvas, Workday, etc.)
- Easy-to-use chat interface
- Connects to existing chat API endpoint
- Responsive and user-friendly design

## Installation

1. Clone this repository or download the source code
2. Open Edge browser and navigate to `edge://extensions/`
3. Enable "Developer mode" in the top right corner
4. Click "Load unpacked" and select the `DuckingAI` folder

## Development

### Project Structure
```
DuckingAI/
├── manifest.json
├── src/
│   ├── css/
│   │   └── chatbot.css
│   ├── js/
│   │   ├── background.js
│   │   ├── content.js
│   │   └── config.js
│   └── components/
└── README.md
```

### Configuration

To add new domains where the chatbot should appear, edit the `ALLOWED_DOMAINS` array in `src/js/config.js`:

```javascript
window.ALLOWED_DOMAINS = [
  'sit.instructure.com',
  'wd5.myworkday.com/stevens'
  // Add more domains here
];
```

### API Integration

The chatbot is configured to connect to your chat API endpoint. Update the `API_ENDPOINT` in `src/js/config.js`:

```javascript
window.API_ENDPOINT = 'http://localhost:8000/api/chat';
```

## Usage

1. Visit any supported Stevens website
2. Click the AI icon in the bottom right corner to open the chat
3. Type your question and press Enter or click the send button
4. The chatbot will respond with relevant information

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. 