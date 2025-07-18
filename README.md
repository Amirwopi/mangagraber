[**![Lang_farsi](https://user-images.githubusercontent.com/125398461/234186932-52f1fa82-52c6-417f-8b37-08fe9250a55f.png) فارسی**](README_fa.md)
# 🎌 Enhanced Manga Grabber for Telegram

A powerful, multi-format manga file search and download tool for Telegram channels with advanced features and multiple interfaces.

## ✨ Features

- **📦 Multi-Format Support**: ZIP, RAR, CBZ files
- **🔍 Smart Search**: Hashtag format support (`#Title_Name`)
- **⚡ Performance Optimized**: Advanced caching and batch processing
- **📊 Export Options**: JSON/CSV export of search results
- **🖥️ Multiple Interfaces**: CLI, GUI, and Telegram Bot
- **📈 Analytics**: Search statistics and performance metrics
- **🎯 Unlimited Search**: Scan entire channel history
- **🔧 Headless Mode**: CLI arguments for automation

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Telegram API credentials ([Get them here](https://my.telegram.org/apps))
- Required packages: `pip install -r requirements_enhanced.txt`

### Basic Usage

1. **CLI Version**:
   ```bash
   python manga_grabber_enhanced.py
   ```

2. **GUI Version**:
   ```bash
   python manga_grabber_gui.py
   ```

3. **Telegram Bot**:
   ```bash
   python manga_grabber_bot.py
   ```

4. **Headless Mode**:
   ```bash
   python manga_grabber_enhanced.py --headless --channel @channelname --search "manga title"
   ```

## 📋 Installation

### Method 1: Simple Installation

```bash
# Clone or download the files
# Install dependencies
pip install -r requirements.txt

# Run the application
python manga_grabber.py
```

### Method 2: Development Setup

```bash
# Install all dependencies including optional ones
pip install telethon rarfile python-telegram-bot

# For GUI support
pip install tkinter

# For enhanced features
pip install pandas openpyxl cachetools
```

## 🛠️ Configuration

### First Time Setup

1. **Get Telegram API Credentials**:
   - Go to [my.telegram.org/apps](https://my.telegram.org/apps)
   - Create a new application
   - Note your `api_id` and `api_hash`

2. **Configure the Application**:
   - Run the application
   - Enter your credentials when prompted
   - Choose to save configuration for future use

### Configuration Files

- `telegram_config.json`: Main Telegram API credentials
- `bot_config.json`: Telegram Bot configuration (for bot interface)

Example `telegram_config.json`:
```json
{
  "api_id": 12345678,
  "api_hash": "your_api_hash_here",
  "phone_number": "+1234567890"
}
```

## 📱 Interfaces

### 1. Command Line Interface (CLI)
The main interface with full functionality:
- Interactive menu system
- Search and download files
- Export results
- Performance statistics
- Cache management

### 2. Graphical User Interface (GUI)
User-friendly tkinter-based interface:
- Easy configuration management
- Visual file browser
- Progress indicators
- Export functionality

### 3. Telegram Bot Interface
Run as a Telegram bot:
- `/start` - Welcome message
- `/search` - Start searching
- `/status` - Check operation status
- `/cancel` - Cancel current operation
- `/help` - Show help

## 🔍 Search Examples

### Basic Search
```
Search: "Naruto"
Matches: "Naruto Chapter 1.zip", "Naruto_001.zip"
```

### Hashtag Search
```
Search: "#The_God_Of_High_School"
Matches: "The God of High School 001.zip", "#The_God_Of_High_School_002.zip"
```

### Advanced Search
```
Search: "God High School"
Matches: "The God of High School {Episodes 1-10}.zip"
```

## 📊 Export Formats

### JSON Export
```json
{
  "search_info": {
    "total_files": 50,
    "export_time": "2024-01-01T12:00:00",
    "stats": {
      "messages_scanned": 10000,
      "files_found": 50,
      "search_time": 45.2,
      "cache_hits": 1200
    }
  },
  "files": [
    {
      "filename": "Manga Title 001.zip",
      "size": 25165824,
      "size_formatted": "24.00MB",
      "mime_type": "application/zip",
      "date": "2024-01-01T10:30:00",
      "message_id": 12345
    }
  ]
}
```

### CSV Export
```csv
Filename,Size,Size (Formatted),MIME Type,Date,Message ID
"Manga Title 001.zip",25165824,"24.00MB","application/zip","2024-01-01T10:30:00",12345
```

## 🎯 Advanced Features

### Caching System
- **Title Normalization Cache**: Speeds up repeated searches
- **Search Term Cache**: Optimizes multi-word searches
- **Performance Tracking**: Monitor cache hit rates

### Performance Optimizations
- **Batch Processing**: Handle large channels efficiently
- **MIME Type Filtering**: Quick file type detection
- **Progress Tracking**: Real-time search progress
- **Memory Management**: Optimized for large datasets

### Archive Support
- **ZIP Files**: Standard ZIP archives
- **RAR Files**: WinRAR archives (requires rarfile)
- **CBZ Files**: Comic book ZIP format
- **Auto-Extraction**: Optional extraction after download

## 🔧 Command Line Arguments

```bash
python manga_grabber_enhanced.py [OPTIONS]

Options:
  --api-id INTEGER        Telegram API ID
  --api-hash TEXT         Telegram API Hash
  --phone TEXT            Phone number with country code
  --channel TEXT          Channel username (with @)
  --search TEXT           Search term
  --headless              Run in headless mode
  --export [json|csv]     Export format
  --config TEXT           Config file path
  --session TEXT          Custom session name
  --help                  Show this message and exit
```

### Examples

```bash
# Headless search with export
python manga_grabber_enhanced.py --headless --channel @mangachannel --search "Naruto" --export json

# Custom configuration
python manga_grabber_enhanced.py --config custom_config.json --session my_session

# Quick search
python manga_grabber_enhanced.py --channel @channel --search "#Manga_Title"
```

## 📁 Project Structure

```
manga-grabber/
├── manga_grabber_enhanced.py    # Main enhanced version
├── manga_grabber_gui.py         # GUI interface
├── manga_grabber_bot.py         # Telegram bot interface
├── manga_utils.py               # Utility functions
├── requirements_enhanced.txt     # Dependencies
├── README.md                    # This file
├── telegram_config.json         # API configuration
├── bot_config.json              # Bot configuration
└── downloads/                   # Downloaded files
```

## 🛡️ Security & Privacy

### Data Protection
- **Local Storage**: All data stored locally
- **Session Management**: Secure session handling
- **API Compliance**: Follows Telegram API guidelines
- **Rate Limiting**: Respects API rate limits

### Best Practices
- **Secure Configuration**: Store credentials safely
- **Session Security**: Use unique session names
- **Regular Updates**: Keep dependencies updated
- **Backup**: Regular backup of configuration

## 🐛 Troubleshooting

### Common Issues

1. **Connection Failed**:
   - Check internet connection
   - Verify API credentials
   - Ensure phone number is correct

2. **No Files Found**:
   - Try shorter search terms
   - Check channel accessibility
   - Verify file formats in channel

3. **Download Errors**:
   - Check available disk space
   - Verify file permissions
   - Restart application

4. **Performance Issues**:
   - Clear cache: Use cache management
   - Reduce search scope
   - Check system resources

### Debug Mode

```bash
# Enable verbose logging
python manga_grabber_enhanced.py --debug

# Check performance statistics
# Use the /status command or statistics menu
```

## 🔄 Updates & Maintenance

### Updating Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Cache Management
- Clear cache through the application menu
- Manual cache clearing: Delete session files
- Monitor cache performance in statistics

### Performance Monitoring
- Check search time and cache hit rates
- Monitor memory usage for large searches
- Review export file sizes

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repo-url>
cd manga-grabber

# Install development dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Document functions and classes
- Add unit tests for new features

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Getting Help
- Check the troubleshooting section
- Review command line help: `--help`
- Check log files in the application directory

### Reporting Issues
- Provide detailed error messages
- Include system information
- Describe steps to reproduce
- Share configuration (without credentials)

### Feature Requests
- Describe the desired functionality
- Explain use cases
- Suggest implementation approaches

## 🎉 Acknowledgments

- **Telethon**: Excellent Telegram client library
- **Python Community**: For amazing libraries and tools
- **Manga Community**: For inspiration and feedback

## 📚 Related Projects

- [Telethon Documentation](https://docs.telethon.dev/)
- [Python Telegram Bot](https://python-telegram-bot.org/)
- [Manga Downloaders](https://github.com/topics/manga-downloader)

---

**Made with ❤️ for the manga community**

*Last updated: july 2025*
