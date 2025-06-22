import os
from PyInstaller.utils.hooks import collect_all, collect_submodules
from PyInstaller.building.build_main import Analysis
from PyInstaller.building.api import EXE, COLLECT
from PyInstaller.building.api import PYZ
import sys

block_cipher = None

# Get the current directory
current_dir = os.path.abspath(os.getcwd())

# Collect all package data
bins = []
datas = []
hiddenimports = []

# Collect Eel package data
tmp_ret = collect_all('eel')
bins.extend(tmp_ret[0])
datas.extend(tmp_ret[1])
hiddenimports.extend(tmp_ret[2])

# Collect APScheduler package data
tmp_ret = collect_all('apscheduler')
bins.extend(tmp_ret[0])
datas.extend(tmp_ret[1])
hiddenimports.extend(tmp_ret[2])

### Web directroy must exist
web_dir = os.path.join(current_dir, 'web')
if not os.path.exists(web_dir):
    raise Exception(f"Web directory not found: {web_dir}")
datas.append(('web', 'web'))

# ✅ REPLACE: Die automatische Collection durch manuelle ersetzen
try:
    # Versuche zuerst automatische Collection
    crawler_submodules = collect_submodules('crawler')
    if len(crawler_submodules) > 0:
        hiddenimports.extend(crawler_submodules)
        print(f"✅ Auto-collected {len(crawler_submodules)} crawler modules")
    else:
        raise Exception("Auto-collection returned 0 modules")
        
except Exception as e:
    print(f"⚠️  Auto-collection failed: {e}")
    print("📝 Using manual module collection...")
    
    # ✅ MANUAL: Alle Module explizit sammeln
    manual_modules = [
        'crawler',
        'crawler.base_crawler',
        'crawler.url_mapping',
        'crawler.crawlMethods',
    ]
    
    # ✅ Alle .py Files in crawlMethods/ hinzufügen
    crawl_methods_dir = os.path.join(current_dir, 'crawler', 'crawlMethods')
    if os.path.exists(crawl_methods_dir):
        for file in os.listdir(crawl_methods_dir):
            if file.endswith('.py') and file != '__init__.py':
                module_name = f'crawler.crawlMethods.{file[:-3]}'
                manual_modules.append(module_name)
                print(f"  Adding: {module_name}")
    
    hiddenimports.extend(manual_modules)
    print(f"✅ Manual collection: {len(manual_modules)} modules")

### Only inclued files that exists
def add_if_exists(filename, target="."):
    filepath = os.path.join(current_dir, filename)
    if os.path.exists(filepath):
        datas.append((filename, target))
    else:
        print(f"File not found: {filename}")

# Add your web files and other resources
resource_files = [
    'image.ico',
    'localities_data.py',
    'database.py',
    'email_notification.py',
    'gui.py',
    'schedule.py',
    'startup_utils.py',
    'version_info_file.txt',
    '.env',
    'image.png',
    'requirements.txt',
    'database_config.py',
    'env_utils.py',
    'version.py',
    'updater.py'
]

for file in resource_files:
    if os.path.exists(os.path.join(current_dir, file)):
        print(f"Adding resource file: {file}")
        datas.append((file, '.'))
    else:
        print(f"WARNING: Optional resource file not found: {file}")


# Add all required hidden imports
hiddenimports.extend([
    'bottle_websocket',
    'engineio.async_drivers.threading',
    'win32timezone',
    'pytz',
    'sqlite3',
    'apscheduler.triggers.cron',
    'logging',
    'win32serviceutil',
    'win32service',
    'servicemanager',
    'requests',
    'bs4',
    'lxml',
    'gevent',
    'gevent_websocket',
    'PIL',
    'pystray',
    'dotenv',
    'zope.event',
    'zope.interface',
    'win32api',
    'win32con',
    'engineio.async_drivers.threading',
    'apscheduler.schedulers.background',
    'apscheduler.executors.pool',
    'engineio',
    'engineio.async_drivers',
    'engineio.async_drivers.threading',
    'bottle',
    'python3',
])

for pkg in ['gevent', 'engineio', 'bottle_websocket']:
    tmp_ret = collect_all(pkg)
    bins.extend(tmp_ret[0])
    datas.extend(tmp_ret[1])
    hiddenimports.extend(tmp_ret[2])
    

a = Analysis(
    ['main.py'],
    pathex=[current_dir],
    binaries=bins,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

print("\nCollected data files")
for src, dst, typecode in a.datas:
    print(f"  {src} -> {dst}") 

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='JobCrawler',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='image.ico', 
    version='version_info_file.txt'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JobCrawler'
)