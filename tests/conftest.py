import pytest
import tkinter as tk
import tempfile
import os
import shutil
from storage import Storage


@pytest.fixture(scope='module')
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


@pytest.fixture(scope='function')
def temp_storage():
    """为每个测试创建临时存储，避免影响用户数据"""
    import tempfile
    import os
    import shutil
    
    # 创建临时DB文件
    temp_dir = tempfile.mkdtemp()
    temp_db_file = os.path.join(temp_dir, 'test_data.db')
    
    # 创建临时Storage实例
    storage = Storage(temp_db_file)
    
    yield storage
    
    # 清理临时目录
    shutil.rmtree(temp_dir, ignore_errors=True)
