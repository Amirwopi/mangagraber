import asyncio
import os
import re
import zipfile
import rarfile
import json
import csv
import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from functools import lru_cache
from dataclasses import dataclass
from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeFilename
from manga_utils import MangaUtils  # We'll create this helper module

@dataclass
class FileInfo:
    """Data class for file information"""
    message_id: int
    filename: str
    size: int
    mime_type: str
    date: datetime
    message: object

class MangaGrabberEnhanced:
    def __init__(self, api_id: int, api_hash: str, phone_number: str, 
                 session_name: Optional[str] = None, headless: bool = False):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.headless = headless
        
        # Dynamic session name based on phone number
        if not session_name:
            phone_hash = hashlib.md5(phone_number.encode()).hexdigest()[:8]
            session_name = f'manga_session_{phone_hash}'
        
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.download_folder = Path('downloads')
        self.download_folder.mkdir(exist_ok=True)
        
        # Supported file types
        self.supported_types = {
            'application/zip': '.zip',
            'application/x-zip-compressed': '.zip',
            'application/x-rar-compressed': '.rar',
            'application/vnd.comicbook+zip': '.cbz',
            'application/x-cbz': '.cbz'
        }
        
        # Cache for normalized titles
        self._title_cache: Dict[str, str] = {}
        self._search_cache: Dict[str, Tuple[str, str, List[str]]] = {}
        
        # Performance tracking
        self.stats = {
            'messages_scanned': 0,
            'files_found': 0,
            'cache_hits': 0,
            'search_time': 0
        }
    
    async def start(self) -> None:
        """Start the Telegram client"""
        await self.client.start(phone=self.phone_number)
        print("✅ Connected to Telegram successfully!")
        
        me = await self.client.get_me()
        print(f"📱 Logged in as: {me.first_name} {me.last_name or ''}")
    
    async def search_files(self, chat_username: str, search_term: str, 
                          limit: Optional[int] = None) -> List[FileInfo]:
        """Search for supported archive files with enhanced performance"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            entity = await self.client.get_entity(chat_username)
            print(f"🔍 Searching in: {entity.title}")
            print(f"⚡ Enhanced search mode - multi-format support")
            
            found_files = []
            message_count = 0
            
            # Pre-cache search terms
            self._prepare_search_cache(search_term)
            
            async for message in self.client.iter_messages(entity, limit=limit, wait_time=0.1):
                message_count += 1
                
                # Progress updates every 1000 messages for large chats
                if message_count % 1000 == 0:
                    print(f"   🚀 Scanned {message_count} messages, found {len(found_files)} files...")
                
                # Skip non-documents immediately
                if not message.document:
                    continue
                
                # Check if mime type is supported
                if message.document.mime_type not in self.supported_types:
                    continue
                
                # Get filename
                filename = self._extract_filename(message.document)
                if not filename:
                    continue
                
                # Verify file extension
                if not self._is_supported_file(filename):
                    continue
                
                # Match against search term
                if self.match_manga_title(search_term, filename):
                    file_info = FileInfo(
                        message_id=message.id,
                        filename=filename,
                        size=message.document.size,
                        mime_type=message.document.mime_type,
                        date=message.date,
                        message=message
                    )
                    found_files.append(file_info)
                    print(f"📄 Found: {filename} ({MangaUtils.format_size(message.document.size)})")
            
            # Update stats
            self.stats['messages_scanned'] = message_count
            self.stats['files_found'] = len(found_files)
            self.stats['search_time'] = asyncio.get_event_loop().time() - start_time
            
            print(f"\n📊 Search Results:")
            print(f"   Messages scanned: {message_count}")
            print(f"   Files found: {len(found_files)}")
            print(f"   Search time: {self.stats['search_time']:.2f}s")
            print(f"   Cache hits: {self.stats['cache_hits']}")
            
            # Sort files by date (newest first)
            found_files.sort(key=lambda x: x.date, reverse=True)
            
            return found_files
            
        except Exception as e:
            print(f"❌ Error searching files: {str(e)}")
            return []
    
    def _prepare_search_cache(self, search_term: str) -> None:
        """Pre-cache search term normalization"""
        if search_term not in self._search_cache:
            normalized = MangaUtils.normalize_title(search_term)
            clean = MangaUtils.clean_title(search_term)
            words = normalized.split()
            self._search_cache[search_term] = (normalized, clean, words)
    
    def _extract_filename(self, document) -> Optional[str]:
        """Extract filename from document attributes"""
        for attr in document.attributes:
            if isinstance(attr, DocumentAttributeFilename):
                return attr.file_name
        return None
    
    def _is_supported_file(self, filename: str) -> bool:
        """Check if file has supported extension"""
        return any(filename.lower().endswith(ext) for ext in self.supported_types.values())
    
    def match_manga_title(self, search_term: str, filename: str) -> bool:
        """Enhanced matching with caching"""
        # Get cached search data
        if search_term in self._search_cache:
            search_normalized, search_clean, search_words = self._search_cache[search_term]
            self.stats['cache_hits'] += 1
        else:
            search_normalized = MangaUtils.normalize_title(search_term)
            search_clean = MangaUtils.clean_title(search_term)
            search_words = search_normalized.split()
            self._search_cache[search_term] = (search_normalized, search_clean, search_words)
        
        # Cache filename normalization
        filename_key = f"filename_{hash(filename)}"
        if filename_key in self._title_cache:
            filename_normalized = self._title_cache[filename_key]
            self.stats['cache_hits'] += 1
        else:
            filename_normalized = MangaUtils.normalize_title(filename)
            self._title_cache[filename_key] = filename_normalized
        
        filename_clean = MangaUtils.clean_title(filename)
        
        # Fast matching logic
        if search_clean in filename_clean:
            return True
        
        if search_normalized in filename_normalized:
            return True
        
        # Word-based matching
        if len(search_words) > 1:
            words_found = sum(1 for word in search_words if len(word) > 2 and word in filename_normalized)
            if words_found / len(search_words) >= 0.7:
                return True
        
        return False
    
    async def download_file(self, file_info: FileInfo, custom_name: Optional[str] = None) -> Optional[str]:
        """Download a file with enhanced extraction support"""
        try:
            filename = custom_name or file_info.filename
            file_path = self.download_folder / filename
            
            # Handle file naming conflicts
            if file_path.exists():
                stem = file_path.stem
                suffix = file_path.suffix
                counter = 1
                while file_path.exists():
                    file_path = self.download_folder / f"{stem}_{counter}{suffix}"
                    counter += 1
            
            print(f"⬇️  Downloading: {filename}")
            print(f"   Size: {MangaUtils.format_size(file_info.size)}")
            
            # Download with progress
            def progress_callback(current, total):
                percent = (current / total) * 100
                print(f"\r   Progress: {percent:.1f}%", end='', flush=True)
            
            await self.client.download_media(
                file_info.message,
                file=str(file_path),
                progress_callback=progress_callback
            )
            
            print(f"\n✅ Downloaded: {file_path.name}")
            
            # Enhanced extraction support
            if not self.headless:
                await self._handle_extraction(file_path)
            
            return str(file_path)
            
        except Exception as e:
            print(f"❌ Error downloading file: {str(e)}")
            return None
    
    async def _handle_extraction(self, file_path: Path) -> None:
        """Handle extraction for various archive formats"""
        if file_path.suffix.lower() == '.zip':
            extract = input(f"📦 Extract ZIP file {file_path.name}? (y/n): ").lower().strip()
            if extract == 'y':
                await self._extract_zip(file_path)
        elif file_path.suffix.lower() == '.rar':
            extract = input(f"📦 Extract RAR file {file_path.name}? (y/n): ").lower().strip()
            if extract == 'y':
                await self._extract_rar(file_path)
        elif file_path.suffix.lower() == '.cbz':
            extract = input(f"📦 Extract CBZ file {file_path.name}? (y/n): ").lower().strip()
            if extract == 'y':
                await self._extract_zip(file_path)  # CBZ is basically ZIP
    
    async def _extract_zip(self, file_path: Path) -> None:
        """Extract ZIP/CBZ files"""
        try:
            extract_folder = file_path.parent / file_path.stem
            extract_folder.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_folder)
            
            print(f"📂 Extracted to: {extract_folder}")
            
            extracted_files = list(extract_folder.iterdir())
            print(f"   Extracted {len(extracted_files)} files")
            
            # Show first few files
            for i, file in enumerate(extracted_files[:5]):
                print(f"   - {file.name}")
            if len(extracted_files) > 5:
                print(f"   ... and {len(extracted_files) - 5} more files")
                
        except Exception as e:
            print(f"❌ Error extracting ZIP: {str(e)}")
    
    async def _extract_rar(self, file_path: Path) -> None:
        """Extract RAR files"""
        try:
            extract_folder = file_path.parent / file_path.stem
            extract_folder.mkdir(exist_ok=True)
            
            with rarfile.RarFile(file_path, 'r') as rar_ref:
                rar_ref.extractall(extract_folder)
            
            print(f"📂 Extracted to: {extract_folder}")
            
            extracted_files = list(extract_folder.iterdir())
            print(f"   Extracted {len(extracted_files)} files")
            
            # Show first few files
            for i, file in enumerate(extracted_files[:5]):
                print(f"   - {file.name}")
            if len(extracted_files) > 5:
                print(f"   ... and {len(extracted_files) - 5} more files")
                
        except Exception as e:
            print(f"❌ Error extracting RAR: {str(e)}")
    
    async def export_results(self, files: List[FileInfo], format_type: str = 'json', 
                           filename: Optional[str] = None) -> None:
        """Export search results to JSON or CSV"""
        if not files:
            print("❌ No files to export!")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not filename:
            filename = f"manga_search_results_{timestamp}.{format_type}"
        
        export_path = self.download_folder / filename
        
        try:
            if format_type.lower() == 'json':
                await self._export_json(files, export_path)
            elif format_type.lower() == 'csv':
                await self._export_csv(files, export_path)
            else:
                print(f"❌ Unsupported export format: {format_type}")
                return
            
            print(f"📊 Results exported to: {export_path}")
            
        except Exception as e:
            print(f"❌ Error exporting results: {str(e)}")
    
    async def _export_json(self, files: List[FileInfo], path: Path) -> None:
        """Export results to JSON"""
        data = {
            'search_info': {
                'total_files': len(files),
                'export_time': datetime.now().isoformat(),
                'stats': self.stats
            },
            'files': [
                {
                    'filename': file.filename,
                    'size': file.size,
                    'size_formatted': MangaUtils.format_size(file.size),
                    'mime_type': file.mime_type,
                    'date': file.date.isoformat(),
                    'message_id': file.message_id
                }
                for file in files
            ]
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    async def _export_csv(self, files: List[FileInfo], path: Path) -> None:
        """Export results to CSV"""
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Filename', 'Size', 'Size (Formatted)', 'MIME Type', 'Date', 'Message ID'])
            
            for file in files:
                writer.writerow([
                    file.filename,
                    file.size,
                    MangaUtils.format_size(file.size),
                    file.mime_type,
                    file.date.isoformat(),
                    file.message_id
                ])
    
    async def download_multiple(self, files: List[FileInfo], indices: Optional[List[int]] = None) -> List[str]:
        """Download multiple files with enhanced progress tracking"""
        if indices:
            files_to_download = [files[i] for i in indices if 0 <= i < len(files)]
        else:
            files_to_download = files
        
        print(f"📥 Starting download of {len(files_to_download)} files...")
        
        downloaded_files = []
        for i, file_info in enumerate(files_to_download, 1):
            print(f"\n[{i}/{len(files_to_download)}]")
            file_path = await self.download_file(file_info)
            if file_path:
                downloaded_files.append(file_path)
        
        print(f"\n🎉 Download complete! Downloaded {len(downloaded_files)} files to '{self.download_folder}'")
        return downloaded_files
    
    def display_files(self, files: List[FileInfo]) -> None:
        """Display found files with enhanced formatting"""
        if not files:
            print("❌ No files found!")
            return
        
        print(f"\n📋 Found {len(files)} files:")
        print("-" * 100)
        
        for i, file_info in enumerate(files):
            print(f"{i+1:3d}. {file_info.filename}")
            print(f"     Size: {MangaUtils.format_size(file_info.size)}")
            print(f"     Type: {file_info.mime_type}")
            print(f"     Date: {file_info.date.strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 100)
    
    async def interactive_menu(self) -> None:
        """Interactive menu with enhanced options"""
        print("🎌 Enhanced Manga Grabber for Telegram")
        print("=" * 60)
        print("📦 Multi-format support: ZIP, RAR, CBZ files")
        print("🔍 Supports various naming patterns:")
        print("   - #Manga_Title_Name")
        print("   - Manga Title Name")
        print("   - Manga Title {Episode} [Group]")
        print("⚡ Enhanced performance with caching")
        print("📊 Export results to JSON/CSV")
        
        while True:
            print("\n📋 Main Menu:")
            print("1. Search manga files in a chat/channel")
            print("2. View performance statistics")
            print("3. Clear cache")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                await self.search_and_download_flow()
            elif choice == '2':
                self.display_stats()
            elif choice == '3':
                self.clear_cache()
            elif choice == '4':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please try again.")
    
    async def search_and_download_flow(self) -> None:
        """Enhanced search and download flow"""
        # Get chat/channel
        chat = input("\n📱 Enter chat/channel username (with @): ").strip()
        if not chat.startswith('@'):
            chat = '@' + chat
        
        # Get search term
        print("\n🔍 Enter manga title to search for:")
        print("   Examples:")
        print("   - The God of High School")
        print("   - God High School")
        print("   - #The_God_Of_High_School")
        search_term = input("   Search term: ").strip()
        if not search_term:
            print("❌ Search term cannot be empty!")
            return
        
        # Clear cache for new search
        self.clear_cache()
        
        print("🔍 Unlimited search enabled: Searching all available messages")
        print("⚡ Enhanced mode: ZIP, RAR, CBZ support with caching")
        
        # Search for files
        print(f"\n🔍 Searching for archive files matching '{search_term}' in {chat}...")
        files = await self.search_files(chat, search_term, None)
        
        if not files:
            print("❌ No files found!")
            print("\n💡 Tips:")
            print("   - Try using fewer words from the title")
            print("   - Try removing special characters")
            print("   - Check if the channel has the manga you're looking for")
            return
        
        # Display found files
        self.display_files(files)
        
        # Enhanced options
        print("\n📥 Options:")
        print("1. Download all files")
        print("2. Download specific files")
        print("3. Export results to JSON")
        print("4. Export results to CSV")
        print("5. Back to main menu")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            await self.download_multiple(files)
        elif choice == '2':
            indices_input = input("Enter file numbers to download (e.g., 1,3,5): ").strip()
            try:
                indices = [int(x.strip()) - 1 for x in indices_input.split(',')]
                await self.download_multiple(files, indices)
            except ValueError:
                print("❌ Invalid file numbers!")
        elif choice == '3':
            await self.export_results(files, 'json')
        elif choice == '4':
            await self.export_results(files, 'csv')
        elif choice == '5':
            return
        else:
            print("❌ Invalid choice!")
    
    def display_stats(self) -> None:
        """Display performance statistics"""
        print("\n📊 Performance Statistics:")
        print("-" * 40)
        print(f"Messages scanned: {self.stats['messages_scanned']}")
        print(f"Files found: {self.stats['files_found']}")
        print(f"Search time: {self.stats['search_time']:.2f}s")
        print(f"Cache hits: {self.stats['cache_hits']}")
        print(f"Cache size: {len(self._title_cache)} title entries")
        print(f"Search cache: {len(self._search_cache)} search entries")
    
    def clear_cache(self) -> None:
        """Clear all caches"""
        self._title_cache.clear()
        self._search_cache.clear()
        print("🧹 Cache cleared!")
    
    async def close(self) -> None:
        """Close the client"""
        await self.client.disconnect()
        print("👋 Disconnected from Telegram")

# CLI argument parsing
def parse_args():
    parser = argparse.ArgumentParser(description='Enhanced Manga Grabber for Telegram')
    parser.add_argument('--api-id', type=int, help='Telegram API ID')
    parser.add_argument('--api-hash', help='Telegram API Hash')
    parser.add_argument('--phone', help='Phone number')
    parser.add_argument('--channel', help='Channel username')
    parser.add_argument('--search', help='Search term')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--export', choices=['json', 'csv'], help='Export format')
    parser.add_argument('--config', help='Config file path')
    parser.add_argument('--session', help='Custom session name')
    return parser.parse_args()

async def main():
    args = parse_args()
    
    # Load configuration
    config_file = args.config or 'telegram_config.json'
    config = {}
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        if not args.headless:
            print("✅ Using saved configuration")
    
    # Get credentials
    api_id = args.api_id or config.get('api_id')
    api_hash = args.api_hash or config.get('api_hash')
    phone_number = args.phone or config.get('phone_number')
    
    if not all([api_id, api_hash, phone_number]):
        if args.headless:
            print("❌ Missing required credentials for headless mode")
            return
        
        print("🔐 Telegram API Configuration")
        print("Get your API credentials from: https://my.telegram.org/apps")
        print("-" * 60)
        
        api_id = int(input("Enter your API ID: "))
        api_hash = input("Enter your API Hash: ")
        phone_number = input("Enter your phone number (with country code): ")
        
        # Save config
        config = {
            'api_id': api_id,
            'api_hash': api_hash,
            'phone_number': phone_number
        }
        
        save_config = input("Save configuration? (y/n): ").lower().strip()
        if save_config == 'y':
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print("✅ Configuration saved!")
    
    # Create and start grabber
    grabber = MangaGrabberEnhanced(
        api_id=api_id,
        api_hash=api_hash,
        phone_number=phone_number,
        session_name=args.session,
        headless=args.headless
    )
    
    try:
        await grabber.start()
        
        # Headless mode
        if args.headless and args.channel and args.search:
            print(f"🤖 Running in headless mode")
            files = await grabber.search_files(args.channel, args.search)
            
            if files:
                print(f"Found {len(files)} files")
                
                if args.export:
                    await grabber.export_results(files, args.export)
                else:
                    grabber.display_files(files)
            else:
                print("No files found")
        else:
            await grabber.interactive_menu()
            
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await grabber.close()

if __name__ == "__main__":
    asyncio.run(main())
