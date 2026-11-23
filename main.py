import os
import shutil


output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
os.makedirs(output_dir, exist_ok=True)
src = os.path.join(os.path.dirname(__file__), "entry.png")
dst = os.path.join(output_dir, "entry.png")
if not os.path.exists(src):
    raise FileNotFoundError(src)
shutil.copy2(src, dst)
print(dst)
