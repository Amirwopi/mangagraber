import re
from functools import lru_cache
from typing import List, Optional

class MangaUtils:
    """Utility class for manga title processing and file operations"""
    
    @staticmethod
    @lru_cache(maxsize=1000)
    def clean_title(title: str) -> str:
        """Clean title for better matching with caching"""
        # Remove common patterns and normalize
        title = title.lower()
        title = re.sub(r'[\[\]{}()"\'`]', '', title)  # Remove brackets and quotes
        title = re.sub(r'\s+', ' ', title)  # Normalize whitespace
        title = title.strip()
        return title
    
    @staticmethod
    @lru_cache(maxsize=1000)
    def normalize_title(title: str) -> str:
        """Normalize title by converting hashtag/underscore format to regular format"""
        # Convert title to lowercase
        title = title.lower()
        
        # Remove hashtag if present
        if title.startswith('#'):
            title = title[1:]
        
        # Replace underscores with spaces
        title = title.replace('_', ' ')
        
        # Replace multiple separators with single space
        title = re.sub(r'[-\s]+', ' ', title)
        
        # Remove brackets, parentheses, and their contents for better matching
        title = re.sub(r'\{[^}]*\}', '', title)  # Remove {content}
        title = re.sub(r'\[[^\]]*\]', '', title)  # Remove [content]
        title = re.sub(r'\([^)]*\)', '', title)  # Remove (content)
        
        # Remove common anime/manga terms that might interfere
        title = re.sub(r'\b(chapters?|episodes?|vol|volume|ch|ep)\b', '', title)
        
        # Clean up extra spaces
        title = re.sub(r'\s+', ' ', title)
        title = title.strip()
        
        return title
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.2f}{size_names[i]}"
    
    @staticmethod
    def extract_chapter_number(filename: str) -> Optional[int]:
        """Extract chapter number from filename"""
        # Common patterns for chapter numbers
        patterns = [
            r'chapter\s*(\d+)',
            r'ch\s*(\d+)',
            r'c(\d+)',
            r'(\d+)\s*\[',
            r'(\d+)\s*\(',
            r'(\d+)\s*\.zip',
            r'(\d+)\s*\.rar',
            r'(\d+)\s*\.cbz',
            r'-\s*(\d+)\s*\[',
            r'\s(\d+)\s*\[',
        ]
        
        filename_lower = filename.lower()
        for pattern in patterns:
            match = re.search(pattern, filename_lower)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    @staticmethod
    def extract_volume_number(filename: str) -> Optional[int]:
        """Extract volume number from filename"""
        patterns = [
            r'volume\s*(\d+)',
            r'vol\s*(\d+)',
            r'v(\d+)',
        ]
        
        filename_lower = filename.lower()
        for pattern in patterns:
            match = re.search(pattern, filename_lower)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    @staticmethod
    def is_manga_file(filename: str) -> bool:
        """Check if filename looks like a manga file"""
        filename_lower = filename.lower()
        
        # Check for common manga file extensions
        manga_extensions = ['.zip', '.rar', '.cbz', '.cbr', '.7z']
        if not any(filename_lower.endswith(ext) for ext in manga_extensions):
            return False
        
        # Check for common manga keywords
        manga_keywords = [
            'chapter', 'ch', 'vol', 'volume', 'manga', 'comic',
            'scan', 'raw', 'translated', 'english', 'jp', 'jpn'
        ]
        
        return any(keyword in filename_lower for keyword in manga_keywords)
    
    @staticmethod
    def get_series_name(filename: str) -> str:
        """Extract series name from filename"""
        # Remove file extension
        name = filename.rsplit('.', 1)[0]
        
        # Remove common patterns
        name = re.sub(r'\s*\[.*?\]', '', name)  # Remove [group] tags
        name = re.sub(r'\s*\(.*?\)', '', name)  # Remove (info) tags
        name = re.sub(r'\s*\{.*?\}', '', name)  # Remove {info} tags
        name = re.sub(r'\s*-\s*\d+.*', '', name)  # Remove chapter numbers
        name = re.sub(r'\s*ch\s*\d+.*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*chapter\s*\d+.*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*vol\s*\d+.*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*volume\s*\d+.*', '', name, flags=re.IGNORECASE)
        
        # Clean up
        name = re.sub(r'\s+', ' ', name)
        name = name.strip()
        
        return name
    
    @staticmethod
    def generate_search_variants(title: str) -> List[str]:
        """Generate search variants for a title"""
        variants = [title]
        
        # Add normalized version
        normalized = MangaUtils.normalize_title(title)
        if normalized != title:
            variants.append(normalized)
        
        # Add hashtag version
        if not title.startswith('#'):
            hashtag_version = '#' + title.replace(' ', '_')
            variants.append(hashtag_version)
        
        # Add underscore version
        underscore_version = title.replace(' ', '_')
        if underscore_version != title:
            variants.append(underscore_version)
        
        # Add abbreviated version (first letters)
        words = title.split()
        if len(words) > 1:
            abbreviated = ''.join(word[0].upper() for word in words if word)
            variants.append(abbreviated)
        
        return list(set(variants))  # Remove duplicates
    
    @staticmethod
    def sort_by_chapter(files: List, key_func=lambda x: x.filename) -> List:
        """Sort files by chapter number"""
        def get_sort_key(file):
            filename = key_func(file)
            chapter = MangaUtils.extract_chapter_number(filename)
            return (chapter if chapter is not None else 999999, filename)
        
        return sorted(files, key=get_sort_key)
    
    @staticmethod
    def group_by_series(files: List, key_func=lambda x: x.filename) -> dict:
        """Group files by series name"""
        series_dict = {}
        
        for file in files:
            filename = key_func(file)
            series_name = MangaUtils.get_series_name(filename)
            
            if series_name not in series_dict:
                series_dict[series_name] = []
            
            series_dict[series_name].append(file)
        
        return series_dict
    
    @staticmethod
    def validate_archive(filepath: str) -> bool:
        """Validate if file is a proper archive"""
        try:
            if filepath.lower().endswith('.zip'):
                import zipfile
                with zipfile.ZipFile(filepath, 'r') as zf:
                    return zf.testzip() is None
            elif filepath.lower().endswith('.rar'):
                import rarfile
                with rarfile.RarFile(filepath, 'r') as rf:
                    return rf.testrar() is None
            elif filepath.lower().endswith('.cbz'):
                import zipfile
                with zipfile.ZipFile(filepath, 'r') as zf:
                    return zf.testzip() is None
            else:
                return False
        except Exception:
            return False
    
    @staticmethod
    def get_archive_info(filepath: str) -> dict:
        """Get information about an archive file"""
        info = {
            'valid': False,
            'file_count': 0,
            'total_size': 0,
            'compression_ratio': 0.0,
            'files': []
        }
        
        try:
            if filepath.lower().endswith(('.zip', '.cbz')):
                import zipfile
                with zipfile.ZipFile(filepath, 'r') as zf:
                    info['valid'] = zf.testzip() is None
                    info['files'] = zf.namelist()
                    info['file_count'] = len(info['files'])
                    
                    for file_info in zf.infolist():
                        info['total_size'] += file_info.file_size
                    
                    # Calculate compression ratio
                    compressed_size = sum(file_info.compress_size for file_info in zf.infolist())
                    if info['total_size'] > 0:
                        info['compression_ratio'] = (info['total_size'] - compressed_size) / info['total_size'] * 100
                        
            elif filepath.lower().endswith('.rar'):
                import rarfile
                with rarfile.RarFile(filepath, 'r') as rf:
                    info['valid'] = rf.testrar() is None
                    info['files'] = rf.namelist()
                    info['file_count'] = len(info['files'])
                    
                    for file_info in rf.infolist():
                        info['total_size'] += file_info.file_size
                    
                    # Calculate compression ratio
                    compressed_size = sum(file_info.compress_size for file_info in rf.infolist())
                    if info['total_size'] > 0:
                        info['compression_ratio'] = (info['total_size'] - compressed_size) / info['total_size'] * 100
                        
        except Exception as e:
            info['error'] = str(e)
        
        return info
