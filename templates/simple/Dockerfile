FROM waggle/plugin-base:0.1.0

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python3", "plugin.py"]
